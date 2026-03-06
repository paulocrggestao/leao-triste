#!/usr/bin/env python3
"""
xml_parser.py — Parser de XML de NFe/NFCe e arquivos ZIP contendo XMLs.

Extrai dados de itens para alimentar o analysis_engine:
  - NCM
  - CST PIS / COFINS
  - Valor do item
  - CFOP
  - Tipo (entrada/saída)
  - Informações de ICMS / ICMS-ST

Suporta:
  - NF-e 4.0 (layout 4.00)
  - NFC-e
  - Arquivos .xml individuais
  - Arquivos .zip contendo múltiplos XMLs
  - Pastas com múltiplos XMLs
"""

from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Iterator
from xml.etree import ElementTree as ET

# Namespace NFe 4.0
NS = {"nfe": "http://www.portalfiscal.inf.br/nfe"}
NFE_NS = "http://www.portalfiscal.inf.br/nfe"


# ──────────────────────────────────────────────────────────────────────────────
# Utilitários
# ──────────────────────────────────────────────────────────────────────────────

def _txt(el, tag: str, ns: str = NFE_NS, default: str = "") -> str:
    """Extrai texto de sub-elemento com namespace."""
    found = el.find(f"{{{ns}}}{tag}")
    return found.text.strip() if found is not None and found.text else default


def _float(val: str) -> float:
    """Converte string para float, tolerando vazio."""
    try:
        return float(val.strip()) if val.strip() else 0.0
    except ValueError:
        return 0.0


def _competencia_from_dhemi(dhemi: str) -> str:
    """Extrai YYYYMM de dHEmi (formato YYYY-MM-DDTHH:MM:SS-HH:MM)."""
    # 2024-03-15T10:30:00-03:00 → 202403
    dhemi = dhemi.strip()
    if len(dhemi) >= 7:
        return dhemi[:4] + dhemi[5:7]
    return ""


# ──────────────────────────────────────────────────────────────────────────────
# Parser de item de NFe
# ──────────────────────────────────────────────────────────────────────────────

