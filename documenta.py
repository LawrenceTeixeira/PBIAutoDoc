import json
from openai import OpenAI
from groq import Groq
from litellm import completion
from io import BytesIO
import pandas as pd
import io
import base64
from streamlit_javascript import st_javascript
from docx import Document
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.shared import Pt, Inches, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from datetime import date
import re
        
def defined_prompt():
    """Retorna o prompt para a documentação do relatório do Power BI."""
    prompt_relatorio = """1 - Você é um documentador especializado em Power BI. Sua função é criar documentações claras e detalhadas para os relatórios, tabelas, medidas e fontes de dados em Power BI. Para cada item, você deve incluir uma descrição compreensiva que ajude os usuários a entenderem sua finalidade e uso no contexto do relatório. Utilize uma linguagem técnica e precisa, mas acessível para usuários com diferentes níveis de conhecimento em Power BI.
2 - Fazer a documentação no formato JSON.
3 - Você deverá dividir em diferentes outputs de acordo com a entrada do usuário, separando em: info_paineis, tabelas, medidas e fonte_de_dados.
4 - Na parte das medidas, você deverá fazer em blocos, das que estiverem sendo solicitadas, mas como continuação do JSON e ao final de todas fechar o JSON igual no exemplo.
5 - Retorne apenas o JSON, sem o ```JSON no inicio e o ``` no final
6 - O JSON deve ser retornado com aspas duplas, não simples.

Instruções Específicas:

Relatórios:
- Título do Relatório
- Descrição do objetivo do relatório
- Principais KPIs e métricas apresentadas
- Público-alvo do relatório
- Exemplos de uso

Formato de Documentação:

Tabelas do Relatório
Nome da Tabela | Descrição da Tabela

Medidas do Relatório
Nome da Medida | Descrição da Medida | Medida DAX

Fontes de Dados
Nome da Fonte de Dados | Descrição da Fonte | Tabelas Contidas no M | Nome da Tabela

Exemplo do JSON:
{
    "Relatorio": {
        "Titulo": "Análise de Vendas Mensais",
        "Descricao": "Este relatório fornece uma visão detalhada das vendas mensais por região e produto. Os principais KPIs incluem receita total, unidades vendidas e margem de lucro. O relatório é destinado aos gerentes de vendas regionais e é atualizado semanalmente para refletir os dados mais recentes.",
        "Principais_KPIs_e_Metricas": [
            "Receita Total",
            "Unidades Vendidas",
            "Margem de Lucro"
        ],
        "Publico_Alvo": "Gerentes de Vendas Regionais",
        "Exemplos_de_Uso": [
            "Identificação de tendências de vendas por região",
            "Comparação de desempenho de produtos"
        ]
    },
    "Tabelas_do_Relatorio": [
        {
            "Nome": "Vendas",
            "Descricao": "Tabela que armazena dados de vendas, incluindo ID do produto, quantidade vendida, preço e data da venda."
        },
        {
            "Nome": "Produtos",
            "Descricao": "Tabela que contém informações detalhadas dos produtos, como nome, categoria e preço unitário."
        }
    ],
    "Medidas_do_Relatorio": [
        {
            "Nome": "Receita Total",
            "Descricao": "Calcula a receita total das vendas somando o preço de venda multiplicado pela quantidade vendida."
        },
        {
            "Nome": "Margem de Lucro",
            "Descricao": "Calcula a margem de lucro subtraindo o custo do preço de venda."
        }
    ],
    "Fontes_de_Dados": [
        {
            "Nome": "SQL Server - Vendas",
            "Descricao": "Base de dados contendo todas as transações de vendas da empresa.",
            "Tabelas_Contidas_no_M": [
                "Vendas",
                "Produtos"
            ],
            "NomeTabela": "Vendas"
        },
        {
            "Nome": "Excel - Orçamento",
            "Descricao": "Planilha contendo dados de orçamento anual por departamento.",
            "Tabelas_Contidas_no_M": [
                "Orçamento"
            ],
            "NomeTabela": "Orçamento"
        }
    ]
}

Abaixo estão dados do relatório do Power BI a ser documentado:"""
    return prompt_relatorio

