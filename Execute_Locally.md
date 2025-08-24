# How to Run Autodoc Locally with Docker

This guide provides a step-by-step walkthrough on how to run Autodoc locally using Docker. It covers creating a Groq account, generating an API key, installing Docker Desktop, and running the Autodoc container.




## Step 1: Create a Groq Account and API Key

First, you need to create a Groq account and generate an API key. This key is required to use the Autodoc application.

1.  **Navigate to the Groq Console:**
    Open your web browser and go to the Groq Console website: [https://console.groq.com/](https://console.groq.com/)

2.  **Create an Account:**
    You can create an account using your Google, GitHub, or email account. Choose your preferred method and follow the on-screen instructions.

3.  **Access API Keys:**
    Once you have created your account and logged in, click on the "API Keys" tab in the left-hand menu.

4.  **Create a New API Key:**
    Click on the "+ Create API Key" button. Give your key a descriptive name and click "Create".

5.  **Copy Your API Key:**
    Your new API key will be displayed. **Copy this key and save it in a secure location.** You will not be able to see it again.




## Step 2: Install Docker Desktop

Next, you need to install Docker Desktop on your computer. Docker Desktop is an application for macOS and Windows machines for the building and sharing of containerized applications.

1.  **Go to the Docker Desktop Website:**
    Open your web browser and go to the Docker Desktop website: [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)

2.  **Download Docker Desktop:**
    Click on the "Download Docker Desktop" button. This will take you to the download page with options for different operating systems.

3.  **Choose Your Operating System:**
    Select the appropriate download for your operating system (macOS, Windows, or Linux).

4.  **Install Docker Desktop:**
    Once the download is complete, run the installer and follow the on-screen instructions to install Docker Desktop on your computer.




## Step 3: Run the Autodoc Container

Now that you have your Groq API key and Docker Desktop installed, you can run the Autodoc container.

1.  **Open a Terminal or Command Prompt:**
    Open a terminal (on macOS or Linux) or a command prompt (on Windows).

2.  **Run the Docker Command:**
    Copy and paste the following command into your terminal, replacing `<YOUR GROQ KEY>` with the API key you generated in Step 1.

    ```bash
    docker rm -f autodoc_v21

    docker run -d --name autodoc_v21 -p 8501:8501 \
      -e "GROQ_API_KEY=<YOUR GROQ KEY>" \
      -e "STREAMLIT_WATCHER_IGNORE_MODULES=torch" \
      -e "AVAILABLE_MODELS=groq/meta-llama/llama-4-maverick-17b-128e-instruct,groq/openai/gpt-oss-120b" \
      lawrenceteixeira/autodoc_v21
    ```

3.  **Access Autodoc:**
    Once the container is running, open your web browser and go to the following URL:

    [http://localhost:8501](http://localhost:8501)

    You should now see the Autodoc application running in your browser.