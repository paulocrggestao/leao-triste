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


# ──────────────────────────────────────────────────────────────────────────────
# Data classes
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class RecoveryItem:
    tax_type: str           # pis, cofins, icms_st, icms, inss, irpj, csll
    description: str
    ncm_code: Optional[str]
    period: str
    base_calculo_original: float
    base_calculo_correto: float
    aliquota: float
    valor_pago_indevido: float
    valor_recuperavel: float
    juros_selic: float
    valor_total: float
    fundamento_legal: str
    risco: str              # baixo, medio, alto
    documentos_necessarios: list[str] = field(default_factory=list)
    observacoes: str = ""


@dataclass
class AnalysisResult:
    company_name: str
    cnpj: str
    period_start: str
    period_end: str
    recovery_items: list[RecoveryItem] = field(default_factory=list)
    total_recuperavel: float = 0.0
    total_com_juros: float = 0.0
    data_source: str = "real"  # "real" or "simulated"
    warnings: list[str] = field(default_factory=list)


# ──────────────────────────────────────────────────────────────────────────────
# Helper: SELIC acumulada simples (fallback offline)
# ──────────────────────────────────────────────────────────────────────────────

def _selic_fator(meses: int) -> float:
    """Fator SELIC acumulado estimado (1% a.m. como fallback conservador)."""
    return 1.0 + 0.01 * meses


def _meses_entre(data_ini: str, data_fim: str) -> int:
    """Conta meses entre duas datas YYYY-MM ou YYYYMM."""
    def parse(d: str):
        d = d.replace("-", "")
        return int(d[:4]), int(d[4:6])
    y1, m1 = parse(data_ini)
    y2, m2 = parse(data_fim)
    return max(0, (y2 - y1) * 12 + (m2 - m1))


# ──────────────────────────────────────────────────────────────────────────────
# Análise A — PIS/COFINS Monofásico
# ──────────────────────────────────────────────────────────────────────────────

