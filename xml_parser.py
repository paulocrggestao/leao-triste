#!/usr/bin/env python3
"""
xml_parser.py — Parser de XML de NFe/NFCe e arquivos ZIP contendo XMLs.

Namespace NFe: http://www.portalfiscal.inf.br/nfe
"""

from __future__ import annotations

import io
import zipfile
from typing import Optional


try:
    from lxml import etree as ET
    LXML_AVAILABLE = True
except ImportError:
    import xml.etree.ElementTree as ET  # type: ignore
    LXML_AVAILABLE = False

# NFe namespace
NFE_NS = "http://www.portalfiscal.inf.br/nfe"
NS = {"nfe": NFE_NS}


# ─────────────────────────────────────────────────────────────────────────────
# Helper utilities
# ─────────────────────────────────────────────────────────────────────────────

def _text(element, path: str, default: str = "") -> str:
    """Safely get text from an element, trying with and without namespace."""
    if element is None:
        return default

    # Try with namespace
    ns_path = "/".join(
        f"nfe:{p}" if not p.startswith("@") else p
        for p in path.split("/")
    )
    try:
        el = element.find(ns_path, NS)
        if el is not None and el.text:
            return el.text.strip()
    except Exception:
        pass

    # Try without namespace (some files strip ns)
    try:
        el = element.find(path)
        if el is not None and el.text:
            return el.text.strip()
    except Exception:
        pass

    return default


def _float(element, path: str, default: float = 0.0) -> float:
    """Get float value from element."""
    val = _text(element, path, "")
    if not val:
        return default
    try:
        return float(val.replace(",", "."))
    except (ValueError, AttributeError):
        return default


def _find(element, path: str):
    """Find element trying both with and without namespace."""
    if element is None:
        return None

    ns_path = "/".join(f"nfe:{p}" for p in path.split("/"))
    try:
        result = element.find(ns_path, NS)
        if result is not None:
            return result
    except Exception:
        pass

    try:
        result = element.find(path)
        if result is not None:
            return result
    except Exception:
        pass

    return None


def _findall(element, path: str) -> list:
    """Findall trying both with and without namespace."""
    if element is None:
        return []

    ns_path = "/".join(f"nfe:{p}" for p in path.split("/"))
    try:
        result = element.findall(ns_path, NS)
        if result:
            return result
    except Exception:
        pass

    try:
        result = element.findall(path)
        if result:
            return result
    except Exception:
        pass

    return []


def _strip_ns(tag: str) -> str:
    """Remove namespace from tag name."""
    if "}" in tag:
        return tag.split("}")[1]
    return tag


# ─────────────────────────────────────────────────────────────────────────────
# ICMS extraction — handles multiple CST sub-elements
# ─────────────────────────────────────────────────────────────────────────────

def _extract_icms_data(imposto_el) -> dict:
    """
    Extract ICMS data from det/imposto/ICMS element.
    Handles sub-elements: ICMS00, ICMS10, ICMS20, ICMS30, ICMS40, ICMS51, 
    ICMS60, ICMS70, ICMS90, ICMSSN101, ICMSSN102, etc.
    """
    data = {
        "cst_icms": "",
        "csosn": "",
        "base_icms": 0.0,
        "aliq_icms": 0.0,
        "valor_icms": 0.0,
        "base_icms_st": 0.0,
        "aliq_icms_st": 0.0,
        "valor_icms_st": 0.0,
        "valor_icms_mono": 0.0,
    }

    if imposto_el is None:
        return data

    icms_container = _find(imposto_el, "ICMS")
    if icms_container is None:
        return data

    # Iterate children to find the actual ICMS sub-element
    for child in icms_container:
        tag = _strip_ns(child.tag)

        # CRT=1 (Simples Nacional) uses CSOSN
        if tag.startswith("ICMSSN"):
            data["csosn"] = _text(child, "CSOSN") or _text(child, "indSN")
            data["base_icms"] = _float(child, "vBC")
            data["aliq_icms"] = _float(child, "pICMS")
            data["valor_icms"] = _float(child, "vICMS")
            data["base_icms_st"] = _float(child, "vBCST")
            data["aliq_icms_st"] = _float(child, "pICMSST")
            data["valor_icms_st"] = _float(child, "vICMSST")
        else:
            # Regular CST-based ICMS
            data["cst_icms"] = _text(child, "CST") or _text(child, "orig") + _text(child, "CST")
            data["base_icms"] = _float(child, "vBC")
            data["aliq_icms"] = _float(child, "pICMS")
            data["valor_icms"] = _float(child, "vICMS")
            data["base_icms_st"] = _float(child, "vBCST")
            data["aliq_icms_st"] = _float(child, "pICMSST")
            data["valor_icms_st"] = _float(child, "vICMSST")
            # Monophasic ICMS for fuels
            data["valor_icms_mono"] = _float(child, "vICMSMono")

    return data


