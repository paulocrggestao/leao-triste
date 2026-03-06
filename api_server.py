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
        get_product_detail as pd_detail,
        PRODUCT_DATABASE as PD_DB
    )
    PRODUCT_DB_AVAILABLE = True
except ImportError as _e3:
    PRODUCT_DB_AVAILABLE = False
    logging.warning(f"Product database not available: {_e3}")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------
DB_PATH = os.environ.get("DB_PATH", "tax_analysis.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            created_at TEXT,
            company_name TEXT,
            cnpj TEXT,
            segment TEXT,
            status TEXT DEFAULT 'active'
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS uploads (
            id TEXT PRIMARY KEY,
            session_id TEXT,
            filename TEXT,
            file_type TEXT,
            file_size INTEGER,
            uploaded_at TEXT,
            parsed BOOLEAN DEFAULT 0,
            parse_error TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS analysis_results (
            id TEXT PRIMARY KEY,
            session_id TEXT,
            created_at TEXT,
            result_json TEXT
        )
    """)
    conn.commit()
    conn.close()

# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="CRG Motor de Análise Tributária",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class SessionCreate(BaseModel):
    company_name: str
    cnpj: str
    segment: str  # 'supermarket' | 'bakery' | 'restaurant'

class SessionResponse(BaseModel):
    session_id: str
    company_name: str
    cnpj: str
    segment: str
    created_at: str
    status: str

class UploadInfo(BaseModel):
    upload_id: str
    filename: str
    file_type: str
    file_size: int
    uploaded_at: str
    parsed: bool
    parse_error: Optional[str]

class AnalysisSummary(BaseModel):
    total_credits: float
    total_revenue: float
    credit_rate: float
    top_opportunities: List[dict]
    file_breakdown: List[dict]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def detect_file_type(filename: str, content_preview: bytes) -> str:
    name_lower = filename.lower()
    if name_lower.endswith(".xml"):
        return "nfe_xml"
    if name_lower.endswith(".txt") or name_lower.endswith(".sped"):
        preview = content_preview[:200].decode("utf-8", errors="replace")
        if "|0000|" in preview:
            if "EFD CONTRIBUICOES" in preview.upper() or "CONTRIBUICOES" in preview.upper():
                return "efd_contribuicoes"
            return "sped_efd"
    if name_lower.endswith(".csv"):
        return "csv"
    return "unknown"


def _demo_analysis(session_id: str, segment: str) -> dict:
    """Generate plausible demo analysis when no real files have been parsed."""
    random.seed(session_id)  # reproducible per session
    seg = segment.lower()

    base_revenue = {
        "supermarket": random.uniform(800_000, 2_000_000),
        "bakery":      random.uniform(100_000,   400_000),
        "restaurant":  random.uniform(200_000,   800_000),
    }.get(seg, random.uniform(300_000, 1_000_000))

    pis_rate   = random.uniform(0.0065, 0.0165)
    cofins_rate= random.uniform(0.030,  0.076)
    icms_rate  = random.uniform(0.04,   0.12)

    pis_credit    = base_revenue * pis_rate
    cofins_credit = base_revenue * cofins_rate
    icms_credit   = base_revenue * icms_rate
    total_credits = pis_credit + cofins_credit + icms_credit

    opportunities = [
        {"type": "PIS/COFINS monofásico",
         "description": "Produtos com tributação monofásica — crédito integral na cadeia",
         "estimated_credit": round(pis_credit + cofins_credit, 2),
         "confidence": "alta"},
        {"type": "ICMS diferencial de alíquota",
         "description": "Diferencial de alíquota em compras interestaduais",
         "estimated_credit": round(icms_credit * 0.6, 2),
         "confidence": "média"},
        {"type": "Substituição Tributária",
         "description": "Ressarcimento de ST em devoluções e vendas abaixo da base",
         "estimated_credit": round(icms_credit * 0.4, 2),
         "confidence": "média"},
    ]
    if seg in ("bakery", "restaurant"):
        opportunities.append({
            "type": "Insumos da produção",
            "description": "Crédito de PIS/COFINS sobre insumos utilizados na produção",
            "estimated_credit": round(base_revenue * 0.012, 2),
            "confidence": "alta",
        })

    return {
        "session_id": session_id,
        "generated_at": datetime.utcnow().isoformat(),
        "data_source": "demo",
        "summary": {
            "total_revenue": round(base_revenue, 2),
            "total_credits_identified": round(total_credits, 2),
            "credit_rate_pct": round(total_credits / base_revenue * 100, 2),
            "period": "últimos 12 meses (estimativa)",
        },
        "tax_breakdown": {
            "PIS":   {"credit": round(pis_credit, 2),    "rate_pct": round(pis_rate*100, 4)},
            "COFINS":{"credit": round(cofins_credit, 2), "rate_pct": round(cofins_rate*100, 4)},
            "ICMS":  {"credit": round(icms_credit, 2),   "rate_pct": round(icms_rate*100, 4)},
        },
        "opportunities": opportunities,
        "disclaimer": "Análise demonstrativa gerada automaticamente. Envie arquivos SPED/NFe reais para análise precisa.",
    }


def _real_analysis(session_id: str, uploads: list, segment: str) -> dict:
    """Run real analysis engine on parsed uploads."""
    if not REAL_ENGINE_AVAILABLE:
        return _demo_analysis(session_id, segment)

    engine = TaxAnalysisEngine()
    parsed_data = []
    for u in uploads:
        if u["parsed"] and not u["parse_error"]:
            # Reload file content from disk (stored path or re-parse)
            file_path = u.get("file_path")
            if file_path and os.path.exists(file_path):
                ftype = u["file_type"]
                if ftype in ("sped_efd", "efd_contribuicoes"):
                    parser = SPEDParser()
                    data = parser.parse_file(file_path)
                elif ftype == "nfe_xml":
                    parser = NFeParser()
                    data = parser.parse_file(file_path)
                else:
                    data = None
                if data:
                    parsed_data.append({"type": ftype, "data": data})

    if not parsed_data:
        return _demo_analysis(session_id, segment)

    result = engine.analyze(parsed_data, segment=segment)
    result["session_id"] = session_id
    result["generated_at"] = datetime.utcnow().isoformat()
    result["data_source"] = "real"
    return result


# ---------------------------------------------------------------------------
# Routes — Sessions
# ---------------------------------------------------------------------------
@app.post("/api/sessions", response_model=SessionResponse)
def create_session(body: SessionCreate):
    sid = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    conn = get_db()
    conn.execute(
        "INSERT INTO sessions (id, created_at, company_name, cnpj, segment) VALUES (?,?,?,?,?)",
        (sid, now, body.company_name, body.cnpj, body.segment)
    )
    conn.commit()
    conn.close()
    return SessionResponse(
        session_id=sid,
        company_name=body.company_name,
        cnpj=body.cnpj,
        segment=body.segment,
        created_at=now,
        status="active"
    )


@app.get("/api/sessions/{session_id}", response_model=SessionResponse)
def get_session(session_id: str):
    conn = get_db()
    row = conn.execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, detail="Session not found")
    return SessionResponse(
        session_id=row["id"],
        company_name=row["company_name"],
        cnpj=row["cnpj"],
        segment=row["segment"],
        created_at=row["created_at"],
        status=row["status"]
    )


# ---------------------------------------------------------------------------
# Routes — File Upload
# ---------------------------------------------------------------------------
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.post("/api/sessions/{session_id}/upload")
async def upload_file(session_id: str, file: UploadFile = File(...)):
    # Check session exists
    conn = get_db()
    row = conn.execute("SELECT id FROM sessions WHERE id=?", (session_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(404, detail="Session not found")

    content = await file.read()
    ftype = detect_file_type(file.filename, content[:200])
    upload_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    # Save to disk
    safe_name = f"{upload_id}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_name)
    with open(file_path, "wb") as fh:
        fh.write(content)

    # Parse immediately if possible
    parsed = False
    parse_error = None
    if REAL_ENGINE_AVAILABLE and ftype != "unknown":
        try:
            if ftype in ("sped_efd", "efd_contribuicoes"):
                parser = SPEDParser()
                parser.parse_file(file_path)  # validate
            elif ftype == "nfe_xml":
                parser = NFeParser()
                parser.parse_file(file_path)
            parsed = True
        except Exception as ex:
            parse_error = str(ex)

    conn.execute(
        "INSERT INTO uploads (id, session_id, filename, file_type, file_size, uploaded_at, parsed, parse_error) VALUES (?,?,?,?,?,?,?,?)",
        (upload_id, session_id, file.filename, ftype, len(content), now, parsed, parse_error)
    )
    conn.commit()
    conn.close()

    return {
        "upload_id": upload_id,
        "filename": file.filename,
        "file_type": ftype,
        "file_size": len(content),
        "uploaded_at": now,
        "parsed": parsed,
        "parse_error": parse_error,
    }


@app.get("/api/sessions/{session_id}/uploads")
def list_uploads(session_id: str):
    conn = get_db()
    rows = conn.execute("SELECT * FROM uploads WHERE session_id=?", (session_id,)).fetchall()
    conn.close()
    return [{"upload_id": r["id"], "filename": r["filename"], "file_type": r["file_type"],
             "file_size": r["file_size"], "uploaded_at": r["uploaded_at"],
             "parsed": bool(r["parsed"]), "parse_error": r["parse_error"]} for r in rows]


# ---------------------------------------------------------------------------
# Routes — Analysis
# ---------------------------------------------------------------------------
@app.post("/api/sessions/{session_id}/analyze")
def run_analysis(session_id: str):
    conn = get_db()
    session = conn.execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone()
    if not session:
        conn.close()
        raise HTTPException(404, detail="Session not found")

    uploads = [
        dict(r) for r in
        conn.execute("SELECT * FROM uploads WHERE session_id=?", (session_id,)).fetchall()
    ]
    segment = session["segment"]

    if uploads and any(u["parsed"] for u in uploads):
        result = _real_analysis(session_id, uploads, segment)
    else:
        result = _demo_analysis(session_id, segment)

    result_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    conn.execute(
        "INSERT INTO analysis_results (id, session_id, created_at, result_json) VALUES (?,?,?,?)",
        (result_id, session_id, now, json.dumps(result))
    )
    conn.commit()
    conn.close()
    return result


@app.get("/api/sessions/{session_id}/results")
def get_results(session_id: str):
    conn = get_db()
    row = conn.execute(
        "SELECT result_json FROM analysis_results WHERE session_id=? ORDER BY created_at DESC LIMIT 1",
        (session_id,)
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, detail="No analysis results found. Run /analyze first.")
    return json.loads(row["result_json"])


# ---------------------------------------------------------------------------
# Routes — NCM Lookup
# ---------------------------------------------------------------------------
@app.get("/api/ncm/{code}")
def get_ncm(code: str):
    if not NCM_DB_AVAILABLE:
        raise HTTPException(503, detail="NCM database not available")
    result = lookup_ncm(code)
    if not result:
        raise HTTPException(404, detail=f"NCM {code} not found")
    return result


@app.get("/api/ncm")
def search_ncm_route(q: str = Query(..., min_length=2)):
    if not NCM_DB_AVAILABLE:
        raise HTTPException(503, detail="NCM database not available")
    return search_ncm(q)


@app.get("/api/ncm-categories")
def get_ncm_categories():
    if not NCM_DB_AVAILABLE:
        raise HTTPException(503, detail="NCM database not available")
    return get_all_categories()


@app.get("/api/ncm-category/{category}")
def get_ncm_by_category(category: str):
    if not NCM_DB_AVAILABLE:
        raise HTTPException(503, detail="NCM database not available")
    return get_ncms_by_category(category)


# ---------------------------------------------------------------------------
# Routes — Product Database
# ---------------------------------------------------------------------------
@app.get("/api/products")
def list_products(
    q: Optional[str] = None,
    category: Optional[str] = None,
    ncm: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    if not PRODUCT_DB_AVAILABLE:
        raise HTTPException(503, detail="Product database not available")
    if q:
        products = pd_search(q)
    elif ncm:
        products = pd_by_ncm(ncm)
    elif category:
        products = pd_by_cat(category)
    else:
        products = pd_get_all()
    return {
        "total": len(products),
        "offset": offset,
        "limit": limit,
        "products": products[offset: offset + limit],
    }


@app.get("/api/products/categories")
def product_categories():
    if not PRODUCT_DB_AVAILABLE:
        raise HTTPException(503, detail="Product database not available")
    return pd_categories()


@app.get("/api/products/{product_id}")
def get_product(product_id: str):
    if not PRODUCT_DB_AVAILABLE:
        raise HTTPException(503, detail="Product database not available")
    product = pd_detail(product_id)
    if not product:
        raise HTTPException(404, detail="Product not found")
    return product


# ---------------------------------------------------------------------------
# Routes — Tax Calculator
# ---------------------------------------------------------------------------
class TaxCalcRequest(BaseModel):
    ncm: str
    valor_total: float
    uf_origem: str = "SP"
    uf_destino: str = "SP"
    regime: str = "lucro_presumido"  # lucro_real | lucro_presumido | simples
    operacao: str = "compra"  # compra | venda


@app.post("/api/tax-calculator")
def calculate_taxes(body: TaxCalcRequest):
    ncm_info = None
    if NCM_DB_AVAILABLE:
        ncm_info = lookup_ncm(body.ncm)

    # Base rates (simplified Brazilian tax rules)
    rates = {
        "PIS":    {"lucro_real": 0.0165, "lucro_presumido": 0.0065, "simples": 0.0},
        "COFINS": {"lucro_real": 0.076,  "lucro_presumido": 0.030,  "simples": 0.0},
        "ICMS":   {"SP->SP": 0.18, "inter": 0.12},
    }
    pis_rate    = rates["PIS"].get(body.regime, 0.0065)
    cofins_rate = rates["COFINS"].get(body.regime, 0.030)
    icms_rate   = rates["ICMS"]["SP->SP"] if body.uf_origem == body.uf_destino else rates["ICMS"]["inter"]

    # Apply NCM-specific overrides if available
    if ncm_info:
        tax = ncm_info.get("tax_treatment", {})
        if tax.get("pis_cofins") == "isento":
            pis_rate = cofins_rate = 0.0
        elif tax.get("pis_cofins") == "monofasico":
            pis_rate = 0.021  # representative consolidated rate
            cofins_rate = 0.0
        if tax.get("icms_reducao_bc"):
            icms_rate *= (1 - tax["icms_reducao_bc"])

    pis_val    = body.valor_total * pis_rate
    cofins_val = body.valor_total * cofins_rate
    icms_val   = body.valor_total * icms_rate
    total_tax  = pis_val + cofins_val + icms_val

    return {
        "ncm": body.ncm,
        "ncm_description": ncm_info.get("description") if ncm_info else None,
        "valor_total": body.valor_total,
        "regime": body.regime,
        "uf_origem": body.uf_origem,
        "uf_destino": body.uf_destino,
        "operacao": body.operacao,
        "taxes": {
            "PIS":    {"rate_pct": round(pis_rate*100, 4),    "value": round(pis_val, 2)},
            "COFINS": {"rate_pct": round(cofins_rate*100, 4), "value": round(cofins_val, 2)},
            "ICMS":   {"rate_pct": round(icms_rate*100, 4),   "value": round(icms_val, 2)},
        },
        "total_tax": round(total_tax, 2),
        "effective_tax_rate_pct": round(total_tax / body.valor_total * 100, 2),
    }


# ---------------------------------------------------------------------------
# Routes — Batch Analysis (CSV upload)
# ---------------------------------------------------------------------------
@app.post("/api/batch-analyze")
async def batch_analyze(
    file: UploadFile = File(...),
    segment: str = Form("supermarket")
):
    """
    Accept a CSV with columns: product_name, ncm, valor_total, regime
    Return per-line tax analysis.
    """
    import csv, io
    content = await file.read()
    text = content.decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    results = []
    for i, row in enumerate(reader):
        if i >= 1000:  # safety limit
            break
        try:
            calc = TaxCalcRequest(
                ncm=row.get("ncm", "0000.00.00"),
                valor_total=float(row.get("valor_total", 0)),
                regime=row.get("regime", "lucro_presumido"),
            )
            tax_result = calculate_taxes(calc)
            tax_result["product_name"] = row.get("product_name", "")
            results.append(tax_result)
        except Exception as ex:
            results.append({"error": str(ex), "row": row})
    return {"total_rows": len(results), "results": results}


# ---------------------------------------------------------------------------
# Routes — Export
# ---------------------------------------------------------------------------
@app.get("/api/sessions/{session_id}/export")
def export_results(session_id: str, fmt: str = Query("json", regex="^(json|csv)$")):
    conn = get_db()
    row = conn.execute(
        "SELECT result_json FROM analysis_results WHERE session_id=? ORDER BY created_at DESC LIMIT 1",
        (session_id,)
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, detail="No results to export")

    data = json.loads(row["result_json"])

    if fmt == "json":
        content_str = json.dumps(data, ensure_ascii=False, indent=2)
        return StreamingResponse(
            iter([content_str]),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=analysis_{session_id[:8]}.json"}
        )
    else:  # csv
        import csv, io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["type", "description", "estimated_credit", "confidence"])
        for opp in data.get("opportunities", []):
            writer.writerow([
                opp.get("type", ""),
                opp.get("description", ""),
                opp.get("estimated_credit", ""),
                opp.get("confidence", ""),
            ])
        csv_content = output.getvalue()
        return StreamingResponse(
            iter([csv_content]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=analysis_{session_id[:8]}.csv"}
        )


# ---------------------------------------------------------------------------
# Routes — Health & Info
# ---------------------------------------------------------------------------
@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "version": "2.0.0",
        "real_engine": REAL_ENGINE_AVAILABLE,
        "ncm_db": NCM_DB_AVAILABLE,
        "product_db": PRODUCT_DB_AVAILABLE,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/api/info")
def info():
    return {
        "name": "CRG Motor de Análise Tributária",
        "version": "2.0.0",
        "description": "FastAPI backend for tax recovery analysis",
        "segments": ["supermarket", "bakery", "restaurant"],
        "supported_files": ["SPED EFD", "EFD Contribuições", "NFe XML"],
        "endpoints": [
            "POST /api/sessions",
            "GET  /api/sessions/{id}",
            "POST /api/sessions/{id}/upload",
            "GET  /api/sessions/{id}/uploads",
            "POST /api/sessions/{id}/analyze",
            "GET  /api/sessions/{id}/results",
            "GET  /api/sessions/{id}/export",
            "GET  /api/ncm/{code}",
            "GET  /api/ncm?q=...",
            "GET  /api/ncm-categories",
            "GET  /api/ncm-category/{cat}",
            "GET  /api/products",
            "GET  /api/products/categories",
            "GET  /api/products/{id}",
            "POST /api/tax-calculator",
            "POST /api/batch-analyze",
            "GET  /api/health",
            "GET  /api/info",
        ],
    }


# ---------------------------------------------------------------------------
# Static files (serve frontend build if present)
# ---------------------------------------------------------------------------
_STATIC_DIR = os.environ.get("STATIC_DIR", "static")
if os.path.isdir(_STATIC_DIR):
    app.mount("/", StaticFiles(directory=_STATIC_DIR, html=True), name="static")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    _port = int(os.environ.get("PORT", 8000))
    _host = os.environ.get("HOST", "0.0.0.0")
    uvicorn.run(app, host=_host, port=_port)