def _analisa_monofasico(
    nfe_items: list[dict],
    period: str,
    hoje: str = "202501",
) -> list[RecoveryItem]:
    """
    Varre itens de NFe de entrada e saída procurando:
    - CST diferente de 04, 06, 07 em produtos monofásicos
    - Débitos de PIS/COFINS gerados indevidamente
    - Créditos bloqueados por CST errado

    nfe_items: lista de dicts com campos:
        ncm, cst_pis, cst_cofins, valor_item, cfop, tipo (E=entrada, S=saída)
    """
    items: list[RecoveryItem] = []
    meses = _meses_entre(period, hoje)

    debitos_indevidos: dict[str, float] = {}   # ncm -> valor acumulado
    creditos_perdidos: dict[str, float] = {}

    for item in nfe_items:
        ncm = str(item.get("ncm", "")).strip().replace(".", "")
        if not is_monofasico(ncm):
            continue

        info = get_monofasico_info(ncm)
        if info is None:
            continue

        cst_pis = str(item.get("cst_pis", "")).zfill(2)
        cst_cofins = str(item.get("cst_cofins", "")).zfill(2)
        valor = float(item.get("valor_item", 0))
        cfop = str(item.get("cfop", ""))
        tipo = str(item.get("tipo", "S")).upper()  # E=entrada, S=saída

        ok_pis, correto_pis = check_cst_correctness(ncm, cst_pis)
        ok_cofins, correto_cofins = check_cst_correctness(ncm, cst_cofins)

        if tipo == "S" and (not ok_pis or not ok_cofins):
            # Débito indevido: tributou saída que deveria ser monofásica
            aliq_pis = info.get("aliq_pis", 0.0165)
            aliq_cofins = info.get("aliq_cofins", 0.076)

            val_pis = valor * aliq_pis
            val_cofins = valor * aliq_cofins
            fator = _selic_fator(meses)

            if not ok_pis and val_pis > 0:
                debitos_indevidos[ncm] = debitos_indevidos.get(ncm, 0) + val_pis
                items.append(RecoveryItem(
                    tax_type="pis",
                    description=f"PIS indevido — NCM {ncm} ({info.get('descricao','')}) monofásico, CST usado: {cst_pis}",
                    ncm_code=ncm,
                    period=period,
                    base_calculo_original=valor,
                    base_calculo_correto=0.0,
                    aliquota=aliq_pis,
                    valor_pago_indevido=val_pis,
                    valor_recuperavel=val_pis,
                    juros_selic=val_pis * (fator - 1),
                    valor_total=val_pis * fator,
                    fundamento_legal=(
                        "Lei 10.637/2002 art.2 §1; Lei 10.485/2002; "
                        f"Solução de Consulta COSIT {info.get('solucao_consulta','')}"
                    ),
                    risco="baixo",
                    documentos_necessarios=["SPED EFD Contribuições", "XMLs NFe saída"],
                    observacoes=f"CST correto seria {correto_pis}",
                ))

            if not ok_cofins and val_cofins > 0:
                items.append(RecoveryItem(
                    tax_type="cofins",
                    description=f"COFINS indevido — NCM {ncm} ({info.get('descricao','')}) monofásico, CST usado: {cst_cofins}",
                    ncm_code=ncm,
                    period=period,
                    base_calculo_original=valor,
                    base_calculo_correto=0.0,
                    aliquota=aliq_cofins,
                    valor_pago_indevido=val_cofins,
                    valor_recuperavel=val_cofins,
                    juros_selic=val_cofins * (fator - 1),
                    valor_total=val_cofins * fator,
                    fundamento_legal=(
                        "Lei 10.833/2003 art.2 §1; Lei 10.485/2002; "
                        f"Solução de Consulta COSIT {info.get('solucao_consulta','')}"
                    ),
                    risco="baixo",
                    documentos_necessarios=["SPED EFD Contribuições", "XMLs NFe saída"],
                    observacoes=f"CST correto seria {correto_cofins}",
                ))

        elif tipo == "E" and (not ok_pis or not ok_cofins):
            # Crédito perdido na entrada
            aliq_pis = info.get("aliq_pis", 0.0165)
            aliq_cofins = info.get("aliq_cofins", 0.076)
            val_pis = valor * aliq_pis
            val_cofins = valor * aliq_cofins
            fator = _selic_fator(meses)

            if not ok_pis and val_pis > 0:
                items.append(RecoveryItem(
                    tax_type="pis",
                    description=f"Crédito PIS perdido — NCM {ncm} monofásico, CST entrada: {cst_pis}",
                    ncm_code=ncm,
                    period=period,
                    base_calculo_original=valor,
                    base_calculo_correto=valor,
                    aliquota=aliq_pis,
                    valor_pago_indevido=0.0,
                    valor_recuperavel=val_pis,
                    juros_selic=val_pis * (fator - 1),
                    valor_total=val_pis * fator,
                    fundamento_legal="Lei 10.637/2002 art.3; IN RFB 2.121/2022",
                    risco="medio",
                    documentos_necessarios=["SPED EFD Contribuições", "XMLs NFe entrada"],
                    observacoes=f"CST entrada deveria ser {correto_pis}",
                ))

    return items


# ──────────────────────────────────────────────────────────────────────────────
# Análise B — ICMS-ST Ressarcimento
# ──────────────────────────────────────────────────────────────────────────────

