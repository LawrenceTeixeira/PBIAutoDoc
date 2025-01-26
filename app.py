import streamlit as st
import os
from dotenv import load_dotenv
from io import BytesIO
import pandas as pd
import json
import tiktoken

# Importando as funções dos outros arquivos
from relatorio import get_token, get_workspaces_id, scan_workspace, clean_reports, upload_file
from documenta import generate_docx, generate_excel, text_to_document, Documenta, defined_prompt_fontes, defined_prompt_medidas, generate_promt_medidas, generate_promt_fontes

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

MODELO = ""
MAX_TOKENS = 0
MAX_TOKENS_SAIDA = 0

def counttokens(text):
    # Inicializando o tokenizador para o modelo desejado (neste exemplo, GPT-4)
    encoding = tiktoken.get_encoding("cl100k_base")
    
    # Contar o número de tokens no texto fornecido
    tokens = len(encoding.encode(text))
    
    return tokens

def configure_app():
    """Configura a aparência e o layout do aplicativo Streamlit."""
    st.set_page_config(
        page_title="AutoDoc",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.header('Documentador de Power BI - Minhas Planilhas')
    st.write("""
    Este aplicativo facilita a organização, o acompanhamento e a análise de dados, fornecendo uma documentação completa e automatizada dos relatórios de Power BI. 
    Ideal para administradores e analistas que buscam eficiência e precisão na geração de documentações detalhadas e formatadas.
    """)

def sidebar_inputs():
    """Exibe o menu lateral para inserção das informações do administrador e upload do arquivo template do Power BI."""
    with st.sidebar:
        
        st.image("https://lawrence.eti.br/wp-content/uploads/2024/06/AutoDoc.png")   
        
        # Opção de seleção entre Open AI e Groq para definir o modelo
        modelo = st.selectbox("Selecione o modelo:", ('gpt-4o-mini','gpt-4o', 'deepseek/deepseek-chat'))
                         
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

        # Set a slider to select max tokens
        max_tokens = st.sidebar.number_input('Selecione o máximo de tokens de entrada:', min_value=256, max_value=8192, value=4096, step=256)

        # Set a slider to select max tokens
        max_tokens_saida = st.sidebar.number_input('Selecione o máximo de tokens de saída:', min_value=512, max_value=16384, value=8192, step=512)

        "💬 Converse com o modelo: 🔗[Chat](https://autodocchat.fly.dev)"
        ""
        "Criado por [Lawrence Teixeira](https://www.linkedin.com/in/lawrenceteixeira/)"
             
    return app_id, tenant_id, secret_value, uploaded_files, modelo, max_tokens, max_tokens_saida

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
    
    st.session_state['df_relationships'] = None

    if uploaded_files:
        df_normalized, df_relationships = upload_file(uploaded_files)

        # Store the df_relationships data in the session state for later use
        st.session_state['df_relationships'] = df_relationships

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
    
    if not df.empty and 'ReportName' in df.columns:
        report_name = df['ReportName'].iloc[0].replace(' ', '_')
    else:
        # Handle the case where the DataFrame is empty or the column doesn't exist
        report_name = "PBIReport"
    
    if 'button' not in st.session_state:
        st.session_state.button = True
    
    on = st.checkbox("Ver dados do relatório")

    if on:
        st.dataframe(df)
        
    verprompt_medidas = st.checkbox("Mostrar Prompt das medidas")

    if verprompt_medidas:
        dados_relatorio_PBI_medidas, dados_relatorio_PBI_fontes, measures_df, tables_df, df_colunas = text_to_document(df, max_tokens=MAX_TOKENS)
        
        prompt = generate_promt_medidas(dados_relatorio_PBI_medidas[0])

        st.text_area("Prompt medidas:", value=prompt, height=300)

    verprompt_fontes = st.checkbox("Mostrar Prompt das fontes de dados")

    if verprompt_fontes:
        dados_relatorio_PBI_medidas, dados_relatorio_PBI_fontes, measures_df, tables_df, df_colunas = text_to_document(df, max_tokens=MAX_TOKENS)
        
        prompt = generate_promt_fontes(dados_relatorio_PBI_fontes[0])

        st.text_area("Prompt fontes de dados:", value=prompt, height=300)

    mostra_total_tokens = st.checkbox("Mostrar total de tokens por interação")

    if mostra_total_tokens:
        dados_relatorio_PBI_medidas, dados_relatorio_PBI_fontes, measures_df, tables_df, df_colunas = text_to_document(df, max_tokens=MAX_TOKENS)
        
        total_tokens = 0
        stringmostra = ""
        conta_interacao= 0
        
        for text in dados_relatorio_PBI_medidas:
            conta_interacao += 1
            total_tokens += counttokens(text)
                        
            stringmostra += f"{conta_interacao}ª interação (prompt das medidas)      | qtde tokens: {counttokens(text):,}\n"
        
        for text in dados_relatorio_PBI_fontes:
            conta_interacao += 1
            total_tokens += counttokens(text)
            stringmostra += f"{conta_interacao}ª interação (prompt fonte de dados) | qtde tokens: {counttokens(text):,}\n"

        stringmostra += f"\nTotal de interações: {conta_interacao}\nTotal de tokens (medidas + fontes de dados) de entrada: {total_tokens:,} tokens.\n"

        st.text_area("Total de Tokens por interação:", value=stringmostra, height=300)
        
    if st.button("Gerar documentação"):
        conta_interacao = 1
        
        # Mostrando uma mensgem de carregamento
        gerando = f"Gerando documentação usando o modelo {MODELO}, configurado com máximo {MAX_TOKENS} tokens de entrada e {MAX_TOKENS_SAIDA} tokens de saída."
                
        with st.spinner(gerando):
            # Executa a função para fazer a documentação a partir do prompt montado com a lista dos dados do relatório
            
            # define the prompts for measures and sources            
            dados_relatorio_PBI_medidas, dados_relatorio_PBI_fontes, measures_df, tables_df, df_colunas = text_to_document(df, max_tokens=MAX_TOKENS)

            medidas_do_relatorio_df = pd.DataFrame()
            fontes_de_dados_df = pd.DataFrame()
            
            Uma = True

            for text in dados_relatorio_PBI_medidas:

                gerando = f"{conta_interacao}ª interação, por favor aguarde..."
 
                with st.spinner(gerando):                                
                    response = Documenta(defined_prompt_medidas(), text, MODELO, max_tokens=MAX_TOKENS, max_tokens_saida=MAX_TOKENS_SAIDA)
                    conta_interacao += 1
                    
                    # Verifica se response contem as 'Relatório' na primeira interação
                    if Uma and 'Relatorio' in response and 'Tabelas_do_Relatorio' in response:
                        Uma = False
                        response_info = response['Relatorio']
                        response_tables = response['Tabelas_do_Relatorio']

                    if 'Medidas_do_Relatorio'  in response:
                        ## add to medidas_do_relatorio_df response["Medidas_do_Relatorio"]
                        medidas_do_relatorio_df = pd.concat([medidas_do_relatorio_df, pd.DataFrame(response["Medidas_do_Relatorio"])], ignore_index=True)
            
            # executa a função para fazer a documentação a partir do prompt montado com a lista dos dados do relatório
            for text in dados_relatorio_PBI_fontes:

                gerando = f"{conta_interacao}ª interação, por favor aguarde..."
 
                with st.spinner(gerando):                                
                    response = Documenta(defined_prompt_fontes(), text, MODELO, max_tokens=MAX_TOKENS, max_tokens_saida=MAX_TOKENS_SAIDA)
                    conta_interacao += 1
                    
                    # Verifica se response contem as 'Relatório' na primeira interação
                    if Uma and 'Relatorio' in response and 'Tabelas_do_Relatorio' in response:
                        print(response)
                        Uma = False
                        response_info = response['Relatorio']
                        response_tables = response['Tabelas_do_Relatorio']

                    # Verifica se response contem as Fontes_de_Dados
                    if 'Fontes_de_Dados' in response:
                        ## add to fonte_de_dados_df response["Fontes_de_Dados"]
                        fontes_de_dados_df = pd.concat([fontes_de_dados_df, pd.DataFrame(response["Fontes_de_Dados"])], ignore_index=True)

            # define the response data for the document            
            response_measures = medidas_do_relatorio_df.to_dict(orient='records')
            response_source = fontes_de_dados_df.to_dict(orient='records')
                        
            # Update the 'FonteDados' field in the response 
            update_fonte_dados(response_source, tables_df)
                                                            
            # Store the response data in the session state for later use
            st.session_state['response_info'] = response_info
            st.session_state['response_tables'] = response_tables
            st.session_state['response_measures'] = response_measures
            st.session_state['response_source'] = response_source
            st.session_state['measures_df'] = measures_df
            st.session_state['df_colunas'] = df_colunas

            st.session_state.button = False
    
    verprompt = st.checkbox("Mostrar JSONs", key='mostrar_json', disabled=st.session_state.button )

    if verprompt:
        # Convert dictionaries to JSON strings
        response_info_str = json.dumps(st.session_state['response_info'], indent=2)
        response_tables_str = json.dumps(st.session_state['response_tables'], indent=2)
        response_measures_str = json.dumps(st.session_state['response_measures'], indent=2)
        response_source_str = json.dumps(st.session_state['response_source'], indent=2)

        # Concatenate the JSON strings
        text = 'JSON com as informações do relatório' + '\n' + response_info_str + '\n\n' + 'JSON com as tabelas do relatório' + '\n' + response_tables_str + '\n\n' + 'JSON com as medidas do relatório' + '\n' + response_measures_str + '\n\n' + 'JSON com as fontes de dados do relatório' + '\n' + response_source_str 
        
        st.text_area("JSON", value=text, height=300)
    
    col1, col2 = st.columns(2)
            
    with col1:
        
        if st.button("Exporta documentação para excel", disabled=st.session_state.button):
            with st.spinner("Gerando arquivo, por favor aguarde..."):
                buffer = generate_excel(st.session_state['response_info'], st.session_state['response_tables'], st.session_state['response_measures'], st.session_state['response_source'], st.session_state['measures_df'], st.session_state['df_relationships'], st.session_state['df_colunas'])
                
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
                doc = generate_docx(st.session_state['response_info'], st.session_state['response_tables'], st.session_state['response_measures'], st.session_state['response_source'], st.session_state['measures_df'], st.session_state['df_relationships'], st.session_state['df_colunas'])
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
            
    global API_KEY, MODELO, MAX_TOKENS, MAX_TOKENS_SAIDA

    app_id, tenant_id, secret_value, uploaded_files, modelo, max_tokens, max_tokens_saida = sidebar_inputs()
    
    MODELO = modelo
    MAX_TOKENS = max_tokens
    MAX_TOKENS_SAIDA = max_tokens_saida
            
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