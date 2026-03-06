#!/usr/bin/env python3
"""
api_server.py — Motor de Análise Tributária
FastAPI backend for CRG Gestão Contábil tax recovery analysis tool.
Serves supermarkets, bakeries, and restaurants in Brazil.

v2.0 — Real file parsing engine (SPED EFD, EFD Contribuições, NFe XML)
Simulated data retained as demo fallback when no real uploads exist.
"""

import hashlib
import json
import logging
import os
import random
import sqlite3
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Real parsers and analysis engine
try:
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from sped_parser import SPEDParser
    from xml_parser import NFeParser
    from analysis_engine import TaxAnalysisEngine
    REAL_ENGINE_AVAILABLE = True
except ImportError as _e:
    REAL_ENGINE_AVAILABLE = False
    logging.warning(f"Real engine modules not available: {_e}")

# NCM Database
try:
    from ncm_database import (
        NCM_DATABASE, lookup_ncm, search_ncm,
        get_ncm_tax_summary, get_ncms_by_category, get_all_categories
    )
    NCM_DB_AVAILABLE = True
except ImportError as _e2:
    NCM_DB_AVAILABLE = False
    logging.warning(f"NCM database not available: {_e2}")

# Product Database
try:
    from product_database import (
        get_all_products as pd_get_all,
        search_products as pd_search,
        get_products_by_ncm as pd_by_ncm,
        get_products_by_category as pd_by_cat,
        get_all_categories as pd_categories,
        get_product_by_ean as pd_by_ean,
        validate_ncm as pd_validate_ncm,
        find_ncm_discrepancies as pd_find_discrepancies,
        get_statistics as pd_statistics,
    )
    PRODUCT_DB_AVAILABLE = True
except ImportError as _e3:
    PRODUCT_DB_AVAILABLE = False
    logging.warning(f"Product database not available: {_e3}")

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────
# Database setup
# ─────────────────────────────────────────────────────────────────────

# Diretórios configuráveis via variáveis de ambiente
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.environ.get("DB_DIR", _BASE_DIR)
_UPLOAD_DIR_ENV = os.environ.get("UPLOAD_DIR", os.path.join(_BASE_DIR, "uploads"))

DB_PATH = os.path.join(_DATA_DIR, "tax_recovery.db")
UPLOAD_DIR = _UPLOAD_DIR_ENV
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(_DATA_DIR, exist_ok=True)

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,
    cnpj TEXT NOT NULL UNIQUE,
    tax_regime TEXT NOT NULL CHECK(tax_regime IN ('simples', 'presumido', 'real')),
    state_uf TEXT NOT NULL,
    activity_sector TEXT NOT NULL CHECK(activity_sector IN ('supermercado', 'padaria', 'restaurante', 'bar', 'farmacia', 'posto_combustivel', 'outro')),
    certificate_file TEXT,
    certificate_password_hash TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS uploads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    file_type TEXT NOT NULL CHECK(file_type IN ('sped_efd', 'sped_contrib', 'nfe_xml', 'pgdas')),
    period_start TEXT,
    period_end TEXT,
    filename TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'processing', 'completed', 'error')),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS tax_analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    upload_id INTEGER REFERENCES uploads(id),
    analysis_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'running', 'completed')),
    total_recovery_amount REAL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS recovery_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_id INTEGER NOT NULL REFERENCES tax_analyses(id) ON DELETE CASCADE,
    tax_type TEXT NOT NULL CHECK(tax_type IN ('pis', 'cofins', 'icms', 'icms_st', 'inss', 'irpj', 'csll')),
    description TEXT NOT NULL,
    ncm_code TEXT,
    period TEXT,
    base_calculo_original REAL DEFAULT 0,
    base_calculo_correta REAL DEFAULT 0,
    aliquota_original REAL DEFAULT 0,
    aliquota_correta REAL DEFAULT 0,
    valor_pago REAL DEFAULT 0,
    valor_devido REAL DEFAULT 0,
    valor_recuperar REAL DEFAULT 0,
    legal_basis TEXT,
    confidence TEXT NOT NULL DEFAULT 'medium' CHECK(confidence IN ('high', 'medium', 'low'))
);

