import streamlit as st
import os
from dotenv import load_dotenv
import pandas as pd
from litellm import completion
from zipfile import ZipFile
import json
import sys

# Adicionando o diretório pai ao caminho
sys.path.append(os.path.abspath('..'))

# Importando as funções dos outros arquivos
from relatorio import get_token, get_workspaces_id, scan_workspace, clean_reports

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

MODELO = ""

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
                        #print(df_tables_rows)
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

        # Extract relationship information
        relationship_info = extract_relationships(content)

        # Create a DataFrame
        df_relationships = pd.DataFrame(relationship_info)

        df_normalized = pd.merge(pd.merge(df_tables, df_measures, left_on='NomeTabela', right_on='NomeTabela', how='left'), df_columns, right_on='NomeTabela', left_on='NomeTabela', how='left')
        
        return df_normalized, df_relationships
    else:
        return 'Arquivo não suportado'


def text_to_document(df, df_relationships=None):    
    """Gera o texto para documentação baseado nos dados do DataFrame."""

    tables_df = df[df['NomeTabela'].notnull() & df['FonteDados'].notnull()]
    tables_df = tables_df[['NomeTabela', 'FonteDados']].drop_duplicates().reset_index(drop=True)
    
    measures_df = df[df['NomeMedida'].notnull() & df['ExpressaoMedida'].notnull()]
    measures_df = measures_df[['NomeMedida', 'ExpressaoMedida']].drop_duplicates().reset_index(drop=True)
    
    df_colunas = df[['NomeTabela','NomeColuna', 'TipoDadoColuna', 'TipoColuna', 'ExpressaoColuna']]
    df_colunas = df_colunas[df_colunas['NomeTabela'] != 'Medidas']

    df_colunas['TipoColuna'] = df_colunas['TipoColuna'].replace('N/A', '')
    df_colunas['ExpressaoColuna'] = df_colunas['ExpressaoColuna'].replace('N/A', '')
        
    if not df.empty and 'ReportName' in df.columns:
        report_name = df['ReportName'].iloc[0]
    else:
        report_name = "PBIReport"

    if df_relationships is None:
        df_relationships = pd.DataFrame()   
    
    document_text = f"""
        
    Relatório: {report_name}
    
    Tabelas:
    {tables_df['NomeTabela'].to_string(index=False)}
    
    Colunas das Tabelas:
    {df_colunas.to_string(index=False)}
    
    Relacionamentos entre as tabelas:
    {df_relationships.to_string(index=False)}
        
    Fontes dos dados das tabelas:
    {tables_df.to_string(index=False)}
    
    Medidas:
    {measures_df.to_string(index=False)}
    """ 
        
    return document_text, measures_df, tables_df

def Chat(modelo, messages):    
    """Interage com qualquer modelo unsando LiteLLM para obter respostas.
       Mais informações em: https://docs.litellm.ai/docs/providers
    """
    try:
        response = completion(
            model=modelo,
            temperature=0,
            max_tokens=1000000,
            messages=messages
        )
        response = response.choices[0].message.content
                
    except Exception as e:
        print(f"Erro ao chamar a API da OpenAI, corrigindo automaticamente... {str(e)}")
        response = {'error': str(e)}
            
    return response

def Chat_promt(text):
    
    prompts = """1 - Você é um especialista em analisar modelos de relatório do Power BI. Sua função responder de forma clara e detalhada qualquer pergunta feita pelo usuário.
2 - As informações do relatório estão contidas abaixo entre as tags: <INICIO DADOS RELATORIO POWER BI> e <FIM DADOS RELATORIO POWER BI>.
3 - As suas respostas precisam ser restritas as informações contidas no relatório do Power BI.

Abaixo estão as informações do relatório do Power BI para ser usado como base para responder as perguntas do usuário:"""
    return f"{prompts}\n<INICIO DADOS RELATORIO POWER BI>\n{text}\n<FIM DADOS RELATORIO POWER BI>"

