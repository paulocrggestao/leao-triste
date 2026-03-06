# ==============================================================================
# Leão Triste — Motor de Análise Tributária
# CRG Gestão Contábil — Recuperação Tributária
# ==============================================================================
FROM python:3.12-slim

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    HOST=0.0.0.0 \
    WORKERS=4 \
    ENVIRONMENT=production

WORKDIR /app

# Instalar dependências do sistema (lxml precisa de libs C)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libxml2-dev \
    libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY api_server.py .
COPY analysis_engine.py .
COPY sped_parser.py .
COPY xml_parser.py .
COPY ncm_database.py .
COPY ncm_monofasico.py .
COPY product_database.py .

# Copiar frontend (servido pelo FastAPI em produção)
COPY index.html .
COPY app.js .
COPY styles.css .
COPY favicon.png .
COPY lion-logo.png .
COPY lion-logo-medium.png .

# Criar diretórios necessários
RUN mkdir -p /app/uploads /app/data

# Volumes para dados persistentes
VOLUME ["/app/data", "/app/uploads"]

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/api/health')" || exit 1

EXPOSE ${PORT}

# Usar gunicorn com uvicorn workers para produção
CMD gunicorn api_server:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers ${WORKERS} \
    --bind ${HOST}:${PORT} \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