CREATE TABLE IF NOT EXISTS analysis_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_id INTEGER NOT NULL REFERENCES tax_analyses(id) ON DELETE CASCADE,
    report_type TEXT NOT NULL,
    generated_at TEXT NOT NULL DEFAULT (datetime('now')),
    data_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS parsed_fiscal_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    upload_id INTEGER NOT NULL REFERENCES uploads(id) ON DELETE CASCADE,
    client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    source_type TEXT NOT NULL CHECK(source_type IN ('sped_efd', 'sped_contrib', 'nfe_xml')),
    document_number TEXT,
    document_date TEXT,
    ind_oper TEXT,
    ncm_code TEXT,
    cfop TEXT,
    product_description TEXT,
    quantity REAL DEFAULT 0,
    unit_value REAL DEFAULT 0,
    total_value REAL DEFAULT 0,
    cst_icms TEXT,
    base_icms REAL DEFAULT 0,
    aliq_icms REAL DEFAULT 0,
    valor_icms REAL DEFAULT 0,
    base_icms_st REAL DEFAULT 0,
    aliq_icms_st REAL DEFAULT 0,
    valor_icms_st REAL DEFAULT 0,
    cst_pis TEXT,
    base_pis REAL DEFAULT 0,
    aliq_pis REAL DEFAULT 0,
    valor_pis REAL DEFAULT 0,
    cst_cofins TEXT,
    base_cofins REAL DEFAULT 0,
    aliq_cofins REAL DEFAULT 0,
    valor_cofins REAL DEFAULT 0,
    is_monofasico INTEGER DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS simulated_fiscal_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    period TEXT NOT NULL,
    ncm_code TEXT NOT NULL,
    product_description TEXT NOT NULL,
    category TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    unit_value REAL NOT NULL,
    total_value REAL NOT NULL,
    icms_base REAL DEFAULT 0,
    icms_value REAL DEFAULT 0,
    icms_st_base REAL DEFAULT 0,
    icms_st_value REAL DEFAULT 0,
    pis_base REAL DEFAULT 0,
    pis_value REAL DEFAULT 0,
    cofins_base REAL DEFAULT 0,
    cofins_value REAL DEFAULT 0,
    ipi_value REAL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS ncm_comparisons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_id INTEGER NOT NULL REFERENCES tax_analyses(id) ON DELETE CASCADE,
    client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    ean TEXT,
    descricao_nfe TEXT,
    ncm_nfe TEXT NOT NULL,
    ncm_referencia TEXT,
    descricao_referencia TEXT,
    categoria_referencia TEXT,
    status TEXT NOT NULL CHECK(status IN ('ok', 'divergencia', 'nao_cadastrado')),
    impacto_fiscal TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS custom_ncm (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ncm TEXT NOT NULL UNIQUE,
    descricao TEXT NOT NULL,
    capitulo INTEGER,
    secao TEXT,
    categoria TEXT,
    ipi REAL DEFAULT 0,
    pis REAL DEFAULT 0,
    cofins REAL DEFAULT 0,
    pis_cumulativo REAL DEFAULT 0,
    cofins_cumulativo REAL DEFAULT 0,
    cest TEXT DEFAULT '',
    ncm_ex TEXT DEFAULT '',
    monofasico INTEGER DEFAULT 0,
    st_icms INTEGER DEFAULT 0,
    aliquota_zero_pis_cofins INTEGER DEFAULT 0,
    base_legal_pis_cofins TEXT DEFAULT '',
    observacoes TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS custom_produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ean TEXT NOT NULL UNIQUE,
    nome TEXT NOT NULL,
    descricao_generica TEXT DEFAULT '',
    ncm TEXT NOT NULL,
    ncm_descricao TEXT DEFAULT '',
    categoria TEXT DEFAULT '',
    subcategoria TEXT DEFAULT '',
    unidade TEXT DEFAULT 'un',
    monofasico INTEGER DEFAULT 0,
    aliquota_zero INTEGER DEFAULT 0,
    ipi REAL DEFAULT 0,
    cest TEXT DEFAULT '',
    marca_exemplo TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS simulated_payroll (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    period TEXT NOT NULL,
    total_salarios REAL NOT NULL,
    total_ferias REAL NOT NULL,
    terco_ferias REAL NOT NULL,
    aviso_previo_indenizado REAL NOT NULL,
    inss_patronal REAL NOT NULL,
    inss_sobre_verbas_indenizatorias REAL NOT NULL,
    fgts REAL NOT NULL,
    total_folha REAL NOT NULL
);
"""


def get_db():
    """Get a database connection with row factory."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Initialize the database schema."""
    conn = get_db()
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────────────────────────────
# NCM / Product catalog for simulation
# ─────────────────────────────────────────────────────────────────────

# Monofásico NCMs (PIS/COFINS = 0% for Simples Nacional)
MONOFASICO_PRODUCTS = {
    # Cap 22 - Bebidas
    "22021000": ("Água mineral com gás", "bebidas", 2.50, 5.00),
    "22029000": ("Água mineral sem gás", "bebidas", 1.80, 3.50),
    "22030000": ("Cerveja de malte", "bebidas", 4.50, 9.00),
    "22041000": ("Vinho espumante", "bebidas", 25.00, 60.00),
    "22042100": ("Vinho tinto", "bebidas", 15.00, 45.00),
    "22060000": ("Sidra", "bebidas", 8.00, 18.00),
    "22086000": ("Vodka", "bebidas", 20.00, 55.00),
    "22089000": ("Aguardente/cachaça", "bebidas", 8.00, 30.00),
    "22011000": ("Água mineral natural", "bebidas", 1.50, 3.00),
    # Cap 33 - Cosméticos/Higiene
    "33030000": ("Perfume/água de colônia", "higiene", 15.00, 80.00),
    "33041000": ("Batom/maquiagem lábios", "higiene", 8.00, 35.00),
    "33049100": ("Pó facial/talco", "higiene", 5.00, 20.00),
    "33051000": ("Xampu", "higiene", 8.00, 25.00),
    "33061000": ("Creme dental", "higiene", 3.00, 10.00),
    "33069000": ("Desodorante", "higiene", 5.00, 18.00),
    "33072000": ("Sabonete", "higiene", 2.00, 8.00),
    # Cap 30 - Medicamentos
    "30049099": ("Medicamento genérico", "medicamentos", 5.00, 30.00),
    "30042099": ("Medicamento de marca", "medicamentos", 10.00, 60.00),
    # Cap 27 - Combustíveis (not typical for supermarket but for completeness)
    "27101259": ("Gasolina", "combustiveis", 5.00, 6.50),
    "27101921": ("Óleo diesel", "combustiveis", 4.50, 6.00),
}

# Regular products (taxed normally)
REGULAR_PRODUCTS = {
    # Alimentos básicos
    "10063021": ("Arroz branco", "alimentos", 3.50, 8.00),
    "07139090": ("Feijão preto", "alimentos", 4.00, 10.00),
    "11010010": ("Farinha de trigo", "alimentos", 2.50, 6.00),
    "15079011": ("Óleo de soja", "alimentos", 5.00, 12.00),
    "17019900": ("Açúcar cristal", "alimentos", 2.00, 5.00),
    "09012100": ("Café torrado", "alimentos", 10.00, 30.00),
    "04012010": ("Leite integral", "alimentos", 3.00, 6.00),
    "02013000": ("Carne bovina", "alimentos", 25.00, 60.00),
    "02071200": ("Frango inteiro", "alimentos", 8.00, 18.00),
    "16010000": ("Linguiça/embutidos", "alimentos", 12.00, 30.00),
    "19053100": ("Biscoito/bolacha", "alimentos", 3.00, 10.00),
    "19021900": ("Macarrão/massa", "alimentos", 2.50, 8.00),
    "20079999": ("Geleia/doce", "alimentos", 5.00, 15.00),
    "04069090": ("Queijo mussarela", "alimentos", 20.00, 45.00),
    "15171000": ("Margarina", "alimentos", 4.00, 10.00),
    "19059020": ("Pão de forma", "alimentos", 4.00, 10.00),
    "02032900": ("Carne suína", "alimentos", 15.00, 35.00),
    "03034200": ("Atum congelado", "alimentos", 12.00, 28.00),
    # Padaria
    "19059090": ("Pão francês", "padaria", 8.00, 15.00),
    "19054000": ("Torrada", "padaria", 3.00, 8.00),
    "18063100": ("Chocolate em barra", "padaria", 6.00, 20.00),
    "19053200": ("Wafer", "padaria", 4.00, 12.00),
    # Limpeza
    "34022000": ("Detergente", "limpeza", 2.00, 6.00),
    "34011190": ("Sabão em pó", "limpeza", 5.00, 15.00),
    "38089190": ("Desinfetante", "limpeza", 3.00, 10.00),
    "48189090": ("Papel higiênico", "limpeza", 8.00, 20.00),
    # Restaurante
    "21069090": ("Preparação alimentícia", "restaurante", 5.00, 15.00),
    "07099900": ("Hortaliças diversas", "restaurante", 3.00, 10.00),
    "08109090": ("Frutas diversas", "restaurante", 4.00, 12.00),
}

# Sector-specific revenue ranges (monthly in BRL)
SECTOR_REVENUE = {
    "supermercado": (500_000, 2_000_000),
    "padaria": (80_000, 300_000),
    "restaurante": (100_000, 500_000),
    "bar": (60_000, 250_000),
    "farmacia": (150_000, 800_000),
    "posto_combustivel": (800_000, 5_000_000),
    "outro": (100_000, 500_000),
}

# Sector product mix (percentage of revenue from monofásicos)
SECTOR_MONOFASICO_MIX = {
    "supermercado": (0.08, 0.15),   # 8-15% from beverages/hygiene
    "padaria": (0.03, 0.08),        # 3-8%
    "restaurante": (0.05, 0.12),    # 5-12% (more beverages)
    "bar": (0.10, 0.20),            # 10-20% (high beverages)
    "farmacia": (0.25, 0.45),       # 25-45% (medicamentos/cosméticos)
    "posto_combustivel": (0.60, 0.85), # 60-85% (combustíveis)
    "outro": (0.05, 0.12),
}

# State ICMS rates
STATE_ICMS_RATES = {
    "AC": 19.0, "AL": 19.0, "AM": 20.0, "AP": 18.0, "BA": 20.5,
    "CE": 20.0, "DF": 20.0, "ES": 17.0, "GO": 19.0, "MA": 22.0,
    "MG": 18.0, "MS": 17.0, "MT": 17.0, "PA": 19.0, "PB": 20.0,
    "PE": 20.5, "PI": 21.0, "PR": 19.5, "RJ": 22.0, "RN": 20.0,
    "RO": 19.5, "RR": 20.0, "RS": 17.0, "SC": 17.0, "SE": 19.0,
    "SP": 18.0, "TO": 20.0,
}


# ─────────────────────────────────────────────────────────────────────
# Simulation Data Generator
# ─────────────────────────────────────────────────────────────────────

def generate_fiscal_data(client_id: int, sector: str, tax_regime: str, state_uf: str, db_conn):
    """Generate 12 months of realistic simulated fiscal data for a client."""
    random.seed(client_id * 1000)  # Reproducible but unique per client

    rev_min, rev_max = SECTOR_REVENUE[sector]
    base_revenue = random.uniform(rev_min, rev_max)
    mono_min, mono_max = SECTOR_MONOFASICO_MIX[sector]
    mono_share = random.uniform(mono_min, mono_max)

    icms_rate = STATE_ICMS_RATES.get(state_uf, 18.0)

    # Generate 12 months of data
    now = datetime(2026, 3, 1)
    for month_offset in range(12):
        period_date = now - timedelta(days=30 * (month_offset + 1))
        period = period_date.strftime("%Y-%m")

        # Monthly revenue varies ±15%
        monthly_rev = base_revenue * random.uniform(0.85, 1.15)
        mono_rev = monthly_rev * mono_share
        regular_rev = monthly_rev - mono_rev

        # Generate monofásico items
        mono_items = random.sample(list(MONOFASICO_PRODUCTS.items()),
                                   min(8, len(MONOFASICO_PRODUCTS)))
        total_mono_allocated = 0
        for i, (ncm, (desc, cat, price_min, price_max)) in enumerate(mono_items):
            if i == len(mono_items) - 1:
                item_value = mono_rev - total_mono_allocated
            else:
                item_value = mono_rev * random.uniform(0.05, 0.25)
                item_value = min(item_value, mono_rev - total_mono_allocated)
            total_mono_allocated += item_value

            if item_value <= 0:
                continue

            unit_price = random.uniform(price_min, price_max)
            qty = max(1, int(item_value / unit_price))
            total = round(qty * unit_price, 2)

            # For Simples Nacional: monofásicos should have PIS/COFINS = 0
            # but simulate that they were INCORRECTLY charged
            if tax_regime == "simples":
                pis_rate = 0.0065  # Incorrectly charged
                cofins_rate = 0.03
            elif tax_regime == "presumido":
                pis_rate = 0.0065
                cofins_rate = 0.03
            else:  # real
                pis_rate = 0.0165
                cofins_rate = 0.076

            pis_base = total
            pis_value = round(total * pis_rate, 2)
            cofins_base = total
            cofins_value = round(total * cofins_rate, 2)

            icms_base = total
            icms_value = round(total * icms_rate / 100, 2)

            # ICMS-ST: some items have ST with inflated base
            icms_st_base = round(total * random.uniform(1.15, 1.45), 2)  # MVA inflated
            icms_st_value = round(icms_st_base * icms_rate / 100 - icms_value, 2)
            icms_st_value = max(0, icms_st_value)

            db_conn.execute("""
                INSERT INTO simulated_fiscal_data
                (client_id, period, ncm_code, product_description, category,
                 quantity, unit_value, total_value,
                 icms_base, icms_value, icms_st_base, icms_st_value,
                 pis_base, pis_value, cofins_base, cofins_value, ipi_value)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (client_id, period, ncm, desc, cat,
                  qty, round(unit_price, 2), total,
                  icms_base, icms_value, icms_st_base, icms_st_value,
                  pis_base, pis_value, cofins_base, cofins_value, 0))

        # Generate regular product items
        reg_items = random.sample(list(REGULAR_PRODUCTS.items()),
                                  min(15, len(REGULAR_PRODUCTS)))
        total_reg_allocated = 0
        for i, (ncm, (desc, cat, price_min, price_max)) in enumerate(reg_items):
            if i == len(reg_items) - 1:
                item_value = regular_rev - total_reg_allocated
            else:
                item_value = regular_rev * random.uniform(0.03, 0.12)
                item_value = min(item_value, regular_rev - total_reg_allocated)
            total_reg_allocated += item_value

            if item_value <= 0:
                continue

            unit_price = random.uniform(price_min, price_max)
            qty = max(1, int(item_value / unit_price))
            total = round(qty * unit_price, 2)

            if tax_regime == "simples":
                pis_rate = 0.0065
                cofins_rate = 0.03
            elif tax_regime == "presumido":
                pis_rate = 0.0065
                cofins_rate = 0.03
            else:
                pis_rate = 0.0165
                cofins_rate = 0.076

            pis_base = total
            pis_value = round(total * pis_rate, 2)
            cofins_base = total
            cofins_value = round(total * cofins_rate, 2)

            icms_base = total
            icms_value = round(total * icms_rate / 100, 2)

            # ICMS-ST for some products
            has_st = random.random() < 0.3
            if has_st:
                icms_st_base = round(total * random.uniform(1.10, 1.40), 2)
                icms_st_value = round(icms_st_base * icms_rate / 100 - icms_value, 2)
                icms_st_value = max(0, icms_st_value)
            else:
                icms_st_base = 0
                icms_st_value = 0

            db_conn.execute("""
                INSERT INTO simulated_fiscal_data
                (client_id, period, ncm_code, product_description, category,
                 quantity, unit_value, total_value,
                 icms_base, icms_value, icms_st_base, icms_st_value,
                 pis_base, pis_value, cofins_base, cofins_value, ipi_value)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (client_id, period, ncm, desc, cat,
                  qty, round(unit_price, 2), total,
                  icms_base, icms_value, icms_st_base, icms_st_value,
                  pis_base, pis_value, cofins_base, cofins_value, 0))

        # Generate payroll data
        num_employees = {
            "supermercado": random.randint(30, 120),
            "padaria": random.randint(8, 30),
            "restaurante": random.randint(10, 40),
            "bar": random.randint(5, 20),
            "farmacia": random.randint(5, 25),
            "posto_combustivel": random.randint(8, 30),
            "outro": random.randint(8, 35),
        }[sector]

        avg_salary = random.uniform(1800, 3500)
        total_salarios = round(num_employees * avg_salary, 2)
        # Roughly 1/12 of employees on vacation each month
        vacation_employees = max(1, num_employees // 12)
        total_ferias = round(vacation_employees * avg_salary, 2)
        terco_ferias = round(total_ferias / 3, 2)
        # Some employees leave each month
        turnover = max(0, random.randint(0, 3))
        aviso_previo = round(turnover * avg_salary, 2)
        inss_patronal = round(total_salarios * 0.20, 2)
        # INSS incorrectly charged on verbas indenizatórias
        inss_verbas_ind = round((terco_ferias + aviso_previo) * 0.20, 2)
        fgts = round(total_salarios * 0.08, 2)
        total_folha = round(total_salarios + total_ferias + terco_ferias + aviso_previo, 2)

        db_conn.execute("""
            INSERT INTO simulated_payroll
            (client_id, period, total_salarios, total_ferias, terco_ferias,
             aviso_previo_indenizado, inss_patronal, inss_sobre_verbas_indenizatorias,
             fgts, total_folha)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (client_id, period, total_salarios, total_ferias, terco_ferias,
              aviso_previo, inss_patronal, inss_verbas_ind, fgts, total_folha))

    db_conn.commit()


# ─────────────────────────────────────────────────────────────────────
# Real File Processing — SPED and NFe parsers
# ─────────────────────────────────────────────────────────────────────

def detect_file_type_from_content(content: bytes, filename: str, declared_type: str) -> str:
    """
    Auto-detect the actual file type from content.
    Returns: 'sped_efd', 'sped_contrib', 'nfe_xml', 'nfe_zip', 'pgdas'
    """
    fn_lower = (filename or "").lower()

    # Check for ZIP
    if fn_lower.endswith(".zip") or content[:2] == b'PK':
        return "nfe_zip"

    # Check for XML
    if content[:5] in (b'<?xml', b'<nfeP', b'<NFe '):
        return "nfe_xml"
    stripped = content[:100].lstrip()
    if stripped.startswith(b'<'):
        return "nfe_xml"

    # Check SPED: starts with |0000|
    try:
        text_start = content[:500].decode("utf-8", errors="replace").strip()
    except Exception:
        text_start = ""

    if "|0000|" in text_start:
        # Distinguish EFD ICMS from EFD Contribuicoes
        try:
            full_text = content.decode("utf-8", errors="replace")
        except Exception:
            full_text = content.decode("latin-1", errors="replace")
        if REAL_ENGINE_AVAILABLE:
            detected = SPEDParser.detect_file_type(full_text)
            return detected
        # Fallback: check for M200/M600 patterns
        if "|M200|" in full_text or "|M600|" in full_text:
            return "sped_contrib"
        return declared_type if declared_type in ("sped_efd", "sped_contrib") else "sped_efd"

    return declared_type


def process_sped_file(
    client_id: int,
    upload_id: int,
    file_content: bytes,
    file_type: str,
    db_conn,
) -> dict:
    """
    Parse a SPED file and store items in parsed_fiscal_items table.
    Returns summary dict.
    """
    if not REAL_ENGINE_AVAILABLE:
        return {"error": "Real engine not available", "items_stored": 0}

    try:
        parser = SPEDParser(file_content, file_type=file_type)
        parsed = parser.parse()
    except Exception as e:
        return {"error": f"Parse error: {e}", "items_stored": 0}

    items_table = parser.get_items_table()
    opening = parser.get_opening()
    period = opening.get("DT_INI", "")  # DDMMYYYY

    # Reconstruct document date from period
    doc_date = ""
    if len(period) == 8 and period.isdigit():
        # DDMMYYYY → YYYY-MM-DD
        doc_date = f"{period[4:8]}-{period[2:4]}-{period[:2]}"

    items_stored = 0
    errors = []

    # Process document items from raw (with IND_OPER from parent C100)
    c170_with_parent = parser.get_document_items_with_parent()

    for item_rec in c170_with_parent:
        cod_item = item_rec.get("COD_ITEM", "")
        ncm = ""
        descricao = cod_item
        if cod_item and cod_item in items_table:
            ncm = items_table[cod_item].get("COD_NCM", "") or ""
            descricao = items_table[cod_item].get("DESCR_ITEM", cod_item)

        ind_oper = str(item_rec.get("_ind_oper", "1")).strip()
        doc_num = item_rec.get("_doc_num", "")
        doc_item_date = item_rec.get("_doc_date", "") or doc_date

        # Convert DDMMYYYY date
        if len(doc_item_date) == 8 and doc_item_date.isdigit():
            doc_item_date = f"{doc_item_date[4:8]}-{doc_item_date[2:4]}-{doc_item_date[:2]}"

        # Determine monofasico status
        is_mono = 0
        if ncm and REAL_ENGINE_AVAILABLE:
            try:
                from ncm_monofasico import is_monofasico as _is_mono
                is_mono = 1 if _is_mono(ncm) else 0
            except Exception:
                pass

        try:
            db_conn.execute("""
                INSERT INTO parsed_fiscal_items (
                    upload_id, client_id, source_type,
                    document_number, document_date, ind_oper,
                    ncm_code, cfop, product_description,
                    quantity, unit_value, total_value,
                    cst_icms, base_icms, aliq_icms, valor_icms,
                    base_icms_st, aliq_icms_st, valor_icms_st,
                    cst_pis, base_pis, aliq_pis, valor_pis,
                    cst_cofins, base_cofins, aliq_cofins, valor_cofins,
                    is_monofasico
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                upload_id, client_id, file_type,
                doc_num, doc_item_date, ind_oper,
                ncm, str(item_rec.get("CFOP", "") or ""), descricao,
                float(item_rec.get("QTD", 0) or 0),
                0.0,  # unit value not in C170
                float(item_rec.get("VL_ITEM", 0) or 0),
                str(item_rec.get("CST_ICMS", "") or ""),
                float(item_rec.get("VL_BC_ICMS", 0) or 0),
                float(item_rec.get("ALIQ_ICMS", 0) or 0),
                float(item_rec.get("VL_ICMS", 0) or 0),
                float(item_rec.get("VL_BC_ICMS_ST", 0) or 0),
                float(item_rec.get("ALIQ_ST", 0) or 0),
                float(item_rec.get("VL_ICMS_ST", 0) or 0),
                str(item_rec.get("CST_PIS", "") or ""),
                float(item_rec.get("VL_BC_PIS", 0) or 0),
                float(item_rec.get("ALIQ_PIS", 0) or 0),
                float(item_rec.get("VL_PIS", 0) or 0),
                str(item_rec.get("CST_COFINS", "") or ""),
                float(item_rec.get("VL_BC_COFINS", 0) or 0),
                float(item_rec.get("ALIQ_COFINS", 0) or 0),
                float(item_rec.get("VL_COFINS", 0) or 0),
                is_mono,
            ))
            items_stored += 1
        except Exception as e:
            errors.append(str(e))

    db_conn.commit()

    summary = parser.get_summary()
    summary["items_stored"] = items_stored
    summary["errors"] = len(errors)
    return summary


def process_nfe_file(
    client_id: int,
    upload_id: int,
    file_content: bytes,
    is_zip: bool,
    db_conn,
) -> dict:
    """
    Parse NFe XML (or ZIP of XMLs) and store items in parsed_fiscal_items.
    Returns summary dict.
    """
    if not REAL_ENGINE_AVAILABLE:
        return {"error": "Real engine not available", "items_stored": 0}

    parser = NFeParser()
    nfes = []

    try:
        if is_zip:
            nfes = parser.parse_zip(file_content)
        else:
            nfe = parser.parse_xml(file_content)
            if "error" not in nfe:
                nfes = [nfe]
    except Exception as e:
        return {"error": f"Parse error: {e}", "items_stored": 0}

    items_stored = 0
    errors = []

    for nfe_data in nfes:
        if "error" in nfe_data:
            errors.append(nfe_data["error"])
            continue

        doc_num = nfe_data.get("numero", "")
        doc_date = nfe_data.get("data_emissao", "")
        # Normalize date: 2025-01-15T10:00:00-03:00 → 2025-01-15
        if "T" in str(doc_date):
            doc_date = str(doc_date)[:10]
        tipo_op = nfe_data.get("tipo_operacao", "1")
        # NFe tpNF: 0=entrada, 1=saída
        ind_oper = "0" if str(tipo_op).strip() == "0" else "1"

        nfe_items = parser.extract_items(nfe_data)

        for item in nfe_items:
            ncm = str(item.get("ncm", "") or "").strip()
            is_mono = 0
            if ncm:
                try:
                    from ncm_monofasico import is_monofasico as _is_mono
                    is_mono = 1 if _is_mono(ncm) else 0
                except Exception:
                    pass

            try:
                db_conn.execute("""
                    INSERT INTO parsed_fiscal_items (
                        upload_id, client_id, source_type,
                        document_number, document_date, ind_oper,
                        ncm_code, cfop, product_description,
                        quantity, unit_value, total_value,
                        cst_icms, base_icms, aliq_icms, valor_icms,
                        base_icms_st, aliq_icms_st, valor_icms_st,
                        cst_pis, base_pis, aliq_pis, valor_pis,
                        cst_cofins, base_cofins, aliq_cofins, valor_cofins,
                        is_monofasico
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    upload_id, client_id, "nfe_xml",
                    doc_num, doc_date, ind_oper,
                    ncm,
                    str(item.get("cfop", "") or ""),
                    str(item.get("descricao", "") or "")[:500],
                    float(item.get("quantidade", 0) or 0),
                    float(item.get("valor_unitario", 0) or 0),
                    float(item.get("valor_total", 0) or 0),
                    str(item.get("cst_icms", "") or ""),
                    float(item.get("base_icms", 0) or 0),
                    float(item.get("aliq_icms", 0) or 0),
                    float(item.get("valor_icms", 0) or 0),
                    float(item.get("base_icms_st", 0) or 0),
                    float(item.get("aliq_icms_st", 0) or 0),
                    float(item.get("valor_icms_st", 0) or 0),
                    str(item.get("cst_pis", "") or ""),
                    float(item.get("base_pis", 0) or 0),
                    float(item.get("aliq_pis", 0) or 0),
                    float(item.get("valor_pis", 0) or 0),
                    str(item.get("cst_cofins", "") or ""),
                    float(item.get("base_cofins", 0) or 0),
                    float(item.get("aliq_cofins", 0) or 0),
                    float(item.get("valor_cofins", 0) or 0),
                    is_mono,
                ))
                items_stored += 1
            except Exception as e:
                errors.append(str(e))

    db_conn.commit()

    return {
        "nfes_parsed": len(nfes),
        "items_stored": items_stored,
        "errors": len(errors),
    }


def build_parsed_data_for_analysis(
    client_id: int,
    db_conn,
    upload_id: Optional[int] = None,
) -> dict:
    """
    Read stored parsed_fiscal_items and build the structure
    expected by TaxAnalysisEngine.
    """
    query = """
        SELECT pfi.*, u.file_type as upload_file_type
        FROM parsed_fiscal_items pfi
        JOIN uploads u ON pfi.upload_id = u.id
        WHERE pfi.client_id = ?
    """
    params = [client_id]

    if upload_id:
        query += " AND pfi.upload_id = ?"
        params.append(upload_id)

    rows = db_conn.execute(query, params).fetchall()

    if not rows:
        return {"nfe_data": [], "sped_efd_items": [], "sped_contrib_items": []}

    # Group by source type
    nfe_items = []
    sped_efd_items = []
    sped_contrib_items = []

    for row in rows:
        item = {
            "ncm": row["ncm_code"] or "",
            "cfop": row["cfop"] or "",
            "descricao": row["product_description"] or "",
            "quantidade": row["quantity"] or 0,
            "valor_unitario": row["unit_value"] or 0,
            "valor_total": row["total_value"] or 0,
            "cst_icms": row["cst_icms"] or "",
            "base_icms": row["base_icms"] or 0,
            "aliq_icms": row["aliq_icms"] or 0,
            "valor_icms": row["valor_icms"] or 0,
            "base_icms_st": row["base_icms_st"] or 0,
            "aliq_icms_st": row["aliq_icms_st"] or 0,
            "valor_icms_st": row["valor_icms_st"] or 0,
            "cst_pis": row["cst_pis"] or "",
            "base_pis": row["base_pis"] or 0,
            "aliq_pis": row["aliq_pis"] or 0,
            "valor_pis": row["valor_pis"] or 0,
            "cst_cofins": row["cst_cofins"] or "",
            "base_cofins": row["base_cofins"] or 0,
            "aliq_cofins": row["aliq_cofins"] or 0,
            "valor_cofins": row["valor_cofins"] or 0,
            "ind_oper": row["ind_oper"] or "1",
            "document_number": row["document_number"] or "",
            "document_date": row["document_date"] or "",
            "source_type": row["source_type"],
        }

        src = row["source_type"]
        if src == "nfe_xml":
            # Build NFe-like structure
            nfe_items.append({
                "numero": row["document_number"] or "",
                "data_emissao": row["document_date"] or "",
                "tipo_operacao": "0" if str(row["ind_oper"]).strip() == "0" else "1",
                "emitente_cnpj": "",
                "emitente_nome": "",
                "items": [{
                    "ncm": item["ncm"],
                    "cfop": item["cfop"],
                    "descricao": item["descricao"],
                    "quantidade": item["quantidade"],
                    "valor_unitario": item["valor_unitario"],
                    "valor_total": item["valor_total"],
                    "cst_icms": item["cst_icms"],
                    "base_icms": item["base_icms"],
                    "aliq_icms": item["aliq_icms"],
                    "valor_icms": item["valor_icms"],
                    "base_icms_st": item["base_icms_st"],
                    "aliq_icms_st": item["aliq_icms_st"],
                    "valor_icms_st": item["valor_icms_st"],
                    "cst_pis": item["cst_pis"],
                    "base_pis": item["base_pis"],
                    "aliq_pis": item["aliq_pis"],
                    "valor_pis": item["valor_pis"],
                    "cst_cofins": item["cst_cofins"],
                    "base_cofins": item["base_cofins"],
                    "aliq_cofins": item["aliq_cofins"],
                    "valor_cofins": item["valor_cofins"],
                }]
            })
        elif src == "sped_efd":
            sped_efd_items.append(item)
        elif src == "sped_contrib":
            sped_contrib_items.append(item)

    return {
        "nfe_data": nfe_items,
        "sped_efd_items": sped_efd_items,
        "sped_contrib_items": sped_contrib_items,
        "total_rows": len(rows),
    }


def run_real_analysis(client_id: int, analysis_id: int, db_conn) -> list:
    """
    Run real analysis using parsed_fiscal_items stored for this client.
    Returns list of recovery item dicts.
    """
    client = db_conn.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()
    if not client:
        return []

    if not REAL_ENGINE_AVAILABLE:
        return []

    parsed_data = build_parsed_data_for_analysis(client_id, db_conn)
    if not parsed_data["nfe_data"] and not parsed_data["sped_efd_items"] and not parsed_data["sped_contrib_items"]:
        return []

    engine = TaxAnalysisEngine({
        "id": client_id,
        "tax_regime": client["tax_regime"],
        "state_uf": client["state_uf"],
        "activity_sector": client["activity_sector"],
    })

    # Build synthetic SPED-like dicts from stored items for the engine
    sped_efd = None
    sped_contrib = None

    if parsed_data["sped_efd_items"]:
        # Convert stored items to structure expected by analyze_sped_efd
        sped_efd = _build_sped_dict_from_items(parsed_data["sped_efd_items"], "sped_efd")

    if parsed_data["sped_contrib_items"]:
        sped_contrib = _build_sped_dict_from_items(parsed_data["sped_contrib_items"], "sped_contrib")

    nfe_data = parsed_data["nfe_data"] if parsed_data["nfe_data"] else None

    result = engine.run_full_analysis(
        sped_efd=sped_efd,
        sped_contrib=sped_contrib,
        nfe_data=nfe_data,
    )

    # Convert RecoveryItem objects to dicts
    return [item.to_dict() for item in result.items]


def _build_sped_dict_from_items(items: list, file_type: str) -> dict:
    """
    Build a synthetic SPED-like parsed dict from stored items,
    suitable for TaxAnalysisEngine.
    """
    c170_records = []
    c100_records = []

    # Group by document to build C100
    doc_groups: dict = {}
    for item in items:
        doc_num = item.get("document_number", "") or ""
        if doc_num not in doc_groups:
            doc_groups[doc_num] = {
                "items": [],
                "date": item.get("document_date", ""),
                "ind_oper": item.get("ind_oper", "1"),
            }
        doc_groups[doc_num]["items"].append(item)

    for doc_num, doc_info in doc_groups.items():
        total_pis = sum(i.get("valor_pis", 0) or 0 for i in doc_info["items"])
        total_cofins = sum(i.get("valor_cofins", 0) or 0 for i in doc_info["items"])
        total_icms = sum(i.get("valor_icms", 0) or 0 for i in doc_info["items"])
        total_doc = sum(i.get("valor_total", 0) or 0 for i in doc_info["items"])

        # Convert date to DDMMYYYY
        doc_date = doc_info["date"] or ""
        if doc_date and "-" in doc_date:
            parts = doc_date[:10].split("-")
            if len(parts) == 3:
                doc_date = f"{parts[2]}{parts[1]}{parts[0]}"

        c100_records.append({
            "REG": "C100",
            "IND_OPER": doc_info["ind_oper"],
            "NUM_DOC": doc_num,
            "DT_DOC": doc_date,
            "VL_DOC": total_doc,
            "VL_PIS": total_pis,
            "VL_COFINS": total_cofins,
            "VL_ICMS": total_icms,
            "VL_BC_ICMS_ST": 0,
            "VL_ICMS_ST": 0,
        })

        for item in doc_info["items"]:
            c170_rec = {
                "REG": "C170",
                "COD_ITEM": item.get("descricao", "") or "",
                "DESCR_COMPL": item.get("descricao", ""),
                "QTD": item.get("quantidade", 0),
                "VL_ITEM": item.get("valor_total", 0),
                "CFOP": item.get("cfop", ""),
                "CST_ICMS": item.get("cst_icms", ""),
                "VL_BC_ICMS": item.get("base_icms", 0),
                "ALIQ_ICMS": item.get("aliq_icms", 0),
                "VL_ICMS": item.get("valor_icms", 0),
                "VL_BC_ICMS_ST": item.get("base_icms_st", 0),
                "ALIQ_ST": item.get("aliq_icms_st", 0),
                "VL_ICMS_ST": item.get("valor_icms_st", 0),
                "CST_PIS": item.get("cst_pis", ""),
                "VL_BC_PIS": item.get("base_pis", 0),
                "ALIQ_PIS": item.get("aliq_pis", 0),
                "VL_PIS": item.get("valor_pis", 0),
                "CST_COFINS": item.get("cst_cofins", ""),
                "VL_BC_COFINS": item.get("base_cofins", 0),
                "ALIQ_COFINS": item.get("aliq_cofins", 0),
                "VL_COFINS": item.get("valor_cofins", 0),
                "_ind_oper": item.get("ind_oper", "1"),
                "_doc_num": doc_num,
            }
            c170_records.append(c170_rec)

    # Build 0200 items table from unique NCM+description combos
    items_0200 = []
    seen_items = {}
    for item in items:
        desc = item.get("descricao", "") or ""
        ncm = item.get("ncm", "") or ""
        key = desc
        if key and key not in seen_items:
            seen_items[key] = True
            items_0200.append({
                "REG": "0200",
                "COD_ITEM": desc,
                "DESCR_ITEM": desc,
                "COD_NCM": ncm,
            })

    # Detect period from items
    dates = [item.get("document_date", "") for item in items if item.get("document_date")]
    dt_ini = ""
    if dates:
        # Sort and take first
        sorted_dates = sorted(d for d in dates if d)
        if sorted_dates:
            d = sorted_dates[0]
            if "-" in d:
                parts = d[:10].split("-")
                if len(parts) == 3:
                    dt_ini = f"{parts[2]}{parts[1]}{parts[0]}"

    return {
        "0000": [{"REG": "0000", "DT_INI": dt_ini, "CNPJ": "", "NOME": ""}],
        "0200": items_0200,
        "C100": c100_records,
        "C170": c170_records,
        "_meta": {"file_type": file_type, "line_count": len(c170_records)},
    }


def client_has_real_uploads(client_id: int, db_conn) -> bool:
    """Check if client has any completed real file uploads with parsed items."""
    count = db_conn.execute("""
        SELECT COUNT(*) as c FROM parsed_fiscal_items WHERE client_id = ?
    """, (client_id,)).fetchone()["c"]
    return count > 0


# ─────────────────────────────────────────────────────────────────────
# Tax Analysis Engine
# ─────────────────────────────────────────────────────────────────────

MONOFASICO_NCMS = set(MONOFASICO_PRODUCTS.keys())

# NCM chapters that are monofásicos
MONOFASICO_CHAPTERS = {"22", "33", "30", "27", "40"}


def is_monofasico(ncm: str) -> bool:
    """Check if NCM is monofásico (chapters 22, 33, 30, 27, 40)."""
    return ncm[:2] in MONOFASICO_CHAPTERS or ncm in MONOFASICO_NCMS


def run_analysis_simples(client_id: int, analysis_id: int, state_uf: str, db_conn):
    """
    Simples Nacional analysis:
    - Monofásicos PIS/COFINS recovery
    - ICMS-ST ressarcimento
    - INSS verbas indenizatórias
    """
    items = []
    icms_rate = STATE_ICMS_RATES.get(state_uf, 18.0)

    # 1. Monofásicos PIS/COFINS
    rows = db_conn.execute("""
        SELECT ncm_code, product_description, period,
               SUM(pis_base) as pis_base, SUM(pis_value) as pis_value,
               SUM(cofins_base) as cofins_base, SUM(cofins_value) as cofins_value,
               SUM(total_value) as total_value
        FROM simulated_fiscal_data
        WHERE client_id = ? AND ncm_code IN ({})
        GROUP BY ncm_code, period
    """.format(",".join(f"'{n}'" for n in MONOFASICO_NCMS)), (client_id,)).fetchall()

    for row in rows:
        ncm = row["ncm_code"]
        period = row["period"]
        desc = row["product_description"]

        # PIS recovery
        if row["pis_value"] > 0:
            items.append({
                "tax_type": "pis",
                "description": f"PIS monofásico indevido - {desc} (NCM {ncm})",
                "ncm_code": ncm,
                "period": period,
                "base_calculo_original": round(row["pis_base"], 2),
                "base_calculo_correta": 0,
                "aliquota_original": 0.65,
                "aliquota_correta": 0,
                "valor_pago": round(row["pis_value"], 2),
                "valor_devido": 0,
                "valor_recuperar": round(row["pis_value"], 2),
                "legal_basis": "Lei 10.147/2000, Art. 2º; LC 123/2006, Art. 18, §4º-A, IV",
                "confidence": "high"
            })

        # COFINS recovery
        if row["cofins_value"] > 0:
            items.append({
                "tax_type": "cofins",
                "description": f"COFINS monofásico indevido - {desc} (NCM {ncm})",
                "ncm_code": ncm,
                "period": period,
                "base_calculo_original": round(row["cofins_base"], 2),
                "base_calculo_correta": 0,
                "aliquota_original": 3.0,
                "aliquota_correta": 0,
                "valor_pago": round(row["cofins_value"], 2),
                "valor_devido": 0,
                "valor_recuperar": round(row["cofins_value"], 2),
                "legal_basis": "Lei 10.147/2000, Art. 2º; LC 123/2006, Art. 18, §4º-A, IV",
                "confidence": "high"
            })

    # 2. ICMS-ST ressarcimento (when effective base < presumed base)
    st_rows = db_conn.execute("""
        SELECT ncm_code, product_description, period,
               SUM(icms_st_base) as st_base, SUM(icms_st_value) as st_value,
               SUM(total_value) as total_value, SUM(icms_value) as icms_value
        FROM simulated_fiscal_data
        WHERE client_id = ? AND icms_st_value > 0
        GROUP BY ncm_code, period
    """, (client_id,)).fetchall()

    for row in st_rows:
        # Simulate that effective sale price was lower than presumed MVA base
        effective_base = round(row["total_value"] * random.uniform(0.80, 0.95), 2)
        presumed_base = round(row["st_base"], 2)

        if effective_base < presumed_base:
            icms_st_pago = round(row["st_value"], 2)
            icms_st_devido = round((effective_base - row["total_value"]) * icms_rate / 100, 2)
            icms_st_devido = max(0, icms_st_devido)
            recovery = round(icms_st_pago - icms_st_devido, 2)

            if recovery > 0:
                items.append({
                    "tax_type": "icms_st",
                    "description": f"ICMS-ST ressarcimento - {row['product_description']} (NCM {row['ncm_code']})",
                    "ncm_code": row["ncm_code"],
                    "period": row["period"],
                    "base_calculo_original": presumed_base,
                    "base_calculo_correta": effective_base,
                    "aliquota_original": icms_rate,
                    "aliquota_correta": icms_rate,
                    "valor_pago": icms_st_pago,
                    "valor_devido": icms_st_devido,
                    "valor_recuperar": recovery,
                    "legal_basis": "CF/88, Art. 150, §7º; RICMS do Estado; Tema 201 STF (ADI 2.777)",
                    "confidence": "medium"
                })

    # 3. INSS sobre verbas indenizatórias
    payroll_rows = db_conn.execute("""
        SELECT period, terco_ferias, aviso_previo_indenizado,
               inss_sobre_verbas_indenizatorias
        FROM simulated_payroll WHERE client_id = ?
    """, (client_id,)).fetchall()

    for row in payroll_rows:
        inss_indevido = round(row["inss_sobre_verbas_indenizatorias"], 2)
        if inss_indevido > 0:
            base_ind = round(row["terco_ferias"] + row["aviso_previo_indenizado"], 2)
            items.append({
                "tax_type": "inss",
                "description": f"INSS patronal sobre 1/3 férias e aviso prévio indenizado",
                "ncm_code": None,
                "period": row["period"],
                "base_calculo_original": base_ind,
                "base_calculo_correta": 0,
                "aliquota_original": 20.0,
                "aliquota_correta": 0,
                "valor_pago": inss_indevido,
                "valor_devido": 0,
                "valor_recuperar": inss_indevido,
                "legal_basis": "Tema 985 STJ (REsp 1.230.957); Súmula 89 CARF",
                "confidence": "high"
            })

    return items


def run_analysis_presumido(client_id: int, analysis_id: int, state_uf: str, db_conn):
    """
    Lucro Presumido analysis:
    - IRPJ/CSLL base de cálculo verification
    - PIS/COFINS cumulativo credit opportunities
    - INSS sobre verbas indenizatórias
    - ICMS-ST ressarcimento
    """
    items = []
    icms_rate = STATE_ICMS_RATES.get(state_uf, 18.0)

    # 1. IRPJ/CSLL base verification
    # For comércio, presunção = 8% IRPJ, 12% CSLL
    # Check if ICMS was included in the base (shouldn't be after Tema 69)
    fiscal_totals = db_conn.execute("""
        SELECT period,
               SUM(total_value) as faturamento,
               SUM(icms_value) as icms_total
        FROM simulated_fiscal_data
        WHERE client_id = ?
        GROUP BY period
    """, (client_id,)).fetchall()

    for row in fiscal_totals:
        faturamento = row["faturamento"]
        icms_total = row["icms_total"]

        # IRPJ: base original includes ICMS, should exclude
        irpj_base_original = round(faturamento * 0.08, 2)
        irpj_base_correta = round((faturamento - icms_total) * 0.08, 2)
        irpj_pago = round(irpj_base_original * 0.15, 2)
        irpj_devido = round(irpj_base_correta * 0.15, 2)
        irpj_recovery = round(irpj_pago - irpj_devido, 2)

        if irpj_recovery > 100:
            items.append({
                "tax_type": "irpj",
                "description": "IRPJ - Exclusão do ICMS da base de presunção",
                "ncm_code": None,
                "period": row["period"],
                "base_calculo_original": irpj_base_original,
                "base_calculo_correta": irpj_base_correta,
                "aliquota_original": 15.0,
                "aliquota_correta": 15.0,
                "valor_pago": irpj_pago,
                "valor_devido": irpj_devido,
                "valor_recuperar": irpj_recovery,
                "legal_basis": "Tema 69 STF (RE 574.706); IN RFB 1.911/2019",
                "confidence": "medium"
            })

        # CSLL
        csll_base_original = round(faturamento * 0.12, 2)
        csll_base_correta = round((faturamento - icms_total) * 0.12, 2)
        csll_pago = round(csll_base_original * 0.09, 2)
        csll_devido = round(csll_base_correta * 0.09, 2)
        csll_recovery = round(csll_pago - csll_devido, 2)

        if csll_recovery > 100:
            items.append({
                "tax_type": "csll",
                "description": "CSLL - Exclusão do ICMS da base de presunção",
                "ncm_code": None,
                "period": row["period"],
                "base_calculo_original": csll_base_original,
                "base_calculo_correta": csll_base_correta,
                "aliquota_original": 9.0,
                "aliquota_correta": 9.0,
                "valor_pago": csll_pago,
                "valor_devido": csll_devido,
                "valor_recuperar": csll_recovery,
                "legal_basis": "Tema 69 STF (RE 574.706); extensão analógica CSLL",
                "confidence": "low"
            })

    # 2. PIS/COFINS cumulativo — check monofásicos (same logic, lower rates)
    mono_rows = db_conn.execute("""
        SELECT ncm_code, product_description, period,
               SUM(pis_value) as pis_value, SUM(cofins_value) as cofins_value,
               SUM(pis_base) as pis_base, SUM(cofins_base) as cofins_base
        FROM simulated_fiscal_data
        WHERE client_id = ? AND ncm_code IN ({})
        GROUP BY ncm_code, period
    """.format(",".join(f"'{n}'" for n in MONOFASICO_NCMS)), (client_id,)).fetchall()

    for row in mono_rows:
        # Even in Lucro Presumido, monofásicos have reduced/zero PIS-COFINS for reseller
        if row["pis_value"] > 0:
            items.append({
                "tax_type": "pis",
                "description": f"PIS monofásico - alíquota zero revenda - {row['product_description']}",
                "ncm_code": row["ncm_code"],
                "period": row["period"],
                "base_calculo_original": round(row["pis_base"], 2),
                "base_calculo_correta": 0,
                "aliquota_original": 0.65,
                "aliquota_correta": 0,
                "valor_pago": round(row["pis_value"], 2),
                "valor_devido": 0,
                "valor_recuperar": round(row["pis_value"], 2),
                "legal_basis": "Lei 10.147/2000, Art. 2º; Lei 10.833/2003, Art. 58-J a 58-V",
                "confidence": "high"
            })

        if row["cofins_value"] > 0:
            items.append({
                "tax_type": "cofins",
                "description": f"COFINS monofásico - alíquota zero revenda - {row['product_description']}",
                "ncm_code": row["ncm_code"],
                "period": row["period"],
                "base_calculo_original": round(row["cofins_base"], 2),
                "base_calculo_correta": 0,
                "aliquota_original": 3.0,
                "aliquota_correta": 0,
                "valor_pago": round(row["cofins_value"], 2),
                "valor_devido": 0,
                "valor_recuperar": round(row["cofins_value"], 2),
                "legal_basis": "Lei 10.147/2000, Art. 2º; Lei 10.833/2003, Art. 58-J a 58-V",
                "confidence": "high"
            })

    # 3. ICMS-ST ressarcimento
    st_rows = db_conn.execute("""
        SELECT ncm_code, product_description, period,
               SUM(icms_st_base) as st_base, SUM(icms_st_value) as st_value,
               SUM(total_value) as total_value
        FROM simulated_fiscal_data
        WHERE client_id = ? AND icms_st_value > 0
        GROUP BY ncm_code, period
    """, (client_id,)).fetchall()

    for row in st_rows:
        effective_base = round(row["total_value"] * random.uniform(0.78, 0.93), 2)
        presumed_base = round(row["st_base"], 2)
        if effective_base < presumed_base:
            st_pago = round(row["st_value"], 2)
            st_devido = round(max(0, (effective_base - row["total_value"]) * icms_rate / 100), 2)
            recovery = round(st_pago - st_devido, 2)
            if recovery > 0:
                items.append({
                    "tax_type": "icms_st",
                    "description": f"ICMS-ST ressarcimento - {row['product_description']}",
                    "ncm_code": row["ncm_code"],
                    "period": row["period"],
                    "base_calculo_original": presumed_base,
                    "base_calculo_correta": effective_base,
                    "aliquota_original": icms_rate,
                    "aliquota_correta": icms_rate,
                    "valor_pago": st_pago,
                    "valor_devido": st_devido,
                    "valor_recuperar": recovery,
                    "legal_basis": "CF/88, Art. 150, §7º; Tema 201 STF",
                    "confidence": "medium"
                })

    # 4. INSS sobre verbas indenizatórias
    payroll_rows = db_conn.execute("""
        SELECT period, terco_ferias, aviso_previo_indenizado,
               inss_sobre_verbas_indenizatorias
        FROM simulated_payroll WHERE client_id = ?
    """, (client_id,)).fetchall()

    for row in payroll_rows:
        inss_indevido = round(row["inss_sobre_verbas_indenizatorias"], 2)
        if inss_indevido > 0:
            base_ind = round(row["terco_ferias"] + row["aviso_previo_indenizado"], 2)
            items.append({
                "tax_type": "inss",
                "description": "INSS patronal sobre verbas indenizatórias (1/3 férias + aviso prévio)",
                "ncm_code": None,
                "period": row["period"],
                "base_calculo_original": base_ind,
                "base_calculo_correta": 0,
                "aliquota_original": 20.0,
                "aliquota_correta": 0,
                "valor_pago": inss_indevido,
                "valor_devido": 0,
                "valor_recuperar": inss_indevido,
                "legal_basis": "Tema 985 STJ (REsp 1.230.957)",
                "confidence": "high"
            })

    return items


def run_analysis_real(client_id: int, analysis_id: int, state_uf: str, db_conn):
    """
    Lucro Real analysis:
    - PIS/COFINS não-cumulativo: créditos sobre insumos
    - Exclusão do ICMS da base de PIS/COFINS (Tema 69 STF)
    - ICMS-ST ressarcimento
    - Créditos de ICMS não aproveitados
    - INSS sobre verbas indenizatórias
    """
    items = []
    icms_rate = STATE_ICMS_RATES.get(state_uf, 18.0)

    # 1. Tema 69 - Exclusão do ICMS da base de PIS/COFINS
    fiscal_totals = db_conn.execute("""
        SELECT period,
               SUM(total_value) as faturamento,
               SUM(icms_value) as icms_total,
               SUM(pis_value) as pis_total,
               SUM(cofins_value) as cofins_total,
               SUM(pis_base) as pis_base_total,
               SUM(cofins_base) as cofins_base_total
        FROM simulated_fiscal_data
        WHERE client_id = ?
        GROUP BY period
    """, (client_id,)).fetchall()

    for row in fiscal_totals:
        icms_total = row["icms_total"]
        faturamento = row["faturamento"]

        # PIS: base should exclude ICMS
        pis_base_original = round(row["pis_base_total"], 2)
        pis_base_correta = round(pis_base_original - icms_total, 2)
        pis_pago = round(row["pis_total"], 2)
        pis_devido = round(pis_base_correta * 0.0165, 2)
        pis_recovery = round(pis_pago - pis_devido, 2)

        if pis_recovery > 100:
            items.append({
                "tax_type": "pis",
                "description": "PIS - Exclusão do ICMS da base de cálculo (Tema 69 STF)",
                "ncm_code": None,
                "period": row["period"],
                "base_calculo_original": pis_base_original,
                "base_calculo_correta": pis_base_correta,
                "aliquota_original": 1.65,
                "aliquota_correta": 1.65,
                "valor_pago": pis_pago,
                "valor_devido": pis_devido,
                "valor_recuperar": pis_recovery,
                "legal_basis": "Tema 69 STF (RE 574.706/PR); Lei 12.973/2014",
                "confidence": "high"
            })

        # COFINS: base should exclude ICMS
        cofins_base_original = round(row["cofins_base_total"], 2)
        cofins_base_correta = round(cofins_base_original - icms_total, 2)
        cofins_pago = round(row["cofins_total"], 2)
        cofins_devido = round(cofins_base_correta * 0.076, 2)
        cofins_recovery = round(cofins_pago - cofins_devido, 2)

        if cofins_recovery > 100:
            items.append({
                "tax_type": "cofins",
                "description": "COFINS - Exclusão do ICMS da base de cálculo (Tema 69 STF)",
                "ncm_code": None,
                "period": row["period"],
                "base_calculo_original": cofins_base_original,
                "base_calculo_correta": cofins_base_correta,
                "aliquota_original": 7.6,
                "aliquota_correta": 7.6,
                "valor_pago": cofins_pago,
                "valor_devido": cofins_devido,
                "valor_recuperar": cofins_recovery,
                "legal_basis": "Tema 69 STF (RE 574.706/PR); Lei 12.973/2014",
                "confidence": "high"
            })

    # 2. PIS/COFINS créditos sobre insumos (energy, rent, freight, depreciation)
    for row in fiscal_totals:
        faturamento = row["faturamento"]

        # Simulate energy costs (2-4% of revenue)
        energia = round(faturamento * random.uniform(0.02, 0.04), 2)
        pis_credito_energia = round(energia * 0.0165, 2)
        cofins_credito_energia = round(energia * 0.076, 2)

        items.append({
            "tax_type": "pis",
            "description": "PIS crédito sobre energia elétrica (insumo)",
            "ncm_code": None,
            "period": row["period"],
            "base_calculo_original": 0,
            "base_calculo_correta": energia,
            "aliquota_original": 0,
            "aliquota_correta": 1.65,
            "valor_pago": 0,
            "valor_devido": 0,
            "valor_recuperar": pis_credito_energia,
            "legal_basis": "Lei 10.637/2002, Art. 3º, III; Parecer Normativo COSIT 5/2018",
            "confidence": "medium"
        })

        items.append({
            "tax_type": "cofins",
            "description": "COFINS crédito sobre energia elétrica (insumo)",
            "ncm_code": None,
            "period": row["period"],
            "base_calculo_original": 0,
            "base_calculo_correta": energia,
            "aliquota_original": 0,
            "aliquota_correta": 7.6,
            "valor_pago": 0,
            "valor_devido": 0,
            "valor_recuperar": cofins_credito_energia,
            "legal_basis": "Lei 10.833/2003, Art. 3º, III; Parecer Normativo COSIT 5/2018",
            "confidence": "medium"
        })

        # Simulate rent costs (3-6% of revenue)
        aluguel = round(faturamento * random.uniform(0.03, 0.06), 2)
        pis_credito_aluguel = round(aluguel * 0.0165, 2)
        cofins_credito_aluguel = round(aluguel * 0.076, 2)

        items.append({
            "tax_type": "pis",
            "description": "PIS crédito sobre aluguel de imóvel",
            "ncm_code": None,
            "period": row["period"],
            "base_calculo_original": 0,
            "base_calculo_correta": aluguel,
            "aliquota_original": 0,
            "aliquota_correta": 1.65,
            "valor_pago": 0,
            "valor_devido": 0,
            "valor_recuperar": pis_credito_aluguel,
            "legal_basis": "Lei 10.637/2002, Art. 3º, IV",
            "confidence": "high"
        })

        items.append({
            "tax_type": "cofins",
            "description": "COFINS crédito sobre aluguel de imóvel",
            "ncm_code": None,
            "period": row["period"],
            "base_calculo_original": 0,
            "base_calculo_correta": aluguel,
            "aliquota_original": 0,
            "aliquota_correta": 7.6,
            "valor_pago": 0,
            "valor_devido": 0,
            "valor_recuperar": cofins_credito_aluguel,
            "legal_basis": "Lei 10.833/2003, Art. 3º, IV",
            "confidence": "high"
        })

        # Simulate freight costs (1-3% of revenue)
        frete = round(faturamento * random.uniform(0.01, 0.03), 2)
        pis_credito_frete = round(frete * 0.0165, 2)
        cofins_credito_frete = round(frete * 0.076, 2)

        items.append({
            "tax_type": "pis",
            "description": "PIS crédito sobre frete na aquisição de mercadorias",
            "ncm_code": None,
            "period": row["period"],
            "base_calculo_original": 0,
            "base_calculo_correta": frete,
            "aliquota_original": 0,
            "aliquota_correta": 1.65,
            "valor_pago": 0,
            "valor_devido": 0,
            "valor_recuperar": pis_credito_frete,
            "legal_basis": "Lei 10.637/2002, Art. 3º, IX",
            "confidence": "medium"
        })

        items.append({
            "tax_type": "cofins",
            "description": "COFINS crédito sobre frete na aquisição de mercadorias",
            "ncm_code": None,
            "period": row["period"],
            "base_calculo_original": 0,
            "base_calculo_correta": frete,
            "aliquota_original": 0,
            "aliquota_correta": 7.6,
            "valor_pago": 0,
            "valor_devido": 0,
            "valor_recuperar": cofins_credito_frete,
            "legal_basis": "Lei 10.833/2003, Art. 3º, IX",
            "confidence": "medium"
        })

    # 3. ICMS créditos não aproveitados (simulate 1-2% of ICMS paid not credited)
    for row in fiscal_totals:
        icms_total = row["icms_total"]
        icms_nao_creditado = round(icms_total * random.uniform(0.01, 0.03), 2)
        if icms_nao_creditado > 50:
            items.append({
                "tax_type": "icms",
                "description": "ICMS créditos não aproveitados sobre aquisições",
                "ncm_code": None,
                "period": row["period"],
                "base_calculo_original": 0,
                "base_calculo_correta": round(icms_nao_creditado / (icms_rate / 100), 2),
                "aliquota_original": 0,
                "aliquota_correta": icms_rate,
                "valor_pago": 0,
                "valor_devido": 0,
                "valor_recuperar": icms_nao_creditado,
                "legal_basis": "RICMS do Estado; CF/88, Art. 155, §2º, I",
                "confidence": "low"
            })

    # 4. ICMS-ST ressarcimento
    st_rows = db_conn.execute("""
        SELECT ncm_code, product_description, period,
               SUM(icms_st_base) as st_base, SUM(icms_st_value) as st_value,
               SUM(total_value) as total_value
        FROM simulated_fiscal_data
        WHERE client_id = ? AND icms_st_value > 0
        GROUP BY ncm_code, period
    """, (client_id,)).fetchall()

    for row in st_rows:
        effective_base = round(row["total_value"] * random.uniform(0.75, 0.92), 2)
        presumed_base = round(row["st_base"], 2)
        if effective_base < presumed_base:
            st_pago = round(row["st_value"], 2)
            st_devido = round(max(0, (effective_base - row["total_value"]) * icms_rate / 100), 2)
            recovery = round(st_pago - st_devido, 2)
            if recovery > 0:
                items.append({
                    "tax_type": "icms_st",
                    "description": f"ICMS-ST ressarcimento - {row['product_description']}",
                    "ncm_code": row["ncm_code"],
                    "period": row["period"],
                    "base_calculo_original": presumed_base,
                    "base_calculo_correta": effective_base,
                    "aliquota_original": icms_rate,
                    "aliquota_correta": icms_rate,
                    "valor_pago": st_pago,
                    "valor_devido": st_devido,
                    "valor_recuperar": recovery,
                    "legal_basis": "CF/88, Art. 150, §7º; Tema 201 STF",
                    "confidence": "medium"
                })

    # 5. INSS sobre verbas indenizatórias
    payroll_rows = db_conn.execute("""
        SELECT period, terco_ferias, aviso_previo_indenizado,
               inss_sobre_verbas_indenizatorias
        FROM simulated_payroll WHERE client_id = ?
    """, (client_id,)).fetchall()

    for row in payroll_rows:
        inss_indevido = round(row["inss_sobre_verbas_indenizatorias"], 2)
        if inss_indevido > 0:
            base_ind = round(row["terco_ferias"] + row["aviso_previo_indenizado"], 2)
            items.append({
                "tax_type": "inss",
                "description": "INSS patronal sobre verbas indenizatórias (1/3 férias + aviso prévio)",
                "ncm_code": None,
                "period": row["period"],
                "base_calculo_original": base_ind,
                "base_calculo_correta": 0,
                "aliquota_original": 20.0,
                "aliquota_correta": 0,
                "valor_pago": inss_indevido,
                "valor_devido": 0,
                "valor_recuperar": inss_indevido,
                "legal_basis": "Tema 985 STJ (REsp 1.230.957)",
                "confidence": "high"
            })

    return items


def _run_simulated_analysis(
    client_id: int,
    analysis_id: int,
    tax_regime: str,
    state_uf: str,
    db_conn,
) -> list:
    """Run simulated analysis (demo fallback). Dispatches by regime."""
    if tax_regime == "simples":
        return run_analysis_simples(client_id, analysis_id, state_uf, db_conn)
    elif tax_regime == "presumido":
        return run_analysis_presumido(client_id, analysis_id, state_uf, db_conn)
    elif tax_regime == "real":
        return run_analysis_real(client_id, analysis_id, state_uf, db_conn)
    return []


def run_ncm_comparison(client_id: int, analysis_id: int, db_conn):
    """
    Compare client's product NCMs (from parsed fiscal items) against
    the reference product database. Stores results in ncm_comparisons table.
    """
    if not PRODUCT_DB_AVAILABLE:
        return

    # Get all unique products from parsed_fiscal_items for this client
    rows = db_conn.execute("""
        SELECT DISTINCT ncm_code, product_description
        FROM parsed_fiscal_items
        WHERE client_id = ? AND ncm_code IS NOT NULL AND ncm_code != ''
    """, (client_id,)).fetchall()

    if not rows:
        # Also check simulated_fiscal_data
        rows = db_conn.execute("""
            SELECT DISTINCT ncm_code, product_description
            FROM simulated_fiscal_data
            WHERE client_id = ? AND ncm_code IS NOT NULL AND ncm_code != ''
        """, (client_id,)).fetchall()

    if not rows:
        return

    # Clear previous comparisons for this analysis
    db_conn.execute("DELETE FROM ncm_comparisons WHERE analysis_id = ?", (analysis_id,))

    from product_database import get_product_by_ean, search_products, get_products_by_ncm, validate_ncm as pd_val_ncm

    for row in rows:
        ncm_nfe = (row["ncm_code"] or "").strip()
        descricao_nfe = (row["product_description"] or "").strip()

        if not ncm_nfe or len(ncm_nfe) < 4:
            continue

        # Search reference database for products with this NCM
        ref_products = get_products_by_ncm(ncm_nfe)

        if ref_products:
            # Found in reference — NCM exists and is valid
            ref = ref_products[0]
            # Check if there's a product with matching description
            best_match = None
            desc_lower = descricao_nfe.lower()
            for p in ref_products:
                if any(w in p.get("nome", "").lower() for w in desc_lower.split() if len(w) > 3):
                    best_match = p
                    break
            if not best_match:
                best_match = ref

            # Check if the NCM makes sense for the product category
            status = "ok"
            impacto = None

            # Verify NCM category alignment
            ref_ncm = best_match.get("ncm", "")
            if ref_ncm and ref_ncm != ncm_nfe:
                # NCM in reference is different — potential divergence
                status = "divergencia"
                # Check fiscal impact
                ref_mono = best_match.get("monofasico", False)
                ref_aliq_zero = best_match.get("aliquota_zero", False)
                # Check if original NCM is monofásico
                from ncm_monofasico import is_monofasico as check_mono
                nfe_mono = check_mono(ncm_nfe)
                if ref_mono and not nfe_mono:
                    impacto = "Produto monofásico classificado como tributação normal — possível pagamento indevido de PIS/COFINS"
                elif ref_aliq_zero and not nfe_mono:
                    impacto = "Produto com alíquota zero classificado incorretamente — possível crédito tributário"
                elif nfe_mono and not ref_mono:
                    impacto = "NCM monofásico aplicado a produto que não deveria ser — verificar classificação"
                else:
                    impacto = f"NCM divergente: NF-e usa {ncm_nfe}, referência sugere {ref_ncm}"
            else:
                status = "ok"

            db_conn.execute("""
                INSERT INTO ncm_comparisons
                (analysis_id, client_id, descricao_nfe, ncm_nfe, ncm_referencia,
                 descricao_referencia, categoria_referencia, status, impacto_fiscal)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                analysis_id, client_id, descricao_nfe, ncm_nfe,
                best_match.get("ncm", ""),
                best_match.get("nome", ""),
                best_match.get("categoria", ""),
                status, impacto
            ))
        else:
            # NCM not found in reference database — check if NCM is valid at all
            from ncm_database import lookup_ncm as ncm_lookup
            ncm_info = ncm_lookup(ncm_nfe) if NCM_DB_AVAILABLE else None

            if ncm_info:
                # NCM exists but no reference product — OK, just not in our food DB
                db_conn.execute("""
                    INSERT INTO ncm_comparisons
                    (analysis_id, client_id, descricao_nfe, ncm_nfe, ncm_referencia,
                     descricao_referencia, categoria_referencia, status, impacto_fiscal)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'ok', ?)
                """, (
                    analysis_id, client_id, descricao_nfe, ncm_nfe,
                    ncm_nfe, ncm_info.get("descricao", ""),
                    ncm_info.get("categoria", "Outros"),
                    None
                ))
            else:
                # NCM doesn't exist in any database — suspicious
                db_conn.execute("""
                    INSERT INTO ncm_comparisons
                    (analysis_id, client_id, descricao_nfe, ncm_nfe,
                     status, impacto_fiscal)
                    VALUES (?, ?, ?, ?, 'nao_cadastrado', ?)
                """, (
                    analysis_id, client_id, descricao_nfe, ncm_nfe,
                    f"NCM {ncm_nfe} não encontrado na tabela oficial — verificar classificação fiscal"
                ))

    db_conn.commit()


def execute_analysis(client_id: int, analysis_id: int, db_conn):
    """Run the full tax analysis for a client."""
    client = db_conn.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()
    if not client:
        return

    tax_regime = client["tax_regime"]
    state_uf = client["state_uf"]

    # Update status to running
    db_conn.execute("UPDATE tax_analyses SET status = 'running' WHERE id = ?", (analysis_id,))
    db_conn.commit()

    # Determine whether to use REAL or SIMULATED analysis
    use_real = client_has_real_uploads(client_id, db_conn) and REAL_ENGINE_AVAILABLE

    if use_real:
        # Use real parsed data from uploaded files
        real_items = run_real_analysis(client_id, analysis_id, db_conn)
        if real_items:
            items = real_items
            # Mark source of items
            for item in items:
                item["_source"] = "real"
        else:
            # Fallback to simulated if real analysis produces nothing
            use_real = False
            items = _run_simulated_analysis(client_id, analysis_id, tax_regime, state_uf, db_conn)
    else:
        # Use simulated data for demo
        items = _run_simulated_analysis(client_id, analysis_id, tax_regime, state_uf, db_conn)

    # Insert recovery items
    total_recovery = 0
    for item in items:
        db_conn.execute("""
            INSERT INTO recovery_items
            (analysis_id, tax_type, description, ncm_code, period,
             base_calculo_original, base_calculo_correta,
             aliquota_original, aliquota_correta,
             valor_pago, valor_devido, valor_recuperar,
             legal_basis, confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            analysis_id, item["tax_type"], item["description"],
            item["ncm_code"], item["period"],
            item["base_calculo_original"], item["base_calculo_correta"],
            item["aliquota_original"], item["aliquota_correta"],
            item["valor_pago"], item["valor_devido"], item["valor_recuperar"],
            item["legal_basis"], item["confidence"]
        ))
        total_recovery += item["valor_recuperar"]

    # Update analysis
    db_conn.execute("""
        UPDATE tax_analyses
        SET status = 'completed',
            total_recovery_amount = ?,
            completed_at = datetime('now')
        WHERE id = ?
    """, (round(total_recovery, 2), analysis_id))

    # ── NCM Comparison against product reference database ──
    if PRODUCT_DB_AVAILABLE:
        run_ncm_comparison(client_id, analysis_id, db_conn)

    # Generate report
    report_data = generate_report_data(analysis_id, db_conn)
    db_conn.execute("""
        INSERT INTO analysis_reports (analysis_id, report_type, data_json)
        VALUES (?, 'completo', ?)
    """, (analysis_id, json.dumps(report_data, ensure_ascii=False)))

    db_conn.commit()


def generate_report_data(analysis_id: int, db_conn) -> dict:
    """Generate structured report data from analysis results."""
    analysis = db_conn.execute("SELECT * FROM tax_analyses WHERE id = ?", (analysis_id,)).fetchone()
    if not analysis:
        return {}

    client = db_conn.execute("SELECT * FROM clients WHERE id = ?", (analysis["client_id"],)).fetchone()

    items = db_conn.execute("""
        SELECT * FROM recovery_items WHERE analysis_id = ?
    """, (analysis_id,)).fetchall()

    # Group by tax type
    by_tax = {}
    for item in items:
        tt = item["tax_type"]
        if tt not in by_tax:
            by_tax[tt] = {"total": 0, "count": 0, "items": []}
        by_tax[tt]["total"] += item["valor_recuperar"]
        by_tax[tt]["count"] += 1
        by_tax[tt]["items"].append(dict(item))

    # Group by period
    by_period = {}
    for item in items:
        p = item["period"]
        if p not in by_period:
            by_period[p] = {"total": 0, "count": 0}
        by_period[p]["total"] += item["valor_recuperar"]
        by_period[p]["count"] += 1

    # Group by confidence
    by_confidence = {"high": 0, "medium": 0, "low": 0}
    for item in items:
        by_confidence[item["confidence"]] += item["valor_recuperar"]

    # Round totals
    for tt in by_tax:
        by_tax[tt]["total"] = round(by_tax[tt]["total"], 2)
    for p in by_period:
        by_period[p]["total"] = round(by_period[p]["total"], 2)
    for c in by_confidence:
        by_confidence[c] = round(by_confidence[c], 2)

    return {
        "empresa": client["company_name"] if client else "N/A",
        "cnpj": client["cnpj"] if client else "N/A",
        "regime_tributario": client["tax_regime"] if client else "N/A",
        "uf": client["state_uf"] if client else "N/A",
        "setor": client["activity_sector"] if client else "N/A",
        "periodo_analise": f"{analysis['created_at']}",
        "total_recuperacao": round(analysis["total_recovery_amount"], 2),
        "total_itens": len(items),
        "por_tributo": {k: {"total": v["total"], "quantidade": v["count"]} for k, v in by_tax.items()},
        "por_periodo": dict(sorted(by_period.items())),
        "por_confianca": by_confidence,
    }


# ─────────────────────────────────────────────────────────────────────
# Pydantic models
# ─────────────────────────────────────────────────────────────────────

class ClientCreate(BaseModel):
    company_name: str
    cnpj: str
    tax_regime: str = Field(..., pattern="^(simples|presumido|real)$")
    state_uf: str = Field(..., min_length=2, max_length=2)
    activity_sector: str = Field(..., pattern="^(supermercado|padaria|restaurante|bar|farmacia|posto_combustivel|outro)$")
    certificate_password: Optional[str] = None


class ClientUpdate(BaseModel):
    company_name: Optional[str] = None
    cnpj: Optional[str] = None
    tax_regime: Optional[str] = None
    state_uf: Optional[str] = None
    activity_sector: Optional[str] = None


class AnalyzeRequest(BaseModel):
    upload_id: Optional[int] = None
    analysis_type: Optional[str] = "completa"


# ─────────────────────────────────────────────────────────────────────
# FastAPI app
# ─────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app):
    init_db()
    yield


app = FastAPI(
    title="CRG Gestão Contábil - Motor de Análise Tributária",
    description="API para recuperação tributária de supermercados, padarias e restaurantes",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Helper ──────────────────────────────────────────────────────────

def dict_row(row):
    """Convert sqlite3.Row to dict."""
    if row is None:
        return None
    return dict(row)


def dict_rows(rows):
    """Convert list of sqlite3.Row to list of dicts."""
    return [dict(r) for r in rows]


# ─── Clients ─────────────────────────────────────────────────────────

@app.post("/api/clients", status_code=201)
def create_client(client: ClientCreate):
    db = get_db()
    try:
        pw_hash = None
        if client.certificate_password:
            pw_hash = hashlib.sha256(client.certificate_password.encode()).hexdigest()

        cur = db.execute("""
            INSERT INTO clients (company_name, cnpj, tax_regime, state_uf, activity_sector,
                                 certificate_password_hash)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (client.company_name, client.cnpj, client.tax_regime,
              client.state_uf.upper(), client.activity_sector, pw_hash))
        db.commit()

        client_id = cur.lastrowid

        # Auto-generate simulated fiscal data
        generate_fiscal_data(client_id, client.activity_sector, client.tax_regime,
                             client.state_uf.upper(), db)

        new_client = db.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()
        return dict_row(new_client)

    except sqlite3.IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"CNPJ já cadastrado: {str(e)}")
    finally:
        db.close()