def _extract_pis_data(imposto_el) -> dict:
    """Extract PIS data from det/imposto/PIS element."""
    data = {
        "cst_pis": "",
        "base_pis": 0.0,
        "aliq_pis": 0.0,
        "valor_pis": 0.0,
    }

    if imposto_el is None:
        return data

    pis_el = _find(imposto_el, "PIS")
    if pis_el is None:
        return data

    for child in pis_el:
        tag = _strip_ns(child.tag)
        if tag in ("PISAliq", "PISQtde", "PISNT", "PISOutr"):
            data["cst_pis"] = _text(child, "CST")
            data["base_pis"] = _float(child, "vBC")
            data["aliq_pis"] = _float(child, "pPIS")
            data["valor_pis"] = _float(child, "vPIS")

    return data


def _extract_cofins_data(imposto_el) -> dict:
    """Extract COFINS data from det/imposto/COFINS element."""
    data = {
        "cst_cofins": "",
        "base_cofins": 0.0,
        "aliq_cofins": 0.0,
        "valor_cofins": 0.0,
    }

    if imposto_el is None:
        return data

    cofins_el = _find(imposto_el, "COFINS")
    if cofins_el is None:
        return data

    for child in cofins_el:
        tag = _strip_ns(child.tag)
        if tag in ("COFINSAliq", "COFINSQtde", "COFINSNT", "COFINSOutr"):
            data["cst_cofins"] = _text(child, "CST")
            data["base_cofins"] = _float(child, "vBC")
            data["aliq_cofins"] = _float(child, "pCOFINS")
            data["valor_cofins"] = _float(child, "vCOFINS")

    return data


# ─────────────────────────────────────────────────────────────────────────────
# NFeParser
# ─────────────────────────────────────────────────────────────────────────────

