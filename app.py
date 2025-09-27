import streamlit as st
import os
from dotenv import load_dotenv
from io import BytesIO
import pandas as pd
import json
import tiktoken

# Importando as funções dos outros arquivos
from relatorio import get_token, get_workspaces_id, scan_workspace, clean_reports, upload_file
from documenta import generate_docx, generate_excel, text_to_document, Documenta, defined_prompt_fontes, defined_prompt_medidas, generate_promt_medidas, generate_promt_fontes, defined_prompt, generate_promt

# Importando o sistema de internacionalização
from i18n import init_i18n, t, language_selector

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Initialize internationalization
init_i18n(default_language="en")

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
    
    # Language selector and GitHub button at the top
    col1, col2, col3, col4 = st.columns([1, 1.5, 1, 0.7])
    with col3:
        language_selector("main_language_selector", use_flags=True, flag_style="image")
    with col4:
        # CSS para fazer o botão GitHub parecer com os botões do Streamlit
        st.markdown("""
        <style>
        /* Estilo para o botão GitHub simular botões do Streamlit */
        .github-button {
            display: inline-block;
            width: 65%;
            padding: 0.375rem 0.5rem;
            margin: 0;
            font-weight: 400;
            color: #262730;
            background-color: #FFFFFF;
            border: 1px solid #D4D4D8;
            border-radius: 0.375rem;
            text-decoration: none !important;
            text-align: center;
            font-size: 0.875rem;
            line-height: 1.5;
            cursor: pointer;
            transition: all 0.15s ease;
            min-height: 38.4px;
            box-sizing: border-box;
        }
        .github-button:hover {
            border-color: #FF4B4B;
            color: #FF4B4B;
            text-decoration: none !important;
        }
        .github-button:visited {
            text-decoration: none !important;
        }
        .github-button:active {
            text-decoration: none !important;
        }
        .github-button:focus {
            text-decoration: none !important;
            outline: none;
        }
        .github-button svg {
            vertical-align: middle;
            margin-right: 6px;
        }
        
        /* Para tema escuro */
        @media (prefers-color-scheme: dark) {
            .github-button {
                color: #FAFAFA;
                background-color: #262730;
                border-color: #4A4A4A;
            }
            .github-button:hover {
                border-color: #FF4B4B;
                color: #FF4B4B;
                text-decoration: none !important;
            }
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Botão GitHub com estilo similar aos botões das bandeiras
        st.markdown(f"""
        <a href="https://github.com/LawrenceTeixeira/PBIAutoDoc" target="_blank" class="github-button" aria-label="{t('ui.github_aria_label')}">
            <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z"/>
            </svg>
            {t('ui.github_button_text')}
        </a>
        """, unsafe_allow_html=True)
    
    st.header(t('ui.app_title'))
    st.write(t('ui.app_description'))

def sidebar_inputs():
    """Exibe o menu lateral para inserção das informações do administrador e upload do arquivo template do Power BI."""    
    with st.sidebar:
        
        st.image("https://lawrence.eti.br/wp-content/uploads/2025/04/AutoDoc.png")
        
        # Carrega os modelos das variáveis de ambiente
        available_models_str = os.getenv('AVAILABLE_MODELS', 'groq/meta-llama/llama-4-maverick-17b-128e-instruct,groq/openai/gpt-oss-120b,gpt-5-mini,gpt-5,azure/gpt-4.1-mini,gemini/gemini-2.5-flash-preview-04-17,claude-3-7-sonnet-20250219,deepseek/deepseek-chat')
        available_models = tuple(model.strip() for model in available_models_str.split(','))
        default_model = os.getenv('DEFAULT_MODEL', available_models[0])
        
        # Encontra o índice do modelo padrão para definir como selecionado
        try:
            default_index = available_models.index(default_model)
        except ValueError:
            default_index = 0
        
        # Opção de seleção de modelo usando variáveis de ambiente
        modelo = st.selectbox(
            t('ui.model_selector'), 
            available_models,
            index=default_index
        )
                         
        # Opção de seleção entre Serviço e Arquivo
        option = st.radio(t('ui.data_source_selector'), (t('ui.power_bi_template'), t('ui.power_bi_service')))
        
        if option == t('ui.power_bi_template'):
            app_id = None
            tenant_id = None
            secret_value = None
            uploaded_files = st.file_uploader(
                t('ui.file_upload_label'), 
                accept_multiple_files=False, 
                type=['pbit', 'zip'], 
                help=t('ui.file_upload_help')
            )
        else:
            app_id = st.text_input(
                label=t('ui.app_id_label'),
                help=t('ui.app_id_help')
            )
            tenant_id = st.text_input(
                label=t('ui.tenant_id_label'),
                help=t('ui.tenant_id_help')
            )
            secret_value = st.text_input(
                label=t('ui.secret_value_label'),
                help=t('ui.secret_value_help'),
                type='password'
            )
            uploaded_files = None  # Nenhum arquivo será necessário            

        # Set a slider to select max tokens
        max_tokens = st.sidebar.number_input(t('ui.max_tokens_input'), min_value=256, max_value=10000000, value=8192, step=256)

        # Set a slider to select max tokens
        max_tokens_saida = st.sidebar.number_input(t('ui.max_tokens_output'), min_value=512, max_value=128000, value=8192, step=512)             
        
        ""
        
        st.sidebar.markdown(t('ui.created_by', author="[Lawrence Teixeira](https://www.linkedin.com/in/lawrenceteixeira/)"))

    return app_id, tenant_id, secret_value, uploaded_files, modelo, max_tokens, max_tokens_saida

def detailed_description():
    """Mostra uma explicação detalhada sobre o aplicativo."""    
    st.write(f"""
    {t('detailed_description.title')}
    {t('detailed_description.features')}
    
    - {t('detailed_description.feature_1')}
    - {t('detailed_description.feature_2')}
    - {t('detailed_description.feature_3')}
    - {t('detailed_description.feature_4')}

    {t('detailed_description.purpose')}

    {t('detailed_description.how_to_use')}
    {t('detailed_description.step_1')}
    {t('detailed_description.step_2')}
    {t('detailed_description.step_3')}

    {t('detailed_description.conclusion')}
    
    {t('detailed_description.created_info')}
    
    Versão: 2.0.0 
    """)

def sidebar_description():
    """Mostra uma descrição resumida com botão para mais informações na barra lateral."""    
    st.sidebar.header(t('ui.about_app'))
    if st.sidebar.button(t('ui.information')):
        st.session_state.show_description = not st.session_state.get('show_description', False)
        
    if st.session_state.get('show_description', False):
        detailed_description()
                
def main_content(headers=None, uploaded_files=None):
    """Exibe as informações principais do aplicativo."""    
    st.session_state['df_relationships'] = None

    if uploaded_files:
        with st.spinner(t('messages.processing_file')):
            try:
                result = upload_file(uploaded_files)
                
                # Verificar se o resultado é uma string (erro) ou tupla (sucesso)
                if isinstance(result, str):
                    # É uma mensagem de erro
                    error_message = result
                    if "Arquivo inválido: não contém 'DataModelSchema'" in error_message or "não é um ZIP/PBIT válido" in error_message:
                        st.error(t('errors.invalid_powerbi_file'))
                    elif "Arquivo não suportado" in error_message:
                        st.error(t('errors.file_not_supported'))
                    elif "arquivo vazio" in error_message.lower():
                        st.error(t('errors.empty_file'))
                    elif "corrompido" in error_message.lower() or "falha" in error_message.lower():
                        st.error(t('errors.corrupted_file'))
                    else:
                        st.error(t('errors.processing_error', error=error_message))
                    return
                
                # Se chegou aqui, deve ser uma tupla com os dados
                if isinstance(result, tuple) and len(result) == 2:
                    df_normalized, df_relationships = result
                else:
                    st.error(t('errors.invalid_powerbi_file'))
                    return
                
            except ValueError as e:
                if "too many values to unpack" in str(e):
                    st.error(t('errors.invalid_powerbi_file'))
                else:
                    st.error(t('errors.processing_error', error=str(e)))
                return
            except Exception as e:
                st.error(t('errors.processing_error', error=str(e)))
                return

        # Store the df_relationships data in the session state for later use
        st.session_state['df_relationships'] = df_relationships

        if isinstance(df_normalized, pd.DataFrame) and not df_normalized.empty:
            st.success(t('messages.file_processed'))
            buttons_download(df_normalized)
        else:
            st.error(t('errors.no_data_found'))

    if headers:        
        with st.spinner(t('messages.loading_workspaces')):
            workspace_dict = get_workspaces_id(headers)
        
        if workspace_dict:
            option = st.selectbox(
                t('ui.workspace_selector'), 
                list(workspace_dict.keys()), 
                index=None, 
                placeholder=t('ui.workspace_placeholder')
            )
            if option:
                with st.spinner(t('messages.scanning_workspace')):
                    workspace_id = workspace_dict[option]
                    scan_response = scan_workspace(headers, workspace_id)
                    display_reports(scan_response)

def display_reports(scan_response):
    """Exibe os painéis e lida com a seleção do usuário."""    
    report_names = [report_info['name'] for report_info in scan_response['datasets'] if 'PbixInImportMode' in report_info['contentProviderType'] and 'Usage Metrics Report' not in report_info['name']]
    
    option = st.selectbox(
        t('ui.report_selector'), 
        list(report_names), 
        index=None, 
        placeholder=t('ui.report_placeholder')
    )
    
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
        report_name = "PBIReport"

    if 'button' not in st.session_state:
        st.session_state.button = True
    if 'show_chat' not in st.session_state:
        st.session_state.show_chat = False
    if 'doc_gerada' not in st.session_state:
        st.session_state['doc_gerada'] = False

    on = st.checkbox(t('ui.view_report_data'))
    if on:
        st.dataframe(df)

    verprompt_completo = st.checkbox(t('ui.show_prompt'))
    if verprompt_completo:
        document_text_all, dados_relatorio_PBI_medidas, dados_relatorio_PBI_fontes, measures_df, tables_df, df_colunas = text_to_document(df, max_tokens=MAX_TOKENS)
        prompt = generate_promt(document_text_all, t('language_name'))
        st.text_area("Prompt:", value=prompt, height=300)

    mostra_total_tokens = st.checkbox(t('ui.show_tokens'))
    if mostra_total_tokens:
        document_text_all, dados_relatorio_PBI_medidas, dados_relatorio_PBI_fontes, measures_df, tables_df, df_colunas = text_to_document(df, max_tokens=MAX_TOKENS)
        total_tokens = 0
        stringmostra = ""
        conta_interacao= 0
        if counttokens(document_text_all) < MAX_TOKENS:
            conta_interacao += 1
            total_tokens += counttokens(document_text_all)
            stringmostra += f"{t('ui.first_interaction')}      | {t('ui.tokens_count')} {counttokens(document_text_all):,}\n"
        else:
            for text in dados_relatorio_PBI_medidas:
                conta_interacao += 1
                total_tokens += counttokens(text)
                stringmostra += f"{conta_interacao}{t('ui.measures_interaction')}      | {t('ui.tokens_count')} {counttokens(text):,}\n"
            for text in dados_relatorio_PBI_fontes:
                conta_interacao += 1
                total_tokens += counttokens(text)
                stringmostra += f"{conta_interacao}{t('ui.sources_interaction')} | {t('ui.tokens_count')} {counttokens(text):,}\n"
        stringmostra += f"\n{t('ui.total_interactions')} {conta_interacao}\n{t('ui.total_tokens')} {total_tokens:,} tokens.\n"
        st.text_area(t('ui.token_analysis_label'), value=stringmostra, height=300)

    colA, colB = st.columns(2)
    with colA:
        gerar_doc = st.button(t('ui.generate_doc'), disabled=st.session_state.get('show_chat', False))
    with colB:
        conversar = st.button(t('ui.chat'), disabled=st.session_state.get('show_chat', False))

    if gerar_doc and not st.session_state.get('show_chat', False):
        conta_interacao = 1
        gerando = t('messages.generating_documentation')
        with st.spinner(gerando):
            document_text_all, dados_relatorio_PBI_medidas, dados_relatorio_PBI_fontes, measures_df, tables_df, df_colunas = text_to_document(df, max_tokens=MAX_TOKENS)
            medidas_do_relatorio_df = pd.DataFrame()
            fontes_de_dados_df = pd.DataFrame()
            Uma = True
            response_info = {}
            response_tables = []
            if counttokens(document_text_all) < MAX_TOKENS:
                response = Documenta(defined_prompt(t('language_name')), document_text_all, MODELO, max_tokens=MAX_TOKENS, max_tokens_saida=MAX_TOKENS_SAIDA)
                conta_interacao += 1
                if Uma and 'Relatorio' in response and 'Tabelas_do_Relatorio' in response:
                    Uma = False
                    response_info = response['Relatorio']
                    response_tables = response['Tabelas_do_Relatorio']
                response_measures = response['Medidas_do_Relatorio']
                response_source = response['Fontes_de_Dados']
            else:
                for text in dados_relatorio_PBI_medidas:
                    gerando = f"{conta_interacao}{t('ui.interaction_progress')}"
                    with st.spinner(gerando):
                        response = Documenta(defined_prompt_medidas(t('language_name')), text, MODELO, max_tokens=MAX_TOKENS, max_tokens_saida=MAX_TOKENS_SAIDA)
                        conta_interacao += 1
                        if Uma and 'Relatorio' in response and 'Tabelas_do_Relatorio' in response:
                            Uma = False
                            response_info = response['Relatorio']
                            response_tables = response['Tabelas_do_Relatorio']
                        if 'Medidas_do_Relatorio'  in response:
                            medidas_do_relatorio_df = pd.concat([medidas_do_relatorio_df, pd.DataFrame(response["Medidas_do_Relatorio"])], ignore_index=True)
                for text in dados_relatorio_PBI_fontes:
                    gerando = f"{conta_interacao}{t('ui.interaction_progress')}"
                    with st.spinner(gerando):
                        response = Documenta(defined_prompt_fontes(t('language_name')), text, MODELO, max_tokens=MAX_TOKENS, max_tokens_saida=MAX_TOKENS_SAIDA)
                        conta_interacao += 1
                        if Uma and 'Relatorio' in response and 'Tabelas_do_Relatorio' in response:
                            print(response)
                            Uma = False
                            response_info = response['Relatorio']
                            response_tables = response['Tabelas_do_Relatorio']
                        if 'Fontes_de_Dados' in response:
                            fontes_de_dados_df = pd.concat([fontes_de_dados_df, pd.DataFrame(response["Fontes_de_Dados"])], ignore_index=True)
                response_measures = medidas_do_relatorio_df.to_dict(orient='records')
                response_source = fontes_de_dados_df.to_dict(orient='records')
            
            update_fonte_dados(response_source, tables_df)
            
            st.session_state['response_info'] = response_info
            st.session_state['response_tables'] = response_tables
            st.session_state['response_measures'] = response_measures
            st.session_state['response_source'] = response_source
            st.session_state['measures_df'] = measures_df
            st.session_state['df_colunas'] = df_colunas
            st.session_state.button = False
            st.session_state['doc_gerada'] = True  # <-- Seta flag após gerar documentação
            st.session_state['modelo'] = MODELO
            st.session_state.show_chat = False
            st.success(t('messages.documentation_generated'))

    if conversar and not st.session_state.get('show_chat', False):
        st.session_state.show_chat = True
        st.session_state['doc_gerada'] = False  # <-- Oculta opções ao entrar no chat

    if st.session_state.show_chat:
        # --- Chat interface ---
        # Prepare chat prompt from the report
        document_text_all, _, _, _, _, _ = text_to_document(df, max_tokens=MAX_TOKENS)        # Adiciona colunas ao contexto
        df_colunas = st.session_state.get('df_colunas')
        if df_colunas is not None and not df_colunas.empty:
            colunas_texto = '\n'.join([
                f"Tabela: {row['NomeTabela']} | Coluna: {row['NomeColuna']} | Tipo: {row['TipoDadoColuna']} | TipoColuna: {row['TipoColuna']} | Expressão: {row['ExpressaoColuna']}"
                for _, row in df_colunas.iterrows()
            ])
        else:
            colunas_texto = t('chat.no_columns_found')

        # Adiciona relacionamentos ao contexto
        df_relationships = st.session_state.get('df_relationships')
        if df_relationships is not None and not df_relationships.empty:
            relacionamentos_texto = '\n'.join([
                f"De: {row['FromTable']}.{row['FromColumn']} -> Para: {row['ToTable']}.{row['ToColumn']}"
                for _, row in df_relationships.iterrows()
            ])
        else:
            relacionamentos_texto = t('chat.no_relationships_found')

        chat_prompt = t('chat.system_prompt', document_text_all=document_text_all, colunas_texto=colunas_texto, relacionamentos_texto=relacionamentos_texto)
        if 'chat_messages' not in st.session_state:
            st.session_state['chat_messages'] = [
                {"role": "system", "content": chat_prompt + t('chat.system_instruction')},
                {"role": "assistant", "content": t('chat.assistant_greeting', report_name=report_name)}
            ]
        st.markdown("<hr>", unsafe_allow_html=True)
        st.subheader(t('chat.title'))
        for msg in st.session_state['chat_messages']:
            if msg["role"] != "system":
                st.chat_message(msg["role"]).write(msg["content"])
        user_input = st.chat_input(t('chat.input_placeholder'))
        if user_input:
            st.session_state['chat_messages'].append({"role": "user", "content": user_input})
            st.chat_message("user").write(user_input)
            with st.spinner(t('chat.processing')):
                from litellm import completion
                try:
                    response = completion(
                        model=MODELO,
                        temperature=0,
                        max_tokens=MAX_TOKENS_SAIDA,
                        messages=st.session_state['chat_messages']
                    )
                    result = response.choices[0].message.content
                except Exception as e:
                    result = t('chat.error', error=str(e))
            msg = {"role": "assistant", "content": result}
            st.session_state['chat_messages'].append(msg)
            st.chat_message("assistant").write(result)

        st.button(t('chat.close_chat'), on_click=lambda: st.session_state.update({'show_chat': False, 'doc_gerada': True}))    # Exibe as opções somente se a documentação foi gerada e o chat não está ativo
    if st.session_state.get('doc_gerada', False) and not st.session_state.get('show_chat', False):
        verprompt = st.checkbox(t('ui.show_json'), key='mostrar_json', disabled=st.session_state.button )
        if verprompt:
            response_info_str = json.dumps(st.session_state.get('response_info', {}), indent=2)
            response_tables_str = json.dumps(st.session_state.get('response_tables', {}), indent=2)
            response_measures_str = json.dumps(st.session_state.get('response_measures', {}), indent=2)
            response_source_str = json.dumps(st.session_state.get('response_source', {}), indent=2)
            text = f"{t('ui.json_report_info')}\n{response_info_str}\n\n{t('ui.json_report_tables')}\n{response_tables_str}\n\n{t('ui.json_report_measures')}\n{response_measures_str}\n\n{t('ui.json_data_sources')}\n{response_source_str}"
            st.text_area(t('ui.json_area_label'), value=text, height=300)

        col1, col2 = st.columns(2)
        with col1:
            if st.button(t('ui.export_excel'), disabled=st.session_state.button):
                with st.spinner(t('ui.generating_file')):
                    buffer = generate_excel(st.session_state['response_info'], st.session_state['response_tables'], st.session_state['response_measures'], st.session_state['response_source'], st.session_state['measures_df'], st.session_state['df_relationships'], st.session_state['df_colunas'])
                    st.download_button(
                        label=t('ui.download_excel_file'),
                        data=buffer,
                        file_name=report_name+'.xlsx',
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
        with col2:
            if st.button(t('ui.export_word'), disabled=st.session_state.button):
                with st.spinner(t('ui.generating_file')):
                    doc = generate_docx(st.session_state['response_info'], st.session_state['response_tables'], st.session_state['response_measures'], st.session_state['response_source'], st.session_state['measures_df'], st.session_state['df_relationships'], st.session_state['df_colunas'], st.session_state['modelo'], st.session_state.language)
                    buffer = BytesIO()
                    doc.save(buffer)
                    buffer.seek(0)
                    st.download_button(
                        label=t('ui.download_word_file'),
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