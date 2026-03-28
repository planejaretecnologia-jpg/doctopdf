FROM python:3.11-slim

# Instala LibreOffice e dependências
RUN apt-get update && apt-get install -y \
    libreoffice \
    libreoffice-writer \
    fonts-liberation \
    fonts-dejavu \
    --no-install-recommends \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# Cria pastas necessárias
RUN mkdir -p /tmp/docx_converter/uploads /tmp/docx_converter/outputs

EXPOSE 7860

CMD ["python", "app.py"]