def _analisa_icms_st(
    sped_c170: list[dict],
    sped_c100: list[dict],
    period: str,
    hoje: str = "202501",
) -> list[RecoveryItem]:
    """
    Compara base de cálculo presumida do ICMS-ST (retido na entrada)
    com o preço de venda real registrado nas saídas.

    Se preço real < base presumida → direito ao ressarcimento do excesso.

    sped_c170: registros C170 do SPED com campos:
        chave_nfe, ncm, valor_bc_st_entrada, valor_icms_st_entrada,
        aliquota_icms, cfop

    sped_c100: registros C100 com campos:
        chave_nfe, valor_total, tipo_operacao (0=entrada, 1=saída)
    """
    items: list[RecoveryItem] = []
    meses = _meses_entre(period, hoje)
    fator = _selic_fator(meses)

    # Agrupa C170 por NCM
    por_ncm: dict[str, list] = {}
    for reg in sped_c170:
        ncm = str(reg.get("ncm", "")).replace(".", "")
        por_ncm.setdefault(ncm, []).append(reg)

    for ncm, regs in por_ncm.items():
        bc_presumida_total = sum(float(r.get("valor_bc_st_entrada", 0)) for r in regs)
        icms_st_retido = sum(float(r.get("valor_icms_st_entrada", 0)) for r in regs)
        aliquota = float(regs[0].get("aliquota_icms", 0.12)) if regs else 0.12

        # Preço médio de venda real (C100 saídas)
        vendas = [c for c in sped_c100 if str(c.get("tipo_operacao")) == "1"]
        preco_venda_total = sum(float(v.get("valor_total", 0)) for v in vendas)

        if bc_presumida_total <= 0 or preco_venda_total <= 0:
            continue

        if preco_venda_total < bc_presumida_total:
            excesso = bc_presumida_total - preco_venda_total
            icms_ressarcivel = excesso * aliquota
            if icms_ressarcivel < 1.0:
                continue

            items.append(RecoveryItem(
                tax_type="icms_st",
                description=f"ICMS-ST ressarcimento — NCM {ncm}: base presumida R${bc_presumida_total:,.2f} > venda real R${preco_venda_total:,.2f}",
                ncm_code=ncm,
                period=period,
                base_calculo_original=bc_presumida_total,
                base_calculo_correto=preco_venda_total,
                aliquota=aliquota,
                valor_pago_indevido=icms_st_retido,
                valor_recuperavel=icms_ressarcivel,
                juros_selic=icms_ressarcivel * (fator - 1),
                valor_total=icms_ressarcivel * fator,
                fundamento_legal=(
                    "Convênio ICMS 13/97; LC 87/96 art.10; "
                    "RE 593.849 STF (repercussão geral)"
                ),
                risco="medio",
                documentos_necessarios=[
                    "SPED ICMS/IPI (C100, C170)",
                    "GIA/DIEF/SINTEGRA",
                    "Nota fiscal de entrada com ST",
                ],
                observacoes="Verificar legislação estadual específica",
            ))

    return items


# ──────────────────────────────────────────────────────────────────────────────
# Análise C — Tema 69 STF (ICMS fora da base PIS/COFINS)
# ──────────────────────────────────────────────────────────────────────────────

def _analisa_tema69(
    faturamento_mensal: list[dict],
    period: str,
    hoje: str = "202501",
) -> list[RecoveryItem]:
    """
    Calcula o excesso de PIS/COFINS pago porque o ICMS estava incluído
    na base de cálculo (antes do Tema 69 STF — julgado em 2017/2021).

    faturamento_mensal: lista de dicts com:
        competencia (YYYYMM), receita_bruta, icms_destacado,
        pis_pago, cofins_pago, regime_tributario
    """
    items: list[RecoveryItem] = []
    meses_total = _meses_entre(period, hoje)

    for row in faturamento_mensal:
        competencia = str(row.get("competencia", period))
        receita = float(row.get("receita_bruta", 0))
        icms = float(row.get("icms_destacado", 0))
        pis_pago = float(row.get("pis_pago", 0))
        cofins_pago = float(row.get("cofins_pago", 0))
        regime = str(row.get("regime_tributario", "simples")).lower()

        if receita <= 0 or icms <= 0:
            continue

        # Alíquotas efetivas
        aliq_pis = pis_pago / receita if receita > 0 and pis_pago > 0 else 0.0065
        aliq_cofins = cofins_pago / receita if receita > 0 and cofins_pago > 0 else 0.03

        excesso_pis = icms * aliq_pis
        excesso_cofins = icms * aliq_cofins

        meses = _meses_entre(competencia, hoje)
        fator = _selic_fator(meses)

        # Prazo decadencial: 5 anos (60 meses)
        if meses > 60:
            continue

        if excesso_pis > 0.01:
            items.append(RecoveryItem(
                tax_type="pis",
                description=f"PIS — Tema 69 STF ({competencia}): ICMS R${icms:,.2f} indevidamente incluído na base",
                ncm_code=None,
                period=competencia,
                base_calculo_original=receita,
                base_calculo_correto=receita - icms,
                aliquota=aliq_pis,
                valor_pago_indevido=excesso_pis,
                valor_recuperavel=excesso_pis,
                juros_selic=excesso_pis * (fator - 1),
                valor_total=excesso_pis * fator,
                fundamento_legal="RE 574.706 STF (Tema 69); IN RFB 2.055/2021",
                risco="baixo",
                documentos_necessarios=["ECF", "EFD Contribuições", "DCTF", "SPED Fiscal"],
            ))

        if excesso_cofins > 0.01:
            items.append(RecoveryItem(
                tax_type="cofins",
                description=f"COFINS — Tema 69 STF ({competencia}): ICMS R${icms:,.2f} indevidamente incluído na base",
                ncm_code=None,
                period=competencia,
                base_calculo_original=receita,
                base_calculo_correto=receita - icms,
                aliquota=aliq_cofins,
                valor_pago_indevido=excesso_cofins,
                valor_recuperavel=excesso_cofins,
                juros_selic=excesso_cofins * (fator - 1),
                valor_total=excesso_cofins * fator,
                fundamento_legal="RE 574.706 STF (Tema 69); IN RFB 2.055/2021",
                risco="baixo",
                documentos_necessarios=["ECF", "EFD Contribuições", "DCTF", "SPED Fiscal"],
            ))

    return items


