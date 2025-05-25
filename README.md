# AutoDoc 2025

![AutoDoc](./images/AutoDoc.png)

AutoDoc é uma ferramenta que simplifica e automatiza a documentação de relatórios do Power BI, ideal para administradores e analistas que buscam eficiência e precisão.

---

## Recursos

- **Upload de Modelos Power BI**: Suporte a arquivos `.pbit` e `.zip`.
- **Documentação Detalhada**: Geração automática em Excel e Word, incluindo tabelas, colunas, medidas e fontes de dados.
- **Visualização Interativa**: Visualize dados antes do download.
- **Automação e Precisão**: Processo rápido, confiável e padronizado.

---

## Acesse o AutoDoc Online

[AutoDoc - Documentador de Power BI](https://autodocpbi.fly.dev/)

---

## Funcionalidade de Chat

- **Chat Inteligente sobre o Relatório**: Após gerar ou carregar a documentação, utilize o chat integrado para tirar dúvidas sobre tabelas, medidas DAX, colunas e relacionamentos do seu modelo Power BI. O assistente responde com base nas informações do relatório carregado, fornecendo explicações detalhadas e técnicas.

---

## Fluxo de Trabalho

```mermaid
graph TD
    A[Início] --> B{Escolha o modelo LLM}
    B -->|OpenAI GPT-4.1 nano| C[OpenAI GPT-4.1 mini]
    B -->|Azure OpenAI GPT-41 nano| D[Azure OpenAI GPT-41 nano selecionado]
    B -->|Anthropic Claude 3.7 Sonnet| E[Anthropic Claude 3.7 Sonnet selecionado]
    B -->|Google Gemini 2.5 Pro| F[Google Gemini 2.5 Pro selecionado]
    B -->|Llama 4| G[Llama 4 selecionado]
    C --> H{Escolha a ação inicial}
    D --> H
    E --> H
    F --> H
    G --> H
    H -->|Opção 1| I[Fazer upload do arquivo de modelo Power BI]
    H -->|Opção 2| J[Preencher informações na barra lateral]
    I --> K{Tipo de arquivo}
    K -->|.pbit| L[Processar arquivo .pbit]
    K -->|.zip| M[Processar arquivo .zip]
    J --> N[App ID]
    J --> O[Tenant ID]
    J --> P[Secret Value]
    L --> Q[Preencher informações na barra lateral]
    M --> Q
    N --> R[Fazer upload do arquivo de modelo Power BI]
    O --> R
    P --> R
    Q --> S[Gerar documentação detalhada]
    R --> S
    S --> T[Visualização interativa dos dados]
    T --> U{Escolher formato de saída}
    U -->|Excel| V[Gerar documento Excel]
    U -->|Word| W[Gerar documento Word]
    V --> X[Download da documentação]
    W --> X
    X --> Z[Utilizar Chat para dúvidas sobre o relatório]
    Z --> Y[Fim]
```

---

## Como Usar

1. Preencha App ID, Tenant ID e Secret Value na barra lateral.
2. Faça upload do arquivo `.pbit` ou `.zip`.
3. Visualize os dados e baixe a documentação em Excel ou Word.
4. **Acesse o Chat**: Após processar o relatório, clique no botão "💬 Chat" para abrir o chat. Faça perguntas sobre tabelas, medidas, colunas ou relacionamentos do seu modelo Power BI. O assistente responderá com base nos dados carregados.

---

## Instalação Local

1. **Clone o repositório:**
    ```sh
    git clone https://github.com/LawrenceTeixeira/PBIAutoDoc.git
    cd AutoDoc
    ```

2. **Crie e ative o ambiente virtual:**
    ```sh
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    # macOS/Linux
    source .venv/bin/activate
    ```

3. **Instale as dependências:**
    ```sh
    pip install -r requirements.txt
    pip install --no-cache-dir chunkipy
    ```

4. **Configure as variáveis de ambiente (`.env`):**
    ```env
    OPENAI_API_KEY=your_openai_api_key
    GROQ_API_KEY=your_groq_api_key
    AZURE_API_KEY=your_azure_api_key
    AZURE_API_BASE=your_endpoint # Exemplo: https://<your alias>.openai.azure.com
    AZURE_API_VERSION=your_version # Exemplo: 2024-02-15-preview
    GEMINI_API_KEY=your_gemini_api_key
    ANTHROPIC_API_KEY=your_anthropic_api_key
    ```
    Consulte outros provedores: [LiteLLM Providers](https://docs.litellm.ai/docs/providers)

5. **Execute o aplicativo:**
    ```sh
    streamlit run app.py --server.fileWatcherType none
    python -X utf8 -m streamlit run app.py --server.fileWatcherType none
    ```

---

## Deploy no Fly.io

```sh
flyctl launch
flyctl deploy
```

### Login/Logout no Fly.io

```sh
flyctl auth login
flyctl auth logout
```

### Instalação manual do Fly.io

```sh
curl -L https://fly.io/install.sh | sh
export PATH=/home/codespace/.fly/bin
```

---

## Pré-requisitos

- Windows, macOS ou Linux
- Python 3.10+
- Internet
- Open AI API Key válida

---

## Sobre

AutoDoc é voltado para administradores e analistas de dados que precisam gerar documentação de alta qualidade para relatórios Power BI, utilizando IA para clareza e detalhamento.

---

## Contribuição

Contribuições são bem-vindas! Abra issues ou pull requests para sugerir melhorias.

---

## Licença

MIT. Veja [LICENSE](LICENSE.md).

---

## Autor

- [Lawrence Teixeira - LinkedIn](https://www.linkedin.com/in/lawrenceteixeira/)
- [Lawrence's Blog](https://lawrence.eti.br)

Contato: [Formulário](https://lawrence.eti.br/contact/)

---

> Simplifique e automatize a documentação dos seus relatórios do Power BI com o **AutoDoc**.
