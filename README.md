# 🦁 Leão Triste — Motor de Análise e Recuperação Tributária

**CRG Gestão Contábil** — Plataforma de análise tributária para supermercados, padarias e restaurantes.

Identifica automaticamente oportunidades de recuperação de PIS, COFINS, ICMS-ST e outros tributos a partir de arquivos SPED e XMLs de NF-e.

---

## Funcionalidades

- **Cadastro de clientes** com CNPJ (preenchimento automático via BrasilAPI)
- **Upload e parsing** de arquivos SPED EFD ICMS/IPI, SPED Contribuições, NF-e XML
- **Análise tributária real** — identifica créditos de PIS/COFINS monofásico, alíquota zero, divergências de NCM
- **Base de NCM** — 404 NCMs com alíquotas, classificação e enquadramento fiscal (CRUD completo)
- **Base de Produtos** — 2.022+ produtos alimentícios com EAN/GTIN e NCM correto (CRUD completo)
- **Comparação NCM** — cruza NCMs das notas fiscais com a base de referência
- **Exportação CSV** — exporta bases de NCM e Produtos para Excel/planilha
- **Dashboard** com KPIs de recuperação e análise
- **Dark/Light mode**

---

## Stack Tecnológica

| Componente | Tecnologia |
|---|---|
| Backend | Python 3.12 + FastAPI |
| Frontend | HTML + CSS + JavaScript (Vanilla) |
| Banco de Dados | SQLite |
| Containerização | Docker + Docker Compose |
| Servidor WSGI | Gunicorn + Uvicorn Workers |

---

## Pré-requisitos