def _parse_det(det: ET.Element, tipo_nfe: str, competencia: str) -> dict | None:
    """
    Parseia um elemento <det> (item) de NFe.

    Retorna dict compatível com nfe_items do analysis_engine:
        ncm, cst_pis, cst_cofins, valor_item, cfop, tipo, competencia,
        cst_icms, valor_bc_icms, aliq_icms, valor_icms,
        valor_bc_st, aliq_st, valor_icms_st
    """
    prod = det.find(f"{{{NFE_NS}}}prod")
    if prod is None:
        return None

    ncm = _txt(prod, "NCM")
    cfop = _txt(prod, "CFOP")
    vl_prod = _float(_txt(prod, "vProd"))
    vl_desc = _float(_txt(prod, "vDesc"))
    valor_item = vl_prod - vl_desc

    # ICMS
    imposto = det.find(f"{{{NFE_NS}}}imposto")
    cst_icms = ""
    valor_bc_icms = 0.0
    aliq_icms = 0.0
    valor_icms = 0.0
    valor_bc_st = 0.0
    aliq_st = 0.0
    valor_icms_st = 0.0

    if imposto is not None:
        icms_el = imposto.find(f"{{{NFE_NS}}}ICMS")
        if icms_el is not None:
            # Tenta todos os filhos (ICMS00, ICMS10, ICMS20, ..., ICMSST)
            for child in icms_el:
                tag = child.tag.replace(f"{{{NFE_NS}}}", "")
                cst_icms = _txt(child, "CST") or _txt(child, "CSOSN")
                valor_bc_icms = _float(_txt(child, "vBC"))
                aliq_icms = _float(_txt(child, "pICMS"))
                valor_icms = _float(_txt(child, "vICMS"))
                valor_bc_st = _float(_txt(child, "vBCST"))
                aliq_st = _float(_txt(child, "pICMSST"))
                valor_icms_st = _float(_txt(child, "vICMSST"))
                break  # Pega apenas o primeiro grupo

        # PIS
        pis_el = imposto.find(f"{{{NFE_NS}}}PIS")
        cst_pis = ""
        if pis_el is not None:
            for child in pis_el:
                cst_pis = _txt(child, "CST")
                break

        # COFINS
        cofins_el = imposto.find(f"{{{NFE_NS}}}COFINS")
        cst_cofins = ""
        if cofins_el is not None:
            for child in cofins_el:
                cst_cofins = _txt(child, "CST")
                break
    else:
        cst_pis = ""
        cst_cofins = ""

    # Tipo: entrada ou saída pelo CFOP
    if cfop.startswith(("1", "2", "3")):
        tipo = "E"
    else:
        tipo = "S"

    # Override pelo tipo da NF-e
    if tipo_nfe == "entrada":
        tipo = "E"
    elif tipo_nfe == "saida":
        tipo = "S"

    return {
        "ncm": ncm.replace(".", ""),
        "cst_pis": cst_pis.zfill(2) if cst_pis else "",
        "cst_cofins": cst_cofins.zfill(2) if cst_cofins else "",
        "valor_item": valor_item,
        "cfop": cfop,
        "tipo": tipo,
        "competencia": competencia,
        "cst_icms": cst_icms,
        "valor_bc_icms": valor_bc_icms,
        "aliq_icms": aliq_icms,
        "valor_icms": valor_icms,
        "valor_bc_st": valor_bc_st,
        "aliq_st": aliq_st,
        "valor_icms_st": valor_icms_st,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Parser de NF-e XML
# ──────────────────────────────────────────────────────────────────────────────

def parse_nfe_xml(xml_content: str | bytes) -> list[dict]:
    """
    Parseia um XML de NF-e/NFC-e e retorna lista de itens (dicts).

    xml_content: string ou bytes do XML da NF-e.
    """
    if isinstance(xml_content, bytes):
        xml_content = xml_content.decode("utf-8", errors="replace")

    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        return []  # XML inválido

    # Remove namespaces para facilitar busca (alguns XMLs não têm)
    # Tenta encontrar nfeProc ou NFe diretamente
    nfe = root.find(f"{{{NFE_NS}}}NFe")
    if nfe is None:
        nfe = root.find("NFe")  # Sem namespace
    if nfe is None:
        # Talvez root já seja NFe
        if root.tag in (f"{{{NFE_NS}}}NFe", "NFe"):
            nfe = root
    if nfe is None:
        return []

    infNFe = nfe.find(f"{{{NFE_NS}}}infNFe")
    if infNFe is None:
        infNFe = nfe.find("infNFe")
    if infNFe is None:
        return []

    # Cabeçalho: data e tipo
    ide = infNFe.find(f"{{{NFE_NS}}}ide")
    dhemi = ""
    tipo_nfe = "saida"  # default
    if ide is not None:
        dhemi = _txt(ide, "dhEmi") or _txt(ide, "dEmi")
        tpnf = _txt(ide, "tpNF")  # 0=entrada, 1=saída
        if tpnf == "0":
            tipo_nfe = "entrada"
        elif tpnf == "1":
            tipo_nfe = "saida"

    competencia = _competencia_from_dhemi(dhemi)

    # Itera sobre itens <det>
    items = []
    for det in infNFe.findall(f"{{{NFE_NS}}}det"):
        item = _parse_det(det, tipo_nfe, competencia)
        if item:
            items.append(item)

    return items


# ──────────────────────────────────────────────────────────────────────────────
# Leitura de arquivos e pastas
# ──────────────────────────────────────────────────────────────────────────────

def parse_nfe_file(path: str | Path) -> list[dict]:
    """Lê um arquivo XML de NF-e e retorna lista de itens."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")
    content = path.read_bytes()
    return parse_nfe_xml(content)


def parse_nfe_zip(path: str | Path) -> list[dict]:
    """
    Lê um arquivo ZIP contendo XMLs de NF-e e retorna lista de itens
    de todos os XMLs encontrados.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Arquivo ZIP não encontrado: {path}")

    all_items: list[dict] = []
    with zipfile.ZipFile(path, "r") as zf:
        for name in zf.namelist():
            if name.lower().endswith(".xml"):
                try:
                    content = zf.read(name)
                    items = parse_nfe_xml(content)
                    all_items.extend(items)
                except Exception:
                    pass  # Ignora XMLs inválidos dentro do ZIP

    return all_items


def parse_nfe_folder(folder: str | Path) -> list[dict]:
    """
    Lê todos os XMLs de NF-e de uma pasta (recursivo).
    """
    folder = Path(folder)
    if not folder.is_dir():
        raise NotADirectoryError(f"Pasta não encontrada: {folder}")

    all_items: list[dict] = []
    for xml_path in folder.rglob("*.xml"):
        try:
            items = parse_nfe_file(xml_path)
            all_items.extend(items)
        except Exception:
            pass

    return all_items


# ──────────────────────────────────────────────────────────────────────────────
# Extração de faturamento para Tema 69
# ──────────────────────────────────────────────────────────────────────────────

def extract_faturamento_from_nfes(
    nfe_items: list[dict],
    regime_tributario: str = "lucro_presumido",
) -> list[dict]:
    """
    Agrega itens de NFe por competência para montar faturamento_mensal
    compatível com _analisa_tema69.

    Calcula ICMS destacado somando valor_icms de todos os itens de saída.
    """
    from collections import defaultdict

    por_competencia: dict[str, dict] = defaultdict(lambda: {
        "receita_bruta": 0.0,
        "icms_destacado": 0.0,
        "pis_pago": 0.0,
        "cofins_pago": 0.0,
    })

    for item in nfe_items:
        comp = item.get("competencia", "")
        if not comp:
            continue
        tipo = item.get("tipo", "S")
        if tipo != "S":
            continue  # Apenas saídas

        row = por_competencia[comp]
        row["receita_bruta"] += item.get("valor_item", 0.0)
        row["icms_destacado"] += item.get("valor_icms", 0.0)
        # PIS e COFINS destacados nos XMLs (se disponíveis)
        # Em geral não estão presentes no XML — serão calculados pelo motor

    result = []
    for comp, data in sorted(por_competencia.items()):
        result.append({
            "competencia": comp,
            "receita_bruta": round(data["receita_bruta"], 2),
            "icms_destacado": round(data["icms_destacado"], 2),
            "pis_pago": round(data["pis_pago"], 2),
            "cofins_pago": round(data["cofins_pago"], 2),
            "regime_tributario": regime_tributario,
        })

    return result