@app.get("/api/clients")
def list_clients():
    db = get_db()
    try:
        rows = db.execute("SELECT * FROM clients ORDER BY created_at DESC").fetchall()
        return dict_rows(rows)
    finally:
        db.close()


@app.get("/api/clients/{client_id}")
def get_client(client_id: int):
    db = get_db()
    try:
        row = db.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")

        client = dict_row(row)

        # Include summary stats
        analyses = db.execute("""
            SELECT COUNT(*) as total, SUM(total_recovery_amount) as total_recovery
            FROM tax_analyses WHERE client_id = ? AND status = 'completed'
        """, (client_id,)).fetchone()

        uploads = db.execute("""
            SELECT COUNT(*) as total FROM uploads WHERE client_id = ?
        """, (client_id,)).fetchone()

        client["total_analyses"] = analyses["total"] if analyses["total"] else 0
        client["total_recovery"] = round(analyses["total_recovery"], 2) if analyses["total_recovery"] else 0
        client["total_uploads"] = uploads["total"] if uploads["total"] else 0

        return client
    finally:
        db.close()


@app.put("/api/clients/{client_id}")
def update_client(client_id: int, update: ClientUpdate):
    db = get_db()
    try:
        existing = db.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")

        updates = {}
        if update.company_name is not None:
            updates["company_name"] = update.company_name
        if update.cnpj is not None:
            updates["cnpj"] = update.cnpj
        if update.tax_regime is not None:
            if update.tax_regime not in ("simples", "presumido", "real"):
                raise HTTPException(status_code=400, detail="Regime tributário inválido")
            updates["tax_regime"] = update.tax_regime
        if update.state_uf is not None:
            updates["state_uf"] = update.state_uf.upper()
        if update.activity_sector is not None:
            if update.activity_sector not in ("supermercado", "padaria", "restaurante", "bar", "farmacia", "posto_combustivel", "outro"):
                raise HTTPException(status_code=400, detail="Setor inválido")
            updates["activity_sector"] = update.activity_sector

        if updates:
            updates["updated_at"] = datetime.now().isoformat()
            set_clause = ", ".join(f"{k} = ?" for k in updates)
            values = list(updates.values()) + [client_id]
            db.execute(f"UPDATE clients SET {set_clause} WHERE id = ?", values)
            db.commit()

        row = db.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()
        return dict_row(row)
    finally:
        db.close()


