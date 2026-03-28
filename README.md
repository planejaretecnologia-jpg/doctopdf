# DocToPDF 📄➡️📕

Converta múltiplos arquivos Word (.docx) para PDF de forma simples e rápida.

## Deploy no Railway (recomendado)

1. Crie sua conta em [railway.app](https://railway.app)
2. Suba esses arquivos no GitHub
3. No Railway: **New Project → Deploy from GitHub repo**
4. Selecione o repositório — o deploy é automático!
5. Copie a URL pública gerada e compartilhe 🎉

## Rodar localmente

```bash
pip install flask gunicorn
python app.py
# Acesse: http://localhost:7860
```

## Arquivos

| Arquivo | Descrição |
|---------|-----------|
| `app.py` | Backend Flask com rotas de conversão |
| `index.html` | Interface web |
| `Dockerfile` | Container com LibreOffice + Python |
| `railway.toml` | Config de deploy no Railway |
| `requirements.txt` | Dependências Python |
