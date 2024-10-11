# start by pulling the python image
FROM python:3.11.3-slim

# switch working directory
WORKDIR /app

COPY requirements.txt /app/

# install the dependencies and packages in the requirements file
RUN pip install -r requirements.txt

COPY . /app

EXPOSE 8501

ENTRYPOINT ["streamlit", "run", "chat.py", "--server.port=8501", "--server.address=0.0.0.0"]