@app.delete("/api/clients/{client_id}")
def delete_client(client_id: int):
    db = get_db()
    try:
        existing = db.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")

        db.execute("DELETE FROM simulated_fiscal_data WHERE client_id = ?", (client_id,))
        db.execute("DELETE FROM simulated_payroll WHERE client_id = ?", (client_id,))
        db.execute("DELETE FROM parsed_fiscal_items WHERE client_id = ?", (client_id,))
        # Cascade will handle recovery_items and analysis_reports
        db.execute("DELETE FROM recovery_items WHERE analysis_id IN (SELECT id FROM tax_analyses WHERE client_id = ?)", (client_id,))
        db.execute("DELETE FROM analysis_reports WHERE analysis_id IN (SELECT id FROM tax_analyses WHERE client_id = ?)", (client_id,))
        db.execute("DELETE FROM tax_analyses WHERE client_id = ?", (client_id,))
        db.execute("DELETE FROM uploads WHERE client_id = ?", (client_id,))
        db.execute("DELETE FROM clients WHERE id = ?", (client_id,))
        db.commit()

        return {"message": "Cliente removido com sucesso", "id": client_id}
    finally:
        db.close()


# ─── File Upload ─────────────────────────────────────────────────────

@app.post("/api/clients/{client_id}/upload", status_code=201)
async def upload_file(
    client_id: int,
    file: UploadFile = File(...),
    file_type: Optional[str] = Form(None),
    period_start: Optional[str] = Form(None),
    period_end: Optional[str] = Form(None),
):
    db = get_db()
    try:
        client = db.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()
        if not client:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")

        # Read content first for auto-detection
        filename = file.filename or "unknown"
        content = await file.read()
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        # Auto-detect file type if not provided
        if not file_type:
            if ext == "xml":
                file_type = "nfe_xml"
            elif ext == "zip":
                file_type = "nfe_xml"  # ZIP of XMLs
            elif ext == "txt":
                file_type = "sped_efd"  # Will be refined by detect_file_type_from_content
            else:
                # Try to detect from content
                file_type = detect_file_type_from_content(content, filename, "sped_efd")

        if file_type not in ("sped_efd", "sped_contrib", "nfe_xml", "pgdas"):
            raise HTTPException(status_code=400, detail="Tipo de arquivo inválido. Envie arquivos .xml, .zip ou .txt (SPED)")

        # Validate file extension
        if file_type in ("sped_efd", "sped_contrib", "pgdas") and ext not in ("txt", ""):
            raise HTTPException(status_code=400, detail="Arquivo SPED deve ser .txt")
        if file_type == "nfe_xml" and ext not in ("xml", "zip", ""):
            raise HTTPException(status_code=400, detail="NFe deve ser .xml ou .zip")

        # Save file
        unique_name = f"{client_id}_{file_type}_{uuid.uuid4().hex[:8]}_{filename}"
        file_path = os.path.join(UPLOAD_DIR, unique_name)
        with open(file_path, "wb") as f:
            f.write(content)

        # Auto-detect actual file type from content
        actual_type = detect_file_type_from_content(content, filename, file_type)
        # Map 'nfe_zip' back to 'nfe_xml' for DB storage (ZIP is just a container)
        db_file_type = "nfe_xml" if actual_type == "nfe_zip" else actual_type
        if db_file_type not in ("sped_efd", "sped_contrib", "nfe_xml", "pgdas"):
            db_file_type = file_type

        cur = db.execute("""
            INSERT INTO uploads (client_id, file_type, period_start, period_end, filename, status)
            VALUES (?, ?, ?, ?, ?, 'processing')
        """, (client_id, db_file_type, period_start, period_end, unique_name))
        db.commit()
        upload_id = cur.lastrowid

        # Parse file and store items in parsed_fiscal_items
        parse_error = None
        parse_summary = {}
        if REAL_ENGINE_AVAILABLE and actual_type not in ("pgdas",):
            try:
                if actual_type in ("sped_efd", "sped_contrib", "efd_icms", "efd_contrib"):
                    # Map detected type back to canonical sped_ names
                    sped_type = "sped_contrib" if actual_type in ("sped_contrib", "efd_contrib") else "sped_efd"
                    parse_summary = process_sped_file(
                        client_id=client_id,
                        upload_id=upload_id,
                        file_content=content,
                        file_type=sped_type,
                        db_conn=db,
                    )
                    # Update DB file_type to the canonical name
                    db.execute("UPDATE uploads SET file_type = ? WHERE id = ?", (sped_type, upload_id))
                    db.commit()
                elif actual_type in ("nfe_xml", "nfe_zip"):
                    parse_summary = process_nfe_file(
                        client_id=client_id,
                        upload_id=upload_id,
                        file_content=content,
                        is_zip=(actual_type == "nfe_zip"),
                        db_conn=db,
                    )
            except Exception as e:
                parse_error = str(e)

        # Update upload status
        final_status = "error" if parse_error else "completed"
        db.execute(
            "UPDATE uploads SET status = ? WHERE id = ?",
            (final_status, upload_id)
        )
        db.commit()

        upload = db.execute("SELECT * FROM uploads WHERE id = ?", (upload_id,)).fetchone()
        result = dict_row(upload)
        result["parse_summary"] = parse_summary
        if parse_error:
            result["parse_error"] = parse_error
        result["detected_type"] = actual_type
        return result
    finally:
        db.close()