class NFeParser:
    """
    Parser para NFe/NFCe em XML ou ZIP contendo múltiplos XMLs.

    Usage:
        parser = NFeParser()
        nfe_data = parser.parse_xml(xml_bytes)
        items = parser.extract_items(nfe_data)

        # Para ZIP:
        nfes = parser.parse_zip(zip_bytes)
    """

    def parse_xml(self, xml_content: bytes) -> dict:
        """
        Parse a single NFe XML file.

        Args:
            xml_content: raw bytes of the XML file

        Returns:
            Structured dict with all NFe data
        """
        try:
            if LXML_AVAILABLE:
                root = ET.fromstring(xml_content)
            else:
                root = ET.fromstring(xml_content.decode("utf-8", errors="replace"))
        except Exception as e:
            return {"error": str(e), "items": []}

        # Find infNFe — may be wrapped in nfeProc
        inf_nfe = None

        # Try nfeProc/NFe/infNFe
        inf_nfe = _find(root, "NFe/infNFe")
        if inf_nfe is None:
            # Try directly on root (some files are just NFe)
            inf_nfe = _find(root, "infNFe")
        if inf_nfe is None:
            # Root might be NFe itself
            inf_nfe = root.find(f"{{{NFE_NS}}}infNFe")
        if inf_nfe is None:
            # Last resort: tag scan
            tag = _strip_ns(root.tag)
            if tag == "NFe":
                for child in root:
                    if _strip_ns(child.tag) == "infNFe":
                        inf_nfe = child
                        break
            elif tag == "nfeProc":
                for child in root:
                    if _strip_ns(child.tag) == "NFe":
                        for grandchild in child:
                            if _strip_ns(grandchild.tag) == "infNFe":
                                inf_nfe = grandchild
                                break
                        break

        if inf_nfe is None:
            return {"error": "infNFe_not_found", "items": []}

        # Parse ide (document identification)
        ide = _find(inf_nfe, "ide")
        emit = _find(inf_nfe, "emit")
        dest = _find(inf_nfe, "dest")
        total = _find(inf_nfe, "total/ICMSTot")

        nfe_data = {
            # Document
            "chave": (inf_nfe.get("Id") or "").replace("NFe", ""),
            "modelo": _text(ide, "mod"),
            "serie": _text(ide, "serie"),
            "numero": _text(ide, "nNF"),
            "data_emissao": _text(ide, "dhEmi") or _text(ide, "dEmi"),
            "natureza_operacao": _text(ide, "natOp"),
            "tipo_operacao": _text(ide, "tpNF"),  # 0=entrada, 1=saída
            "cfop_principal": _text(ide, "CFOP"),
            # Emitter
            "emitente_cnpj": _text(emit, "CNPJ"),
            "emitente_cpf": _text(emit, "CPF"),
            "emitente_nome": _text(emit, "xNome"),
            "emitente_uf": _text(_find(emit, "enderEmit") if emit is not None else None, "UF"),
            # Recipient
            "destinatario_cnpj": _text(dest, "CNPJ") if dest is not None else "",
            "destinatario_cpf": _text(dest, "CPF") if dest is not None else "",
            "destinatario_nome": _text(dest, "xNome") if dest is not None else "",
            # Totals
            "total_produtos": _float(total, "vProd"),
            "total_nota": _float(total, "vNF"),
            "total_icms": _float(total, "vICMS"),
            "total_icms_st": _float(total, "vST"),
            "total_pis": _float(total, "vPIS"),
            "total_cofins": _float(total, "vCOFINS"),
            "total_ipi": _float(total, "vIPI"),
            "total_frete": _float(total, "vFrete"),
            # Items
            "items": [],
        }

        # Parse items (det elements)
        det_elements = _findall(inf_nfe, "det")
        for det in det_elements:
            prod = _find(det, "prod")
            imposto = _find(det, "imposto")

            if prod is None:
                continue

            icms_data = _extract_icms_data(imposto)
            pis_data = _extract_pis_data(imposto)
            cofins_data = _extract_cofins_data(imposto)

            item = {
                "numero_item": det.get("nItem", ""),
                "ncm": _text(prod, "NCM"),
                "cfop": _text(prod, "CFOP"),
                "codigo_produto": _text(prod, "cProd"),
                "descricao": _text(prod, "xProd"),
                "ean": _text(prod, "cEAN"),
                "unidade": _text(prod, "uCom"),
                "quantidade": _float(prod, "qCom"),
                "valor_unitario": _float(prod, "vUnCom"),
                "valor_total": _float(prod, "vProd"),
                "valor_desconto": _float(prod, "vDesc"),
                # ICMS
                "cst_icms": icms_data["cst_icms"] or icms_data["csosn"],
                "csosn": icms_data["csosn"],
                "base_icms": icms_data["base_icms"],
                "aliq_icms": icms_data["aliq_icms"],
                "valor_icms": icms_data["valor_icms"],
                "base_icms_st": icms_data["base_icms_st"],
                "aliq_icms_st": icms_data["aliq_icms_st"],
                "valor_icms_st": icms_data["valor_icms_st"],
                # PIS
                "cst_pis": pis_data["cst_pis"],
                "base_pis": pis_data["base_pis"],
                "aliq_pis": pis_data["aliq_pis"],
                "valor_pis": pis_data["valor_pis"],
                # COFINS
                "cst_cofins": cofins_data["cst_cofins"],
                "base_cofins": cofins_data["base_cofins"],
                "aliq_cofins": cofins_data["aliq_cofins"],
                "valor_cofins": cofins_data["valor_cofins"],
            }
            nfe_data["items"].append(item)

        return nfe_data

    def parse_zip(self, zip_content: bytes) -> list:
        """
        Parse a ZIP archive containing multiple NFe XML files.

        Args:
            zip_content: raw bytes of the ZIP archive

        Returns:
            List of parsed NFe dicts
        """
        results = []
        try:
            with zipfile.ZipFile(io.BytesIO(zip_content)) as zf:
                for name in zf.namelist():
                    lower = name.lower()
                    if not (lower.endswith(".xml") or lower.endswith("-nfe.xml")):
                        continue
                    try:
                        xml_bytes = zf.read(name)
                        nfe = self.parse_xml(xml_bytes)
                        nfe["_source_filename"] = name
                        results.append(nfe)
                    except Exception as e:
                        results.append({
                            "_source_filename": name,
                            "error": str(e),
                            "items": [],
                        })
        except zipfile.BadZipFile as e:
            return [{"error": f"Invalid ZIP: {e}", "items": []}]
        return results

    def extract_items(self, nfe_data: dict) -> list:
        """
        Extract all items with their tax info from a parsed NFe.

        Args:
            nfe_data: dict returned by parse_xml()

        Returns:
            List of item dicts with all tax fields
        """
        if not nfe_data or "items" not in nfe_data:
            return []

        items = []
        for raw_item in nfe_data["items"]:
            item = {
                # Document info
                "documento_numero": nfe_data.get("numero", ""),
                "documento_serie": nfe_data.get("serie", ""),
                "documento_data": nfe_data.get("data_emissao", ""),
                "tipo_operacao": nfe_data.get("tipo_operacao", "1"),
                "emitente_cnpj": nfe_data.get("emitente_cnpj", ""),
                "emitente_nome": nfe_data.get("emitente_nome", ""),
                # Product
                "ncm": raw_item.get("ncm", ""),
                "cfop": raw_item.get("cfop", ""),
                "codigo_produto": raw_item.get("codigo_produto", ""),
                "descricao": raw_item.get("descricao", ""),
                "quantidade": raw_item.get("quantidade", 0.0),
                "valor_unitario": raw_item.get("valor_unitario", 0.0),
                "valor_total": raw_item.get("valor_total", 0.0),
                # ICMS
                "cst_icms": raw_item.get("cst_icms", ""),
                "base_icms": raw_item.get("base_icms", 0.0),
                "aliq_icms": raw_item.get("aliq_icms", 0.0),
                "valor_icms": raw_item.get("valor_icms", 0.0),
                "base_icms_st": raw_item.get("base_icms_st", 0.0),
                "aliq_icms_st": raw_item.get("aliq_icms_st", 0.0),
                "valor_icms_st": raw_item.get("valor_icms_st", 0.0),
                # PIS
                "cst_pis": raw_item.get("cst_pis", ""),
                "base_pis": raw_item.get("base_pis", 0.0),
                "aliq_pis": raw_item.get("aliq_pis", 0.0),
                "valor_pis": raw_item.get("valor_pis", 0.0),
                # COFINS
                "cst_cofins": raw_item.get("cst_cofins", ""),
                "base_cofins": raw_item.get("base_cofins", 0.0),
                "aliq_cofins": raw_item.get("aliq_cofins", 0.0),
                "valor_cofins": raw_item.get("valor_cofins", 0.0),
                # Source
                "_source": "nfe_xml",
            }
            items.append(item)
        return items

    def extract_items_from_list(self, nfe_list: list) -> list:
        """Extract all items from a list of parsed NFes."""
        all_items = []
        for nfe in nfe_list:
            all_items.extend(self.extract_items(nfe))
        return all_items


