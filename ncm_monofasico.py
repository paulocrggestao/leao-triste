#!/usr/bin/env python3
"""
ncm_monofasico.py — Tabela de NCMs sujeitos a PIS/COFINS monofásico no Brasil

Fonte legal:
  - Lei 10.485/2002 (veículos, autopeças)
  - Lei 10.147/2000 (medicamentos, produtos de higiene pessoal, cosméticos)
  - Lei 9.718/1998 art. 4 (combustíveis)
  - Lei 11.116/2005 (biodiesel)
  - Lei 10.560/2002 (querosene de aviação)
  - MP 2.158-35/2001 (água, refrigerantes, cervejas)
  - Decreto 3.859/2001 e atualizações NCM

CSTs corretos para produtos monofásicos:
  Saída do fabricante/importador:
    01 — Alíquota básica (contribuinte de fato paga)
  Saída do atacadista/varejista:
    02 — Alíquota diferenciada
    03 — Alíquota por unidade de medida
    04 — Monofásico (mais comum no varejo — alíquota zero)
    06 — Alíquota zero
    07 — Operação isenta

CSTs incorretos típicos encontrados em auditorias:
  01 no varejista → está gerando débito indevido (deveria ser 04/06/07)
  50 na saída     → pagando PIS/COFINS pleno em produto monofásico
"""

from __future__ import annotations

from typing import Optional

# ──────────────────────────────────────────────────────────────────────────────
# Constantes
# ──────────────────────────────────────────────────────────────────────────────

CSTS_MONOFASICO_CORRETOS = {"04", "06", "07", "02", "03"}
CSTS_MONOFASICO_INCORRETOS_SAIDA = {"01", "50", "99"}  # Geram débito indevido

# ──────────────────────────────────────────────────────────────────────────────
# Tabela NCM Monofásico
# Estrutura: NCM → dict com descrição, lei, alíquotas e notas
# ──────────────────────────────────────────────────────────────────────────────