def client_chat_LiteLLM(modelo, messages):    
    """Interage com qualquer modelo unsando LiteLLM para obter respostas.
       Mais informações em: https://docs.litellm.ai/docs/providers
    """
    try:
        response = completion(
            model=modelo,
            temperature=0,
            max_tokens=4096,
            messages=messages
        )
        response_content = json.loads( response.choices[0].message.content )
    except Exception as e:
        print(f"Erro ao chamar a API da OpenAI, corrigindo automaticamente... {str(e)}")
        response_content = {'error': str(e)}
            
    return response_content

def Documenta(prompt, text, api_key, modelo):
    """Gera a documentação do relatório em formato JSON."""
    
    messages = [
        {"role": "system", "content": "Você é um documentador especializado em relatórios do Power BI."},
        {"role": "user", "content": f"{prompt}\n<INICIO DADOS RELATORIO POWER BI>\n{text}\n<FIM DADOS RELATORIO POWER BI>"}
    ]
    
    print('Usando o modelo:', modelo)
    
    messages.append({"role": "user", "content": "Você deve retornar somente a parte do JSON: 'Relatorio'"})
    response_info = client_chat_LiteLLM(modelo, messages)
    
    messages.append({"role": "user", "content": "Você deve retornar somente a parte do JSON: 'Tabelas_do_Relatorio'"})
    response_tables = client_chat_LiteLLM(modelo, messages)
    
    messages.append({"role": "user", "content": "Você deve retornar somente a parte do JSON: 'Medidas_do_Relatorio'. Se a medida for NaN, não retorne ela."})
    response_measures = client_chat_LiteLLM(modelo, messages)
    
    messages.append({"role": "user", "content": "Você deve retornar somente a parte do JSON: 'Fontes_de_Dados.'"})
    response_source = client_chat_LiteLLM(modelo, messages)
    
    return response_info, response_tables, response_measures, response_source

def set_heading(doc, text, level=1):
    heading = doc.add_heading(level=level)
    run = heading.add_run(text)
    run.bold = True
    run.font.size = Pt(14 + (1 - level) * 2)
    heading.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT

def add_bullet_list(doc, items):
    for item in items:
        paragraph = doc.add_paragraph(style='List Bullet')
        run = paragraph.add_run(item)
        run.font.size = Pt(11)

def set_column_width(column, width):
    for cell in column.cells:
        cell.width = width

def add_table_borders(table):
    for row in table.rows:
        for cell in row.cells:
            tc = cell._element
            tcPr = tc.get_or_add_tcPr()
            tcBorders = OxmlElement('w:tcBorders')
            for border_name in ['top', 'left', 'bottom', 'right']:
                border = OxmlElement(f'w:{border_name}')
                border.set(qn('w:val'), 'single')
                border.set(qn('w:sz'), '4')
                border.set(qn('w:space'), '0')
                border.set(qn('w:color'), '000000')
                tcBorders.append(border)
            tcPr.append(tcBorders)

def style_table_header(cell):
    """Apply style to the table header cell."""
    # Set background color
    cell_fill = cell._element.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:fill'), '000080')  # Navy blue background
    cell_fill.append(shd)
    # Set font color to white
    for paragraph in cell.paragraphs:
        for run in paragraph.runs:
            run.font.color.rgb = RGBColor(255, 255, 255)  # White text

def add_measure_table(doc, measures, measures_df):
    table = doc.add_table(rows=1, cols=3)
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = 'Nome'
    hdr_cells[1].text = 'Descrição'
    hdr_cells[2].text = 'Fórmula DAX'
    
    # Style header cells
    for cell in hdr_cells:
        style_table_header(cell)
    
    # Adjust column widths
    widths = [Inches(1.5), Inches(3.0), Inches(2.5)]  # Set appropriate widths for columns
    for i, width in enumerate(widths):
        set_column_width(table.columns[i], width)
    
    def add_measure_row(measure):
        measure_name = measure["Nome"]
        #expression = measures_df.loc[measures_df['NomeMedida'] == measure_name, 'ExpressaoMedida'].values[0]
        
        matching_rows = measures_df.loc[measures_df['NomeMedida'] == measure_name, 'ExpressaoMedida']
            
        if not matching_rows.empty:
            expression = matching_rows.values[0]
        else:
            # Handle the case where there is no matching measure
            expression = "No mesure found"  # or any default value        
                
        row_cells = table.add_row().cells
        row_cells[0].text = measure_name
        row_cells[1].text = measure["Descricao"]
        row_cells[2].text = expression

    if isinstance(measures, list):
        for measure in measures:
            add_measure_row(measure)
    elif 'Medidas_do_Relatorio' in measures:
        for measure in measures['Medidas_do_Relatorio']:
            add_measure_row(measure)

    for row in table.rows:
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                paragraph.style = 'Body Text'
    
    add_table_borders(table)