# ──────────────────────────────────────────────────────────────────────────────
# Análise D — Créditos PIS/COFINS não aproveitados (Lucro Real)
# ──────────────────────────────────────────────────────────────────────────────

def _analisa_creditos_pis_cofins(
    entradas: list[dict],
    period: str,
    hoje: str = "202501",
) -> list[RecoveryItem]:
    """
    Verifica entradas que geram crédito de PIS/COFINS mas não foram
    aproveitadas (CST 01 = crédito básico não escriturado).

    entradas: lista de dicts com:
        ncm, valor_item, cst_pis, cst_cofins, cfop, tipo_credito
        (insumo, frete, energia, aluguel, depreciacao, outros)
    """
    items: list[RecoveryItem] = []
    meses = _meses_entre(period, hoje)
    fator = _selic_fator(meses)

    # Alíquotas padrão Lucro Real não-cumulativo
    ALIQ_PIS = 0.0165
    ALIQ_COFINS = 0.076

    # Agrupa por tipo de crédito
    por_tipo: dict[str, float] = {}
    for item in entradas:
        cst_pis = str(item.get("cst_pis", "")).zfill(2)
        # CST 01 = crédito básico; outros CSTs podem indicar crédito não tomado
        # Verifica se o crédito foi realmente escriturado
        credito_escriturado = item.get("credito_escriturado", False)
        if credito_escriturado:
            continue

        tipo = str(item.get("tipo_credito", "outros"))
        valor = float(item.get("valor_item", 0))
        cfop = str(item.get("cfop", ""))

        # CFOPs que geram crédito (aquisição de insumos, mercadorias p/ revenda etc)
        cfops_credito = {"1101", "1102", "1111", "1116", "1120", "1121", "1122",
                         "2101", "2102", "2111", "2116", "2120", "2121", "2122"}
        if cfop not in cfops_credito and tipo not in ("insumo", "frete", "energia", "aluguel"):
            continue

        por_tipo[tipo] = por_tipo.get(tipo, 0) + valor

    for tipo, base in por_tipo.items():
        if base < 100:
            continue

        val_pis = base * ALIQ_PIS
        val_cofins = base * ALIQ_COFINS

        items.append(RecoveryItem(
            tax_type="pis",
            description=f"Crédito PIS não aproveitado — {tipo}: base R${base:,.2f}",
            ncm_code=None,
            period=period,
            base_calculo_original=0.0,
            base_calculo_correto=base,
            aliquota=ALIQ_PIS,
            valor_pago_indevido=0.0,
            valor_recuperavel=val_pis,
            juros_selic=val_pis * (fator - 1),
            valor_total=val_pis * fator,
            fundamento_legal="Lei 10.637/2002 art.3; IN RFB 2.121/2022",
            risco="medio",
            documentos_necessarios=["SPED EFD Contribuições", "XMLs NFe entrada", "Contratos de serviço"],
        ))
        items.append(RecoveryItem(
            tax_type="cofins",
            description=f"Crédito COFINS não aproveitado — {tipo}: base R${base:,.2f}",
            ncm_code=None,
            period=period,
            base_calculo_original=0.0,
            base_calculo_correto=base,
            aliquota=ALIQ_COFINS,
            valor_pago_indevido=0.0,
            valor_recuperavel=val_cofins,
            juros_selic=val_cofins * (fator - 1),
            valor_total=val_cofins * fator,
            fundamento_legal="Lei 10.833/2003 art.3; IN RFB 2.121/2022",
            risco="medio",
            documentos_necessarios=["SPED EFD Contribuições", "XMLs NFe entrada", "Contratos de serviço"],
        ))

    return items


# ──────────────────────────────────────────────────────────────────────────────
# Motor principal
# ──────────────────────────────────────────────────────────────────────────────