_NCM_MONOFASICO: dict[str, dict] = {

    # ── Combustíveis e derivados de petróleo (Lei 9.718/1998 art.4) ──────────
    "27101112": {
        "descricao": "Gasolina automotiva tipo A",
        "lei": "Lei 9.718/1998 art.4; Lei 10.336/2001",
        "aliq_pis": 0.07689,
        "aliq_cofins": 0.35403,
        "unidade": "m3",
        "solucao_consulta": "COSIT 1/2014",
        "segmento": "combustiveis",
    },
    "27101113": {
        "descricao": "Gasolina automotiva tipo C",
        "lei": "Lei 9.718/1998 art.4",
        "aliq_pis": 0.07689,
        "aliq_cofins": 0.35403,
        "unidade": "m3",
        "solucao_consulta": "COSIT 1/2014",
        "segmento": "combustiveis",
    },
    "27101500": {
        "descricao": "Óleo diesel",
        "lei": "Lei 9.718/1998 art.4",
        "aliq_pis": 0.05250,
        "aliq_cofins": 0.24200,
        "unidade": "m3",
        "solucao_consulta": "COSIT 6/2014",
        "segmento": "combustiveis",
    },
    "27101921": {
        "descricao": "Óleo diesel B5",
        "lei": "Lei 9.718/1998 art.4",
        "aliq_pis": 0.05250,
        "aliq_cofins": 0.24200,
        "unidade": "m3",
        "solucao_consulta": "COSIT 6/2014",
        "segmento": "combustiveis",
    },
    "27111100": {
        "descricao": "Gás natural",
        "lei": "Lei 9.718/1998 art.4",
        "aliq_pis": 0.0100,
        "aliq_cofins": 0.0460,
        "unidade": "m3",
        "solucao_consulta": "",
        "segmento": "combustiveis",
    },
    "27111900": {
        "descricao": "Outros gases de petróleo (GLP)",
        "lei": "Lei 9.718/1998 art.4",
        "aliq_pis": 0.0669,
        "aliq_cofins": 0.3082,
        "unidade": "kg",
        "solucao_consulta": "COSIT 3/2014",
        "segmento": "combustiveis",
    },
    "27102000": {
        "descricao": "Querosene de aviação (QAV)",
        "lei": "Lei 10.560/2002",
        "aliq_pis": 0.0392,
        "aliq_cofins": 0.1809,
        "unidade": "m3",
        "solucao_consulta": "",
        "segmento": "combustiveis",
    },
    "38260000": {
        "descricao": "Biodiesel",
        "lei": "Lei 11.116/2005",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "m3",
        "solucao_consulta": "",
        "segmento": "combustiveis",
    },

    # ── Veículos automotores (Lei 10.485/2002) ───────────────────────────────
    "87032110": {
        "descricao": "Automóveis com motor de explosão até 1.0L",
        "lei": "Lei 10.485/2002 art.1",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "un",
        "solucao_consulta": "COSIT 222/2014",
        "segmento": "veiculos",
    },
    "87032190": {
        "descricao": "Automóveis com motor de explosão 1.0L a 1.6L",
        "lei": "Lei 10.485/2002 art.1",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "un",
        "solucao_consulta": "COSIT 222/2014",
        "segmento": "veiculos",
    },
    "87032290": {
        "descricao": "Automóveis com motor de explosão acima de 1.6L",
        "lei": "Lei 10.485/2002 art.1",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "un",
        "solucao_consulta": "COSIT 222/2014",
        "segmento": "veiculos",
    },
    "87033110": {
        "descricao": "Automóveis com motor diesel até 1.5L",
        "lei": "Lei 10.485/2002 art.1",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "un",
        "solucao_consulta": "COSIT 222/2014",
        "segmento": "veiculos",
    },
    "87033190": {
        "descricao": "Automóveis com motor diesel acima de 1.5L",
        "lei": "Lei 10.485/2002 art.1",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "un",
        "solucao_consulta": "COSIT 222/2014",
        "segmento": "veiculos",
    },
    "87042100": {
        "descricao": "Caminhões com motor a diesel",
        "lei": "Lei 10.485/2002 art.1",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "un",
        "solucao_consulta": "",
        "segmento": "veiculos",
    },
    "87050000": {
        "descricao": "Veículos especiais (ambulâncias, etc.)",
        "lei": "Lei 10.485/2002 art.1",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "un",
        "solucao_consulta": "",
        "segmento": "veiculos",
    },
    "87060010": {
        "descricao": "Chassis com motor para ônibus",
        "lei": "Lei 10.485/2002 art.1",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "un",
        "solucao_consulta": "",
        "segmento": "veiculos",
    },
    "87060090": {
        "descricao": "Outros chassis com motor",
        "lei": "Lei 10.485/2002 art.1",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "un",
        "solucao_consulta": "",
        "segmento": "veiculos",
    },
    "87089100": {
        "descricao": "Radiadores e suas partes (autopeças)",
        "lei": "Lei 10.485/2002 art.2",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "un",
        "solucao_consulta": "",
        "segmento": "autopecas",
    },
    "87089200": {
        "descricao": "Silenciosos e tubos de escape (autopeças)",
        "lei": "Lei 10.485/2002 art.2",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "un",
        "solucao_consulta": "",
        "segmento": "autopecas",
    },
    "87089300": {
        "descricao": "Embreagens e partes (autopeças)",
        "lei": "Lei 10.485/2002 art.2",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "un",
        "solucao_consulta": "",
        "segmento": "autopecas",
    },
    "87089900": {
        "descricao": "Outras partes e acessórios (autopeças)",
        "lei": "Lei 10.485/2002 art.2",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "un",
        "solucao_consulta": "",
        "segmento": "autopecas",
    },

    # ── Medicamentos (Lei 10.147/2000) ───────────────────────────────────────
    "30041011": {
        "descricao": "Medicamento com penicilina",
        "lei": "Lei 10.147/2000 art.1 I a",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "un",
        "solucao_consulta": "COSIT 60/2014",
        "segmento": "medicamentos",
    },
    "30041012": {
        "descricao": "Medicamento com ampicilina",
        "lei": "Lei 10.147/2000 art.1 I a",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "un",
        "solucao_consulta": "COSIT 60/2014",
        "segmento": "medicamentos",
    },
    "30042011": {
        "descricao": "Antibiótico com rifampicina",
        "lei": "Lei 10.147/2000 art.1 I a",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "un",
        "solucao_consulta": "COSIT 60/2014",
        "segmento": "medicamentos",
    },
    "30049010": {
        "descricao": "Medicamentos de uso humano — outros",
        "lei": "Lei 10.147/2000 art.1 I a",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "un",
        "solucao_consulta": "COSIT 60/2014",
        "segmento": "medicamentos",
    },
    "30049099": {
        "descricao": "Outros medicamentos de uso humano",
        "lei": "Lei 10.147/2000 art.1 I a",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "un",
        "solucao_consulta": "COSIT 60/2014",
        "segmento": "medicamentos",
    },
    "30059010": {
        "descricao": "Algodão, gaze, ataduras e semelhantes",
        "lei": "Lei 10.147/2000 art.1 I a",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "un",
        "solucao_consulta": "",
        "segmento": "medicamentos",
    },

    # ── Produtos de higiene e cosméticos (Lei 10.147/2000) ───────────────────
    "33030010": {
        "descricao": "Perfumes e águas-de-colônia",
        "lei": "Lei 10.147/2000 art.1 I b",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "un",
        "solucao_consulta": "COSIT 61/2014",
        "segmento": "cosmeticos",
    },
    "33041000": {
        "descricao": "Preparação para lábios",
        "lei": "Lei 10.147/2000 art.1 I b",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "un",
        "solucao_consulta": "COSIT 61/2014",
        "segmento": "cosmeticos",
    },
    "33042000": {
        "descricao": "Preparação para olhos",
        "lei": "Lei 10.147/2000 art.1 I b",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "un",
        "solucao_consulta": "COSIT 61/2014",
        "segmento": "cosmeticos",
    },
    "33043000": {
        "descricao": "Preparação para manicure/pedicure",
        "lei": "Lei 10.147/2000 art.1 I b",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "un",
        "solucao_consulta": "COSIT 61/2014",
        "segmento": "cosmeticos",
    },
    "33049100": {
        "descricao": "Pós para maquiagem",
        "lei": "Lei 10.147/2000 art.1 I b",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "un",
        "solucao_consulta": "COSIT 61/2014",
        "segmento": "cosmeticos",
    },
    "33049910": {
        "descricao": "Outros produtos de beleza/maquiagem",
        "lei": "Lei 10.147/2000 art.1 I b",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "un",
        "solucao_consulta": "COSIT 61/2014",
        "segmento": "cosmeticos",
    },
    "33051000": {
        "descricao": "Xampus",
        "lei": "Lei 10.147/2000 art.1 I b",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "un",
        "solucao_consulta": "COSIT 61/2014",
        "segmento": "cosmeticos",
    },
    "33052000": {
        "descricao": "Preparação para ondulação/alisamento",
        "lei": "Lei 10.147/2000 art.1 I b",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "un",
        "solucao_consulta": "COSIT 61/2014",
        "segmento": "cosmeticos",
    },
    "33053000": {
        "descricao": "Laquê para cabelos",
        "lei": "Lei 10.147/2000 art.1 I b",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "un",
        "solucao_consulta": "COSIT 61/2014",
        "segmento": "cosmeticos",
    },
    "33059000": {
        "descricao": "Outros preparações capilares",
        "lei": "Lei 10.147/2000 art.1 I b",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "un",
        "solucao_consulta": "COSIT 61/2014",
        "segmento": "cosmeticos",
    },
    "33061000": {
        "descricao": "Dentifrícios (pasta de dente)",
        "lei": "Lei 10.147/2000 art.1 I b",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "un",
        "solucao_consulta": "COSIT 62/2014",
        "segmento": "higiene",
    },
    "33062000": {
        "descricao": "Fio dental",
        "lei": "Lei 10.147/2000 art.1 I b",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "un",
        "solucao_consulta": "COSIT 62/2014",
        "segmento": "higiene",
    },
    "33069000": {
        "descricao": "Outros produtos para higiene bucal",
        "lei": "Lei 10.147/2000 art.1 I b",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "un",
        "solucao_consulta": "COSIT 62/2014",
        "segmento": "higiene",
    },
    "33071000": {
        "descricao": "Preparação para barbear",
        "lei": "Lei 10.147/2000 art.1 I b",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "un",
        "solucao_consulta": "COSIT 61/2014",
        "segmento": "higiene",
    },
    "33072000": {
        "descricao": "Desodorantes e antiperspirantes",
        "lei": "Lei 10.147/2000 art.1 I b",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "un",
        "solucao_consulta": "COSIT 61/2014",
        "segmento": "higiene",
    },
    "33074900": {
        "descricao": "Outros produtos de higiene pessoal",
        "lei": "Lei 10.147/2000 art.1 I b",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "un",
        "solucao_consulta": "COSIT 61/2014",
        "segmento": "higiene",
    },
    "34011100": {
        "descricao": "Sabão de toucador",
        "lei": "Lei 10.147/2000 art.1 I b",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "un",
        "solucao_consulta": "COSIT 61/2014",
        "segmento": "higiene",
    },
    "34012000": {
        "descricao": "Sabão em pó e líquido",
        "lei": "Lei 10.147/2000 art.1 I b",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "un",
        "solucao_consulta": "COSIT 61/2014",
        "segmento": "higiene",
    },

    # ── Bebidas (MP 2.158-35/2001) ───────────────────────────────────────────
    "22011000": {
        "descricao": "Água mineral natural",
        "lei": "MP 2.158-35/2001 art.52",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "un",
        "solucao_consulta": "COSIT 174/2014",
        "segmento": "bebidas",
    },
    "22019000": {
        "descricao": "Outras águas",
        "lei": "MP 2.158-35/2001 art.52",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "un",
        "solucao_consulta": "COSIT 174/2014",
        "segmento": "bebidas",
    },
    "22021000": {
        "descricao": "Água mineral com gás / gaseificada",
        "lei": "MP 2.158-35/2001 art.52",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "un",
        "solucao_consulta": "COSIT 174/2014",
        "segmento": "bebidas",
    },
    "22029000": {
        "descricao": "Outras bebidas não alcoólicas",
        "lei": "MP 2.158-35/2001 art.52",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "un",
        "solucao_consulta": "COSIT 174/2014",
        "segmento": "bebidas",
    },
    "22030000": {
        "descricao": "Cervejas de malte",
        "lei": "MP 2.158-35/2001 art.52; Lei 13.097/2015",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "litro",
        "solucao_consulta": "COSIT 175/2014",
        "segmento": "bebidas",
    },
    "22060000": {
        "descricao": "Outras bebidas fermentadas (cidra, perada, hidromel)",
        "lei": "MP 2.158-35/2001 art.52",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "litro",
        "solucao_consulta": "",
        "segmento": "bebidas",
    },
    "22084000": {
        "descricao": "Rum e outras aguardentes de cana",
        "lei": "MP 2.158-35/2001 art.52",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "litro",
        "solucao_consulta": "",
        "segmento": "bebidas",
    },
    "22086000": {
        "descricao": "Uísque",
        "lei": "MP 2.158-35/2001 art.52",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "litro",
        "solucao_consulta": "",
        "segmento": "bebidas",
    },
    "22087000": {
        "descricao": "Licores",
        "lei": "MP 2.158-35/2001 art.52",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "litro",
        "solucao_consulta": "",
        "segmento": "bebidas",
    },
    "22089011": {
        "descricao": "Cachaça",
        "lei": "MP 2.158-35/2001 art.52",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "litro",
        "solucao_consulta": "",
        "segmento": "bebidas",
    },
    "22089090": {
        "descricao": "Outras bebidas espirituosas",
        "lei": "MP 2.158-35/2001 art.52",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "litro",
        "solucao_consulta": "",
        "segmento": "bebidas",
    },
    "22043100": {
        "descricao": "Vinho espumante",
        "lei": "MP 2.158-35/2001 art.52; Lei 14.988/2024",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "litro",
        "solucao_consulta": "",
        "segmento": "bebidas",
    },
    "22042100": {
        "descricao": "Outros vinhos",
        "lei": "MP 2.158-35/2001 art.52; Lei 14.988/2024",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "litro",
        "solucao_consulta": "",
        "segmento": "bebidas",
    },
    "21069090": {
        "descricao": "Refrigerantes e extratos concentrados",
        "lei": "MP 2.158-35/2001 art.52; Lei 13.097/2015",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "litro",
        "solucao_consulta": "COSIT 176/2014",
        "segmento": "bebidas",
    },
    "22021000": {
        "descricao": "Refrigerantes / bebidas com adição de açúcar",
        "lei": "MP 2.158-35/2001 art.52; Lei 13.097/2015",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "litro",
        "solucao_consulta": "COSIT 176/2014",
        "segmento": "bebidas",
    },

    # ── Embalagens para bebidas (Lei 13.097/2015) ────────────────────────────
    "39239090": {
        "descricao": "Embalagens plásticas para bebidas",
        "lei": "Lei 13.097/2015 art.14",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "un",
        "solucao_consulta": "",
        "segmento": "embalagens",
    },
    "76129010": {
        "descricao": "Latas de alumínio para bebidas",
        "lei": "Lei 13.097/2015 art.14",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "un",
        "solucao_consulta": "",
        "segmento": "embalagens",
    },
    "70109010": {
        "descricao": "Garrafas de vidro para bebidas",
        "lei": "Lei 13.097/2015 art.14",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "un",
        "solucao_consulta": "",
        "segmento": "embalagens",
    },

    # ── Pneus (Lei 10.485/2002) ──────────────────────────────────────────────
    "40111000": {
        "descricao": "Pneus de automóvel",
        "lei": "Lei 10.485/2002 Anexo I",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "un",
        "solucao_consulta": "",
        "segmento": "pneus",
    },
    "40112000": {
        "descricao": "Pneus de ônibus e caminhão",
        "lei": "Lei 10.485/2002 Anexo I",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "un",
        "solucao_consulta": "",
        "segmento": "pneus",
    },
    "40114000": {
        "descricao": "Pneus de motocicleta",
        "lei": "Lei 10.485/2002 Anexo I",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "un",
        "solucao_consulta": "",
        "segmento": "pneus",
    },
    "40119990": {
        "descricao": "Outros pneus novos",
        "lei": "Lei 10.485/2002 Anexo I",
        "aliq_pis": 0.0,
        "aliq_cofins": 0.0,
        "unidade": "un",
        "solucao_consulta": "",
        "segmento": "pneus",
    },
}