@app.get("/api/clients/{client_id}/uploads")
def list_uploads(client_id: int):
    db = get_db()
    try:
        client = db.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()
        if not client:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")

        rows = db.execute("""
            SELECT * FROM uploads WHERE client_id = ? ORDER BY created_at DESC
        """, (client_id,)).fetchall()
        return dict_rows(rows)
    finally:
        db.close()


# ─── Analysis ────────────────────────────────────────────────────────

@app.post("/api/clients/{client_id}/analyze", status_code=201)
def trigger_analysis(client_id: int, request: AnalyzeRequest = AnalyzeRequest()):
    db = get_db()
    try:
        client = db.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()
        if not client:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")

        # ── Validação: exigir uploads ou certificado digital ──
        uploads_count = db.execute(
            "SELECT COUNT(*) as c FROM uploads WHERE client_id = ? AND status = 'completed'",
            (client_id,)
        ).fetchone()["c"]
        has_certificate = bool(client["certificate_file"])

        if uploads_count == 0 and not has_certificate:
            raise HTTPException(
                status_code=422,
                detail="Não é possível realizar a análise. Nenhum arquivo fiscal foi importado e nenhum certificado digital foi cadastrado para este cliente. Faça upload de arquivos SPED/XML ou cadastre o certificado digital A1 antes de executar a análise."
            )

        analysis_type = request.analysis_type or "completa"

        cur = db.execute("""
            INSERT INTO tax_analyses (client_id, upload_id, analysis_type, status)
            VALUES (?, ?, ?, 'pending')
        """, (client_id, request.upload_id, analysis_type))
        db.commit()

        analysis_id = cur.lastrowid

        # Run analysis synchronously (in production, this would be async/background)
        execute_analysis(client_id, analysis_id, db)

        analysis = db.execute("SELECT * FROM tax_analyses WHERE id = ?", (analysis_id,)).fetchone()
        result = dict_row(analysis)
        result["total_recovery_amount"] = round(result["total_recovery_amount"], 2)

        return result
    finally:
        db.close()


