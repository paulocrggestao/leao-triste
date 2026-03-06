#!/usr/bin/env python3
"""
analysis_engine.py — Motor de Análise Tributária Real

Substitui a análise baseada em dados simulados por análise real
a partir de arquivos SPED e XMLs de NFe.

Análises implementadas:
A. PIS/COFINS Monofásico — verificação de CSTs incorretos
B. ICMS-ST Ressarcimento — base presumida vs preço real
C. Tema 69 STF — exclusão do ICMS da base de PIS/COFINS
D. Créditos PIS/COFINS não aproveitados (Lucro Real)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ncm_monofasico import (
    is_monofasico,
    get_monofasico_info,
    check_cst_correctness,
    CSTS_MONOFASICO_CORRETOS,
)


# ─────────────────────────────────────────────────────────────────────────────
# Data classes
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class RecoveryItem:
    tax_type: str           # pis, cofins, icms_st, icms, inss, irpj, csll
    description: str
    ncm_code: Optional[str]
    period: str
    base_calculo_original: float
    base_calculo_correta: float
    aliquota_original: float
    aliquota_correta: float
    valor_pago: float
    valor_devido: float
    valor_recuperar: float
    legal_basis: str
    confidence: str         # high, medium, low
    source_document: str = ""

    def to_dict(self) -> dict:
        return {
            "tax_type": self.tax_type,
            "description": self.description,
            "ncm_code": self.ncm_code,
            "period": self.period,
            "base_calculo_original": round(self.base_calculo_original, 2),
            "base_calculo_correta": round(self.base_calculo_correta, 2),
            "aliquota_original": round(self.aliquota_original, 4),
            "aliquota_correta": round(self.aliquota_correta, 4),
            "valor_pago": round(self.valor_pago, 2),
            "valor_devido": round(self.valor_devido, 2),
            "valor_recuperar": round(self.valor_recuperar, 2),
            "legal_basis": self.legal_basis,
            "confidence": self.confidence,
            "source_document": self.source_document,
        }


@dataclass
class AnalysisResult:
    total_recovery: float
    items: list[RecoveryItem] = field(default_factory=list)
    summary_by_tax: dict = field(default_factory=dict)
    summary_by_period: dict = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    data_quality_score: float = 0.0     # 0-1

    def to_dict(self) -> dict:
        return {
            "total_recovery": round(self.total_recovery, 2),
            "items": [i.to_dict() for i in self.items],
            "summary_by_tax": self.summary_by_tax,
            "summary_by_period": self.summary_by_period,
            "warnings": self.warnings,
            "data_quality_score": round(self.data_quality_score, 3),
        }


# ─────────────────────────────────────────────────────────────────────────────
# State ICMS rates (for ST calculations)
# ─────────────────────────────────────────────────────────────────────────────

STATE_ICMS_RATES = {
    "AC": 19.0, "AL": 19.0, "AM": 20.0, "AP": 18.0, "BA": 20.5,
    "CE": 20.0, "DF": 20.0, "ES": 17.0, "GO": 19.0, "MA": 22.0,
    "MG": 18.0, "MS": 17.0, "MT": 17.0, "PA": 19.0, "PB": 20.0,
    "PE": 20.5, "PI": 21.0, "PR": 19.5, "RJ": 22.0, "RN": 20.0,
    "RO": 19.5, "RR": 20.0, "RS": 17.0, "SC": 17.0, "SE": 19.0,
    "SP": 18.0, "TO": 20.0,
}

# CSTs with ICMS-ST (substitution)
ICMS_ST_CSTS = {"10", "30", "60", "70", "110", "130", "150", "160", "170", "500"}


def _parse_period(date_str: str) -> str:
    """Extract YYYY-MM from a date string (DDMMYYYY, YYYY-MM-DD, etc.)."""
    if not date_str:
        return ""
    s = str(date_str).strip()
    # DDMMYYYY
    if len(s) == 8 and s.isdigit():
        return f"{s[4:8]}-{s[2:4]}"
    # YYYYMMDD
    if len(s) == 8 and s.isdigit():
        return f"{s[:4]}-{s[4:6]}"
    # ISO: 2024-01-15 or 2024-01-15T...
    if len(s) >= 7 and s[4] == "-":
        return s[:7]
    # Brazilian: 01/01/2024
    if len(s) == 10 and s[2] == "/" and s[5] == "/":
        return f"{s[6:10]}-{s[3:5]}"
    return s[:7] if len(s) >= 7 else s


# ─────────────────────────────────────────────────────────────────────────────
# Main engine
# ─────────────────────────────────────────────────────────────────────────────

class TaxAnalysisEngine:
    """
    Motor de análise tributária real.

    Recebe dados já parseados (de SPEDParser ou NFeParser) e realiza
    as verificações de recuperação tributária baseadas na legislação vigente.
    """

    def __init__(self, client_info: dict):
        """
        Args:
            client_info: {
                id, tax_regime (simples|presumido|real),
                state_uf, activity_sector
            }
        """
        self.client_info = client_info
        self.tax_regime = client_info.get("tax_regime", "simples")
        self.state_uf = client_info.get("state_uf", "SP")
        self.icms_rate = STATE_ICMS_RATES.get(self.state_uf, 18.0)
        self._warnings: list[str] = []

    # ─────────────────────────────────────────────────────────────────────────
    # Analysis A: PIS/COFINS Monofásico
    # ─────────────────────────────────────────────────────────────────────────

    def _analyze_monofasico_item(
        self,
        ncm: str,
        cst_pis: str,
        cst_cofins: str,
        valor_pis: float,
        valor_cofins: float,
        base_pis: float,
        base_cofins: float,
        aliq_pis: float,
        aliq_cofins: float,
        period: str,
        descricao: str,
        source_doc: str = "",
    ) -> list[RecoveryItem]:
        """Check a single item for monofásico PIS/COFINS incorrectly applied."""
        items = []
        check = check_cst_correctness(ncm, cst_pis, cst_cofins)

        if not check["is_monofasico"]:
            return items

        info = check["info"]
        cat = info.get("categoria", "")
        base_legal = info.get("base_legal", "Lei 10.147/2000")

        # CST check: if CST is 01, 02, 03, 49-99 (not 04/05/06/07)
        # → PIS/COFINS was charged when it shouldn't have been

        if not check["pis_correto"] and valor_pis > 0.001:
            items.append(RecoveryItem(
                tax_type="pis",
                description=f"PIS monofásico indevido — {descricao} (NCM {ncm}, categoria: {cat})",
                ncm_code=ncm,
                period=period,
                base_calculo_original=round(base_pis, 2),
                base_calculo_correta=0.0,
                aliquota_original=round(aliq_pis, 4),
                aliquota_correta=0.0,
                valor_pago=round(valor_pis, 2),
                valor_devido=0.0,
                valor_recuperar=round(valor_pis, 2),
                legal_basis=f"{base_legal}; CST correto para revenda: 04/05/06",
                confidence="high",
                source_document=source_doc,
            ))

        if not check["cofins_correto"] and valor_cofins > 0.001:
            items.append(RecoveryItem(
                tax_type="cofins",
                description=f"COFINS monofásico indevido — {descricao} (NCM {ncm}, categoria: {cat})",
                ncm_code=ncm,
                period=period,
                base_calculo_original=round(base_cofins, 2),
                base_calculo_correta=0.0,
                aliquota_original=round(aliq_cofins, 4),
                aliquota_correta=0.0,
                valor_pago=round(valor_cofins, 2),
                valor_devido=0.0,
                valor_recuperar=round(valor_cofins, 2),
                legal_basis=f"{base_legal}; CST correto para revenda: 04/05/06",
                confidence="high",
                source_document=source_doc,
            ))

        return items

    # ─────────────────────────────────────────────────────────────────────────
    # Analysis B: ICMS-ST Ressarcimento
    # ─────────────────────────────────────────────────────────────────────────

    def _analyze_icms_st_item(
        self,
        ncm: str,
        cst_icms: str,
        base_icms_st: float,
        valor_icms_st: float,
        valor_total_item: float,
        period: str,
        descricao: str,
        ind_oper: str = "0",
        source_doc: str = "",
    ) -> list[RecoveryItem]:
        """
        Check for ICMS-ST ressarcimento opportunity.

        When effective sale price < presumed MVA base, the difference can be reclaimed.
        This check is only valid for entradas (IND_OPER=0).
        """
        items = []

        # Only analyze purchases (entrada = 0) with ICMS-ST
        if str(ind_oper).strip() != "0":
            return items
        if base_icms_st <= 0 or valor_icms_st <= 0:
            return items
        cst_norm = (cst_icms or "").strip().lstrip("0") or "0"
        # Only CSTs that indicate ICMS-ST: 10, 30, 60, 70
        # (full CST is 3 chars: origem + 2-digit, we check last 2)
        cst_2d = cst_norm[-2:] if len(cst_norm) >= 2 else cst_norm
        if cst_2d not in {"10", "30", "60", "70"}:
            return items

        # The presumed base (MVA) vs item value
        # If item value (our sale price) < base_st (presumed price), we overpaid
        if valor_total_item <= 0:
            return items

        # Calculate effective ICMS that should have been paid on actual price
        diferenca_base = base_icms_st - valor_total_item
        if diferenca_base <= 0:
            return items  # No overpayment

        valor_ressarcir = round(diferenca_base * self.icms_rate / 100, 2)
        if valor_ressarcir <= 0.01:
            return items

        items.append(RecoveryItem(
            tax_type="icms_st",
            description=f"ICMS-ST ressarcimento — {descricao} (NCM {ncm}, CST {cst_icms})",
            ncm_code=ncm,
            period=period,
            base_calculo_original=round(base_icms_st, 2),
            base_calculo_correta=round(valor_total_item, 2),
            aliquota_original=self.icms_rate,
            aliquota_correta=self.icms_rate,
            valor_pago=round(valor_icms_st, 2),
            valor_devido=round(max(0, (valor_total_item - valor_total_item) * self.icms_rate / 100), 2),
            valor_recuperar=round(min(valor_ressarcir, valor_icms_st), 2),
            legal_basis=(
                "CF/88, Art. 150, §7º; RE 593.849 STF (Tema 201); "
                f"RICMS/{self.state_uf} — ressarcimento por preço real menor que base presumida"
            ),
            confidence="medium",
            source_document=source_doc,
        ))

        return items

    # ─────────────────────────────────────────────────────────────────────────
    # Analysis C: Tema 69 STF — ICMS na base PIS/COFINS
    # ─────────────────────────────────────────────────────────────────────────

    def _analyze_tema69(
        self,
        period: str,
        total_pis_pago: float,
        total_cofins_pago: float,
        total_icms_saidas: float,
        base_pis_original: float,
        base_cofins_original: float,
    ) -> list[RecoveryItem]:
        """
        Tema 69 STF (RE 574.706): ICMS não compõe a base de cálculo do PIS/COFINS.
        Aplica-se a Lucro Real (PIS 1,65%/COFINS 7,6%) e Presumido (0,65%/3%).
        """
        items = []

        if self.tax_regime not in ("real", "presumido"):
            return items
        if total_icms_saidas <= 0:
            return items

        aliq_pis = 0.0165 if self.tax_regime == "real" else 0.0065
        aliq_cofins = 0.076 if self.tax_regime == "real" else 0.03

        # PIS
        base_pis_correta = base_pis_original - total_icms_saidas
        pis_devido = round(max(0, base_pis_correta * aliq_pis), 2)
        pis_recovery = round(total_pis_pago - pis_devido, 2)

        if pis_recovery > 1.0:
            items.append(RecoveryItem(
                tax_type="pis",
                description="PIS — Exclusão do ICMS da base de cálculo (Tema 69 STF)",
                ncm_code=None,
                period=period,
                base_calculo_original=round(base_pis_original, 2),
                base_calculo_correta=round(base_pis_correta, 2),
                aliquota_original=round(aliq_pis * 100, 4),
                aliquota_correta=round(aliq_pis * 100, 4),
                valor_pago=round(total_pis_pago, 2),
                valor_devido=pis_devido,
                valor_recuperar=pis_recovery,
                legal_basis=(
                    "Tema 69 STF (RE 574.706/PR); Tese: ICMS não compõe base do PIS/COFINS; "
                    "IN RFB 1.911/2019, Art. 27, I"
                ),
                confidence="high",
            ))

        # COFINS
        base_cofins_correta = base_cofins_original - total_icms_saidas
        cofins_devido = round(max(0, base_cofins_correta * aliq_cofins), 2)
        cofins_recovery = round(total_cofins_pago - cofins_devido, 2)

        if cofins_recovery > 1.0:
            items.append(RecoveryItem(
                tax_type="cofins",
                description="COFINS — Exclusão do ICMS da base de cálculo (Tema 69 STF)",
                ncm_code=None,
                period=period,
                base_calculo_original=round(base_cofins_original, 2),
                base_calculo_correta=round(base_cofins_correta, 2),
                aliquota_original=round(aliq_cofins * 100, 4),
                aliquota_correta=round(aliq_cofins * 100, 4),
                valor_pago=round(total_cofins_pago, 2),
                valor_devido=cofins_devido,
                valor_recuperar=cofins_recovery,
                legal_basis=(
                    "Tema 69 STF (RE 574.706/PR); Tese: ICMS não compõe base do PIS/COFINS; "
                    "IN RFB 1.911/2019, Art. 27, I"
                ),
                confidence="high",
            ))

        return items

    # ─────────────────────────────────────────────────────────────────────────
    # Analysis D: Créditos PIS/COFINS não aproveitados (Lucro Real)
    # ─────────────────────────────────────────────────────────────────────────

    def _analyze_creditos_pis_cofins(
        self,
        period: str,
        parsed_items: list[dict],
    ) -> list[RecoveryItem]:
        """
        Identify PIS/COFINS credit opportunities for Lucro Real clients.

        Checks for:
        - Energy (CFOP 1253/2253 or 3253)
        - Rent
        - Freight on purchases (CFOP 1353, 2353)
        """
        items = []
        if self.tax_regime != "real":
            return items

        aliq_pis = 0.0165
        aliq_cofins = 0.076

        # Group by CFOP to identify energy, freight, etc.
        cfop_totals: dict[str, float] = {}
        for item in parsed_items:
            cfop = str(item.get("cfop", "") or "").strip()
            val = float(item.get("valor_total", 0) or 0)
            if cfop:
                cfop_totals[cfop] = cfop_totals.get(cfop, 0) + val

        # Energy (CFOP 1253/2253 = aquisição de energia elétrica)
        energia_total = cfop_totals.get("1253", 0) + cfop_totals.get("2253", 0)
        if energia_total > 100:
            pis_cred = round(energia_total * aliq_pis, 2)
            cofins_cred = round(energia_total * aliq_cofins, 2)
            if pis_cred > 0.01:
                items.append(RecoveryItem(
                    tax_type="pis",
                    description="PIS — Crédito sobre energia elétrica (CFOP 1253/2253)",
                    ncm_code=None,
                    period=period,
                    base_calculo_original=0.0,
                    base_calculo_correta=round(energia_total, 2),
                    aliquota_original=0.0,
                    aliquota_correta=1.65,
                    valor_pago=0.0,
                    valor_devido=0.0,
                    valor_recuperar=pis_cred,
                    legal_basis="Lei 10.637/2002, Art. 3º, III; Parecer Normativo COSIT 5/2018",
                    confidence="medium",
                ))
            if cofins_cred > 0.01:
                items.append(RecoveryItem(
                    tax_type="cofins",
                    description="COFINS — Crédito sobre energia elétrica (CFOP 1253/2253)",
                    ncm_code=None,
                    period=period,
                    base_calculo_original=0.0,
                    base_calculo_correta=round(energia_total, 2),
                    aliquota_original=0.0,
                    aliquota_correta=7.6,
                    valor_pago=0.0,
                    valor_devido=0.0,
                    valor_recuperar=cofins_cred,
                    legal_basis="Lei 10.833/2003, Art. 3º, III; Parecer Normativo COSIT 5/2018",
                    confidence="medium",
                ))

        # Freight on purchases (CFOP 1353/2353)
        frete_total = cfop_totals.get("1353", 0) + cfop_totals.get("2353", 0)
        if frete_total > 100:
            pis_cred = round(frete_total * aliq_pis, 2)
            cofins_cred = round(frete_total * aliq_cofins, 2)
            if pis_cred > 0.01:
                items.append(RecoveryItem(
                    tax_type="pis",
                    description="PIS — Crédito sobre frete na aquisição de mercadorias (CFOP 1353/2353)",
                    ncm_code=None,
                    period=period,
                    base_calculo_original=0.0,
                    base_calculo_correta=round(frete_total, 2),
                    aliquota_original=0.0,
                    aliquota_correta=1.65,
                    valor_pago=0.0,
                    valor_devido=0.0,
                    valor_recuperar=pis_cred,
                    legal_basis="Lei 10.637/2002, Art. 3º, IX; IN RFB 2.121/2022",
                    confidence="medium",
                ))
            if cofins_cred > 0.01:
                items.append(RecoveryItem(
                    tax_type="cofins",
                    description="COFINS — Crédito sobre frete na aquisição de mercadorias (CFOP 1353/2353)",
                    ncm_code=None,
                    period=period,
                    base_calculo_original=0.0,
                    base_calculo_correta=round(frete_total, 2),
                    aliquota_original=0.0,
                    aliquota_correta=7.6,
                    valor_pago=0.0,
                    valor_devido=0.0,
                    valor_recuperar=cofins_cred,
                    legal_basis="Lei 10.833/2003, Art. 3º, IX; IN RFB 2.121/2022",
                    confidence="medium",
                ))

        return items

    # ─────────────────────────────────────────────────────────────────────────
    # Public analysis methods
    # ─────────────────────────────────────────────────────────────────────────

    def analyze_sped_efd(self, parsed_sped: dict) -> list[RecoveryItem]:
        """
        Analyze EFD ICMS/IPI SPED data.

        Args:
            parsed_sped: dict returned by SPEDParser.parse()

        Returns:
            list of RecoveryItem
        """
        items = []
        if not parsed_sped:
            return items

        # Build items table for NCM lookup
        items_table = {}
        for rec in parsed_sped.get("0200", []):
            cod = rec.get("COD_ITEM", "")
            if cod:
                items_table[cod] = rec

        # Get opening for period
        opening = (parsed_sped.get("0000") or [{}])[0]
        period = _parse_period(opening.get("DT_INI", ""))

        # Parse C170 items with parent C100 for IND_OPER
        c100_docs = parsed_sped.get("C100", [])
        c170_items = parsed_sped.get("C170", [])

        # Build doc map: we need to associate C170 with parent C100
        # SPED sequential: C100 followed by its C170s
        # We reconstruct this from raw (handled by get_document_items_with_parent)
        # Here we work with what we have — assume all C170 with ind_oper from first pass

        # Accumulate for Tema 69
        total_pis_pago = sum(float(d.get("VL_PIS", 0) or 0) for d in c100_docs)
        total_cofins_pago = sum(float(d.get("VL_COFINS", 0) or 0) for d in c100_docs)
        total_icms_saidas = 0.0
        base_pis_total = 0.0
        base_cofins_total = 0.0

        for doc in c100_docs:
            if str(doc.get("IND_OPER", "1")).strip() == "1":  # saída
                total_icms_saidas += float(doc.get("VL_ICMS", 0) or 0)

        for doc in c100_docs:
            base_pis_total += float(doc.get("VL_DOC", 0) or 0)
            base_cofins_total += float(doc.get("VL_DOC", 0) or 0)

        # Analyze C170 items for monofásico and ICMS-ST
        for item_rec in c170_items:
            cod_item = item_rec.get("COD_ITEM", "")
            ncm = ""

            # Try to get NCM from items table first
            if cod_item and cod_item in items_table:
                ncm = items_table[cod_item].get("COD_NCM", "") or ""

            if not ncm:
                continue

            cst_pis = str(item_rec.get("CST_PIS", "") or "")
            cst_cofins = str(item_rec.get("CST_COFINS", "") or "")
            valor_pis = float(item_rec.get("VL_PIS", 0) or 0)
            valor_cofins = float(item_rec.get("VL_COFINS", 0) or 0)
            base_pis = float(item_rec.get("VL_BC_PIS", 0) or 0)
            base_cofins = float(item_rec.get("VL_BC_COFINS", 0) or 0)
            aliq_pis = float(item_rec.get("ALIQ_PIS", 0) or 0)
            aliq_cofins = float(item_rec.get("ALIQ_COFINS", 0) or 0)
            descricao = items_table.get(cod_item, {}).get("DESCR_ITEM", cod_item)

            # Analysis A: PIS/COFINS Monofásico
            mono_items = self._analyze_monofasico_item(
                ncm=ncm,
                cst_pis=cst_pis,
                cst_cofins=cst_cofins,
                valor_pis=valor_pis,
                valor_cofins=valor_cofins,
                base_pis=base_pis,
                base_cofins=base_cofins,
                aliq_pis=aliq_pis,
                aliq_cofins=aliq_cofins,
                period=period,
                descricao=descricao,
                source_doc=item_rec.get("_doc_num", ""),
            )
            items.extend(mono_items)

            # Analysis B: ICMS-ST Ressarcimento
            cst_icms = str(item_rec.get("CST_ICMS", "") or "")
            base_icms_st = float(item_rec.get("VL_BC_ICMS_ST", 0) or 0)
            valor_icms_st = float(item_rec.get("VL_ICMS_ST", 0) or 0)
            valor_total_item = float(item_rec.get("VL_ITEM", 0) or 0)
            ind_oper = str(item_rec.get("_ind_oper", "1")).strip()

            st_items = self._analyze_icms_st_item(
                ncm=ncm,
                cst_icms=cst_icms,
                base_icms_st=base_icms_st,
                valor_icms_st=valor_icms_st,
                valor_total_item=valor_total_item,
                period=period,
                descricao=descricao,
                ind_oper=ind_oper,
                source_doc=item_rec.get("_doc_num", ""),
            )
            items.extend(st_items)

        # Analysis C: Tema 69 (period-level)
        if total_pis_pago > 0 or total_cofins_pago > 0:
            tema69_items = self._analyze_tema69(
                period=period,
                total_pis_pago=total_pis_pago,
                total_cofins_pago=total_cofins_pago,
                total_icms_saidas=total_icms_saidas,
                base_pis_original=base_pis_total,
                base_cofins_original=base_cofins_total,
            )
            items.extend(tema69_items)

        # Analysis D: PIS/COFINS credits (Lucro Real)
        if self.tax_regime == "real":
            all_items_list = [
                {
                    "cfop": str(r.get("CFOP", "") or ""),
                    "valor_total": float(r.get("VL_ITEM", 0) or 0),
                }
                for r in c170_items
            ]
            credit_items = self._analyze_creditos_pis_cofins(period, all_items_list)
            items.extend(credit_items)

        if not items:
            self._warnings.append(
                "EFD ICMS/IPI: nenhuma oportunidade encontrada — verifique se o arquivo contém "
                "registros C170 com NCMs e CSTs preenchidos"
            )

        return items

    def analyze_sped_contrib(self, parsed_sped: dict) -> list[RecoveryItem]:
        """
        Analyze EFD Contribuições SPED data.

        Args:
            parsed_sped: dict returned by SPEDParser.parse()

        Returns:
            list of RecoveryItem
        """
        items = []
        if not parsed_sped:
            return items

        # Build items table
        items_table = {}
        for rec in parsed_sped.get("0200", []):
            cod = rec.get("COD_ITEM", "")
            if cod:
                items_table[cod] = rec

        opening = (parsed_sped.get("0000") or [{}])[0]
        period = _parse_period(opening.get("DT_INI", ""))

        # M200/M600: PIS/COFINS apportionment
        m200_list = parsed_sped.get("M200", [])
        m600_list = parsed_sped.get("M600", [])
        m200 = m200_list[0] if m200_list else {}
        m600 = m600_list[0] if m600_list else {}

        # Get totals from apportionment
        total_pis_pago = float(m200.get("VL_TOT_CONT_REC", 0) or 0)
        total_cofins_pago = float(m600.get("VL_TOT_CONT_REC", 0) or 0)

        # C170 items (EFD Contrib also has C170)
        c170_items = parsed_sped.get("C170", [])

        # Accumulate for Tema 69
        total_icms_saidas = 0.0
        base_pis_total = 0.0
        base_cofins_total = 0.0

        for item_rec in c170_items:
            val = float(item_rec.get("VL_ITEM", 0) or 0)
            base_pis_total += float(item_rec.get("VL_BC_PIS", 0) or 0) or val
            base_cofins_total += float(item_rec.get("VL_BC_COFINS", 0) or 0) or val

        # Analyze C170 for monofásico
        for item_rec in c170_items:
            cod_item = item_rec.get("COD_ITEM", "")
            ncm = ""
            if cod_item and cod_item in items_table:
                ncm = items_table[cod_item].get("COD_NCM", "") or ""
            if not ncm:
                continue

            cst_pis = str(item_rec.get("CST_PIS", "") or "")
            cst_cofins = str(item_rec.get("CST_COFINS", "") or "")
            valor_pis = float(item_rec.get("VL_PIS", 0) or 0)
            valor_cofins = float(item_rec.get("VL_COFINS", 0) or 0)
            base_pis = float(item_rec.get("VL_BC_PIS", 0) or 0)
            base_cofins = float(item_rec.get("VL_BC_COFINS", 0) or 0)
            aliq_pis = float(item_rec.get("ALIQ_PIS", 0) or 0)
            aliq_cofins = float(item_rec.get("ALIQ_COFINS", 0) or 0)
            descricao = items_table.get(cod_item, {}).get("DESCR_ITEM", cod_item)

            mono_items = self._analyze_monofasico_item(
                ncm=ncm,
                cst_pis=cst_pis,
                cst_cofins=cst_cofins,
                valor_pis=valor_pis,
                valor_cofins=valor_cofins,
                base_pis=base_pis,
                base_cofins=base_cofins,
                aliq_pis=aliq_pis,
                aliq_cofins=aliq_cofins,
                period=period,
                descricao=descricao,
                source_doc=item_rec.get("_doc_num", ""),
            )
            items.extend(mono_items)

        # Tema 69 from apportionment data
        if total_pis_pago > 0 and total_icms_saidas == 0:
            # If we don't have ICMS breakout, skip Tema 69 for contrib SPED
            # (need EFD ICMS data for ICMS destacado)
            self._warnings.append(
                "EFD Contribuições: Tema 69 requer dados do EFD ICMS/IPI para calcular ICMS destacado. "
                "Faça upload do arquivo EFD ICMS/IPI também."
            )
        elif total_pis_pago > 0:
            tema69_items = self._analyze_tema69(
                period=period,
                total_pis_pago=total_pis_pago,
                total_cofins_pago=total_cofins_pago,
                total_icms_saidas=total_icms_saidas,
                base_pis_original=base_pis_total,
                base_cofins_original=base_cofins_total,
            )
            items.extend(tema69_items)

        # Credits for Lucro Real
        if self.tax_regime == "real":
            all_items_list = [
                {
                    "cfop": str(r.get("CFOP", "") or ""),
                    "valor_total": float(r.get("VL_ITEM", 0) or 0),
                }
                for r in c170_items
            ]
            credit_items = self._analyze_creditos_pis_cofins(period, all_items_list)
            items.extend(credit_items)

        return items

    def analyze_nfe_xmls(self, parsed_nfes: list[dict]) -> list[RecoveryItem]:
        """
        Analyze NFe XML data.

        Args:
            parsed_nfes: list of dicts returned by NFeParser.parse_xml() or extract_items()

        Returns:
            list of RecoveryItem
        """
        items = []
        if not parsed_nfes:
            return items

        # Group items by period for Tema 69
        period_data: dict[str, dict] = {}

        for nfe_or_item in parsed_nfes:
            # Support both full NFe dict and pre-extracted item list
            if "items" in nfe_or_item:
                nfe_items = nfe_or_item["items"]
                doc_date = nfe_or_item.get("data_emissao", "")
                doc_num = nfe_or_item.get("numero", "")
                tipo_op = nfe_or_item.get("tipo_operacao", "1")
            else:
                # Single item dict (from extract_items)
                nfe_items = [nfe_or_item]
                doc_date = nfe_or_item.get("documento_data", "")
                doc_num = nfe_or_item.get("documento_numero", "")
                tipo_op = nfe_or_item.get("tipo_operacao", "1")

            period = _parse_period(doc_date)
            if period not in period_data:
                period_data[period] = {
                    "pis_pago": 0.0,
                    "cofins_pago": 0.0,
                    "icms_saidas": 0.0,
                    "base_pis": 0.0,
                    "base_cofins": 0.0,
                    "all_items": [],
                }

            for item in nfe_items:
                ncm = str(item.get("ncm", "") or "").strip()
                cst_pis = str(item.get("cst_pis", "") or "")
                cst_cofins = str(item.get("cst_cofins", "") or "")
                valor_pis = float(item.get("valor_pis", 0) or 0)
                valor_cofins = float(item.get("valor_cofins", 0) or 0)
                base_pis = float(item.get("base_pis", 0) or 0)
                base_cofins = float(item.get("base_cofins", 0) or 0)
                aliq_pis = float(item.get("aliq_pis", 0) or 0)
                aliq_cofins = float(item.get("aliq_cofins", 0) or 0)
                descricao = str(item.get("descricao", "") or ncm)
                valor_total = float(item.get("valor_total", 0) or 0)
                valor_icms = float(item.get("valor_icms", 0) or 0)
                cst_icms = str(item.get("cst_icms", "") or "")
                base_icms_st = float(item.get("base_icms_st", 0) or 0)
                valor_icms_st = float(item.get("valor_icms_st", 0) or 0)

                # Accumulate for Tema 69
                period_data[period]["pis_pago"] += valor_pis
                period_data[period]["cofins_pago"] += valor_cofins
                period_data[period]["base_pis"] += base_pis or valor_total
                period_data[period]["base_cofins"] += base_cofins or valor_total
                if str(tipo_op).strip() == "1":
                    period_data[period]["icms_saidas"] += valor_icms
                period_data[period]["all_items"].append({
                    "cfop": str(item.get("cfop", "") or ""),
                    "valor_total": valor_total,
                })

                if not ncm:
                    continue

                # Analysis A: Monofásico
                mono_items = self._analyze_monofasico_item(
                    ncm=ncm,
                    cst_pis=cst_pis,
                    cst_cofins=cst_cofins,
                    valor_pis=valor_pis,
                    valor_cofins=valor_cofins,
                    base_pis=base_pis,
                    base_cofins=base_cofins,
                    aliq_pis=aliq_pis,
                    aliq_cofins=aliq_cofins,
                    period=period,
                    descricao=descricao,
                    source_doc=f"NFe {doc_num}",
                )
                items.extend(mono_items)

                # Analysis B: ICMS-ST Ressarcimento
                ind_oper = "0" if str(tipo_op).strip() == "0" else "1"
                # NFe tipo 0 = entrada (compra), tipo 1 = saída (venda)
                # For NFe, tipo_operacao 0=entrada → compra → IND_OPER=0
                if str(tipo_op).strip() == "0" and base_icms_st > 0:
                    st_items = self._analyze_icms_st_item(
                        ncm=ncm,
                        cst_icms=cst_icms,
                        base_icms_st=base_icms_st,
                        valor_icms_st=valor_icms_st,
                        valor_total_item=valor_total,
                        period=period,
                        descricao=descricao,
                        ind_oper="0",
                        source_doc=f"NFe {doc_num}",
                    )
                    items.extend(st_items)

        # Analysis C: Tema 69 (per period)
        for period, pdata in period_data.items():
            if pdata["pis_pago"] > 0 or pdata["cofins_pago"] > 0:
                tema69_items = self._analyze_tema69(
                    period=period,
                    total_pis_pago=pdata["pis_pago"],
                    total_cofins_pago=pdata["cofins_pago"],
                    total_icms_saidas=pdata["icms_saidas"],
                    base_pis_original=pdata["base_pis"],
                    base_cofins_original=pdata["base_cofins"],
                )
                items.extend(tema69_items)

            # Analysis D: PIS/COFINS credits (Lucro Real)
            if self.tax_regime == "real":
                credit_items = self._analyze_creditos_pis_cofins(period, pdata["all_items"])
                items.extend(credit_items)

        if not items:
            self._warnings.append(
                "XMLs NFe: nenhuma oportunidade encontrada — verifique se os XMLs contêm "
                "produtos com NCM preenchido e CSTs de PIS/COFINS"
            )

        return items

    def run_full_analysis(
        self,
        sped_efd: Optional[dict] = None,
        sped_contrib: Optional[dict] = None,
        nfe_data: Optional[list] = None,
    ) -> AnalysisResult:
        """
        Run all applicable analyses and return consolidated result.

        Args:
            sped_efd: Parsed EFD ICMS/IPI data (from SPEDParser)
            sped_contrib: Parsed EFD Contribuições data (from SPEDParser)
            nfe_data: List of parsed NFe dicts (from NFeParser)

        Returns:
            AnalysisResult with all findings
        """
        all_items: list[RecoveryItem] = []

        if sped_efd:
            efd_items = self.analyze_sped_efd(sped_efd)
            all_items.extend(efd_items)

        if sped_contrib:
            contrib_items = self.analyze_sped_contrib(sped_contrib)
            # Deduplicate: if same period+tax+ncm found in both, keep the highest
            existing_keys = {(i.tax_type, i.ncm_code, i.period) for i in all_items}
            for ci in contrib_items:
                key = (ci.tax_type, ci.ncm_code, ci.period)
                if key not in existing_keys:
                    all_items.append(ci)

        if nfe_data:
            nfe_items = self.analyze_nfe_xmls(nfe_data)
            existing_keys = {(i.tax_type, i.ncm_code, i.period, i.source_document) for i in all_items}
            for ni in nfe_items:
                key = (ni.tax_type, ni.ncm_code, ni.period, ni.source_document)
                if key not in existing_keys:
                    all_items.append(ni)

        # Build summaries
        total_recovery = sum(i.valor_recuperar for i in all_items)

        summary_by_tax: dict = {}
        for item in all_items:
            tt = item.tax_type
            if tt not in summary_by_tax:
                summary_by_tax[tt] = {"total": 0.0, "count": 0}
            summary_by_tax[tt]["total"] += item.valor_recuperar
            summary_by_tax[tt]["count"] += 1

        for tt in summary_by_tax:
            summary_by_tax[tt]["total"] = round(summary_by_tax[tt]["total"], 2)

        summary_by_period: dict = {}
        for item in all_items:
            p = item.period or "unknown"
            if p not in summary_by_period:
                summary_by_period[p] = {"total": 0.0, "count": 0}
            summary_by_period[p]["total"] += item.valor_recuperar
            summary_by_period[p]["count"] += 1

        for p in summary_by_period:
            summary_by_period[p]["total"] = round(summary_by_period[p]["total"], 2)

        # Data quality score
        quality = 0.0
        sources = 0
        if sped_efd:
            sources += 1
        if sped_contrib:
            sources += 1
        if nfe_data:
            sources += 1
        quality = min(1.0, 0.4 + sources * 0.2 + (0.2 if len(all_items) > 0 else 0))

        return AnalysisResult(
            total_recovery=round(total_recovery, 2),
            items=sorted(all_items, key=lambda x: -x.valor_recuperar),
            summary_by_tax=summary_by_tax,
            summary_by_period=dict(sorted(summary_by_period.items())),
            warnings=self._warnings,
            data_quality_score=quality,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Demo / testing
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    engine = TaxAnalysisEngine(
        client_info={
            "id": 1,
            "tax_regime": "simples",
            "state_uf": "SP",
            "activity_sector": "supermercado",
        }
    )

    # Test with minimal NFe-like data
    fake_nfe = {
        "numero": "12345",
        "serie": "1",
        "data_emissao": "2025-01-15",
        "tipo_operacao": "1",
        "emitente_cnpj": "12345678000100",
        "emitente_nome": "Fornecedor Teste",
        "total_nota": 1500.0,
        "items": [
            {
                "ncm": "33030010",  # Perfume — monofásico
                "cfop": "5102",
                "descricao": "Perfume 50ml",
                "quantidade": 10,
                "valor_unitario": 50.0,
                "valor_total": 500.0,
                "cst_icms": "000",
                "base_icms": 500.0,
                "aliq_icms": 18.0,
                "valor_icms": 90.0,
                "base_icms_st": 0.0,
                "aliq_icms_st": 0.0,
                "valor_icms_st": 0.0,
                "cst_pis": "01",   # WRONG — should be 04/05/06 for monofásico
                "base_pis": 500.0,
                "aliq_pis": 0.65,
                "valor_pis": 3.25,
                "cst_cofins": "01",  # WRONG
                "base_cofins": 500.0,
                "aliq_cofins": 3.0,
                "valor_cofins": 15.0,
            },
            {
                "ncm": "10063021",  # Arroz — NOT monofásico
                "cfop": "5102",
                "descricao": "Arroz tipo 1",
                "quantidade": 50,
                "valor_unitario": 20.0,
                "valor_total": 1000.0,
                "cst_icms": "000",
                "base_icms": 0.0,
                "aliq_icms": 0.0,
                "valor_icms": 0.0,
                "base_icms_st": 0.0,
                "aliq_icms_st": 0.0,
                "valor_icms_st": 0.0,
                "cst_pis": "07",
                "base_pis": 0.0,
                "aliq_pis": 0.0,
                "valor_pis": 0.0,
                "cst_cofins": "07",
                "base_cofins": 0.0,
                "aliq_cofins": 0.0,
                "valor_cofins": 0.0,
            },
        ],
    }

    result = engine.run_full_analysis(nfe_data=[fake_nfe])
    print("=== Teste Analysis Engine ===")
    print(f"Total recovery: R$ {result.total_recovery:.2f}")
    print(f"Items found: {len(result.items)}")
    for item in result.items:
        print(f"  [{item.confidence.upper()}] {item.tax_type.upper()} — R$ {item.valor_recuperar:.2f}")
        print(f"    {item.description}")
    print(f"\nData quality: {result.data_quality_score:.2%}")
    print(f"Warnings: {result.warnings}")