# ──────────────────────────────────────────────────────────────────────────────
# API pública
# ──────────────────────────────────────────────────────────────────────────────

def _normalize_ncm(ncm: str) -> str:
    """Remove pontos e espaços do NCM."""
    return ncm.strip().replace(".", "").replace("-", "").replace(" ", "")


def is_monofasico(ncm: str) -> bool:
    """
    Verifica se um NCM está sujeito ao regime monofásico de PIS/COFINS.

    Args:
        ncm: Código NCM com ou sem pontuação (ex: '3004.90.99' ou '30049099')

    Returns:
        True se o NCM está na tabela monofásica
    """
    ncm_clean = _normalize_ncm(ncm)
    # Busca exata
    if ncm_clean in _NCM_MONOFASICO:
        return True
    # Busca por prefixo (NCMs de 6 dígitos podem cobrir vários de 8)
    for key in _NCM_MONOFASICO:
        if ncm_clean.startswith(key[:6]) and len(key) >= 6:
            if len(ncm_clean) <= len(key):
                return True
    return False


def get_monofasico_info(ncm: str) -> Optional[dict]:
    """
    Retorna informações completas sobre o NCM monofásico.

    Args:
        ncm: Código NCM com ou sem pontuação

    Returns:
        dict com {descricao, lei, aliq_pis, aliq_cofins, unidade,
                  solucao_consulta, segmento} ou None se não encontrado
    """
    ncm_clean = _normalize_ncm(ncm)
    if ncm_clean in _NCM_MONOFASICO:
        return _NCM_MONOFASICO[ncm_clean]
    for key in _NCM_MONOFASICO:
        if ncm_clean.startswith(key[:6]) and len(key) >= 6:
            if len(ncm_clean) <= len(key):
                return _NCM_MONOFASICO[key]
    return None


