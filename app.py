import streamlit as st
import os
from dotenv import load_dotenv
from io import BytesIO
import pandas as pd
import json

# Importando as funções dos outros arquivos
from relatorio import get_token, get_workspaces_id, scan_workspace, clean_reports, upload_file
from documenta import generate_docx, generate_excel, text_to_document, generate_promt, defined_prompt, Documenta

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()
OPENAI_API_KEY = os.getenv('API_KEY')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

API_KEY = ""
MODELO = ""

def configure_app():
    """Configura a aparência e o layout do aplicativo Streamlit."""
    st.set_page_config(
        page_title="AutoDoc",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.header('Documentador de Power BI')
    st.write("""
    Este aplicativo facilita a organização, o acompanhamento e a análise de dados, fornecendo uma documentação completa e automatizada dos relatórios de Power BI. 
    Ideal para administradores e analistas que buscam eficiência e precisão na geração de documentações detalhadas e formatadas.
    """)

def sidebar_inputs():
    """Exibe o menu lateral para inserção das informações do administrador e upload do arquivo."""
    with st.sidebar:
        
        st.image("https://lawrence.eti.br/wp-content/uploads/2024/06/AutoDoc.png")   
        
        # Opção de seleção entre Open AI e Groq para definir o modelo
        modelo = st.selectbox("Selecione o modelo:", ('gpt-4o', 'azure/gpt-4o','claude-3-5-sonnet-20240620', 'gemini/gemini-1.5-pro'))
                         
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
        "Criado por [Lawrence Teixeira](https://www.linkedin.com/in/lawrenceteixeira/)"

    return app_id, tenant_id, secret_value, uploaded_files, modelo

def detailed_description():
    """Mostra uma explicação detalhada sobre o aplicativo."""
    st.write("""
    **Documentador de Power BI** é uma ferramenta desenvolvida para simplificar e automatizar o processo de documentação de relatórios do Power BI. 
    Com este aplicativo, você pode:
    
    - **Carregar seus arquivos de modelo Power BI (.pbit ou .zip)**: Faça upload dos seus arquivos de modelo diretamente no aplicativo.
    - **Gerar Documentação Detalhada**: Obtenha documentos completos em formatos Excel e Word, com informações sobre tabelas, colunas, medidas e fontes de dados.
    - **Visualização Interativa**: Veja as tabelas e dados detalhados diretamente na interface do aplicativo antes de fazer o download.
    - **Eficiência e Precisão**: Automatize o processo de documentação, economizando tempo e garantindo a precisão das informações.

    O aplicativo é projetado para administradores e analistas de dados que precisam de uma forma eficiente e precisa de gerar documentações de alta qualidade para seus relatórios do Power BI. 
    A ferramenta utiliza tecnologias avançadas de processamento de dados e inteligência artificial para fornecer documentações claras, detalhadas e formatadas de acordo com suas necessidades.

    **Como usar o Documentador de Power BI**:
    1. Preencha as informações do App ID, Tenant ID e Secret Value na barra lateral.
    2. Faça o upload do arquivo de modelo Power BI (.pbit ou .zip).
    3. Visualize os dados e faça o download da documentação gerada em formatos Excel ou Word.

    Simplifique e automatize a documentação dos seus relatórios do Power BI com o **Documentador de Power BI**.
    
    Criado por [Lawrence Teixeira](https://www.linkedin.com/in/lawrenceteixeira/) em 22/06/2024.
       
    """)

def sidebar_description():
    """Mostra uma descrição resumida com botão para mais informações na barra lateral."""
    st.sidebar.header("Sobre o App")
    if st.sidebar.button("Informações"):
        st.session_state.show_description = not st.session_state.get('show_description', False)
    if st.session_state.get('show_description', False):
        detailed_description()

def main_content(headers=None, uploaded_files=None):
    """Exibe as informações principais do aplicativo."""
    if uploaded_files:
        df_normalized = upload_file(uploaded_files)
        if isinstance(df_normalized, pd.DataFrame):
            buttons_download(df_normalized)
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

def buttons_download(df):
    """Exibe botões para download e visualização dos dados processados."""
    
    report_name = df['ReportName'].iloc[0].replace(' ', '_')
    
    if 'button' not in st.session_state:
        st.session_state.button = True
    
    on = st.checkbox("Ver dados do relatório")

    if on:
        st.dataframe(df)
        
    verprompt = st.checkbox("Mostrar Prompt")

    if verprompt:
        text, measures_df, tables_df = text_to_document(df)
        
        prompt = generate_promt(text)

        st.text_area("Prompt", value=prompt, height=300)    
        
    if st.button("Gerar documentação"):
        
        # Mostrando uma mensgem de carregamento
        gerando = f"Gerando documentação usando o modelo {MODELO}, por favor aguarde..."
        
        with st.spinner(gerando):
            text, measures_df, tables_df = text_to_document(df)
            prompts = defined_prompt()

            response_info, response_tables, response_measures, response_source = Documenta(prompts, text, MODELO)
            
            # Update the 'FonteDados' field in the response data
            update_fonte_dados(response_source, tables_df)
                                                            
            # Store the response data in the session state for later use
            st.session_state['response_info'] = response_info
            st.session_state['response_tables'] = response_tables
            st.session_state['response_measures'] = response_measures
            st.session_state['response_source'] = response_source
            st.session_state['measures_df'] = measures_df
            
            st.session_state.button = False
    
    verprompt = st.checkbox("Mostrar JSON", key='mostrar_json', disabled=st.session_state.button )

    if verprompt:
        # Convert dictionaries to JSON strings
        response_info_str = json.dumps(st.session_state['response_info'], indent=2)
        response_tables_str = json.dumps(st.session_state['response_tables'], indent=2)
        response_measures_str = json.dumps(st.session_state['response_measures'], indent=2)
        response_source_str = json.dumps(st.session_state['response_source'], indent=2)

        # Concatenate the JSON strings
        text = response_info_str + '\n' + response_tables_str + '\n' + response_measures_str + '\n' + response_source_str 
        
        st.text_area("JSON", value=text, height=300)
    
    col1, col2 = st.columns(2)
            
    with col1:
        
        if st.button("Exporta documentação para excel", disabled=st.session_state.button):
            with st.spinner("Gerando arquivo, por favor aguarde..."):
                buffer = generate_excel(st.session_state['response_info'], st.session_state['response_tables'], st.session_state['response_measures'], st.session_state['response_source'], st.session_state['measures_df'])
                
                # Utilize st.download_button para permitir o download direto
                st.download_button(
                    label="Baixar xlsx",
                    data=buffer,
                    file_name=report_name+'.xlsx',
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
    with col2:
        if st.button("Exporta documentação para word", disabled=st.session_state.button):
            with st.spinner("Gerando arquivo, por favor aguarde..."):
                doc = generate_docx(st.session_state['response_info'], st.session_state['response_tables'], st.session_state['response_measures'], st.session_state['response_source'], st.session_state['measures_df'])
                buffer = BytesIO()
                doc.save(buffer)
                buffer.seek(0)
                st.download_button(
                    label="Baixar docx",
                    data=buffer,
                    file_name=report_name+'.docx',
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )

        
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

    if 'show_description' not in st.session_state:
        st.session_state.show_description = False

    sidebar_description()

if __name__ == "__main__":
    main()