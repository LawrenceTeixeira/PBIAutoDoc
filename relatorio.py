import msal
import requests
import pandas as pd
import time
from zipfile import ZipFile, BadZipFile
import io, json

def get_token(APP_ID, TENANT_ID, SECRET_VALUE):
    """Obtém o token de autenticação da Microsoft para acessar a API do Power BI."""
    authority = f"https://login.microsoftonline.com/{TENANT_ID}"
    scopes = ["https://analysis.windows.net/powerbi/api/.default"]

    app = msal.ConfidentialClientApplication(APP_ID, authority=authority, client_credential=SECRET_VALUE)
    result = app.acquire_token_for_client(scopes=scopes)
    access_token = result["access_token"]

    headers = {
        'Authorization': f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    return headers

def get_workspaces_id(headers):
    """Obtém os IDs e nomes das workspaces do Power BI."""
    retries = 5
    workspaces_url = 'https://api.powerbi.com/v1.0/myorg/admin/groups?$top=100'

    for i in range(retries):
        response_workspaces = requests.get(url=workspaces_url, headers=headers)
        if response_workspaces.status_code == 200:
            workspaces = response_workspaces.json().get('value', [])
            workspace_dict = {workspace['name']: workspace['id'] for workspace in workspaces}
            return workspace_dict
        elif response_workspaces.status_code == 429:
            time.sleep(2 ** i)
        else:
            break
    return None

def scan_workspace(headers, workspace_id):
    """Escaneia a workspace selecionada e recupera suas informações."""
    url = 'https://api.powerbi.com/v1.0/myorg/admin/workspaces/getInfo?datasetSchema=True&datasetExpressions=True'
    body = {"workspaces": [f'{workspace_id}']}

    response = requests.post(url=url, headers=headers, json=body)
    scanId = response.json()['id']
        
    time.sleep(5)  # Aguarda a finalização do escaneamento
    
    scan_url = f'https://api.powerbi.com/v1.0/myorg/admin/workspaces/scanResult/{scanId}'

    scan_response = requests.get(url=scan_url, headers=headers)
    reports = scan_response.json()['workspaces'][0]
    
    return reports

def clean_reports(reports, option):
    """Limpa o JSON recebido da API da Microsoft e armazena em um DataFrame do Pandas."""
    df_workspaces = pd.json_normalize(reports).explode('datasets', ignore_index=True)

    # Filtrando e tratando o dataset principal
    df_normalized = pd.json_normalize(df_workspaces['datasets'])
    df_normalized = df_normalized.query(f"name == '{option}'")

    # Verificando se a coluna 'expressions' existe antes de tentar acessá-la
    expected_columns = ['id', 'name', 'configuredBy', 'createdDate', 'tables']
    if 'expressions' in df_normalized.columns:
        expected_columns.append('expressions')

    df_normalized = df_normalized[expected_columns].copy()
    df_normalized.rename(columns={'id': 'DatasetId', 'name': 'ReportName'}, inplace=True)
    datasets_exploded = df_normalized.explode('tables', ignore_index=True)

    # Normalizando e tratando a tabela de 'tables'
    tables_normalized = pd.concat([datasets_exploded[['DatasetId', 'ReportName', 'configuredBy']], pd.json_normalize(datasets_exploded['tables'])], axis=1)
    tables_normalized.rename(columns={'name': 'NomeTabela'}, inplace=True)
    
    if 'source' in tables_normalized.columns:
        tables_normalized['source'] = tables_normalized['source'].apply(lambda x: x[0]['expression'] if isinstance(x, list) and len(x) > 0 else None)
    else:
        tables_normalized['source'] = None
    
    if 'storageMode' not in tables_normalized.columns:
        tables_normalized['storageMode'] = None

    # Criando e tratando a tabela de medidas, verificando se a coluna 'measures' existe
    if 'measures' in tables_normalized.columns:
        measures_normalized = tables_normalized.explode('measures', ignore_index=True)
        measures_normalized = pd.concat([measures_normalized[['NomeTabela']], pd.json_normalize(measures_normalized['measures'])], axis=1)
        measures_normalized['name'] = measures_normalized.get('name', 'N/A')
        measures_normalized['expression'] = measures_normalized.get('expression', 'N/A')
        measures_normalized = measures_normalized[['NomeTabela', 'name', 'expression']]
        measures_normalized.rename(columns={'name': 'NomeMedida', 'expression': 'ExpressaoMedida'}, inplace=True)
    else:
        measures_normalized = pd.DataFrame(columns=['NomeTabela', 'NomeMedida', 'ExpressaoMedida'])

    # Criando e tratando a tabela de colunas, verificando se a coluna 'columns' existe
    if 'columns' in tables_normalized.columns:
        columns_normalized = tables_normalized.explode('columns', ignore_index=True)
        columns_normalized = pd.concat([columns_normalized[['NomeTabela']], pd.json_normalize(columns_normalized['columns'])], axis=1)
        
        # Verificando se as colunas existem antes de acessá-las
        if 'expression' in columns_normalized.columns:
            columns_normalized['expression'] = columns_normalized['expression'].fillna('N/A')
        else:
            columns_normalized['expression'] = 'N/A'
        
        columns_normalized = columns_normalized[['NomeTabela', 'name', 'dataType', 'columnType', 'expression']]
        columns_normalized.rename(columns={'name': 'NomeColuna', 'dataType': 'TipoDadoColuna', 'columnType': 'TipoColuna', 'expression': 'ExpressaoColuna'}, inplace=True)
    else:
        columns_normalized = pd.DataFrame(columns=['NomeTabela', 'NomeColuna', 'TipoDadoColuna', 'TipoColuna', 'ExpressaoColuna'])

    # Verificando se a coluna 'NomeTabela' existe antes de continuar
    if 'NomeTabela' in tables_normalized.columns:
        tables_normalized = tables_normalized[['DatasetId', 'ReportName', 'NomeTabela', 'storageMode', 'source', 'configuredBy']]
        tables_normalized.rename(columns={'source': 'FonteDados'}, inplace=True)
        dataset_desnormalized = tables_normalized.merge(measures_normalized, on='NomeTabela', how='left')
        dataset_desnormalized = dataset_desnormalized.merge(columns_normalized, on='NomeTabela', how='left')
    else:
        dataset_desnormalized = pd.DataFrame(columns=['DatasetId', 'ReportName', 'NomeTabela', 'storageMode', 'FonteDados', 'configuredBy', 'NomeMedida', 'ExpressaoMedida', 'NomeColuna', 'TipoDadoColuna', 'TipoColuna', 'ExpressaoColuna'])

    return dataset_desnormalized

def extract_relationships(json_data):
    relationships = json_data['model'].get('relationships', [])
    
    relationship_info = []
    
    for rel in relationships:
        relationship_info.append({
            'Name': rel.get('name', ''),
            'FromTable': rel.get('fromTable', ''),
            'FromColumn': rel.get('fromColumn', ''),
            'ToTable': rel.get('toTable', ''),
            'ToColumn': rel.get('toColumn', '')
        })
    
    return relationship_info

def upload_file(uploaded_file):
    """Processa o upload do arquivo .pbit ou .zip e extrai os dados relevantes."""
    # Aceita .pbit ou .zip
    if not uploaded_file.name.endswith(('.pbit', '.zip')):
        return 'Arquivo não suportado'

    datasetid_content = None
    reportid_content = None
    reportname_content = uploaded_file.name.rsplit('.', 1)[0]
    content = {}  # <- IMPORTANT: inicializar para evitar UnboundLocalError

    # Garantir um buffer "seekable"
    buf = io.BytesIO(uploaded_file.read())

    try:
        with ZipFile(buf, 'r') as zipf:
            members = set(zipf.namelist())

            # alguns pacotes trazem subpastas; casamos pelo sufixo
            def open_member(name):
                for m in members:
                    if m.endswith(name):
                        return zipf.open(m)
                return None

            # Connections (UTF-8)
            f = open_member('Connections')
            if f is not None:
                connections_content = json.loads(f.read().decode('utf-8'))
                ra = (connections_content.get('RemoteArtifacts') or [{}])[0]
                datasetid_content = ra.get('DatasetId')
                reportid_content  = ra.get('ReportId')

            # DataModelSchema (UTF-16 LE)
            f = open_member('DataModelSchema')
            if f is None:
                return "Arquivo inválido: não contém 'DataModelSchema'."
            raw = f.read()
            try:
                content = json.loads(raw.decode('utf-16-le'))
            except Exception as e:
                return f"Falha ao ler DataModelSchema (UTF-16-LE): {e}"

    except BadZipFile:
        return 'Arquivo inválido: não é um ZIP/PBIT válido.'
    except Exception as e:
        return f'Falha ao abrir o arquivo: {e}'

    # --------- Extração dos dados ---------
    df_columns = pd.DataFrame()
    df_tables  = pd.DataFrame()
    measure_names, measure_expression, tables_names = [], [], []

    model = content.get('model', {})
    for rows in model.get('tables', []):
        # pular tabelas de data geradas automaticamente
        if 'DateTable' in rows.get('name', ''):
            continue

        # Medidas
        for m in rows.get('measures', []):
            folder = m.get('displayFolder')
            full_name = f"{folder} / {m.get('name')}" if folder else m.get('name')
            expr = m.get('expression', 'N/A')
            if isinstance(expr, list):
                expr = ''.join(expr)
            tables_names.append(rows.get('name'))
            measure_names.append(full_name)
            measure_expression.append(expr)

        # Colunas
        for c in rows.get('columns', []):
            col_data = pd.DataFrame([{
                'NomeTabela': rows.get('name'),
                'NomeColuna': c.get('name'),
                'TipoDadoColuna': c.get('dataType', 'N/A'),
                'TipoColuna': c.get('type', 'N/A'),
                'ExpressaoColuna': c.get('expression', 'N/A')
            }])
            df_columns = pd.concat([df_columns, col_data], ignore_index=True)

        # Fonte (M code) da primeira partição, se existir
        part = (rows.get('partitions') or [{}])[0]
        src = part.get('source', {})
        mcode = src.get('expression', 'N/A')
        if isinstance(mcode, list):
            mcode = ''.join(mcode)

        df_tables_rows = pd.DataFrame([{
            'DatasetId': datasetid_content or '0',
            'ReportId':  reportid_content,
            'ReportName': reportname_content or 'PBIReport',
            'NomeTabela': rows.get('name'),
            'FonteDados': mcode
        }])
        df_tables = pd.concat([df_tables, df_tables_rows], ignore_index=True)

    # Normalizações finais
    df_columns['ExpressaoColuna'] = df_columns['ExpressaoColuna'].apply(
        lambda v: ''.join(v) if isinstance(v, list) else v
    )

    df_measures = pd.DataFrame({
        'NomeTabela': tables_names,
        'NomeMedida': measure_names,
        'ExpressaoMedida': measure_expression
    })

    # Relacionamentos (se existirem)
    rels = []
    for r in model.get('relationships', []):
        rels.append({
            'FromTable': r.get('fromTable'),
            'FromColumn': r.get('fromColumn'),
            'ToTable': r.get('toTable'),
            'ToColumn': r.get('toColumn'),
            'Cardinality': r.get('cardinality')
        })
    df_relationships = pd.DataFrame(rels)

    df_normalized = pd.merge(
        pd.merge(df_tables, df_measures, on='NomeTabela', how='left'),
        df_columns, on='NomeTabela', how='left'
    )

    return df_normalized, df_relationships