def add_report_tables(doc, response_tables):
    table = doc.add_table(rows=1, cols=2)
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = 'Tabela'
    hdr_cells[1].text = 'Descrição'
    
    # Style header cells
    for cell in hdr_cells:
        style_table_header(cell)
    
    # Adjust column widths
    widths = [Inches(2.0), Inches(5.0)]  # Set appropriate widths for columns
    for i, width in enumerate(widths):
        set_column_width(table.columns[i], width)

    def add_table_row(table_info):
        row_cells = table.add_row().cells
        row_cells[0].text = table_info["Nome"]
        row_cells[1].text = table_info["Descricao"]

    if isinstance(response_tables, list):
        for table_info in response_tables:
            add_table_row(table_info)
    elif 'Tabelas_do_Relatorio' in response_tables:
        for table_info in response_tables['Tabelas_do_Relatorio']:
            add_table_row(table_info)
    
    for row in table.rows:
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                paragraph.style = 'Body Text'
    
    add_table_borders(table)

def add_data_sources_table(doc, response_source):
    table = doc.add_table(rows=1, cols=4)
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = 'Nome'
    hdr_cells[1].text = 'Descrição'
    hdr_cells[2].text = 'Tabelas contidas no M'
    hdr_cells[3].text = 'Código M'
    
    # Style header cells
    for cell in hdr_cells:
        style_table_header(cell)
    
    # Adjust column widths
    widths = [Inches(2.0), Inches(3.0), Inches(2.0)]  # Set appropriate widths for columns
    for i, width in enumerate(widths):
        set_column_width(table.columns[i], width)

    def add_source_row(source_info):
        row_cells = table.add_row().cells
        row_cells[0].text = source_info["Nome"]
        row_cells[1].text = source_info["Descricao"]
        row_cells[2].text = ", ".join(source_info["Tabelas_Contidas_no_M"])         
        row_cells[3].text = source_info.get("FonteDados", "N/A")
    
    if isinstance(response_source, list):
        for source_info in response_source:
            add_source_row(source_info)
    elif 'Fontes_de_Dados' in response_source:
        for source_info in response_source['Fontes_de_Dados']:
            add_source_row(source_info)
    
    for row in table.rows:
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                paragraph.style = 'Body Text'
    
    add_table_borders(table)

def add_centered_title(doc, title, color=RGBColor(0, 0, 128)):
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
    run = paragraph.add_run(title)
    run.bold = True
    run.font.size = Pt(20)
    run.font.color.rgb = color

def generate_promt(text):
    
    prompts = defined_prompt().strip()
    
    return f"{prompts}\n<INICIO DADOS RELATORIO POWER BI>\n{text}\n<FIM DADOS RELATORIO POWER BI>"

    
