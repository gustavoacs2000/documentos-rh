# 1. Imagem base
FROM python:3.11-slim

# 2. Define variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. Instala dependências do sistema operacional
#    - tesseract-ocr: O programa de OCR
#    - tesseract-ocr-por: O pacote de língua portuguesa para o Tesseract
#    - libpq-dev: Necessário para o psycopg2 (Postgres)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-por \
    poppler-utils \
    libpq-dev \
    build-essential \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 4. Define o diretório de trabalho
WORKDIR /app

# 5. Instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copia o código da aplicação
#    (O docker-compose usará um volume para desenvolvimento)
COPY ./src /app/