def run_analysis(
    company_name: str,
    cnpj: str,
    period_start: str,
    period_end: str,
    nfe_items: list[dict] | None = None,
    sped_c170: list[dict] | None = None,
    sped_c100: list[dict] | None = None,
    faturamento_mensal: list[dict] | None = None,
    entradas_lucro_real: list[dict] | None = None,
    hoje: str = "202501",
) -> AnalysisResult:
    """
    Ponto de entrada principal do motor de análise.

    Aceita dados reais vindos dos parsers SPED/XML e executa todas as
    análises configuradas.

    Retorna AnalysisResult com lista de RecoveryItems e totais.
    """
    result = AnalysisResult(
        company_name=company_name,
        cnpj=cnpj,
        period_start=period_start,
        period_end=period_end,
        data_source="real",
    )

    # A — Monofásico
    if nfe_items:
        for period in _iter_periods(period_start, period_end):
            items_periodo = [i for i in nfe_items if i.get("competencia", period_start) == period]
            if items_periodo:
                result.recovery_items.extend(
                    _analisa_monofasico(items_periodo, period, hoje)
                )
            else:
                # Usa todos se não houver competência discriminada
                result.recovery_items.extend(
                    _analisa_monofasico(nfe_items, period, hoje)
                )
                break
    else:
        result.warnings.append("Análise monofásico ignorada: nenhum item de NFe fornecido")

    # B — ICMS-ST
    if sped_c170 and sped_c100:
        for period in _iter_periods(period_start, period_end):
            result.recovery_items.extend(
                _analisa_icms_st(sped_c170, sped_c100, period, hoje)
            )
    else:
        result.warnings.append("Análise ICMS-ST ignorada: SPED C170/C100 não fornecidos")

    # C — Tema 69
    if faturamento_mensal:
        result.recovery_items.extend(
            _analisa_tema69(faturamento_mensal, period_start, hoje)
        )
    else:
        result.warnings.append("Análise Tema 69 ignorada: faturamento mensal não fornecido")

    # D — Créditos PIS/COFINS
    if entradas_lucro_real:
        for period in _iter_periods(period_start, period_end):
            entradas_p = [e for e in entradas_lucro_real if e.get("competencia", period_start) == period]
            result.recovery_items.extend(
                _analisa_creditos_pis_cofins(entradas_p or entradas_lucro_real, period, hoje)
            )
            if not entradas_p:
                break
    else:
        result.warnings.append("Análise créditos PIS/COFINS ignorada: entradas não fornecidas")

    # Totais
    result.total_recuperavel = sum(i.valor_recuperavel for i in result.recovery_items)
    result.total_com_juros = sum(i.valor_total for i in result.recovery_items)

    return result


def _iter_periods(start: str, end: str):
    """Itera sobre períodos mensais YYYYMM entre start e end."""
    def to_ym(s):
        s = s.replace("-", "")
        return int(s[:4]), int(s[4:6])

    y, m = to_ym(start)
    ey, em = to_ym(end)
    while (y, m) <= (ey, em):
        yield f"{y:04d}{m:02d}"
        m += 1
        if m > 12:
            m = 1
            y += 1


# ──────────────────────────────────────────────────────────────────────────────
# Serialização
# ──────────────────────────────────────────────────────────────────────────────

def result_to_dict(result: AnalysisResult) -> dict:
    """Converte AnalysisResult para dict serializável (JSON-safe)."""
    return {
        "company_name": result.company_name,
        "cnpj": result.cnpj,
        "period_start": result.period_start,
        "period_end": result.period_end,
        "data_source": result.data_source,
        "total_recuperavel": round(result.total_recuperavel, 2),
        "total_com_juros": round(result.total_com_juros, 2),
        "warnings": result.warnings,
        "recovery_items": [
            {
                "tax_type": i.tax_type,
                "description": i.description,
                "ncm_code": i.ncm_code,
                "period": i.period,
                "base_calculo_original": round(i.base_calculo_original, 2),
                "base_calculo_correto": round(i.base_calculo_correto, 2),
                "aliquota": i.aliquota,
                "valor_pago_indevido": round(i.valor_pago_indevido, 2),
                "valor_recuperavel": round(i.valor_recuperavel, 2),
                "juros_selic": round(i.juros_selic, 2),
                "valor_total": round(i.valor_total, 2),
                "fundamento_legal": i.fundamento_legal,
                "risco": i.risco,
                "documentos_necessarios": i.documentos_necessarios,
                "observacoes": i.observacoes,
            }
            for i in result.recovery_items
        ],
    }
