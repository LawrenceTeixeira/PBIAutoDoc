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
    df_normalized = df_normalized[['id', 'name', 'configuredBy', 'createdDate', 'tables', 'expressions']].copy()
    df_normalized.rename(columns={'id': 'DatasetId', 'name': 'ReportName'}, inplace=True)
    datasets_exploded = df_normalized.explode('tables', ignore_index=True)

    # Normalizando e tratando a tabela de 'tables'
    tables_normalized = pd.concat([datasets_exploded[['DatasetId', 'ReportName', 'configuredBy']], pd.json_normalize(datasets_exploded['tables'])], axis=1)
    tables_normalized.rename(columns={'name': 'NomeTabela'}, inplace=True)
    tables_normalized['source'] = tables_normalized['source'].apply(lambda x: x[0]['expression'] if isinstance(x, list) and len(x) > 0 else None)
    if 'storageMode' not in tables_normalized.columns:
        tables_normalized['storageMode'] = None

    # Criando e tratando a tabela de medidas
    measures_normalized = tables_normalized.explode('measures', ignore_index=True)
    measures_normalized = pd.concat([measures_normalized[['NomeTabela']], pd.json_normalize(measures_normalized['measures'])], axis=1)
    measures_normalized['name'] = measures_normalized.get('name', 'N/A')
    measures_normalized['expression'] = measures_normalized.get('expression', 'N/A')
    measures_normalized = measures_normalized[['NomeTabela', 'name', 'expression']]
    measures_normalized.rename(columns={'name': 'NomeMedida', 'expression': 'ExpressaoMedida'}, inplace=True)

    # Criando e tratando a tabela de colunas
    columns_normalized = tables_normalized.explode('columns', ignore_index=True)
    columns_normalized = pd.concat([columns_normalized[['NomeTabela']], pd.json_normalize(columns_normalized['columns'])], axis=1)
    columns_normalized = columns_normalized[['NomeTabela', 'name', 'dataType', 'columnType', 'expression']]
    columns_normalized['expression'] = columns_normalized.get('expression', 'N/A')
    columns_normalized.rename(columns={'name': 'NomeColuna', 'dataType': 'TipoDadoColuna', 'columnType': 'TipoColuna', 'expression': 'ExpressaoColuna'}, inplace=True)

    tables_normalized = tables_normalized[['DatasetId', 'ReportName', 'NomeTabela', 'storageMode', 'source', 'configuredBy']]
    tables_normalized.rename(columns={'source': 'FonteDados'}, inplace=True)
    dataset_desnormalized = tables_normalized.merge(measures_normalized, on='NomeTabela', how='left')
    dataset_desnormalized = dataset_desnormalized.merge(columns_normalized, on='NomeTabela', how='left')

    return dataset_desnormalized

def upload_file(uploaded_files):
    """Processa o upload do arquivo .pbit ou .zip e extrai os dados relevantes."""
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
                            tables_names.append(rows['name'])
                            measure_names.append(measures['name'])
                            expression = measures.get('expression', 'N/A')
                            measure_expression.append("".join(expression) if isinstance(expression, list) else expression)

                    
                    if 'columns' in rows:
                        for cols in rows['columns']:
                            col_data = pd.DataFrame([{
                                'NomeTabela': rows['name'],
                                'NomeColuna': cols['name'],
                                'TipoDadoColuna': cols['dataType'],
                                'TipoColuna': cols.get('type', 'N/A'),
                                'ExpressaoColuna': cols.get('expression', 'N/A')
                            }])

                            df_columns = pd.concat([df_columns, col_data], ignore_index=True)

                    mcode = [''.join(rows['partitions'][0]['source']['expression'])]
                    
                    df_tables_rows = pd.DataFrame([{
                        'DatasetId': datasetid_content,
                        'ReportId': reportid_content,
                        'ReportName': reportname_content,
                        'NomeTabela': rows['name'], 
                        'FonteDados': mcode[0]
                    }])

                    df_tables = pd.concat([df_tables, df_tables_rows], ignore_index=True)

        df_columns['ExpressaoColuna'] = df_columns['ExpressaoColuna'].apply(lambda l: "".join(l))
        
        df_measures = pd.DataFrame({
            'NomeTabela': tables_names,
            'NomeMedida': measure_names,
            'ExpressaoMedida': measure_expression
        })

        df_normalized = pd.merge(pd.merge(df_tables, df_measures, left_on='NomeTabela', right_on='NomeTabela', how='left'), df_columns, right_on='NomeTabela', left_on='NomeTabela', how='left')
        
        return df_normalized
    else:
        return 'Arquivo não suportado'