def configure_app():
    """Configura a aparência e o layout do aplicativo Streamlit."""
    st.set_page_config(
        page_title="Chat",
        page_icon="💬",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.header('Converse com o seu modelo do Power BI')
    st.write("""
    Com o chat, você pode interagir diretamente com a estrutura do seu modelo do Power BI, obtendo respostas rápidas sobre suas configurações e relacionamentos, sem acessar os dados específicos dos relatórios. Isso torna a análise mais ágil e focada na compreensão do modelo.
    """)

def sidebar_inputs():
    """Exibe o menu lateral para inserção das informações do administrador e upload do arquivo."""
    with st.sidebar:
        
        st.image("https://lawrence.eti.br/wp-content/uploads/2024/09/Chat.png")   
        
        # Opção de seleção entre Open AI e Groq para definir o modelo
        modelo = st.selectbox("Selecione o modelo:", ('gpt-4.1-nano','gpt-4.1-mini', 'gpt-4.1', 'groq/meta-llama/llama-4-maverick-17b-128e-instruct', 'gemini/gemini-2.5-flash-preview-04-17', 'deepseek/deepseek-chat' ))
                         
        # Opção de seleção entre Serviço e Arquivo
        option = st.radio("Selecione a fonte de dados:", ('Power BI Template .pbit', 'Serviço do Power BI'))
        
        if option == 'Power BI Template .pbit':
            app_id = None
            tenant_id = None
            secret_value = None
            uploaded_files = st.file_uploader("Apenas arquivo '.pbit' ou '.zip'", accept_multiple_files=False, type=['pbit', 'zip'], help="""

1. **Salvar com a extensão .pbit**: Ao salvar o arquivo, selecione a extensão .pbit na janela de salvamento. Isso garantirá que seu relatório do Power BI seja salvo como um template.

2. **Exportar como Power BI Template**: Outra maneira de salvar seu relatório como um template é através do menu. Vá até o menu superior e selecione `Arquivo > Exportar > Power BI Template`. Isso abrirá uma janela onde você poderá definir o nome do arquivo e outras configurações antes de salvar o template.

Usar o formato .pbit permite que você crie templates reutilizáveis, facilitando a criação de novos relatórios baseados no mesmo modelo.""")
        else:
            st.write('Preencha com as informações do App')
            app_id = st.text_input(label='App ID')
            tenant_id = st.text_input(label='Tenant ID')
            secret_value = st.text_input(label='Secret value')
            uploaded_files = None  # Nenhum arquivo será necessário            
        ""
        "📄 Documente o modelo: 🔗[AutoDoc](https://autodocpbi.fly.dev/)"
        ""
        "Criado por [Lawrence Teixeira](https://www.linkedin.com/in/lawrenceteixeira/)"

    return app_id, tenant_id, secret_value, uploaded_files, modelo

def main_content(headers=None, uploaded_files=None):
    """Exibe as informações principais do aplicativo."""
    if uploaded_files:
        df_normalized, df_relationships = upload_file(uploaded_files)
        if isinstance(df_normalized, pd.DataFrame):
            buttons_download(df_normalized, df_relationships)
        else:
            st.error("Erro ao processar o arquivo enviado. Por favor, verifique o formato do arquivo.")

    if headers:
        workspace_dict = get_workspaces_id(headers)
        
        if workspace_dict:
            option = st.selectbox("Qual workspace você gostaria de visualizar?", list(workspace_dict.keys()), index=None, placeholder='Selecione a workspace...')
            if option:
                with st.spinner('Retornando relatório...'):
                    workspace_id = workspace_dict[option]
                    scan_response = scan_workspace(headers, workspace_id)
                    display_reports(scan_response)

def display_reports(scan_response):
    """Exibe os painéis e lida com a seleção do usuário."""
    report_names = [report_info['name'] for report_info in scan_response['datasets'] if 'PbixInImportMode' in report_info['contentProviderType'] and 'Usage Metrics Report' not in report_info['name']]
    
    option = st.selectbox("Qual relatório você gostaria de visualizar?", list(report_names), index=None, placeholder='Selecione o relatório...')
    
    if option:
        df_desnormalized = clean_reports(scan_response, option)
        buttons_download(df_desnormalized)

def click_button():
    st.session_state.button = not st.session_state.button
    
# Function to recursively update the 'FonteDados' field
def update_fonte_dados(data, tables_df):
    if isinstance(data, dict):
        # Collect keys to modify in a separate list
        keys_to_update = []
        for key, value in data.items():
            if key == 'NomeTabela' and value in tables_df['NomeTabela'].to_list():
                keys_to_update.append((key, value))
            elif isinstance(value, (dict, list)):
                update_fonte_dados(value, tables_df)
        
        # Apply the modifications
        for key, value in keys_to_update:
            table_index = tables_df[tables_df['NomeTabela'] == value].index[0]
            data['FonteDados'] = tables_df['FonteDados'].iloc[table_index]
            
    elif isinstance(data, list):
        for item in data:
            update_fonte_dados(item, tables_df)  

def buttons_download(df, df_relationships=None):
    """Exibe botões para download e visualização dos dados processados."""
    
    if not df.empty and 'ReportName' in df.columns:
        report_name = df['ReportName'].iloc[0].replace(' ', '_')
    else:
        # Handle the case where the DataFrame is empty or the column doesn't exist
        report_name = "PBIReport"
    
    if 'button' not in st.session_state:
        st.session_state.button = True
                        
    verprompt = st.checkbox("Mostrar Prompt")
    
    text, measures_df, tables_df = text_to_document(df, df_relationships)    
    systemprompt = Chat_promt(text)
    
    if verprompt:
        st.text_area("Prompt", value=systemprompt, height=300)    
    
    if "messages" not in st.session_state:
        st.session_state["messages"] = [{"role": "system", "content": systemprompt}]
        st.session_state.messages.append( {"role": "assistant", "content": "Oi! 😊 Como você está? 💬 Pergunte qualquer coisa sobre o seu relatório '"+ report_name +"'."} )

    for msg in st.session_state.messages:
        if msg["role"] != "system":
            st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input():
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        
        with st.spinner('Pensando...'): 
            response = Chat(MODELO, st.session_state.messages)
        
        if response:
            result = (str(response))
        else:
            result = (str(":)"))

        msg = { "role": "assistant",
                "content": result
        }

        st.session_state.messages.append(msg)
                
        st.chat_message("assistant").write(msg["content"])    
        
def main():    
    """Função principal do aplicativo, onde todas as funções são chamadas."""
        
    configure_app()
            
    global API_KEY, MODELO

    app_id, tenant_id, secret_value, uploaded_files, modelo = sidebar_inputs()
    
    MODELO = modelo
            
    if app_id and tenant_id and secret_value:
        headers = get_token(app_id, tenant_id, secret_value)
        if headers:
            main_content(headers, None)
    
    if uploaded_files:
        main_content(None, uploaded_files)

if __name__ == "__main__":
    main()