- **Docker** e **Docker Compose** instalados ([instalar Docker](https://docs.docker.com/engine/install/))
- Ou **Python 3.10+** para rodar sem Docker
- Porta 8000 livre (ou configure outra)

---

## Deploy Rápido com Docker (Recomendado)

### 1. Clone o repositório

```bash
git clone https://github.com/SEU_USUARIO/leao-triste.git
cd leao-triste
```

### 2. Configure o ambiente

```bash
cp .env.example .env
# Edite o .env conforme necessário (porta, workers, etc.)
```

### 3. Suba o sistema

```bash
docker compose up -d
```

### 4. Acesse

Abra `http://SEU_IP:8000` no navegador.

### Comandos úteis

```bash
# Ver logs em tempo real
docker compose logs -f app

# Parar o sistema
docker compose down

# Rebuild após mudanças no código
docker compose build && docker compose up -d

# Backup do banco de dados
docker cp leao-triste:/app/data/tax_recovery.db ./backup_$(date +%Y%m%d).db
```

---

## Deploy sem Docker (Python direto)

### 1. Clone e instale dependências

```bash
git clone https://github.com/SEU_USUARIO/leao-triste.git
cd leao-triste
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Inicie o servidor

**Desenvolvimento:**
```bash
python api_server.py
```

**Produção (com Gunicorn):**
```bash
gunicorn api_server:app \
  --worker-class uvicorn.workers.UvicornWorker \
  --workers 4 \
  --bind 0.0.0.0:8000 \
  --timeout 120
```

### 3. Acesse

Abra `http://localhost:8000` no navegador.

---

## Opções de Hospedagem

### Opção 1: VPS (Recomendado para início)
**Custo: R$ 25-50/mês**

Provedores sugeridos:
- [DigitalOcean](https://digitalocean.com) — Droplet básico ($6/mês)
- [Hetzner](https://hetzner.com) — VPS mais barato da Europa (€3.79/mês)
- [Contabo](https://contabo.com) — Excelente custo/benefício
- [Hostinger VPS](https://hostinger.com.br) — Servidores no Brasil (R$ 25/mês)
- [Locaweb Cloud](https://locaweb.com.br) — Datacenter brasileiro

**Passo a passo VPS:**

```bash
# 1. Conectar via SSH
ssh root@SEU_IP

# 2. Instalar Docker
curl -fsSL https://get.docker.com | sh

# 3. Clone o repo
git clone https://github.com/SEU_USUARIO/leao-triste.git
cd leao-triste

# 4. Configurar
cp .env.example .env

# 5. Subir
docker compose up -d

# 6. (Opcional) Configurar domínio + HTTPS
# Instalar Nginx
apt install nginx certbot python3-certbot-nginx -y

# Copiar config do Nginx
cp nginx.conf.example /etc/nginx/conf.d/leao-triste.conf
# EDITE o arquivo para usar seu domínio real

# Obter certificado SSL
certbot --nginx -d fiscal.crggestao.com.br

# Reiniciar Nginx
systemctl restart nginx
```

### Opção 2: Railway / Render (PaaS)
**Custo: $0-7/mês**

Plataformas que fazem deploy direto do GitHub:

- [Railway](https://railway.app) — Deploy automático, plano gratuito generoso
- [Render](https://render.com) — Free tier disponível
- [Fly.io](https://fly.io) — Free tier com 3 máquinas

No Railway, por exemplo:
1. Conecte seu GitHub
2. Selecione o repositório `leao-triste`
3. Railway detecta o Dockerfile automaticamente
4. Deploy automático a cada push

### Opção 3: AWS / GCP / Azure (Cloud Enterprise)
**Para escala maior (múltiplos clientes simultâneos)**

- AWS: ECS Fargate ou EC2 + Docker
- GCP: Cloud Run (serverless) ou GCE
- Azure: App Service ou ACI

---

## Configuração de Domínio

1. Registre um domínio (ex: `fiscal.crggestao.com.br`)
2. Aponte o DNS para o IP do seu servidor:
   - Registro **A** → IP do servidor
3. Configure HTTPS com Let's Encrypt (veja seção VPS acima)
4. Use o arquivo `nginx.conf.example` como base

---

## Estrutura do Projeto

```
leao-triste/
├── api_server.py          # Backend FastAPI (API REST + static files)
├── analysis_engine.py     # Motor de análise tributária
├── sped_parser.py         # Parser de arquivos SPED EFD
├── xml_parser.py          # Parser de NF-e XML
├── ncm_database.py        # Base de 404 NCMs com alíquotas
├── ncm_monofasico.py      # Checker de NCMs monofásicos
├── product_database.py    # Base de 2.022 produtos alimentícios
├── index.html             # Frontend SPA
├── app.js                 # Lógica do frontend
├── styles.css             # Estilos
├── favicon.png            # Ícone do site
├── lion-logo.png          # Logo do Leão Triste
├── lion-logo-medium.png   # Logo médio
├── Dockerfile             # Container Docker
├── docker-compose.yml     # Orquestração Docker
├── requirements.txt       # Dependências Python
├── nginx.conf.example     # Config Nginx (opcional)
├── .env.example           # Variáveis de ambiente (template)
├── .gitignore             # Arquivos ignorados pelo Git
└── README.md              # Este arquivo
```

---

## API Documentation

Com o servidor rodando, acesse:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Endpoints principais

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/health` | Status do sistema |
| `POST` | `/api/clients` | Criar cliente |
| `GET` | `/api/clients` | Listar clientes |
| `POST` | `/api/clients/{id}/upload` | Upload de arquivo |
| `POST` | `/api/clients/{id}/analyze` | Executar análise |
| `GET` | `/api/analyses/{id}` | Resultado da análise |
| `GET` | `/api/ncm/busca` | Buscar NCMs |
| `POST` | `/api/ncm` | Criar NCM |
| `PUT` | `/api/ncm/{code}` | Editar NCM |
| `DELETE` | `/api/ncm/{code}` | Excluir NCM |
| `GET` | `/api/ncm/export/csv` | Exportar NCMs |
| `GET` | `/api/produtos/busca` | Buscar produtos |
| `POST` | `/api/produtos` | Criar produto |
| `PUT` | `/api/produtos/{ean}` | Editar produto |
| `DELETE` | `/api/produtos/remover/{ean}` | Excluir produto |
| `GET` | `/api/produtos/export/csv` | Exportar produtos |

---

## Backup e Manutenção

### Backup do banco de dados

```bash
# Docker
docker cp leao-triste:/app/data/tax_recovery.db ./backup_$(date +%Y%m%d).db

# Sem Docker
cp tax_recovery.db backup_$(date +%Y%m%d).db
```

### Atualização do sistema

```bash
cd leao-triste
git pull
docker compose build
docker compose up -d
```

---

## Segurança (Produção)

Para uso em produção com dados reais de clientes:

- [ ] Configurar HTTPS (obrigatório) via Let's Encrypt
- [ ] Alterar `CORS_ORIGINS` no `.env` para aceitar apenas seu domínio
- [ ] Implementar autenticação de usuários (JWT ou sessão)
- [ ] Configurar firewall (UFW) para permitir apenas portas 80, 443 e SSH
- [ ] Backup automático diário do banco de dados
- [ ] Monitoramento com Uptime Robot ou similar

---

## Licença

Projeto proprietário — CRG Gestão Contábil.
Desenvolvido para uso interno e de clientes da CRG.

---

**CRG Gestão Contábil** — Recuperação Tributária