def generate_docx(response_info, response_tables, response_measures, response_source, measures_df):
    """Gera um documento Word com a documentação do relatório."""
    doc = Document()
    
    # Add centered title
    add_centered_title(doc, "AutoDoc - Documentador de Power BI")
        
    # Title and Description
    set_heading(doc, 'Relatório:', level=1)
    doc.add_paragraph(response_info["Relatorio"]["Titulo"], style='Body Text')

    # Data
    set_heading(doc, 'Data:', level=1)
    today = date.today()
    doc.add_paragraph(today.strftime("%d/%m/%Y"), style='Body Text')
    
    set_heading(doc, 'Descrição:', level=1)
    doc.add_paragraph(response_info["Relatorio"]["Descricao"], style='Body Text')
    
    # Main KPIs and Metrics
    set_heading(doc, 'Principais KPIs e Métricas:', level=1)
    add_bullet_list(doc, response_info["Relatorio"]["Principais_KPIs_e_Metricas"])
    
    # Target Audience
    set_heading(doc, 'Público alvo:', level=1)
    doc.add_paragraph(response_info["Relatorio"]["Publico_Alvo"], style='Body Text')
    
    # Use Cases
    set_heading(doc, 'Exemplos de uso:', level=1)
    add_bullet_list(doc, response_info["Relatorio"]["Exemplos_de_Uso"])
    
    # Report Tables
    set_heading(doc, 'Tabelas', level=1)
    add_report_tables(doc, response_tables)
    
    # Report Measures
    set_heading(doc, 'Medidas', level=1)
    add_measure_table(doc, response_measures, measures_df)
    
    # Data Sources
    set_heading(doc, 'Fonte de dados', level=1)
    add_data_sources_table(doc, response_source)

    return doc

def generate_excel(response_info, response_tables, response_measures, response_source, measures_df):
    """Gera um arquivo Excel com a documentação do relatório."""
    buffer = io.BytesIO()
    
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        all_info = []
        all_tables = []
        all_measures = []
        all_sources = []
                
        info = pd.DataFrame([response_info['Relatorio']]).transpose()
        info.reset_index(inplace=True)
        info.columns = ['Informações do relatório', 'Dados']
        all_info.append(info)
        
        if isinstance(response_tables, list):
            tables = pd.DataFrame(response_tables)
        elif 'Tabelas_do_Relatorio' in response_tables:
            tables = pd.DataFrame(response_tables['Tabelas_do_Relatorio'])
        all_tables.append(tables)
        
        if isinstance(response_measures, list):
            measures = pd.DataFrame(response_measures)
        elif 'Medidas_do_Relatorio' in response_measures:
            measures = pd.DataFrame(response_measures['Medidas_do_Relatorio'])
        else:
            measures = pd.DataFrame()
            
        all_measures.append(measures)
        
        if isinstance(response_source, list):
            sources = pd.DataFrame(response_source)
        elif 'Fontes_de_Dados' in response_source:
            sources = pd.DataFrame(response_source['Fontes_de_Dados'])
        all_sources.append(sources)
    
        df_info = pd.concat(all_info, ignore_index=True)
        df_tabelas = pd.concat(all_tables, ignore_index=True)
        df_medidas = pd.concat(all_measures, ignore_index=True)
        df_fontes = pd.concat(all_sources, ignore_index=True)
        
        if 'Nome' in response_measures['Medidas_do_Relatorio']:
            df_medidas = pd.merge(df_medidas, measures_df,  left_on='Nome', right_on='Medida', how='left')
            df_medidas = df_medidas[['Medida', 'Descricao', 'expression']]
    
        df_info.to_excel(writer, sheet_name='info_painel', index=False)
        df_tabelas.to_excel(writer, sheet_name='tabelas', index=False) 
        df_medidas.to_excel(writer, sheet_name='medidas', index=False) 
        df_fontes.to_excel(writer, sheet_name='fonte_de_dados', index=False)
            
    buffer.seek(0)
    return buffer

def text_to_document(df):
    """Gera o texto para documentação baseado nos dados do DataFrame."""
    tables_df = df[df['NomeTabela'].notnull() & df['FonteDados'].notnull()]
    tables_df = tables_df[['NomeTabela', 'FonteDados']].drop_duplicates().reset_index(drop=True)
    
    measures_df = df[df['NomeMedida'].notnull() & df['ExpressaoMedida'].notnull()]
    measures_df = measures_df[['NomeMedida', 'ExpressaoMedida']].drop_duplicates().reset_index(drop=True)
        
    document_text = f"""
    Relatório: {df['ReportName'].iloc[0]}
    
    Tabelas:
    {tables_df['NomeTabela'].to_string(index=False)}
    
    Fontes dos dados das tabelas:
    {tables_df.to_string(index=False)}
    
    Medidas:
    {measures_df.to_string(index=False)}
    """ 
        
    return document_text, measures_df, tables_df
