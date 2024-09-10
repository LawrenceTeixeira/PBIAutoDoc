import msal
import requests
import pandas as pd
import time
from zipfile import ZipFile
import json

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


def upload_file(uploaded_files):
    """Processa o upload do arquivo .pbit ou .zip e extrai os dados relevantes."""

    datasetid_content = None  # Initialize with a default value
    reportid_content = None
    reportname_content = None

    if uploaded_files.name.endswith('.pbit') or uploaded_files.name.endswith('.zip'):
        if uploaded_files.name.endswith('.pbit'):
            uploaded_files.name = uploaded_files.name[:-5] + '.zip'
            
        with ZipFile(uploaded_files, 'r') as zipf:
            zipf.extractall('temp')
            file_list = zipf.namelist()
            
            for file_name in file_list:
                with zipf.open(file_name) as extracted_file:
                    if file_name == 'Connections':
                        connections_content = extracted_file.read().decode("utf-8")
                        connections_content = json.loads(connections_content)
                        
                        datasetid_content = connections_content['RemoteArtifacts'][0]['DatasetId']
                        reportid_content = connections_content['RemoteArtifacts'][0]['ReportId']
                        reportname_content = uploaded_files.name[:-4]
                    
                    if file_name == 'DataModelSchema':
                        content = extracted_file.read().decode("utf-16-le")
                        content = json.loads(content)
                        
        df_columns, df_tables = pd.DataFrame(), pd.DataFrame()
        
        measure_names, measure_expression, tables_names = [], [], []
        
        if 'model' in content and 'tables' in content['model']:
            tables = content['model']['tables']            
            for rows in tables:
                if 'DateTable' not in rows['name']:
                    if 'measures' in rows:
                        for measures in rows['measures']:
                            # Verificando se a medida está dentro de uma pasta
                            folder_name = measures.get('displayFolder', None)
                            if folder_name:
                                full_measure_name = f"{folder_name} / {measures['name']}"
                            else:
                                full_measure_name = measures['name']
                            
                            tables_names.append(rows['name'])
                            measure_names.append(full_measure_name)
                            expression = measures.get('expression', 'N/A')
                            measure_expression.append("".join(expression) if isinstance(expression, list) else expression)

                    if 'columns' in rows:
                        for cols in rows['columns']:
                            col_data = pd.DataFrame([{
                                'NomeTabela': rows['name'],
                                'NomeColuna': cols['name'],
                                'TipoDadoColuna': cols.get('dataType', 'N/A'),
                                'TipoColuna': cols.get('type', 'N/A'),
                                'ExpressaoColuna': cols.get('expression', 'N/A')
                            }])

                            df_columns = pd.concat([df_columns, col_data], ignore_index=True)

                    mcode = [''.join(rows['partitions'][0]['source']['expression'])]
                    
                    if datasetid_content is not None:
                        df_tables_rows = pd.DataFrame([{
                            'DatasetId': datasetid_content,
                            'ReportId': reportid_content,
                            'ReportName': reportname_content,
                            'NomeTabela': rows['name'], 
                            'FonteDados': mcode[0]
                        }])
                        print(df_tables_rows)
                    else:
                        df_tables_rows = pd.DataFrame([{
                            'DatasetId': '0',
                            'ReportId': reportid_content,
                            'ReportName': 'PBIReport',
                            'NomeTabela': rows['name'], 
                            'FonteDados': mcode[0]
                        }])

                    df_tables = pd.concat([df_tables, df_tables_rows], ignore_index=True)

        df_columns['ExpressaoColuna'] = df_columns['ExpressaoColuna'].apply(lambda l: "".join(l) if isinstance(l, list) else l)
        
        df_measures = pd.DataFrame({
            'NomeTabela': tables_names,
            'NomeMedida': measure_names,
            'ExpressaoMedida': measure_expression
        })

        # Debugging output to inspect data
        print("Measures DataFrame:", df_measures)

        df_normalized = pd.merge(pd.merge(df_tables, df_measures, left_on='NomeTabela', right_on='NomeTabela', how='left'), df_columns, right_on='NomeTabela', left_on='NomeTabela', how='left')
        
        return df_normalized
    else:
        return 'Arquivo não suportado'