@app.get("/api/analyses/{analysis_id}")
def get_analysis(analysis_id: int):
    db = get_db()
    try:
        analysis = db.execute("SELECT * FROM tax_analyses WHERE id = ?", (analysis_id,)).fetchone()
        if not analysis:
            raise HTTPException(status_code=404, detail="Análise não encontrada")

        result = dict_row(analysis)
        result["total_recovery_amount"] = round(result["total_recovery_amount"], 2)

        # Get recovery items
        items = db.execute("""
            SELECT * FROM recovery_items WHERE analysis_id = ? ORDER BY valor_recuperar DESC
        """, (analysis_id,)).fetchall()
        result["recovery_items"] = dict_rows(items)

        # Round all monetary values
        for item in result["recovery_items"]:
            for key in ["base_calculo_original", "base_calculo_correta",
                        "valor_pago", "valor_devido", "valor_recuperar"]:
                if item.get(key) is not None:
                    item[key] = round(item[key], 2)

        # Get client info
        client = db.execute("SELECT company_name, cnpj, tax_regime, state_uf, activity_sector FROM clients WHERE id = ?",
                            (analysis["client_id"],)).fetchone()
        if client:
            result["client"] = dict_row(client)

        return result
    finally:
        db.close()


def _get_ncm_comparison_summary(analysis_id: int, db) -> dict:
    """Get a summary of NCM comparison results for inclusion in analysis summary."""
    comparisons = db.execute("""
        SELECT status, COUNT(*) as cnt FROM ncm_comparisons
        WHERE analysis_id = ? GROUP BY status
    """, (analysis_id,)).fetchall()

    if not comparisons:
        return None

    result = {"total": 0, "ncm_correto": 0, "ncm_divergente": 0, "ncm_nao_cadastrado": 0}
    for row in comparisons:
        result["total"] += row["cnt"]
        if row["status"] == "ok":
            result["ncm_correto"] = row["cnt"]
        elif row["status"] == "divergencia":
            result["ncm_divergente"] = row["cnt"]
        elif row["status"] == "nao_cadastrado":
            result["ncm_nao_cadastrado"] = row["cnt"]

    result["taxa_conformidade"] = round(
        result["ncm_correto"] / result["total"] * 100, 1
    ) if result["total"] > 0 else 0

    # Get top divergencias
    divs = db.execute("""
        SELECT descricao_nfe, ncm_nfe, ncm_referencia, impacto_fiscal
        FROM ncm_comparisons WHERE analysis_id = ? AND status = 'divergencia'
        LIMIT 5
    """, (analysis_id,)).fetchall()
    result["divergencias"] = [dict(r) for r in divs]

    return result


@app.get("/api/analyses/{analysis_id}/summary")
def get_analysis_summary(analysis_id: int):
    db = get_db()
    try:
        analysis = db.execute("SELECT * FROM tax_analyses WHERE id = ?", (analysis_id,)).fetchone()
        if not analysis:
            raise HTTPException(status_code=404, detail="Análise não encontrada")

        # Get client
        client = db.execute("SELECT * FROM clients WHERE id = ?", (analysis["client_id"],)).fetchone()

        # Aggregate by tax type
        by_tax = db.execute("""
            SELECT tax_type,
                   COUNT(*) as quantidade,
                   SUM(valor_recuperar) as total_recuperar,
                   SUM(valor_pago) as total_pago,
                   SUM(valor_devido) as total_devido
            FROM recovery_items WHERE analysis_id = ?
            GROUP BY tax_type ORDER BY total_recuperar DESC
        """, (analysis_id,)).fetchall()

        # Aggregate by confidence
        by_conf = db.execute("""
            SELECT confidence,
                   COUNT(*) as quantidade,
                   SUM(valor_recuperar) as total_recuperar
            FROM recovery_items WHERE analysis_id = ?
            GROUP BY confidence
        """, (analysis_id,)).fetchall()

        # Aggregate by period
        by_period = db.execute("""
            SELECT period,
                   COUNT(*) as quantidade,
                   SUM(valor_recuperar) as total_recuperar
            FROM recovery_items WHERE analysis_id = ?
            GROUP BY period ORDER BY period
        """, (analysis_id,)).fetchall()

        # Top items
        top_items = db.execute("""
            SELECT tax_type, description, ncm_code, period, valor_recuperar, legal_basis, confidence
            FROM recovery_items WHERE analysis_id = ?
            ORDER BY valor_recuperar DESC LIMIT 10
        """, (analysis_id,)).fetchall()

        return {
            "analysis_id": analysis_id,
            "status": analysis["status"],
            "empresa": client["company_name"] if client else "N/A",
            "cnpj": client["cnpj"] if client else "N/A",
            "regime_tributario": client["tax_regime"] if client else "N/A",
            "setor": client["activity_sector"] if client else "N/A",
            "uf": client["state_uf"] if client else "N/A",
            "total_recuperacao": round(analysis["total_recovery_amount"], 2),
            "por_tributo": [
                {
                    "tributo": r["tax_type"],
                    "quantidade": r["quantidade"],
                    "total_recuperar": round(r["total_recuperar"], 2),
                    "total_pago": round(r["total_pago"], 2),
                    "total_devido": round(r["total_devido"], 2),
                }
                for r in by_tax
            ],
            "por_confianca": [
                {
                    "nivel": r["confidence"],
                    "quantidade": r["quantidade"],
                    "total_recuperar": round(r["total_recuperar"], 2),
                }
                for r in by_conf
            ],
            "por_periodo": [
                {
                    "periodo": r["period"],
                    "quantidade": r["quantidade"],
                    "total_recuperar": round(r["total_recuperar"], 2),
                }
                for r in by_period
            ],
            "top_itens": [dict(r) for r in top_items],
            "created_at": analysis["created_at"],
            "completed_at": analysis["completed_at"],
            "ncm_comparacao": _get_ncm_comparison_summary(analysis_id, db),
        }
    finally:
        db.close()


# ─── Reports ─────────────────────────────────────────────────────────

@app.get("/api/analyses/{analysis_id}/report")
def get_analysis_report(analysis_id: int):
    db = get_db()
    try:
        report = db.execute("""
            SELECT * FROM analysis_reports WHERE analysis_id = ? ORDER BY generated_at DESC LIMIT 1
        """, (analysis_id,)).fetchone()

        if not report:
            # Generate on the fly
            analysis = db.execute("SELECT * FROM tax_analyses WHERE id = ?", (analysis_id,)).fetchone()
            if not analysis:
                raise HTTPException(status_code=404, detail="Análise não encontrada")
            data = generate_report_data(analysis_id, db)
            return data

        return json.loads(report["data_json"])
    finally:
        db.close()


@app.get("/api/analyses/{analysis_id}/ncm-comparacao")
def get_ncm_comparison(analysis_id: int):
    """Get NCM comparison results for an analysis."""
    db = get_db()
    try:
        analysis = db.execute("SELECT * FROM tax_analyses WHERE id = ?", (analysis_id,)).fetchone()
        if not analysis:
            raise HTTPException(status_code=404, detail="Análise não encontrada")

        comparisons = db.execute("""
            SELECT * FROM ncm_comparisons WHERE analysis_id = ? ORDER BY status DESC, descricao_nfe
        """, (analysis_id,)).fetchall()

        items = dict_rows(comparisons)

        # Summary stats
        total = len(items)
        ok_count = len([i for i in items if i["status"] == "ok"])
        divergencia_count = len([i for i in items if i["status"] == "divergencia"])
        nao_cadastrado_count = len([i for i in items if i["status"] == "nao_cadastrado"])

        return {
            "analysis_id": analysis_id,
            "resumo": {
                "total_produtos": total,
                "ncm_correto": ok_count,
                "ncm_divergente": divergencia_count,
                "ncm_nao_cadastrado": nao_cadastrado_count,
                "taxa_conformidade": round(ok_count / total * 100, 1) if total > 0 else 0,
            },
            "comparacoes": items,
        }
    finally:
        db.close()