def check_cst_correctness(ncm: str, cst: str) -> tuple[bool, str]:
    """
    Verifica se o CST usado está correto para o NCM monofásico.

    Args:
        ncm: Código NCM
        cst: CST PIS ou COFINS usado (string, ex: '01', '04')

    Returns:
        Tuple (correto: bool, cst_recomendado: str)
        correto = True se o CST está adequado para produto monofásico
    """
    cst_norm = str(cst).strip().zfill(2)
    correto = cst_norm in CSTS_MONOFASICO_CORRETOS
    # Recomendação padrão: CST 04 (monofásico — alíquota zero)
    return correto, "04"


def list_ncms_by_segmento(segmento: str) -> list[str]:
    """
    Lista NCMs de um segmento específico.

    Args:
        segmento: Ex: 'combustiveis', 'medicamentos', 'cosmeticos',
                      'higiene', 'bebidas', 'veiculos', 'autopecas', 'pneus'

    Returns:
        Lista de NCMs (8 dígitos)
    """
    return [
        ncm for ncm, info in _NCM_MONOFASICO.items()
        if info.get("segmento") == segmento
    ]


def get_all_ncms() -> list[str]:
    """Retorna todos os NCMs monofásicos cadastrados."""
    return list(_NCM_MONOFASICO.keys())


def get_segmentos() -> list[str]:
    """Retorna todos os segmentos disponíveis."""
    return list({info["segmento"] for info in _NCM_MONOFASICO.values()})
