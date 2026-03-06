#!/usr/bin/env python3
"""
sped_parser.py — Parser de arquivos SPED (EFD ICMS/IPI e EFD Contribuições)

Lê arquivos SPED em texto e extrai os registros relevantes para
recuperação tributária:

  EFD ICMS/IPI:
    C100 — Nota fiscal (cabeçalho)
    C170 — Itens da nota fiscal
    C190 — Analítico do documento

  EFD Contribuições:
    F100 — Demais documentos e operações geradoras de crédito
    M200 — Apuração PIS (contribuição + crédito)
    M600 — Apuração COFINS

Retorna dicts compatíveis com analysis_engine.py
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator


# ──────────────────────────────────────────────────────────────────────────────
# Constantes
# ──────────────────────────────────────────────────────────────────────────────

REGISTROS_EFD = {"0000", "0001", "0005", "C001", "C100", "C170", "C190",
                 "C400", "C405", "C420", "C425", "C460", "C470",
                 "D001", "D100", "D190",
                 "E001", "E110", "E111", "E112", "E116",
                 "G001", "G110", "G125",
                 "H001", "H010",
                 "9001", "9900", "9999"}

REGISTROS_CONTRIB = {"0000", "0001", "0140",
                     "A001", "A010", "A100", "A110", "A111",
                     "C001", "C010", "C100", "C110", "C111", "C120",
                     "C170", "C175", "C180", "C181", "C185", "C188",
                     "C190", "C191", "C195", "C198", "C199",
                     "F001", "F010", "F100", "F111", "F120", "F129",
                     "F130", "F139", "F150", "F200", "F205", "F210",
                     "F500", "F509", "F510", "F519", "F520", "F525",
                     "F600", "F700", "F800",
                     "M001", "M100", "M105", "M110", "M115",
                     "M200", "M205", "M210", "M211", "M215",
                     "M220", "M225", "M230", "M400", "M410",
                     "M500", "M505", "M510", "M515",
                     "M600", "M605", "M610", "M611", "M615",
                     "M620", "M625", "M630", "M800", "M810",
                     "P001", "P010", "P100", "P110", "P199",
                     "Q001", "Q010", "Q100", "Q110",
                     "1001", "1010", "1011", "1020", "1050",
                     "1100", "1101", "1102", "1200", "1201",
                     "1300", "1500", "1501", "1502",
                     "9001", "9900", "9999"}


# ──────────────────────────────────────────────────────────────────────────────
# Data classes de saída
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class SpedC100:
    """Registro C100 — Nota Fiscal (EFD ICMS/IPI)"""
    ind_oper: str        # 0=entrada, 1=saída
    chave_nfe: str
    num_doc: str
    cnpj_emit: str
    data_doc: str        # DDMMAAAA
    valor_total: float
    valor_bc_icms: float
    valor_icms: float
    valor_icms_st: float
    valor_bc_st: float
    cod_part: str
    cod_sit: str


@dataclass
class SpedC170:
    """Registro C170 — Itens da NF (EFD ICMS/IPI)"""
    num_item: str
    cod_item: str
    descr_compl: str
    qtd: float
    unid: str
    vl_item: float
    vl_desc: float
    cst_icms: str
    cfop: str
    cod_nat: str
    ncm: str
    vl_bc_icms: float
    aliq_icms: float
    vl_icms: float
    vl_bc_icms_st: float
    aliq_st: float
    vl_icms_st: float
    # SPED Contribuições
    cst_pis: str = ""
    vl_bc_pis: float = 0.0
    aliq_pis: float = 0.0
    vl_pis: float = 0.0
    cst_cofins: str = ""
    vl_bc_cofins: float = 0.0
    aliq_cofins: float = 0.0
    vl_cofins: float = 0.0


@dataclass
class SpedResult:
    """Resultado consolidado do parse SPED"""
    cnpj: str
    competencia_inicio: str   # YYYYMM
    competencia_fim: str      # YYYYMM
    tipo: str                 # "icms_ipi" | "contribuicoes"
    c100_list: list[SpedC100] = field(default_factory=list)
    c170_list: list[SpedC170] = field(default_factory=list)
    pis_apurado: float = 0.0
    cofins_apurado: float = 0.0
    credito_pis: float = 0.0
    credito_cofins: float = 0.0
    warnings: list[str] = field(default_factory=list)


# ──────────────────────────────────────────────────────────────────────────────
# Utilitários
# ──────────────────────────────────────────────────────────────────────────────

def _to_float(s: str) -> float:
    """Converte string SPED para float (vírgula → ponto)."""
    s = s.strip().replace(".", "").replace(",", ".")
    try:
        return float(s) if s else 0.0
    except ValueError:
        return 0.0


def _parse_linha(linha: str) -> list[str]:
    """Divide linha SPED em campos pelo separador '|'."""
    if linha.startswith("|"):
        linha = linha[1:]
    if linha.endswith("|"):
        linha = linha[:-1]
    return linha.split("|")


def _data_para_yyyymm(data_ddmmaaaa: str) -> str:
    """Converte DDMMAAAA para YYYYMM."""
    data = data_ddmmaaaa.strip()
    if len(data) == 8:
        return data[4:8] + data[2:4]
    return data[:6]  # Já está em YYYYMM


# ──────────────────────────────────────────────────────────────────────────────
# Parser EFD ICMS/IPI
# ──────────────────────────────────────────────────────────────────────────────

def parse_efd_icms_ipi(path: str | Path) -> SpedResult:
    """
    Lê um arquivo EFD ICMS/IPI e retorna SpedResult com:
    - Lista de C100 (notas fiscais)
    - Lista de C170 (itens)
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Arquivo SPED não encontrado: {path}")

    cnpj = ""
    comp_ini = ""
    comp_fim = ""
    c100_list: list[SpedC100] = []
    c170_list: list[SpedC170] = []
    warnings: list[str] = []
    current_c100: SpedC100 | None = None

    with open(path, encoding="latin-1", errors="replace") as fh:
        for num, linha in enumerate(fh, 1):
            linha = linha.rstrip("\n\r")
            campos = _parse_linha(linha)
            if not campos:
                continue
            reg = campos[0].upper()

            if reg == "0000":
                # |0000|COD_VER|COD_FIN|DT_INI|DT_FIN|NOME|CNPJ|...|
                if len(campos) > 7:
                    cnpj = campos[7].strip()
                if len(campos) > 3:
                    comp_ini = _data_para_yyyymm(campos[3])
                if len(campos) > 4:
                    comp_fim = _data_para_yyyymm(campos[4])

            elif reg == "C100":
                # |C100|IND_OPER|IND_EMIT|COD_PART|COD_MOD|COD_SIT|SER|NUM_DOC
                # |CHV_NFE|DT_DOC|DT_E_S|VL_DOC|...|VL_BC_ICMS|VL_ICMS
                # |VL_BC_ICMS_ST|VL_ICMS_ST|...|
                try:
                    ind_oper = campos[1] if len(campos) > 1 else ""
                    cod_part = campos[3] if len(campos) > 3 else ""
                    cod_sit = campos[5] if len(campos) > 5 else ""
                    num_doc = campos[7] if len(campos) > 7 else ""
                    chv_nfe = campos[8] if len(campos) > 8 else ""
                    dt_doc = campos[9] if len(campos) > 9 else ""
                    vl_doc = _to_float(campos[11]) if len(campos) > 11 else 0.0
                    vl_bc_icms = _to_float(campos[16]) if len(campos) > 16 else 0.0
                    vl_icms = _to_float(campos[17]) if len(campos) > 17 else 0.0
                    vl_bc_st = _to_float(campos[18]) if len(campos) > 18 else 0.0
                    vl_icms_st = _to_float(campos[19]) if len(campos) > 19 else 0.0

                    current_c100 = SpedC100(
                        ind_oper=ind_oper,
                        chave_nfe=chv_nfe,
                        num_doc=num_doc,
                        cnpj_emit=cnpj,
                        data_doc=dt_doc,
                        valor_total=vl_doc,
                        valor_bc_icms=vl_bc_icms,
                        valor_icms=vl_icms,
                        valor_icms_st=vl_icms_st,
                        valor_bc_st=vl_bc_st,
                        cod_part=cod_part,
                        cod_sit=cod_sit,
                    )
                    c100_list.append(current_c100)
                except (IndexError, ValueError) as e:
                    warnings.append(f"Linha {num} C100 erro: {e}")

            elif reg == "C170":
                # |C170|NUM_ITEM|COD_ITEM|DESCR_COMPL|QTD|UNID|VL_ITEM|VL_DESC
                # |IND_MOV|CST_ICMS|CFOP|COD_NAT|VL_BC_ICMS|ALIQ_ICMS|VL_ICMS
                # |VL_BC_ICMS_ST|ALIQ_ST|VL_ICMS_ST|IND_APUR|CST_IPI|COD_ENQ
                # |VL_BC_IPI|ALIQ_IPI|VL_IPI|
                try:
                    num_item = campos[1] if len(campos) > 1 else ""
                    cod_item = campos[2] if len(campos) > 2 else ""
                    descr = campos[3] if len(campos) > 3 else ""
                    qtd = _to_float(campos[4]) if len(campos) > 4 else 0.0
                    unid = campos[5] if len(campos) > 5 else ""
                    vl_item = _to_float(campos[6]) if len(campos) > 6 else 0.0
                    vl_desc = _to_float(campos[7]) if len(campos) > 7 else 0.0
                    cst_icms = campos[9] if len(campos) > 9 else ""
                    cfop = campos[10] if len(campos) > 10 else ""
                    cod_nat = campos[11] if len(campos) > 11 else ""
                    vl_bc_icms = _to_float(campos[12]) if len(campos) > 12 else 0.0
                    aliq_icms = _to_float(campos[13]) if len(campos) > 13 else 0.0
                    vl_icms = _to_float(campos[14]) if len(campos) > 14 else 0.0
                    vl_bc_st = _to_float(campos[15]) if len(campos) > 15 else 0.0
                    aliq_st = _to_float(campos[16]) if len(campos) > 16 else 0.0
                    vl_icms_st = _to_float(campos[17]) if len(campos) > 17 else 0.0

                    # NCM vem do C100 (não está no C170 do ICMS/IPI diretamente)
                    ncm = ""

                    c170 = SpedC170(
                        num_item=num_item,
                        cod_item=cod_item,
                        descr_compl=descr,
                        qtd=qtd,
                        unid=unid,
                        vl_item=vl_item,
                        vl_desc=vl_desc,
                        cst_icms=cst_icms,
                        cfop=cfop,
                        cod_nat=cod_nat,
                        ncm=ncm,
                        vl_bc_icms=vl_bc_icms,
                        aliq_icms=aliq_icms,
                        vl_icms=vl_icms,
                        vl_bc_icms_st=vl_bc_st,
                        aliq_st=aliq_st,
                        vl_icms_st=vl_icms_st,
                    )
                    c170_list.append(c170)
                except (IndexError, ValueError) as e:
                    warnings.append(f"Linha {num} C170 erro: {e}")

    return SpedResult(
        cnpj=cnpj,
        competencia_inicio=comp_ini,
        competencia_fim=comp_fim,
        tipo="icms_ipi",
        c100_list=c100_list,
        c170_list=c170_list,
        warnings=warnings,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Parser EFD Contribuições
# ──────────────────────────────────────────────────────────────────────────────

def parse_efd_contribuicoes(path: str | Path) -> SpedResult:
    """
    Lê um arquivo EFD Contribuições e retorna SpedResult com:
    - C100/C170 com CSTs de PIS/COFINS
    - Valores apurados M200/M600
    - Créditos M100/M500
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Arquivo SPED não encontrado: {path}")

    cnpj = ""
    comp_ini = ""
    comp_fim = ""
    c100_list: list[SpedC100] = []
    c170_list: list[SpedC170] = []
    pis_apurado = 0.0
    cofins_apurado = 0.0
    credito_pis = 0.0
    credito_cofins = 0.0
    warnings: list[str] = []
    current_c100: SpedC100 | None = None

    with open(path, encoding="latin-1", errors="replace") as fh:
        for num, linha in enumerate(fh, 1):
            linha = linha.rstrip("\n\r")
            campos = _parse_linha(linha)
            if not campos:
                continue
            reg = campos[0].upper()

            if reg == "0000":
                if len(campos) > 7:
                    cnpj = campos[7].strip()
                if len(campos) > 3:
                    comp_ini = _data_para_yyyymm(campos[3])
                if len(campos) > 4:
                    comp_fim = _data_para_yyyymm(campos[4])

            elif reg == "C100":
                try:
                    ind_oper = campos[1] if len(campos) > 1 else ""
                    cod_part = campos[3] if len(campos) > 3 else ""
                    cod_sit = campos[5] if len(campos) > 5 else ""
                    num_doc = campos[7] if len(campos) > 7 else ""
                    chv_nfe = campos[8] if len(campos) > 8 else ""
                    dt_doc = campos[9] if len(campos) > 9 else ""
                    vl_doc = _to_float(campos[11]) if len(campos) > 11 else 0.0

                    current_c100 = SpedC100(
                        ind_oper=ind_oper,
                        chave_nfe=chv_nfe,
                        num_doc=num_doc,
                        cnpj_emit=cnpj,
                        data_doc=dt_doc,
                        valor_total=vl_doc,
                        valor_bc_icms=0.0,
                        valor_icms=0.0,
                        valor_icms_st=0.0,
                        valor_bc_st=0.0,
                        cod_part=cod_part,
                        cod_sit=cod_sit,
                    )
                    c100_list.append(current_c100)
                except (IndexError, ValueError) as e:
                    warnings.append(f"Linha {num} C100 erro: {e}")

            elif reg == "C170":
                # EFD Contribuições C170 tem campos adicionais de PIS/COFINS
                # |C170|NUM_ITEM|COD_ITEM|DESCR_COMPL|QTD|UNID|VL_ITEM|VL_DESC
                # |IND_MOV|CST_ICMS|CFOP|COD_NAT|VL_BC_ICMS|ALIQ_ICMS|VL_ICMS
                # |VL_BC_ICMS_ST|ALIQ_ST|VL_ICMS_ST|IND_APUR|CST_IPI|COD_ENQ
                # |VL_BC_IPI|ALIQ_IPI|VL_IPI|NCM|EX_IPI|
                # |CST_PIS|VL_BC_PIS|ALIQ_PIS|VL_PIS|
                # |CST_COFINS|VL_BC_COFINS|ALIQ_COFINS|VL_COFINS|...|
                try:
                    vl_item = _to_float(campos[6]) if len(campos) > 6 else 0.0
                    cst_icms = campos[9] if len(campos) > 9 else ""
                    cfop = campos[10] if len(campos) > 10 else ""
                    cod_nat = campos[11] if len(campos) > 11 else ""
                    vl_bc_icms = _to_float(campos[12]) if len(campos) > 12 else 0.0
                    aliq_icms = _to_float(campos[13]) if len(campos) > 13 else 0.0
                    vl_icms = _to_float(campos[14]) if len(campos) > 14 else 0.0
                    vl_bc_st = _to_float(campos[15]) if len(campos) > 15 else 0.0
                    aliq_st = _to_float(campos[16]) if len(campos) > 16 else 0.0
                    vl_icms_st = _to_float(campos[17]) if len(campos) > 17 else 0.0
                    ncm = campos[24].strip() if len(campos) > 24 else ""

                    # PIS (campos 26-29) e COFINS (campos 30-33)
                    cst_pis = campos[26].zfill(2) if len(campos) > 26 else ""
                    vl_bc_pis = _to_float(campos[27]) if len(campos) > 27 else 0.0
                    aliq_pis_val = _to_float(campos[28]) if len(campos) > 28 else 0.0
                    vl_pis = _to_float(campos[29]) if len(campos) > 29 else 0.0

                    cst_cofins = campos[30].zfill(2) if len(campos) > 30 else ""
                    vl_bc_cofins = _to_float(campos[31]) if len(campos) > 31 else 0.0
                    aliq_cofins_val = _to_float(campos[32]) if len(campos) > 32 else 0.0
                    vl_cofins = _to_float(campos[33]) if len(campos) > 33 else 0.0

                    c170 = SpedC170(
                        num_item=campos[1] if len(campos) > 1 else "",
                        cod_item=campos[2] if len(campos) > 2 else "",
                        descr_compl=campos[3] if len(campos) > 3 else "",
                        qtd=_to_float(campos[4]) if len(campos) > 4 else 0.0,
                        unid=campos[5] if len(campos) > 5 else "",
                        vl_item=vl_item,
                        vl_desc=_to_float(campos[7]) if len(campos) > 7 else 0.0,
                        cst_icms=cst_icms,
                        cfop=cfop,
                        cod_nat=cod_nat,
                        ncm=ncm,
                        vl_bc_icms=vl_bc_icms,
                        aliq_icms=aliq_icms,
                        vl_icms=vl_icms,
                        vl_bc_icms_st=vl_bc_st,
                        aliq_st=aliq_st,
                        vl_icms_st=vl_icms_st,
                        cst_pis=cst_pis,
                        vl_bc_pis=vl_bc_pis,
                        aliq_pis=aliq_pis_val,
                        vl_pis=vl_pis,
                        cst_cofins=cst_cofins,
                        vl_bc_cofins=vl_bc_cofins,
                        aliq_cofins=aliq_cofins_val,
                        vl_cofins=vl_cofins,
                    )
                    c170_list.append(c170)
                except (IndexError, ValueError) as e:
                    warnings.append(f"Linha {num} C170 contrib erro: {e}")

            elif reg == "M200":
                # Apuração PIS — VL_TOT_CONT_NC_PER
                if len(campos) > 1:
                    pis_apurado += _to_float(campos[1])

            elif reg == "M600":
                # Apuração COFINS
                if len(campos) > 1:
                    cofins_apurado += _to_float(campos[1])

            elif reg == "M100":
                # Crédito PIS
                if len(campos) > 17:
                    credito_pis += _to_float(campos[17])

            elif reg == "M500":
                # Crédito COFINS
                if len(campos) > 17:
                    credito_cofins += _to_float(campos[17])

    return SpedResult(
        cnpj=cnpj,
        competencia_inicio=comp_ini,
        competencia_fim=comp_fim,
        tipo="contribuicoes",
        c100_list=c100_list,
        c170_list=c170_list,
        pis_apurado=pis_apurado,
        cofins_apurado=cofins_apurado,
        credito_pis=credito_pis,
        credito_cofins=credito_cofins,
        warnings=warnings,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Conversores para analysis_engine
# ──────────────────────────────────────────────────────────────────────────────

def sped_to_nfe_items(result: SpedResult) -> list[dict]:
    """
    Converte C170 do SPED para o formato nfe_items do analysis_engine.
    """
    items = []
    for c170 in result.c170_list:
        # Tenta descobrir tipo (entrada/saída) pelo CFOP
        cfop = str(c170.cfop)
        if cfop.startswith(("1", "2", "3")):
            tipo = "E"  # Entrada
        else:
            tipo = "S"  # Saída

        items.append({
            "ncm": c170.ncm,
            "cst_pis": c170.cst_pis,
            "cst_cofins": c170.cst_cofins,
            "valor_item": c170.vl_item,
            "cfop": c170.cfop,
            "tipo": tipo,
        })
    return items


def sped_to_c100_dicts(result: SpedResult) -> list[dict]:
    """Converte C100 para lista de dicts."""
    return [
        {
            "chave_nfe": c.chave_nfe,
            "valor_total": c.valor_total,
            "tipo_operacao": c.ind_oper,
            "cnpj_emit": c.cnpj_emit,
            "data_doc": c.data_doc,
        }
        for c in result.c100_list
    ]


def sped_to_c170_dicts(result: SpedResult) -> list[dict]:
    """Converte C170 para lista de dicts."""
    return [
        {
            "ncm": c.ncm,
            "valor_bc_st_entrada": c.vl_bc_icms_st,
            "valor_icms_st_entrada": c.vl_icms_st,
            "aliquota_icms": c.aliq_icms / 100 if c.aliq_icms > 1 else c.aliq_icms,
            "cfop": c.cfop,
        }
        for c in result.c170_list
    ]