# ─── Dashboard ───────────────────────────────────────────────────────

@app.get("/api/dashboard/stats")
def dashboard_stats():
    db = get_db()
    try:
        # Total clients
        total_clients = db.execute("SELECT COUNT(*) as c FROM clients").fetchone()["c"]

        # Clients by regime
        by_regime = db.execute("""
            SELECT tax_regime, COUNT(*) as quantidade
            FROM clients GROUP BY tax_regime
        """).fetchall()

        # Clients by sector
        by_sector = db.execute("""
            SELECT activity_sector, COUNT(*) as quantidade
            FROM clients GROUP BY activity_sector
        """).fetchall()

        # Total analyses
        total_analyses = db.execute("SELECT COUNT(*) as c FROM tax_analyses").fetchone()["c"]
        completed_analyses = db.execute(
            "SELECT COUNT(*) as c FROM tax_analyses WHERE status = 'completed'"
        ).fetchone()["c"]

        # Total recovery
        total_recovery = db.execute("""
            SELECT COALESCE(SUM(total_recovery_amount), 0) as total
            FROM tax_analyses WHERE status = 'completed'
        """).fetchone()["total"]

        # Recovery by tax type
        by_tax = db.execute("""
            SELECT tax_type,
                   COUNT(*) as quantidade,
                   SUM(valor_recuperar) as total_recuperar
            FROM recovery_items
            GROUP BY tax_type ORDER BY total_recuperar DESC
        """).fetchall()

        # Recovery by confidence
        by_confidence = db.execute("""
            SELECT confidence,
                   COUNT(*) as quantidade,
                   SUM(valor_recuperar) as total_recuperar
            FROM recovery_items
            GROUP BY confidence
        """).fetchall()

        # Average recovery per client
        avg_recovery = round(total_recovery / total_clients, 2) if total_clients > 0 else 0

        # Recent analyses
        recent = db.execute("""
            SELECT ta.id, ta.client_id, ta.status, ta.total_recovery_amount, ta.created_at, ta.completed_at,
                   c.company_name, c.cnpj, c.tax_regime
            FROM tax_analyses ta
            JOIN clients c ON ta.client_id = c.id
            ORDER BY ta.created_at DESC LIMIT 10
        """).fetchall()

        # Total uploads
        total_uploads = db.execute("SELECT COUNT(*) as c FROM uploads").fetchone()["c"]

        return {
            "total_clientes": total_clients,
            "total_analises": total_analyses,
            "analises_concluidas": completed_analyses,
            "total_uploads": total_uploads,
            "total_recuperacao": round(total_recovery, 2),
            "media_recuperacao_por_cliente": avg_recovery,
            "por_regime": [{"regime": r["tax_regime"], "quantidade": r["quantidade"]} for r in by_regime],
            "por_setor": [{"setor": r["activity_sector"], "quantidade": r["quantidade"]} for r in by_sector],
            "por_tributo": [
                {
                    "tributo": r["tax_type"],
                    "quantidade": r["quantidade"],
                    "total_recuperar": round(r["total_recuperar"], 2) if r["total_recuperar"] else 0,
                }
                for r in by_tax
            ],
            "por_confianca": [
                {
                    "nivel": r["confidence"],
                    "quantidade": r["quantidade"],
                    "total_recuperar": round(r["total_recuperar"], 2) if r["total_recuperar"] else 0,
                }
                for r in by_confidence
            ],
            "analises_recentes": [
                {
                    "id": r["id"],
                    "client_id": r["client_id"],
                    "empresa": r["company_name"],
                    "cnpj": r["cnpj"],
                    "regime": r["tax_regime"],
                    "status": r["status"],
                    "total_recuperacao": round(r["total_recovery_amount"], 2),
                    "created_at": r["created_at"],
                    "completed_at": r["completed_at"],
                }
                for r in recent
            ],
        }
    finally:
        db.close()


# ─── NCM Database API ────────────────────────────────────────────────

@app.get("/api/ncm/stats/resumo")
def ncm_stats():
    """Estatísticas gerais da base de NCM."""
    if not NCM_DB_AVAILABLE:
        raise HTTPException(status_code=400, detail="Base de NCM não disponível")

    total = len(NCM_DATABASE)
    monofasicos = sum(1 for v in NCM_DATABASE.values() if v.get("monofasico"))
    aliq_zero = sum(1 for v in NCM_DATABASE.values() if v.get("aliquota_zero_pis_cofins"))
    st_count = sum(1 for v in NCM_DATABASE.values() if v.get("st_icms"))
    cats = get_all_categories()
    capitulos = set()
    for v in NCM_DATABASE.values():
        cap = v.get("capitulo")
        if cap:
            capitulos.add(cap)

    return {
        "total_ncms": total,
        "monofasicos": monofasicos,
        "aliquota_zero_pis_cofins": aliq_zero,
        "icms_st": st_count,
        "categorias": len(cats),
        "capitulos": len(capitulos),
    }


@app.get("/api/ncm/categorias")
def list_ncm_categories():
    """Lista todas as categorias de NCM disponíveis."""
    if not NCM_DB_AVAILABLE:
        raise HTTPException(status_code=400, detail="Base de NCM não disponível")
    cats = get_all_categories()
    cat_counts = {}
    for data in NCM_DATABASE.values():
        cat = data.get("categoria", "outros")
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
    return {
        "categorias": [
            {"nome": c, "quantidade": cat_counts.get(c, 0)}
            for c in sorted(cats)
        ]
    }


@app.get("/api/ncm/busca")
def search_ncm_endpoint(
    q: Optional[str] = Query(None, description="Busca por descrição ou código NCM"),
    categoria: Optional[str] = Query(None, description="Filtrar por categoria"),
    monofasico: Optional[bool] = Query(None, description="Filtrar monofásicos"),
    aliquota_zero: Optional[bool] = Query(None, description="Filtrar alíquota zero PIS/COFINS"),
    st_icms: Optional[bool] = Query(None, description="Filtrar ICMS ST"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=10, le=500),
):
    """Lista e pesquisa NCMs na base de dados tributária."""
    if not NCM_DB_AVAILABLE:
        raise HTTPException(status_code=400, detail="Base de NCM não disponível")

    results = []

    if q and len(q.strip()) >= 2:
        query = q.strip()
        if query.replace(".", "").isdigit():
            clean_q = query.replace(".", "").replace("-", "")
            entry = lookup_ncm(clean_q)
            if entry:
                results = [{"ncm": clean_q.ljust(8, '0')[:8], **entry}]
            else:
                for ncm_code, data in NCM_DATABASE.items():
                    if ncm_code.startswith(clean_q):
                        results.append({"ncm": ncm_code, **data})
        else:
            results = search_ncm(query)
    elif categoria:
        results = get_ncms_by_category(categoria)
    else:
        results = [{"ncm": k, **v} for k, v in sorted(NCM_DATABASE.items())]

    if monofasico is not None:
        results = [r for r in results if r.get("monofasico") == monofasico]
    if aliquota_zero is not None:
        results = [r for r in results if r.get("aliquota_zero_pis_cofins") == aliquota_zero]
    if st_icms is not None:
        results = [r for r in results if r.get("st_icms") == st_icms]

    total = len(results)
    start = (page - 1) * per_page
    end = start + per_page
    page_results = results[start:end]

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
        "items": page_results,
    }


@app.get("/api/ncm/export/csv")
def export_ncm_csv_route():
    """Exportar toda a base de NCM como CSV."""
    import io
    import csv
    if not NCM_DB_AVAILABLE:
        raise HTTPException(status_code=400, detail="Base de NCM não disponível")
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow(["NCM", "Descrição", "Capítulo", "Seção", "Categoria", "IPI%", "PIS%", "COFINS%",
                     "PIS Cumulativo%", "COFINS Cumulativo%", "CEST", "Monofásico", "ICMS-ST",
                     "Alíquota Zero PIS/COFINS", "Base Legal", "Observações"])
    for ncm_code_key in sorted(NCM_DATABASE.keys()):
        d = NCM_DATABASE[ncm_code_key]
        writer.writerow([
            ncm_code_key, d.get("descricao", ""), d.get("capitulo", ""), d.get("secao", ""),
            d.get("categoria", ""), d.get("ipi", 0), d.get("pis", 0), d.get("cofins", 0),
            d.get("pis_cumulativo", 0), d.get("cofins_cumulativo", 0), d.get("cest", ""),
            "Sim" if d.get("monofasico") else "Não", "Sim" if d.get("st_icms") else "Não",
            "Sim" if d.get("aliquota_zero_pis_cofins") else "Não",
            d.get("base_legal_pis_cofins", ""), d.get("observacoes", "")
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=base_ncm.csv"}
    )


@app.get("/api/ncm/{ncm_code}")
def get_ncm_detail(ncm_code: str, regime: Optional[str] = Query("presumido")):
    """Consulta detalhada de um NCM específico com resumo tributário."""
    if not NCM_DB_AVAILABLE:
        raise HTTPException(status_code=400, detail="Base de NCM não disponível")

    clean = ncm_code.replace(".", "").replace("-", "").replace(" ", "")
    entry = lookup_ncm(clean)
    if not entry:
        raise HTTPException(status_code=404, detail=f"NCM {ncm_code} não encontrado na base")

    summary = get_ncm_tax_summary(clean, regime or "presumido")
    return {
        "ncm": clean.ljust(8, '0')[:8],
        **entry,
        "resumo_tributario": summary,
    }


# ─── Product Database API ────────────────────────────────────────────

@app.get("/api/produtos/stats")
def product_stats():
    if not PRODUCT_DB_AVAILABLE:
        raise HTTPException(status_code=400, detail="Base de produtos não disponível")
    return pd_statistics()


@app.get("/api/produtos/categorias")
def list_product_categories():
    if not PRODUCT_DB_AVAILABLE:
        raise HTTPException(status_code=400, detail="Base de produtos não disponível")
    cats = pd_categories()
    # Count products per category
    all_prods = pd_get_all()
    counts = {}
    for p in all_prods:
        c = p.get("categoria", "Outros")
        counts[c] = counts.get(c, 0) + 1
    return {"categorias": [{"nome": c, "quantidade": counts.get(c, 0)} for c in sorted(cats)]}


@app.get("/api/produtos/busca")
def search_products_endpoint(
    q: Optional[str] = Query(None, description="Busca por nome, EAN ou NCM"),
    categoria: Optional[str] = Query(None, description="Filtrar por categoria"),
    ncm: Optional[str] = Query(None, description="Filtrar por NCM"),
    monofasico: Optional[bool] = Query(None, description="Filtrar monofásicos"),
    aliquota_zero: Optional[bool] = Query(None, description="Filtrar alíquota zero"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=10, le=500),
):
    if not PRODUCT_DB_AVAILABLE:
        raise HTTPException(status_code=400, detail="Base de produtos não disponível")

    # Start with all or search results
    if q and len(q.strip()) >= 2:
        results = pd_search(q.strip())
    elif ncm:
        results = pd_by_ncm(ncm.replace(".", "").replace("-", ""))
    elif categoria:
        results = pd_by_cat(categoria)
    else:
        results = pd_get_all()

    # Apply additional filters
    if categoria and q:
        results = [r for r in results if r.get("categoria", "") == categoria]
    if monofasico is not None:
        results = [r for r in results if r.get("monofasico", False) == monofasico]
    if aliquota_zero is not None:
        results = [r for r in results if r.get("aliquota_zero", False) == aliquota_zero]

    total = len(results)
    start = (page - 1) * per_page
    end = start + per_page
    page_items = results[start:end]

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
        "items": page_items,
    }


