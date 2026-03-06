# 🦁 Leão Triste — Motor de Análise e Recuperação Tributária

> Sistema especializado em identificação de créditos tributários para recuperação fiscal
> Desenvolvido por **CRG Gestão Contábil**

---

## 📋 Visão Geral

O **Leão Triste** é um sistema web completo para análise automática de arquivos fiscais brasileiros (SPED e XML de NF-e), identificando oportunidades de recuperação de créditos tributários de PIS, COFINS e outros tributos.

### Funcionalidades Principais

- 📁 **Upload de Arquivos**: Suporte a SPED Fiscal (EFD-ICMS/IPI), SPED Contribuições (EFD-PIS/COFINS) e XML de NF-e
- 🔍 **Análise Automática**: Identificação de NCMs com tributação monofásica, ST e outras situações especiais
- 💰 **Cálculo de Créditos**: Estimativa de créditos recuperáveis de PIS/COFINS
- 📊 **Relatórios Detalhados**: Visualização por período, por produto e por tipo de crédito
- 🚀 **Deploy Simplificado**: Docker-ready para deploy imediato

---

## 🏗️ Arquitetura

```
leao-triste/
├── api_server.py          # FastAPI — servidor principal
├── analysis_engine.py     # Motor de análise tributária
├── sped_parser.py         # Parser de arquivos SPED
├── xml_parser.py          # Parser de XML NF-e
├── ncm_database.py        # Base de dados NCM
├── ncm_monofasico.py      # NCMs com tributação monofásica
├── product_database.py    # Base de produtos
├── index.html             # Frontend SPA
├── app.js                 # Lógica frontend
├── styles.css             # Estilos
├── Dockerfile             # Container Docker
├── docker-compose.yml     # Orquestração
└── requirements.txt       # Dependências Python
```

---

## 🚀 Deploy Rápido (Docker)

### Pré-requisitos
- Docker 20.10+
- Docker Compose 2.0+

### 1. Clone o repositório
```bash
git clone https://github.com/paulocrggestao/leao-triste.git
cd leao-triste
```

### 2. Configure o ambiente
```bash
cp .env.example .env
# Edite .env com suas configurações
nano .env
```

### 3. Suba o container
```bash
docker-compose up -d
```

### 4. Verifique o status
```bash
docker-compose ps
docker-compose logs -f
```

Acesse: **http://localhost:8000**

---

## 🛠️ Desenvolvimento Local

### Pré-requisitos
- Python 3.12+
- pip

### 1. Crie o ambiente virtual
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# ou
venv\Scripts\activate     # Windows
```

### 2. Instale as dependências
```bash
pip install -r requirements.txt
```

### 3. Configure o ambiente
```bash
cp .env.example .env
```

### 4. Inicie o servidor de desenvolvimento
```bash
uvicorn api_server:app --reload --host 0.0.0.0 --port 8000
```

---

## 📊 Tipos de Análise

### SPED Fiscal (EFD-ICMS/IPI)
- Identificação de NCMs com substituição tributária
- Análise de ICMS-ST pago
- Verificação de CSTs aplicados

### SPED Contribuições (EFD-PIS/COFINS)
- Créditos de PIS/COFINS não aproveitados
- NCMs com tributação monofásica
- Verificação de alíquotas diferenciadas

### XML NF-e
- Análise item a item
- Verificação de CST e NCM
- Identificação de inconsistências

---

## 🔒 Segurança

- Arquivos enviados são processados em memória e descartados
- Sem armazenamento permanente de dados fiscais
- HTTPS recomendado em produção (ver `nginx.conf.example`)

---

## 📄 Licença

Proprietário — CRG Gestão Contábil  
Todos os direitos reservados.

---

## 📞 Contato

**CRG Gestão Contábil**  
🌐 [eco1.com.br](https://eco1.com.br)  
📧 contato@eco1.com.br