# ─────────────────────────────────────────────────────────────────────────────
# CLI for testing
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python xml_parser.py <file.xml|file.zip>")
        sys.exit(1)

    path = sys.argv[1]
    parser = NFeParser()

    with open(path, "rb") as f:
        content = f.read()

    if path.lower().endswith(".zip"):
        nfes = parser.parse_zip(content)
        print(f"Parsed {len(nfes)} NFes from ZIP")
        for nfe in nfes[:3]:
            if "error" in nfe:
                print(f"  Error in {nfe.get('_source_filename', '')}: {nfe['error']}")
            else:
                print(f"  NFe {nfe.get('numero', '?')} — {nfe.get('emitente_nome', '?')} — {len(nfe.get('items', []))} items")
                print(f"    Total: R$ {nfe.get('total_nota', 0):.2f}")
    else:
        nfe = parser.parse_xml(content)
        if "error" in nfe:
            print(f"Error: {nfe['error']}")
        else:
            print(f"NFe {nfe.get('numero', '?')} — Série {nfe.get('serie', '?')}")
            print(f"Emitente: {nfe.get('emitente_nome', '?')} ({nfe.get('emitente_cnpj', '?')})")
            print(f"Data: {nfe.get('data_emissao', '?')}")
            print(f"Total nota: R$ {nfe.get('total_nota', 0):.2f}")
            print(f"Items: {len(nfe.get('items', []))}")

            items = parser.extract_items(nfe)
            for item in items[:5]:
                print(f"\n  Item: {item['descricao']} (NCM {item['ncm']})")
                print(f"    CFOP: {item['cfop']}, Qtd: {item['quantidade']}, Total: R$ {item['valor_total']:.2f}")
                print(f"    CST PIS: {item['cst_pis']}, VL PIS: R$ {item['valor_pis']:.2f}")
                print(f"    CST COFINS: {item['cst_cofins']}, VL COFINS: R$ {item['valor_cofins']:.2f}")