@app.get("/api/produtos/export/csv")
def export_produtos_csv_route():
    """Exportar toda a base de produtos como CSV."""
    import io
    import csv
    if not PRODUCT_DB_AVAILABLE:
        raise HTTPException(status_code=400, detail="Base de produtos não disponível")
    all_prods = pd_get_all()
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow(["EAN/GTIN", "Nome", "Descrição Genérica", "NCM", "Descrição NCM",
                     "Categoria", "Subcategoria", "Unidade", "Monofásico", "Alíquota Zero",
                     "IPI%", "CEST", "Marca"])
    for p in all_prods:
        writer.writerow([
            p.get("ean", ""), p.get("nome", ""), p.get("descricao_generica", ""),
            p.get("ncm", ""), p.get("ncm_descricao", ""),
            p.get("categoria", ""), p.get("subcategoria", ""), p.get("unidade", ""),
            "Sim" if p.get("monofasico") else "Não",
            "Sim" if p.get("aliquota_zero") else "Não",
            p.get("ipi", 0), p.get("cest", ""), p.get("marca_exemplo", "")
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=base_produtos.csv"}
    )


@app.get("/api/produtos/{ean}")
def get_product_detail(ean: str):
    if not PRODUCT_DB_AVAILABLE:
        raise HTTPException(status_code=400, detail="Base de produtos não disponível")
    product = pd_by_ean(ean)
    if not product:
        raise HTTPException(status_code=404, detail=f"Produto com EAN {ean} não encontrado na base")
    return product


@app.post("/api/produtos/validar-ncm")
def validate_product_ncm(payload: dict):
    """Valida se o NCM de um produto está correto.
    Payload: {ean: str, ncm: str}
    """
    if not PRODUCT_DB_AVAILABLE:
        raise HTTPException(status_code=400, detail="Base de produtos não disponível")
    ean = payload.get("ean", "")
    ncm = payload.get("ncm", "")
    result = pd_validate_ncm(ean, ncm)
    return result


@app.post("/api/produtos/comparar")
def compare_products_ncm(payload: dict):
    """Compara uma lista de produtos (de XML/NF-e) com a base de referência.
    Payload: {produtos: [{ean, ncm, descricao}, ...]}
    """
    if not PRODUCT_DB_AVAILABLE:
        raise HTTPException(status_code=400, detail="Base de produtos não disponível")
    produtos = payload.get("produtos", [])
    if not produtos:
        raise HTTPException(status_code=400, detail="Lista de produtos vazia")
    discrepancies = pd_find_discrepancies(produtos)
    total = len(produtos)
    divergencias = len([d for d in discrepancies if d.get("tipo") == "DIVERGENCIA_NCM"])
    nao_cadastrados = len([d for d in discrepancies if d.get("tipo") == "EAN_NAO_CADASTRADO"])
    return {
        "total_analisados": total,
        "total_divergencias": divergencias,
        "total_nao_cadastrados": nao_cadastrados,
        "total_ok": total - divergencias - nao_cadastrados,
        "divergencias": discrepancies,
    }


# ─── NCM CRUD ─────────────────────────────────────────────────────

class NCMCreate(BaseModel):
    ncm: str
    descricao: str
    capitulo: Optional[int] = None
    secao: Optional[str] = ""
    categoria: Optional[str] = ""
    ipi: Optional[float] = 0.0
    pis: Optional[float] = 0.0
    cofins: Optional[float] = 0.0
    pis_cumulativo: Optional[float] = 0.0
    cofins_cumulativo: Optional[float] = 0.0
    cest: Optional[str] = ""
    ncm_ex: Optional[str] = ""
    monofasico: Optional[bool] = False
    st_icms: Optional[bool] = False
    aliquota_zero_pis_cofins: Optional[bool] = False
    base_legal_pis_cofins: Optional[str] = ""
    observacoes: Optional[str] = ""


@app.post("/api/ncm", status_code=201)
def create_ncm(payload: NCMCreate):
    """Criar novo NCM customizado."""
    ncm_clean = payload.ncm.replace(".", "").replace("-", "").replace(" ", "").strip()
    if len(ncm_clean) < 4 or len(ncm_clean) > 8:
        raise HTTPException(status_code=422, detail="Código NCM deve ter entre 4 e 8 dígitos")
    # Check if exists in built-in DB
    if NCM_DB_AVAILABLE and ncm_clean in NCM_DATABASE:
        raise HTTPException(status_code=422, detail=f"NCM {ncm_clean} já existe na base padrão. Use editar para alterar.")
    db = get_db()
    try:
        db.execute(
            """INSERT INTO custom_ncm (ncm, descricao, capitulo, secao, categoria, ipi, pis, cofins,
               pis_cumulativo, cofins_cumulativo, cest, ncm_ex, monofasico, st_icms,
               aliquota_zero_pis_cofins, base_legal_pis_cofins, observacoes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (ncm_clean, payload.descricao, payload.capitulo, payload.secao, payload.categoria,
             payload.ipi, payload.pis, payload.cofins, payload.pis_cumulativo, payload.cofins_cumulativo,
             payload.cest, payload.ncm_ex, 1 if payload.monofasico else 0, 1 if payload.st_icms else 0,
             1 if payload.aliquota_zero_pis_cofins else 0, payload.base_legal_pis_cofins, payload.observacoes)
        )
        db.commit()
        # Also inject into in-memory NCM_DATABASE so it appears in search results
        if NCM_DB_AVAILABLE:
            NCM_DATABASE[ncm_clean] = {
                "descricao": payload.descricao,
                "capitulo": payload.capitulo,
                "secao": payload.secao or "",
                "categoria": payload.categoria or "",
                "ipi": payload.ipi or 0.0,
                "pis": payload.pis or 0.0,
                "cofins": payload.cofins or 0.0,
                "pis_cumulativo": payload.pis_cumulativo or 0.0,
                "cofins_cumulativo": payload.cofins_cumulativo or 0.0,
                "cest": payload.cest or "",
                "ncm_ex": payload.ncm_ex or "",
                "monofasico": bool(payload.monofasico),
                "st_icms": bool(payload.st_icms),
                "aliquota_zero_pis_cofins": bool(payload.aliquota_zero_pis_cofins),
                "base_legal_pis_cofins": payload.base_legal_pis_cofins or "",
                "observacoes": payload.observacoes or "",
            }
        return {"ncm": ncm_clean, "message": "NCM criado com sucesso"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=422, detail=f"NCM {ncm_clean} já existe na base customizada")
    finally:
        db.close()


@app.put("/api/ncm/{ncm_code}")
def update_ncm(ncm_code: str, payload: NCMCreate):
    """Editar NCM (atualiza in-memory + SQLite custom)."""
    ncm_clean = ncm_code.replace(".", "").replace("-", "").replace(" ", "").strip()
    db = get_db()
    try:
        # Upsert into custom_ncm
        db.execute(
            """INSERT INTO custom_ncm (ncm, descricao, capitulo, secao, categoria, ipi, pis, cofins,
               pis_cumulativo, cofins_cumulativo, cest, ncm_ex, monofasico, st_icms,
               aliquota_zero_pis_cofins, base_legal_pis_cofins, observacoes, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
               ON CONFLICT(ncm) DO UPDATE SET
               descricao=excluded.descricao, capitulo=excluded.capitulo, secao=excluded.secao,
               categoria=excluded.categoria, ipi=excluded.ipi, pis=excluded.pis, cofins=excluded.cofins,
               pis_cumulativo=excluded.pis_cumulativo, cofins_cumulativo=excluded.cofins_cumulativo,
               cest=excluded.cest, ncm_ex=excluded.ncm_ex, monofasico=excluded.monofasico,
               st_icms=excluded.st_icms, aliquota_zero_pis_cofins=excluded.aliquota_zero_pis_cofins,
               base_legal_pis_cofins=excluded.base_legal_pis_cofins, observacoes=excluded.observacoes,
               updated_at=datetime('now')""",
            (ncm_clean, payload.descricao, payload.capitulo, payload.secao, payload.categoria,
             payload.ipi, payload.pis, payload.cofins, payload.pis_cumulativo, payload.cofins_cumulativo,
             payload.cest, payload.ncm_ex, 1 if payload.monofasico else 0, 1 if payload.st_icms else 0,
             1 if payload.aliquota_zero_pis_cofins else 0, payload.base_legal_pis_cofins, payload.observacoes)
        )
        db.commit()
        # Update in-memory
        if NCM_DB_AVAILABLE:
            NCM_DATABASE[ncm_clean] = {
                "descricao": payload.descricao,
                "capitulo": payload.capitulo,
                "secao": payload.secao or "",
                "categoria": payload.categoria or "",
                "ipi": payload.ipi or 0.0,
                "pis": payload.pis or 0.0,
                "cofins": payload.cofins or 0.0,
                "pis_cumulativo": payload.pis_cumulativo or 0.0,
                "cofins_cumulativo": payload.cofins_cumulativo or 0.0,
                "cest": payload.cest or "",
                "ncm_ex": payload.ncm_ex or "",
                "monofasico": bool(payload.monofasico),
                "st_icms": bool(payload.st_icms),
                "aliquota_zero_pis_cofins": bool(payload.aliquota_zero_pis_cofins),
                "base_legal_pis_cofins": payload.base_legal_pis_cofins or "",
                "observacoes": payload.observacoes or "",
            }
        return {"ncm": ncm_clean, "message": "NCM atualizado com sucesso"}
    finally:
        db.close()


@app.delete("/api/ncm/{ncm_code}")
def delete_ncm(ncm_code: str):
    """Excluir NCM customizado (não exclui da base padrão)."""
    ncm_clean = ncm_code.replace(".", "").replace("-", "").replace(" ", "").strip()
    db = get_db()
    try:
        # Remove from custom table
        cur = db.execute("DELETE FROM custom_ncm WHERE ncm = ?", (ncm_clean,))
        db.commit()
        # Remove from in-memory if it was custom-only
        if NCM_DB_AVAILABLE and ncm_clean in NCM_DATABASE:
            del NCM_DATABASE[ncm_clean]
        return {"ncm": ncm_clean, "message": "NCM excluído com sucesso", "rows_deleted": cur.rowcount}
    finally:
        db.close()





# ─── Produtos CRUD ────────────────────────────────────────────────────

class ProdutoCreate(BaseModel):
    ean: str
    nome: str
    descricao_generica: Optional[str] = ""
    ncm: str
    ncm_descricao: Optional[str] = ""
    categoria: Optional[str] = ""
    subcategoria: Optional[str] = ""
    unidade: Optional[str] = "un"
    monofasico: Optional[bool] = False
    aliquota_zero: Optional[bool] = False
    ipi: Optional[float] = 0.0
    cest: Optional[str] = ""
    marca_exemplo: Optional[str] = ""


@app.post("/api/produtos", status_code=201)
def create_produto(payload: ProdutoCreate):
    """Criar novo produto customizado."""
    ean = payload.ean.strip()
    if not ean:
        raise HTTPException(status_code=422, detail="EAN/GTIN é obrigatório")
    # Check if exists in built-in DB
    if PRODUCT_DB_AVAILABLE:
        existing = pd_by_ean(ean)
        if existing:
            raise HTTPException(status_code=422, detail=f"Produto com EAN {ean} já existe na base padrão. Use editar.")
    db = get_db()
    try:
        db.execute(
            """INSERT INTO custom_produtos (ean, nome, descricao_generica, ncm, ncm_descricao,
               categoria, subcategoria, unidade, monofasico, aliquota_zero, ipi, cest, marca_exemplo)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (ean, payload.nome, payload.descricao_generica, payload.ncm.replace(".", "").replace("-", ""),
             payload.ncm_descricao, payload.categoria, payload.subcategoria, payload.unidade,
             1 if payload.monofasico else 0, 1 if payload.aliquota_zero else 0,
             payload.ipi, payload.cest, payload.marca_exemplo)
        )
        db.commit()
        # Add to in-memory product list
        if PRODUCT_DB_AVAILABLE:
            from product_database import _PRODUCTS
            _PRODUCTS.append({
                "ean": ean, "nome": payload.nome, "descricao_generica": payload.descricao_generica or "",
                "ncm": payload.ncm.replace(".", "").replace("-", ""),
                "ncm_descricao": payload.ncm_descricao or "",
                "categoria": payload.categoria or "", "subcategoria": payload.subcategoria or "",
                "unidade": payload.unidade or "un",
                "monofasico": bool(payload.monofasico), "aliquota_zero": bool(payload.aliquota_zero),
                "ipi": payload.ipi or 0.0, "cest": payload.cest or "",
                "marca_exemplo": payload.marca_exemplo or "",
            })
        return {"ean": ean, "message": "Produto criado com sucesso"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=422, detail=f"Produto com EAN {ean} já existe na base customizada")
    finally:
        db.close()


@app.put("/api/produtos/{ean}")
def update_produto(ean: str, payload: ProdutoCreate):
    """Editar produto (atualiza in-memory + SQLite custom)."""
    ean_clean = ean.strip()
    db = get_db()
    try:
        # Upsert into custom_produtos
        db.execute(
            """INSERT INTO custom_produtos (ean, nome, descricao_generica, ncm, ncm_descricao,
               categoria, subcategoria, unidade, monofasico, aliquota_zero, ipi, cest, marca_exemplo, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
               ON CONFLICT(ean) DO UPDATE SET
               nome=excluded.nome, descricao_generica=excluded.descricao_generica, ncm=excluded.ncm,
               ncm_descricao=excluded.ncm_descricao, categoria=excluded.categoria,
               subcategoria=excluded.subcategoria, unidade=excluded.unidade,
               monofasico=excluded.monofasico, aliquota_zero=excluded.aliquota_zero,
               ipi=excluded.ipi, cest=excluded.cest, marca_exemplo=excluded.marca_exemplo,
               updated_at=datetime('now')""",
            (ean_clean, payload.nome, payload.descricao_generica,
             payload.ncm.replace(".", "").replace("-", ""), payload.ncm_descricao,
             payload.categoria, payload.subcategoria, payload.unidade,
             1 if payload.monofasico else 0, 1 if payload.aliquota_zero else 0,
             payload.ipi, payload.cest, payload.marca_exemplo)
        )
        db.commit()
        # Update in-memory
        if PRODUCT_DB_AVAILABLE:
            from product_database import _PRODUCTS
            updated_data = {
                "ean": ean_clean, "nome": payload.nome,
                "descricao_generica": payload.descricao_generica or "",
                "ncm": payload.ncm.replace(".", "").replace("-", ""),
                "ncm_descricao": payload.ncm_descricao or "",
                "categoria": payload.categoria or "",
                "subcategoria": payload.subcategoria or "",
                "unidade": payload.unidade or "un",
                "monofasico": bool(payload.monofasico),
                "aliquota_zero": bool(payload.aliquota_zero),
                "ipi": payload.ipi or 0.0, "cest": payload.cest or "",
                "marca_exemplo": payload.marca_exemplo or "",
            }
            found = False
            for i, p in enumerate(_PRODUCTS):
                if p.get("ean") == ean_clean:
                    _PRODUCTS[i] = updated_data
                    found = True
                    break
            if not found:
                _PRODUCTS.append(updated_data)
        return {"ean": ean_clean, "message": "Produto atualizado com sucesso"}
    finally:
        db.close()


@app.delete("/api/produtos/remover/{ean}")
def delete_produto(ean: str):
    """Excluir produto customizado."""
    ean_clean = ean.strip()
    db = get_db()
    try:
        cur = db.execute("DELETE FROM custom_produtos WHERE ean = ?", (ean_clean,))
        db.commit()
        # Remove from in-memory
        if PRODUCT_DB_AVAILABLE:
            from product_database import _PRODUCTS
            for i, p in enumerate(_PRODUCTS):
                if p.get("ean") == ean_clean:
                    _PRODUCTS.pop(i)
                    break
        return {"ean": ean_clean, "message": "Produto excluído com sucesso", "rows_deleted": cur.rowcount}
    finally:
        db.close()





# ─── Health check ────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "CRG Motor de Análise Tributária",
        "version": "2.0.0",
        "real_engine": REAL_ENGINE_AVAILABLE,
    }


@app.get("/api/reports/summary")
def reports_summary():
    """Summary of all analyses for reporting purposes."""
    db = get_db()
    try:
        # Total recovery by tax type across all completed analyses
        by_tax = db.execute("""
            SELECT ri.tax_type,
                   COUNT(*) as quantidade,
                   SUM(ri.valor_recuperar) as total_recuperar,
                   AVG(ri.valor_recuperar) as media_recuperar
            FROM recovery_items ri
            JOIN tax_analyses ta ON ri.analysis_id = ta.id
            WHERE ta.status = 'completed'
            GROUP BY ri.tax_type
            ORDER BY total_recuperar DESC
        """).fetchall()

        # Top clients by recovery
        top_clients = db.execute("""
            SELECT c.company_name, c.cnpj, c.tax_regime, c.activity_sector,
                   SUM(ta.total_recovery_amount) as total_recuperado,
                   COUNT(ta.id) as num_analises
            FROM clients c
            JOIN tax_analyses ta ON ta.client_id = c.id
            WHERE ta.status = 'completed'
            GROUP BY c.id
            ORDER BY total_recuperado DESC
            LIMIT 10
        """).fetchall()

        # Recovery by confidence level
        by_confidence = db.execute("""
            SELECT confidence, COUNT(*) as quantidade,
                   SUM(valor_recuperar) as total_recuperar
            FROM recovery_items
            GROUP BY confidence ORDER BY total_recuperar DESC
        """).fetchall()

        total_recovery = db.execute("""
            SELECT COALESCE(SUM(total_recovery_amount), 0) as total
            FROM tax_analyses WHERE status = 'completed'
        """).fetchone()["total"]

        return {
            "total_recuperacao": round(total_recovery, 2),
            "por_tributo": [
                {
                    "tributo": r["tax_type"],
                    "quantidade": r["quantidade"],
                    "total_recuperar": round(r["total_recuperar"] or 0, 2),
                    "media_recuperar": round(r["media_recuperar"] or 0, 2),
                }
                for r in by_tax
            ],
            "top_clientes": [
                {
                    "empresa": r["company_name"],
                    "cnpj": r["cnpj"],
                    "regime": r["tax_regime"],
                    "setor": r["activity_sector"],
                    "total_recuperado": round(r["total_recuperado"] or 0, 2),
                    "num_analises": r["num_analises"],
                }
                for r in top_clients
            ],
            "por_confianca": [
                {
                    "nivel": r["confidence"],
                    "quantidade": r["quantidade"],
                    "total_recuperar": round(r["total_recuperar"] or 0, 2),
                }
                for r in by_confidence
            ],
        }
    finally:
        db.close()


# ─────────────────────────────────────────────────────────────────────
# Static files + Run server
# ─────────────────────────────────────────────────────────────────────

# Em produção, servir arquivos estáticos (frontend) diretamente pelo FastAPI
# O index.html, app.js, styles.css etc. ficam no mesmo diretório
from fastapi.responses import FileResponse


@app.get("/")
def serve_index():
    """Serve the main SPA page."""
    index_path = os.path.join(_BASE_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html")
    return {"message": "Leão Triste API", "docs": "/docs"}


# Servir assets estáticos (JS, CSS, imagens)
_STATIC_EXTENSIONS = {".js", ".css", ".png", ".ico", ".svg", ".jpg", ".jpeg", ".gif", ".woff", ".woff2"}


@app.get("/{filename:path}")
def serve_static(filename: str):
    """Fallback: serve static files from the app directory."""
    # Somente servir arquivos com extensões estáticas conhecidas
    ext = os.path.splitext(filename)[1].lower()
    if ext not in _STATIC_EXTENSIONS:
        # Para rotas SPA (ex: /#/ncm), retornar index.html
        index_path = os.path.join(_BASE_DIR, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path, media_type="text/html")
        raise HTTPException(status_code=404)
    file_path = os.path.join(_BASE_DIR, filename)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404)


if __name__ == "__main__":
    import uvicorn
    _port = int(os.environ.get("PORT", 8000))
    _host = os.environ.get("HOST", "0.0.0.0")
    uvicorn.run(app, host=_host, port=_port)
