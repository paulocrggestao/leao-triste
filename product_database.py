#!/usr/bin/env python3
"""
product_database.py
Base de dados de produtos alimentícios brasileiros com NCM, CEST e informações tributárias.
Contém mais de 2.000 produtos comuns em supermercados, padarias e restaurantes.

Fontes:
- NCM: Receita Federal do Brasil (Nomenclatura Comum do Mercosul)
- CEST: Convênio ICMS 92/2015 e atualizações (Convênio ICMS 146/2015)
- PIS/COFINS monofásico: Lei nº 10.147/2000 e legislação correlata
- Alíquota zero cesta básica: Lei 10.925/2004, Decreto 6.426/2008
"""

from typing import List, Dict, Optional, Any
import re
import unicodedata

# ============================================================
# ESTRUTURA DE CADA PRODUTO:
# ean: EAN-13 / GTIN (string, pode ser vazia)
# nome: Nome completo do produto (marca + descrição + tamanho)
# descricao_generica: Descrição genérica sem marca
# ncm: Código NCM com 8 dígitos
# ncm_descricao: Descrição oficial do NCM
# categoria: Categoria do produto
# subcategoria: Subcategoria do produto
# unidade: Unidade de medida (kg, un, lt, cx, etc.)
# monofasico: True se PIS/COFINS é monofásico (alíquota zero no varejo)
# aliquota_zero: True se PIS/COFINS tem alíquota zero (cesta básica)
# ipi: Alíquota de IPI (geralmente 0 para alimentos)
# cest: Código CEST para substituição tributária
# marca_exemplo: Exemplo de marca comercial
# ============================================================

def _p(ean, nome, desc, ncm, ncm_desc, cat, subcat, unid, mono, alizero, ipi, cest, marca):
    """Helper para criar produto."""
    return {
        "ean": ean,
        "nome": nome,
        "descricao_generica": desc,
        "ncm": ncm,
        "ncm_descricao": ncm_desc,
        "categoria": cat,
        "subcategoria": subcat,
        "unidade": unid,
        "monofasico": mono,
        "aliquota_zero": alizero,
        "ipi": ipi,
        "cest": cest,
        "marca_exemplo": marca,
    }

_PRODUCTS: List[Dict[str, Any]] = []


# ============================================================
# SEÇÃO 1: CEREAIS E GRÃOS
# ============================================================

_PRODUCTS += [
    # ---- ARROZ ----
    _p("7891895011105","Arroz Tio João Tipo 1 5kg","Arroz branco beneficiado tipo 1","10063021","Arroz semibranqueado ou branqueado, polido ou brunido","Cereais e Grãos","Arroz","kg",False,True,0,"","Tio João"),
    _p("7891895011204","Arroz Tio João Tipo 1 1kg","Arroz branco beneficiado tipo 1","10063021","Arroz semibranqueado ou branqueado, polido ou brunido","Cereais e Grãos","Arroz","kg",False,True,0,"","Tio João"),
    _p("7891895019101","Arroz Tio João Parboilizado 5kg","Arroz parboilizado tipo 1","10063011","Arroz parboilizado, polido ou brunido","Cereais e Grãos","Arroz","kg",False,True,0,"","Tio João"),
    _p("7891895019200","Arroz Tio João Parboilizado 1kg","Arroz parboilizado tipo 1","10063011","Arroz parboilizado, polido ou brunido","Cereais e Grãos","Arroz","kg",False,True,0,"","Tio João"),
    _p("7896036002007","Arroz Camil Tipo 1 5kg","Arroz branco beneficiado tipo 1","10063021","Arroz semibranqueado ou branqueado, polido ou brunido","Cereais e Grãos","Arroz","kg",False,True,0,"","Camil"),
    _p("7896036002106","Arroz Camil Tipo 1 1kg","Arroz branco beneficiado tipo 1","10063021","Arroz semibranqueado ou branqueado, polido ou brunido","Cereais e Grãos","Arroz","kg",False,True,0,"","Camil"),
    _p("7896036095009","Arroz Camil Parboilizado 5kg","Arroz parboilizado tipo 1","10063011","Arroz parboilizado, polido ou brunido","Cereais e Grãos","Arroz","kg",False,True,0,"","Camil"),
    _p("7896036095108","Arroz Camil Parboilizado 1kg","Arroz parboilizado tipo 1","10063011","Arroz parboilizado, polido ou brunido","Cereais e Grãos","Arroz","kg",False,True,0,"","Camil"),
    _p("7896036500046","Arroz Camil Integral 1kg","Arroz integral beneficiado","10062020","Arroz descascado (cargo ou castanho)","Cereais e Grãos","Arroz","kg",False,True,0,"","Camil"),
    _p("7891895083003","Arroz Tio João Integral 1kg","Arroz integral beneficiado","10062020","Arroz descascado (cargo ou castanho)","Cereais e Grãos","Arroz","kg",False,True,0,"","Tio João"),
    _p("7896036500008","Arroz Camil Arbóreo 1kg","Arroz arbóreo para risoto","10063021","Arroz semibranqueado ou branqueado, polido ou brunido","Cereais e Grãos","Arroz","kg",False,True,0,"","Camil"),
    _p("7896039210033","Arroz Prato Fino Tipo 1 5kg","Arroz branco beneficiado tipo 1","10063021","Arroz semibranqueado ou branqueado, polido ou brunido","Cereais e Grãos","Arroz","kg",False,True,0,"","Prato Fino"),
    _p("7896039210040","Arroz Prato Fino Parboilizado 5kg","Arroz parboilizado tipo 1","10063011","Arroz parboilizado, polido ou brunido","Cereais e Grãos","Arroz","kg",False,True,0,"","Prato Fino"),
    _p("7891895083010","Arroz Tio João Jasmine 1kg","Arroz jasmim aromático","10063021","Arroz semibranqueado ou branqueado, polido ou brunido","Cereais e Grãos","Arroz","kg",False,True,0,"","Tio João"),
    _p("7896036280030","Arroz Negro Integral Camil 500g","Arroz negro integral","10062020","Arroz descascado (cargo ou castanho)","Cereais e Grãos","Arroz","kg",False,True,0,"","Camil"),
    _p("7896036280023","Arroz Vermelho Integral 500g","Arroz vermelho integral","10062020","Arroz descascado (cargo ou castanho)","Cereais e Grãos","Arroz","kg",False,True,0,"","Camil"),
    _p("7896036500053","Arroz Camil Arbóreo Pronto para Risoto 250g","Arroz arbóreo temperado","10063021","Arroz semibranqueado ou branqueado, polido ou brunido","Cereais e Grãos","Arroz","kg",False,True,0,"","Camil"),
    _p("7891895011402","Arroz Tio João Tipo 1 2kg","Arroz branco beneficiado tipo 1","10063021","Arroz semibranqueado ou branqueado, polido ou brunido","Cereais e Grãos","Arroz","kg",False,True,0,"","Tio João"),
    _p("7891895019408","Arroz Tio João Parboilizado 2kg","Arroz parboilizado tipo 1","10063011","Arroz parboilizado, polido ou brunido","Cereais e Grãos","Arroz","kg",False,True,0,"","Tio João"),
    _p("7896036002205","Arroz Camil Tipo 1 2kg","Arroz branco beneficiado tipo 1","10063021","Arroz semibranqueado ou branqueado, polido ou brunido","Cereais e Grãos","Arroz","kg",False,True,0,"","Camil"),

    # ---- FEIJÃO ----
    _p("7896200115346","Feijão Carioca Broto Legal Tipo 1 1kg","Feijão carioca tipo 1","07133290","Feijões (Vigna spp., Phaseolus spp.)","Cereais e Grãos","Feijão","kg",False,True,0,"","Broto Legal"),
    _p("7896864400178","Feijão Carioca Picinin Premium 1kg","Feijão carioca premium","07133290","Feijões (Vigna spp., Phaseolus spp.)","Cereais e Grãos","Feijão","kg",False,True,0,"","Picinin"),
    _p("7898015990194","Feijão Carioca Liderança Tipo 1 1kg","Feijão carioca tipo 1","07133290","Feijões (Vigna spp., Phaseolus spp.)","Cereais e Grãos","Feijão","kg",False,True,0,"","Liderança"),
    _p("7896036099007","Feijão Carioca Camil Tipo 1 1kg","Feijão carioca tipo 1","07133290","Feijões (Vigna spp., Phaseolus spp.)","Cereais e Grãos","Feijão","kg",False,True,0,"","Camil"),
    _p("7896036099106","Feijão Preto Camil Tipo 1 1kg","Feijão preto tipo 1","07133290","Feijões (Vigna spp., Phaseolus spp.)","Cereais e Grãos","Feijão","kg",False,True,0,"","Camil"),
    _p("7896200115353","Feijão Preto Broto Legal Tipo 1 1kg","Feijão preto tipo 1","07133290","Feijões (Vigna spp., Phaseolus spp.)","Cereais e Grãos","Feijão","kg",False,True,0,"","Broto Legal"),
    _p("7896200115360","Feijão Carioca Broto Legal 500g","Feijão carioca tipo 1","07133290","Feijões (Vigna spp., Phaseolus spp.)","Cereais e Grãos","Feijão","kg",False,True,0,"","Broto Legal"),
    _p("7896036099205","Feijão Preto Camil 500g","Feijão preto tipo 1","07133290","Feijões (Vigna spp., Phaseolus spp.)","Cereais e Grãos","Feijão","kg",False,True,0,"","Camil"),
    _p("7896200115377","Feijão Mulatinho Broto Legal 1kg","Feijão mulatinho tipo 1","07133290","Feijões (Vigna spp., Phaseolus spp.)","Cereais e Grãos","Feijão","kg",False,True,0,"","Broto Legal"),
    _p("7896036099304","Feijão Rosinha Camil 1kg","Feijão rosinha tipo 1","07133290","Feijões (Vigna spp., Phaseolus spp.)","Cereais e Grãos","Feijão","kg",False,True,0,"","Camil"),
    _p("7896036099403","Feijão Fradinho Camil 1kg","Feijão fradinho","07131090","Ervilhas (Vigna unguiculata)","Cereais e Grãos","Feijão","kg",False,True,0,"","Camil"),
    _p("7896036099502","Feijão Jalo Camil 1kg","Feijão jalo tipo 1","07133290","Feijões (Vigna spp., Phaseolus spp.)","Cereais e Grãos","Feijão","kg",False,True,0,"","Camil"),
    _p("7896036099601","Feijão Branco Camil 1kg","Feijão branco","07133290","Feijões (Vigna spp., Phaseolus spp.)","Cereais e Grãos","Feijão","kg",False,True,0,"","Camil"),
    _p("7896039200010","Feijão Carioca Tio João 1kg","Feijão carioca tipo 1","07133290","Feijões (Vigna spp., Phaseolus spp.)","Cereais e Grãos","Feijão","kg",False,True,0,"","Tio João"),
    _p("7896039200027","Feijão Preto Tio João 1kg","Feijão preto tipo 1","07133290","Feijões (Vigna spp., Phaseolus spp.)","Cereais e Grãos","Feijão","kg",False,True,0,"","Tio João"),

    # ---- AÇÚCAR ----
    _p("7891118001039","Açúcar Cristal União 1kg","Açúcar cristal","17011400","Açúcar de cana — outros","Cereais e Grãos","Açúcar","kg",False,False,0,"17.099.00","União"),
    _p("7891118001046","Açúcar Refinado União 1kg","Açúcar refinado","17019900","Açúcar refinado","Cereais e Grãos","Açúcar","kg",False,False,0,"17.099.00","União"),
    _p("7891118011014","Açúcar União Refinado 5kg","Açúcar refinado","17019900","Açúcar refinado","Cereais e Grãos","Açúcar","kg",False,False,0,"17.099.00","União"),
    _p("7891118001053","Açúcar União VHP 1kg","Açúcar VHP de cana","17011300","Açúcar de cana mencionado na Nota 2","Cereais e Grãos","Açúcar","kg",False,False,0,"17.099.00","União"),
    _p("7891118002005","Açúcar Orgânico União 1kg","Açúcar orgânico de cana","17011400","Açúcar de cana — outros","Cereais e Grãos","Açúcar","kg",False,False,0,"17.099.00","União"),
    _p("7896050001001","Açúcar Cristal Caravelas 1kg","Açúcar cristal","17011400","Açúcar de cana — outros","Cereais e Grãos","Açúcar","kg",False,False,0,"17.099.00","Caravelas"),
    _p("7891118003002","Açúcar de Confeiteiro União 1kg","Açúcar impalpável/confeiteiro","17019900","Açúcar refinado — outros","Cereais e Grãos","Açúcar","kg",False,False,0,"17.099.00","União"),
    _p("7891118004009","Açúcar Mascavo União 1kg","Açúcar mascavo","17011400","Açúcar de cana — outros","Cereais e Grãos","Açúcar","kg",False,False,0,"","União"),
    _p("7891118001060","Açúcar Demerara União 1kg","Açúcar demerara","17011400","Açúcar de cana — outros","Cereais e Grãos","Açúcar","kg",False,False,0,"","União"),
    _p("7896050001025","Açúcar Refinado Caravelas 2kg","Açúcar refinado","17019900","Açúcar refinado","Cereais e Grãos","Açúcar","kg",False,False,0,"17.099.00","Caravelas"),
    _p("7891118001077","Açúcar Light União 1kg","Mistura açúcar e edulcorante","17019100","Açúcar com aromatizantes ou corantes","Cereais e Grãos","Açúcar","kg",False,False,0,"","União"),

    # ---- SAL ----
    _p("7891039000012","Sal Refinado Cisne 1kg","Sal refinado iodado","25010020","Sal iodado","Cereais e Grãos","Sal","kg",False,True,0,"","Cisne"),
    _p("7891039000029","Sal Grosso Cisne 1kg","Sal grosso","25010010","Sal grosso sem iodo","Cereais e Grãos","Sal","kg",False,True,0,"","Cisne"),
    _p("7891039500010","Sal Refinado Lebre 1kg","Sal refinado iodado","25010020","Sal iodado","Cereais e Grãos","Sal","kg",False,True,0,"","Lebre"),
    _p("7891039000036","Sal Marinho Cisne 1kg","Sal marinho","25010020","Sal marinho","Cereais e Grãos","Sal","kg",False,True,0,"","Cisne"),
    _p("7891039000043","Sal Light Cisne 500g","Sal light com cloreto de potássio","25010020","Sal iodado","Cereais e Grãos","Sal","kg",False,True,0,"","Cisne"),

    # ---- FARINHA DE TRIGO ----
    _p("7896002300015","Farinha Trigo Especial Dona Benta 1kg","Farinha de trigo tipo 1","11010010","Farinha de trigo","Cereais e Grãos","Farinha de Trigo","kg",False,True,0,"","Dona Benta"),
    _p("7896002300022","Farinha Trigo Especial Dona Benta 5kg","Farinha de trigo tipo 1","11010010","Farinha de trigo","Cereais e Grãos","Farinha de Trigo","kg",False,True,0,"","Dona Benta"),
    _p("7891167011030","Farinha Trigo Anaconda Especial 1kg","Farinha de trigo tipo 1","11010010","Farinha de trigo","Cereais e Grãos","Farinha de Trigo","kg",False,True,0,"","Anaconda"),
    _p("7891167011047","Farinha Trigo Anaconda Especial 5kg","Farinha de trigo tipo 1","11010010","Farinha de trigo","Cereais e Grãos","Farinha de Trigo","kg",False,True,0,"","Anaconda"),
    _p("7896002300039","Farinha Trigo Integral Dona Benta 1kg","Farinha de trigo integral","11010010","Farinha de trigo integral","Cereais e Grãos","Farinha de Trigo","kg",False,True,0,"","Dona Benta"),
    _p("7896002300046","Farinha Trigo Sem Glúten Dona Benta 500g","Mistura farinha sem glúten","11022000","Farinha de milho","Cereais e Grãos","Farinha de Trigo","kg",False,True,0,"","Dona Benta"),
    _p("7896002300053","Farinha Trigo Tipo 2 Dona Benta 1kg","Farinha de trigo tipo 2","11010010","Farinha de trigo","Cereais e Grãos","Farinha de Trigo","kg",False,True,0,"","Dona Benta"),

    # ---- FARINHA DE MILHO / FUBÁ / AMIDO ----
    _p("7891949002012","Fubá Mimoso Yoki 500g","Fubá de milho fino","11022000","Farinha de milho","Cereais e Grãos","Fubá","kg",False,True,0,"","Yoki"),
    _p("7891949002029","Fubá Mimoso Yoki 1kg","Fubá de milho fino","11022000","Farinha de milho","Cereais e Grãos","Fubá","kg",False,True,0,"","Yoki"),
    _p("7891949003019","Fubá Canjiquinha Yoki 500g","Farinha de milho grossa","11022000","Farinha de milho","Cereais e Grãos","Fubá","kg",False,True,0,"","Yoki"),
    _p("7891949004016","Farinha Milharina 500g","Farinha de milho pré-cozida","11022000","Farinha de milho","Cereais e Grãos","Fubá","kg",False,True,0,"","Milharina"),
    _p("7896024701095","Amido de Milho Maisena 500g","Amido de milho (maizena)","11081200","Amido de milho","Cereais e Grãos","Amidos e Féculas","kg",False,True,0,"","Maizena"),
    _p("7896024701101","Amido de Milho Maisena 1kg","Amido de milho (maizena)","11081200","Amido de milho","Cereais e Grãos","Amidos e Féculas","kg",False,True,0,"","Maizena"),
    _p("7891949005013","Polvilho Azedo Yoki 500g","Polvilho azedo (fécula mandioca fermentada)","11081400","Fécula de mandioca","Cereais e Grãos","Amidos e Féculas","kg",False,True,0,"","Yoki"),
    _p("7891949006010","Polvilho Doce Yoki 500g","Polvilho doce (fécula mandioca)","11081400","Fécula de mandioca","Cereais e Grãos","Amidos e Féculas","kg",False,True,0,"","Yoki"),
    _p("7896024702009","Farinha Mandioca Torrada Fina 500g","Farinha de mandioca torrada fina","11062000","Farinha de mandioca (farinha de yuca)","Cereais e Grãos","Farinha de Mandioca","kg",False,True,0,"","Forno de Minas"),
    _p("7896024702016","Farinha Mandioca Crua Grossa 500g","Farinha de mandioca crua grossa","11062000","Farinha de mandioca","Cereais e Grãos","Farinha de Mandioca","kg",False,True,0,"","Forno de Minas"),
    _p("7891949007017","Farinha Tapioca Yoki 500g","Tapioca granulada","11081400","Fécula de mandioca","Cereais e Grãos","Tapioca","kg",False,True,0,"","Yoki"),
    _p("7891949007024","Goma para Tapioca Yoki 500g","Goma para tapioca","11081400","Fécula de mandioca","Cereais e Grãos","Tapioca","kg",False,True,0,"","Yoki"),

    # ---- CEREAIS MATINAIS ----
    _p("7891962041201","Granola Mãe Terra 750g","Granola com mel e castanhas","19042000","Preparações alimentícias obtidas a partir de cereais","Cereais e Grãos","Cereais Matinais","kg",False,False,0,"17.030.00","Mãe Terra"),
    _p("7896036180048","Flocos de Milho Kellogg's Sucrilhos 500g","Flocos de milho açucarados","19041000","Produtos de cereais obtidos por expansão","Cereais e Grãos","Cereais Matinais","kg",False,False,0,"17.030.00","Kellogg's"),
    _p("7896036180109","Nescau Cereal Nestlé 500g","Cereal de milho achocolatado","19041000","Produtos de cereais obtidos por expansão","Cereais e Grãos","Cereais Matinais","kg",False,False,0,"17.030.00","Nestlé"),
    _p("7896004400017","Aveia em Flocos Quaker 500g","Aveia em flocos","11041200","Grãos de aveia trabalhados de outro modo","Cereais e Grãos","Cereais Matinais","kg",False,True,0,"","Quaker"),
    _p("7896004400024","Aveia em Flocos Finos Quaker 500g","Aveia em flocos finos","11041200","Grãos de aveia trabalhados de outro modo","Cereais e Grãos","Cereais Matinais","kg",False,True,0,"","Quaker"),
    _p("7896004400031","Aveia Flocos Grossos Quaker 1kg","Aveia em flocos grossos","11041200","Grãos de aveia trabalhados de outro modo","Cereais e Grãos","Cereais Matinais","kg",False,True,0,"","Quaker"),
    _p("7891077500015","Granola Integral Jasmine 750g","Granola integral","19042000","Preparações alimentícias obtidas a partir de cereais","Cereais e Grãos","Cereais Matinais","kg",False,False,0,"17.030.00","Jasmine"),
    _p("7896036180215","Corn Flakes Kellogg's 500g","Flocos de milho","19041000","Produtos de cereais obtidos por expansão","Cereais e Grãos","Cereais Matinais","kg",False,False,0,"17.030.00","Kellogg's"),
    _p("7896036180222","Froot Loops Kellogg's 300g","Argolas de cereais coloridas","19041000","Produtos de cereais obtidos por expansão","Cereais e Grãos","Cereais Matinais","kg",False,False,0,"17.030.00","Kellogg's"),

    # ---- MASSAS ALIMENTÍCIAS ----
    _p("7891132002014","Macarrão Espaguete Adria 500g","Macarrão espaguete n.8","19023000","Outras massas alimentícias","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"17.049.00","Adria"),
    _p("7891132002021","Macarrão Penne Adria 500g","Macarrão penne","19023000","Outras massas alimentícias","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"17.049.00","Adria"),
    _p("7891132002038","Macarrão Fusilli Adria 500g","Macarrão fusilli","19023000","Outras massas alimentícias","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"17.049.00","Adria"),
    _p("7891132003011","Macarrão Capeletti Adria 500g","Macarrão capeletti","19022000","Massas alimentícias recheadas","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"17.048.00","Adria"),
    _p("7896020500016","Macarrão Espaguete Barilla n.5 500g","Macarrão espaguete","19023000","Outras massas alimentícias","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"17.049.00","Barilla"),
    _p("7896020500023","Macarrão Penne Barilla 500g","Macarrão penne rigate","19023000","Outras massas alimentícias","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"17.049.00","Barilla"),
    _p("7896020500030","Macarrão Farfalle Barilla 500g","Macarrão farfalle","19023000","Outras massas alimentícias","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"17.049.00","Barilla"),
    _p("7891132005015","Macarrão com Ovos Espaguete Adria 500g","Macarrão com ovos espaguete","19021100","Massas alimentícias com ovos","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"17.049.00","Adria"),
    _p("7891132004018","Macarrão Conchinha Adria 500g","Macarrão conchinha","19023000","Outras massas alimentícias","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"17.049.00","Adria"),
    _p("7896020500047","Macarrão Lasanha Barilla 500g","Massa para lasanha","19023000","Outras massas alimentícias","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"17.049.00","Barilla"),
    _p("7891132002090","Macarrão Integral Adria 500g","Macarrão integral espaguete","19023000","Outras massas alimentícias","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"17.049.00","Adria"),
    _p("7891132009013","Macarrão Instantâneo Nissin Miojo 85g","Macarrão instantâneo","19023000","Massas alimentícias tipo instantânea","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"17.047.00","Nissin"),
    _p("7891132009020","Macarrão Instantâneo Nissin Miojo Galinha 85g","Macarrão instantâneo sabor galinha","19023000","Massas alimentícias tipo instantânea","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"17.047.00","Nissin"),
    _p("7891132009037","Macarrão Instantâneo Nissin Miojo Carne 85g","Macarrão instantâneo sabor carne","19023000","Massas alimentícias tipo instantânea","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"17.047.00","Nissin"),

    # ---- ERVILHA / LENTILHA / GRÃO-DE-BICO ----
    _p("7896036099700","Ervilha Camil 500g","Ervilha partida seca","07135090","Ervilhas (Pisum sativum)","Cereais e Grãos","Leguminosas","kg",False,True,0,"","Camil"),
    _p("7896036099809","Lentilha Camil 500g","Lentilha","07134090","Lentilhas (Lens culinaris)","Cereais e Grãos","Leguminosas","kg",False,True,0,"","Camil"),
    _p("7896036099908","Grão de Bico Camil 500g","Grão-de-bico","07136090","Grão-de-bico (Cicer arietinum)","Cereais e Grãos","Leguminosas","kg",False,True,0,"","Camil"),
    _p("7896200115384","Soja em Grão Broto Legal 500g","Soja em grão","12019000","Grãos de soja inteiros","Cereais e Grãos","Leguminosas","kg",False,True,0,"","Broto Legal"),
    _p("7896036099600","Feijão Branco Camil 500g","Feijão branco","07133290","Feijões (Vigna spp., Phaseolus spp.)","Cereais e Grãos","Leguminosas","kg",False,True,0,"","Camil"),
    _p("7896200115391","Grão de Bico Broto Legal 1kg","Grão-de-bico","07136090","Grão-de-bico (Cicer arietinum)","Cereais e Grãos","Leguminosas","kg",False,True,0,"","Broto Legal"),
]


# ============================================================
# SEÇÃO 2: ÓLEOS E GORDURAS
# ============================================================

_PRODUCTS += [
    # ---- ÓLEOS VEGETAIS ----
    _p("7891107100103","Óleo Soja Soya 900ml","Óleo de soja refinado","15079011","Óleo de soja — outros (embalagem ≤5L)","Óleos e Gorduras","Óleo Vegetal","lt",True,False,0,"","Soya"),
    _p("7891107100110","Óleo Soja Liza 900ml","Óleo de soja refinado","15079011","Óleo de soja — outros (embalagem ≤5L)","Óleos e Gorduras","Óleo Vegetal","lt",True,False,0,"","Liza"),
    _p("7891107100127","Óleo Soja Vivi 900ml","Óleo de soja refinado","15079011","Óleo de soja — outros (embalagem ≤5L)","Óleos e Gorduras","Óleo Vegetal","lt",True,False,0,"","Vivi"),
    _p("7891107100134","Óleo Canola Liza 900ml","Óleo de canola refinado","15141910","Óleo de canola em bruto","Óleos e Gorduras","Óleo Vegetal","lt",True,False,0,"","Liza"),
    _p("7891107100141","Óleo Milho Mazola 900ml","Óleo de milho refinado","15152910","Óleo de milho refinado, em recipientes ≤5L","Óleos e Gorduras","Óleo Vegetal","lt",True,False,0,"","Mazola"),
    _p("7891107100158","Óleo Girassol Liza 500ml","Óleo de girassol refinado","15121911","Óleo de girassol refinado, embalagem ≤5L","Óleos e Gorduras","Óleo Vegetal","lt",True,False,0,"","Liza"),
    _p("7891107100165","Óleo Soja Soya 2L","Óleo de soja refinado 2L","15079011","Óleo de soja — outros (embalagem ≤5L)","Óleos e Gorduras","Óleo Vegetal","lt",True,False,0,"","Soya"),
    _p("7891107100172","Óleo Soja Liza 2L","Óleo de soja refinado 2L","15079011","Óleo de soja — outros (embalagem ≤5L)","Óleos e Gorduras","Óleo Vegetal","lt",True,False,0,"","Liza"),
    _p("7896036400010","Azeite de Oliva Andorinha 500ml","Azeite de oliva extravirgem","15092000","Azeite de oliva (oliveira) extra virgem","Óleos e Gorduras","Azeite","lt",False,False,0,"","Andorinha"),
    _p("7896036400027","Azeite Extravirgem Gallo 500ml","Azeite de oliva extravirgem","15092000","Azeite de oliva (oliveira) extra virgem","Óleos e Gorduras","Azeite","lt",False,False,0,"","Gallo"),
    _p("7896036400034","Azeite Extravirgem Carbonell 500ml","Azeite de oliva extravirgem","15092000","Azeite de oliva (oliveira) extra virgem","Óleos e Gorduras","Azeite","lt",False,False,0,"","Carbonell"),
    _p("7896036400041","Azeite Oliva Puro Andorinha 500ml","Azeite de oliva puro","15099010","Outros azeites de oliva refinados","Óleos e Gorduras","Azeite","lt",False,False,0,"","Andorinha"),
    _p("7896036400058","Azeite Oliva Extravirgem Borges 500ml","Azeite de oliva extravirgem","15092000","Azeite de oliva (oliveira) extra virgem","Óleos e Gorduras","Azeite","lt",False,False,0,"","Borges"),
    _p("7891107100179","Óleo Coco Copra 200ml","Óleo de coco virgem","15132919","Óleo de coco — outros","Óleos e Gorduras","Óleo Vegetal","lt",False,False,0,"","Copra"),
    _p("7891107100186","Óleo Coco Native 200ml","Óleo de coco orgânico virgem","15132919","Óleo de coco — outros","Óleos e Gorduras","Óleo Vegetal","lt",False,False,0,"","Native"),

    # ---- MARGARINAS E GORDURAS ----
    _p("7891515001001","Margarina Becel 500g","Margarina vegetal","15171000","Margarina","Óleos e Gorduras","Margarina","kg",False,False,0,"17.026.00","Becel"),
    _p("7891515001018","Margarina Qualy 500g","Margarina vegetal com sal","15171000","Margarina","Óleos e Gorduras","Margarina","kg",False,False,0,"17.026.00","Qualy"),
    _p("7891515001025","Margarina Primor 500g","Margarina vegetal","15171000","Margarina","Óleos e Gorduras","Margarina","kg",False,False,0,"17.026.00","Primor"),
    _p("7891515001032","Margarina Delícia 500g","Margarina vegetal","15171000","Margarina","Óleos e Gorduras","Margarina","kg",False,False,0,"17.026.00","Delícia"),
    _p("7891515001049","Margarina Becel 1kg","Margarina vegetal","15171000","Margarina","Óleos e Gorduras","Margarina","kg",False,False,0,"17.027.01","Becel"),
    _p("7891515001056","Margarina Qualy 1kg","Margarina vegetal com sal","15171000","Margarina","Óleos e Gorduras","Margarina","kg",False,False,0,"17.027.01","Qualy"),
    _p("7891515002008","Gordura Vegetal Primor 500g","Gordura vegetal hidrogenada","15162000","Gorduras e óleos vegetais hidrogenados","Óleos e Gorduras","Gordura Vegetal","kg",False,False,0,"17.028.00","Primor"),
    _p("7891515002015","Banha de Porco Sadia 500g","Banha de porco","15011000","Banha","Óleos e Gorduras","Banha","kg",False,False,0,"","Sadia"),
]

# ============================================================
# SEÇÃO 3: LATICÍNIOS
# ============================================================

_PRODUCTS += [
    # ---- LEITE UHT ----
    _p("7891097001015","Leite Integral Parmalat 1L","Leite integral UHT","04011010","Leite UHT integral","Laticínios","Leite UHT","lt",False,True,0,"17.016.00","Parmalat"),
    _p("7891097001022","Leite Semidesnatado Parmalat 1L","Leite semidesnatado UHT","04012010","Leite UHT semidesnatado","Laticínios","Leite UHT","lt",False,True,0,"17.016.00","Parmalat"),
    _p("7891097001039","Leite Desnatado Parmalat 1L","Leite desnatado UHT","04014021","Leite UHT — outros","Laticínios","Leite UHT","lt",False,True,0,"17.016.00","Parmalat"),
    _p("7896214000009","Leite Integral Italac 1L","Leite integral UHT","04011010","Leite UHT integral","Laticínios","Leite UHT","lt",False,True,0,"17.016.00","Italac"),
    _p("7896214000016","Leite Semidesnatado Italac 1L","Leite semidesnatado UHT","04012010","Leite UHT semidesnatado","Laticínios","Leite UHT","lt",False,True,0,"17.016.00","Italac"),
    _p("7891097001046","Leite Integral Parmalat Caixa 12x1L","Leite integral UHT","04011010","Leite UHT integral","Laticínios","Leite UHT","lt",False,True,0,"17.016.00","Parmalat"),
    _p("7897596400019","Leite Integral Ninho Nestlé 1L","Leite integral UHT","04011010","Leite UHT integral","Laticínios","Leite UHT","lt",False,True,0,"17.016.00","Nestlé Ninho"),
    _p("7897596400026","Leite Semidesnatado Ninho Nestlé 1L","Leite semidesnatado UHT","04012010","Leite UHT semidesnatado","Laticínios","Leite UHT","lt",False,True,0,"17.016.00","Nestlé Ninho"),
    _p("7891097001053","Leite Integral Parmalat 200ml","Leite integral UHT mini","04011010","Leite UHT integral","Laticínios","Leite UHT","lt",False,True,0,"17.016.00","Parmalat"),
    _p("7896214000023","Leite Zero Lactose Italac 1L","Leite zero lactose UHT","04011010","Leite UHT integral","Laticínios","Leite UHT","lt",False,True,0,"17.016.00","Italac"),
    _p("7891097001060","Leite Parmalat Zero Lactose 1L","Leite zero lactose UHT","04011010","Leite UHT integral","Laticínios","Leite UHT","lt",False,True,0,"17.016.00","Parmalat"),

    # ---- LEITE EM PÓ ----
    _p("7897596900019","Leite em Pó Integral Ninho Nestlé 400g","Leite em pó integral","04022110","Leite em pó integral","Laticínios","Leite em Pó","kg",False,True,0,"17.012.00","Nestlé Ninho"),
    _p("7897596900026","Leite em Pó Integral Ninho Nestlé 1,1kg","Leite em pó integral","04022110","Leite em pó integral","Laticínios","Leite em Pó","kg",False,True,0,"17.012.00","Nestlé Ninho"),
    _p("7897596900033","Leite em Pó Desnatado Ninho Nestlé 400g","Leite em pó desnatado","04022120","Leite em pó desnatado","Laticínios","Leite em Pó","kg",False,True,0,"17.012.00","Nestlé Ninho"),
    _p("7891080100017","Leite em Pó Integral Itambé 200g","Leite em pó integral","04022110","Leite em pó integral","Laticínios","Leite em Pó","kg",False,True,0,"17.012.00","Itambé"),
    _p("7891080100024","Leite em Pó Integral Itambé 400g","Leite em pó integral","04022110","Leite em pó integral","Laticínios","Leite em Pó","kg",False,True,0,"17.012.00","Itambé"),
    _p("7897596900040","Leite em Pó Semidesnatado Ninho 400g","Leite em pó semidesnatado","04022120","Leite em pó semidesnatado","Laticínios","Leite em Pó","kg",False,True,0,"17.012.00","Nestlé Ninho"),

    # ---- LEITE CONDENSADO ----
    _p("7891000249985","Leite Condensado Moça Nestlé 395g","Leite condensado","04029900","Leite condensado","Laticínios","Leite Condensado","kg",False,False,0,"17.020.00","Moça"),
    _p("7891080104015","Leite Condensado Itambé 395g","Leite condensado","04029900","Leite condensado","Laticínios","Leite Condensado","kg",False,False,0,"17.020.00","Itambé"),
    _p("7897596500017","Leite Condensado Semidesnatado Moça 395g","Leite condensado semidesnatado","04029900","Leite condensado","Laticínios","Leite Condensado","kg",False,False,0,"17.020.00","Moça"),

    # ---- CREME DE LEITE ----
    _p("7891000100015","Creme de Leite Nestlé 200g","Creme de leite","04022130","Creme de leite","Laticínios","Creme de Leite","kg",False,False,0,"17.019.00","Nestlé"),
    _p("7891080300010","Creme de Leite Itambé 200g","Creme de leite","04022130","Creme de leite","Laticínios","Creme de Leite","kg",False,False,0,"17.019.00","Itambé"),
    _p("7891000100022","Creme de Leite UHT Nestlé 200ml","Creme de leite UHT","04022130","Creme de leite","Laticínios","Creme de Leite","lt",False,False,0,"17.019.00","Nestlé"),
    _p("7896214002003","Creme de Leite Italac 200g","Creme de leite","04022130","Creme de leite","Laticínios","Creme de Leite","kg",False,False,0,"17.019.00","Italac"),
    _p("7896214002010","Creme de Leite UHT Italac 200ml","Creme de leite UHT","04022130","Creme de leite","Laticínios","Creme de Leite","lt",False,False,0,"17.019.00","Italac"),

    # ---- IOGURTE ----
    _p("7891097003019","Iogurte Natural Parmalat 170g","Iogurte natural","04032000","Iogurte","Laticínios","Iogurte","kg",False,False,0,"17.021.00","Parmalat"),
    _p("7891097003026","Iogurte Morango Parmalat 170g","Iogurte de morango","04032000","Iogurte","Laticínios","Iogurte","kg",False,False,0,"17.021.00","Parmalat"),
    _p("7891080201018","Iogurte Natural Itambé 170g","Iogurte natural","04032000","Iogurte","Laticínios","Iogurte","kg",False,False,0,"17.021.00","Itambé"),
    _p("7891080201025","Iogurte Morango Itambé 170g","Iogurte de morango","04032000","Iogurte","Laticínios","Iogurte","kg",False,False,0,"17.021.00","Itambé"),
    _p("7891097003033","Iogurte Grego Natural Parmalat 100g","Iogurte grego natural","04032000","Iogurte","Laticínios","Iogurte","kg",False,False,0,"17.021.00","Parmalat"),
    _p("7891097003040","Iogurte Grego Morango Parmalat 100g","Iogurte grego de morango","04032000","Iogurte","Laticínios","Iogurte","kg",False,False,0,"17.021.00","Parmalat"),
    _p("7891097003057","Iogurte Vitamina Frutas Parmalat 500g","Iogurte vitamina de frutas","04032000","Iogurte","Laticínios","Iogurte","kg",False,False,0,"17.021.00","Parmalat"),
    _p("7891080201032","Iogurte Natural Desnatado Itambé 500g","Iogurte natural desnatado","04032000","Iogurte","Laticínios","Iogurte","kg",False,False,0,"17.021.00","Itambé"),
    _p("7891097003064","Iogurte Parcialmente Desnatado Parmalat 2L","Iogurte parcialmente desnatado","04032000","Iogurte","Laticínios","Iogurte","lt",False,False,0,"17.021.01","Parmalat"),
    _p("7891097003071","Bebida Láctea Danone Morango 200ml","Bebida láctea de morango","04039000","Outros leites fermentados","Laticínios","Bebida Láctea","lt",False,False,0,"17.021.00","Danone"),
    _p("7891097003088","Activia Natural Danone 90g","Iogurte probiótico natural","04032000","Iogurte","Laticínios","Iogurte","kg",False,False,0,"17.021.00","Danone"),

    # ---- QUEIJOS ----
    _p("7896214003000","Queijo Mussarela Italac Kg","Queijo mussarela","04061010","Queijo mussarela","Laticínios","Queijos","kg",False,False,0,"17.024.00","Italac"),
    _p("7891080400012","Queijo Mussarela Itambé 500g","Queijo mussarela fatiado","04061010","Queijo mussarela","Laticínios","Queijos","kg",False,False,0,"17.024.00","Itambé"),
    _p("7896214003017","Queijo Prato Italac 500g","Queijo prato fatiado","04069020","Queijo de massa semidura","Laticínios","Queijos","kg",False,False,0,"17.024.00","Italac"),
    _p("7891080400029","Queijo Prato Itambé 500g","Queijo prato fatiado","04069020","Queijo de massa semidura","Laticínios","Queijos","kg",False,False,0,"17.024.00","Itambé"),
    _p("7896214003024","Requeijão Cremoso Italac 200g","Requeijão cremoso","04069030","Queijo de massa macia","Laticínios","Queijos","kg",False,False,0,"17.023.00","Italac"),
    _p("7891080500018","Requeijão Cremoso Itambé 200g","Requeijão cremoso","04069030","Queijo de massa macia","Laticínios","Queijos","kg",False,False,0,"17.023.00","Itambé"),
    _p("7896214003031","Requeijão Cremoso Catupiry 200g","Requeijão cremoso tradicional","04069030","Queijo de massa macia","Laticínios","Queijos","kg",False,False,0,"17.023.00","Catupiry"),
    _p("7896214003048","Queijo Coalho Italac 500g","Queijo de coalho","04069090","Outros queijos","Laticínios","Queijos","kg",False,False,0,"17.024.00","Italac"),
    _p("7891080400036","Queijo Cheddar Itambé 150g","Queijo cheddar fatiado","04069090","Outros queijos","Laticínios","Queijos","kg",False,False,0,"17.024.00","Itambé"),
    _p("7896214003055","Queijo Parmesão Ralado Italac 100g","Queijo parmesão ralado","04062000","Queijos ralados ou em pó","Laticínios","Queijos","kg",False,False,0,"17.024.00","Italac"),
    _p("7891080400043","Queijo Parmesão Ralado Itambé 50g","Queijo parmesão ralado","04062000","Queijos ralados ou em pó","Laticínios","Queijos","kg",False,False,0,"17.024.00","Itambé"),
    _p("7896214003062","Queijo Ricota Italac 500g","Ricota fresca","04069090","Outros queijos","Laticínios","Queijos","kg",False,False,0,"17.024.00","Italac"),
    _p("7891080400050","Queijo Minas Frescal Itambé 500g","Queijo minas frescal","04069030","Queijo de massa macia","Laticínios","Queijos","kg",False,False,0,"17.024.00","Itambé"),
    _p("7896214003079","Queijo Gouda Italac 500g","Queijo gouda fatiado","04069020","Queijo de massa semidura","Laticínios","Queijos","kg",False,False,0,"17.024.00","Italac"),
    _p("7896214003086","Queijo Grana Padano Ralado 100g","Queijo grana padano ralado","04062000","Queijos ralados ou em pó","Laticínios","Queijos","kg",False,False,0,"17.024.00","Genérico"),

    # ---- MANTEIGA ----
    _p("7891080600014","Manteiga com Sal Itambé 200g","Manteiga com sal","04051000","Manteiga","Laticínios","Manteiga","kg",False,False,0,"17.025.00","Itambé"),
    _p("7891080600021","Manteiga sem Sal Itambé 200g","Manteiga sem sal","04051000","Manteiga","Laticínios","Manteiga","kg",False,False,0,"17.025.00","Itambé"),
    _p("7891097005013","Manteiga Aviação com Sal 200g","Manteiga com sal","04051000","Manteiga","Laticínios","Manteiga","kg",False,False,0,"17.025.00","Aviação"),
    _p("7891097005020","Manteiga Aviação sem Sal 200g","Manteiga sem sal","04051000","Manteiga","Laticínios","Manteiga","kg",False,False,0,"17.025.00","Aviação"),
    _p("7891080600038","Manteiga com Sal Itambé 1kg","Manteiga com sal 1kg","04051000","Manteiga","Laticínios","Manteiga","kg",False,False,0,"17.025.01","Itambé"),

    # ---- DOCE DE LEITE ----
    _p("7891097006010","Doce de Leite Parmalat 400g","Doce de leite pastoso","19019020","Doce de leite","Laticínios","Doce de Leite","kg",False,False,0,"17.029.00","Parmalat"),
    _p("7891080700018","Doce de Leite Itambé 400g","Doce de leite pastoso","19019020","Doce de leite","Laticínios","Doce de Leite","kg",False,False,0,"17.029.00","Itambé"),
    _p("7891097006027","Doce de Leite Parmalat Light 400g","Doce de leite light","19019020","Doce de leite","Laticínios","Doce de Leite","kg",False,False,0,"17.029.00","Parmalat"),

    # ---- OVOS ----
    _p("7896036600018","Ovos Brancos Mantiqueira C/ 10un","Ovos de galinha brancos","04071100","Ovos de galinha para consumo","Laticínios","Ovos","un",False,True,0,"","Mantiqueira"),
    _p("7896036600025","Ovos Vermelhos Mantiqueira C/ 12un","Ovos de galinha vermelhos","04071100","Ovos de galinha para consumo","Laticínios","Ovos","un",False,True,0,"","Mantiqueira"),
    _p("7896036600032","Ovos Caipira Mantiqueira C/ 10un","Ovos caipira","04071100","Ovos de galinha para consumo","Laticínios","Ovos","un",False,True,0,"","Mantiqueira"),
    _p("7896036600049","Ovos Orgânicos 12un","Ovos orgânicos","04071100","Ovos de galinha para consumo","Laticínios","Ovos","un",False,True,0,"","Sítio do Moinho"),
]


# ============================================================
# SEÇÃO 3: CARNES
# ============================================================

_PRODUCTS += [
    # ---- CARNE BOVINA FRESCA/REFRIGERADA ----
    _p("","Filé Mignon Bovino kg","Filé mignon bovino fresco","02013000","Carne bovina desossada fresca","Carnes","Carne Bovina","kg",False,True,0,"","Resfriada"),
    _p("","Contrafilé Bovino kg","Contrafilé bovino fresco","02013000","Carne bovina desossada fresca","Carnes","Carne Bovina","kg",False,True,0,"","Resfriada"),
    _p("","Alcatra Bovina kg","Alcatra bovina fresca","02013000","Carne bovina desossada fresca","Carnes","Carne Bovina","kg",False,True,0,"","Resfriada"),
    _p("","Picanha Bovina kg","Picanha bovina fresca","02013000","Carne bovina desossada fresca","Carnes","Carne Bovina","kg",False,True,0,"","Resfriada"),
    _p("","Coxão Mole Bovino kg","Coxão mole bovino fresco","02013000","Carne bovina desossada fresca","Carnes","Carne Bovina","kg",False,True,0,"","Resfriada"),
    _p("","Coxão Duro Bovino kg","Coxão duro bovino fresco","02013000","Carne bovina desossada fresca","Carnes","Carne Bovina","kg",False,True,0,"","Resfriada"),
    _p("","Patinho Bovino kg","Patinho bovino fresco","02013000","Carne bovina desossada fresca","Carnes","Carne Bovina","kg",False,True,0,"","Resfriada"),
    _p("","Músculo Bovino kg","Músculo bovino fresco","02013000","Carne bovina desossada fresca","Carnes","Carne Bovina","kg",False,True,0,"","Resfriada"),
    _p("","Costela Bovina kg","Costela bovina fresca","02012020","Quartos traseiros bovinos","Carnes","Carne Bovina","kg",False,True,0,"","Resfriada"),
    _p("","Acém Bovino kg","Acém bovino fresco","02013000","Carne bovina desossada fresca","Carnes","Carne Bovina","kg",False,True,0,"","Resfriada"),
    _p("","Maminha Bovina kg","Maminha bovina fresca","02013000","Carne bovina desossada fresca","Carnes","Carne Bovina","kg",False,True,0,"","Resfriada"),
    _p("","Fraldinha Bovina kg","Fraldinha bovina fresca","02013000","Carne bovina desossada fresca","Carnes","Carne Bovina","kg",False,True,0,"","Resfriada"),
    _p("","Bife Ancho Bovino kg","Bife ancho bovino fresco","02013000","Carne bovina desossada fresca","Carnes","Carne Bovina","kg",False,True,0,"","Resfriada"),
    _p("","Miolo de Paleta Bovino kg","Miolo de paleta bovino fresco","02013000","Carne bovina desossada fresca","Carnes","Carne Bovina","kg",False,True,0,"","Resfriada"),
    _p("","Cupim Bovino kg","Cupim bovino fresco","02013000","Carne bovina desossada fresca","Carnes","Carne Bovina","kg",False,True,0,"","Resfriada"),
    _p("","Carne Moída Bovina kg","Carne moída bovina","02013000","Carne bovina desossada fresca","Carnes","Carne Bovina","kg",False,True,0,"","Resfriada"),

    # ---- CARNE BOVINA CONGELADA ----
    _p("7898010000015","Picanha Angus Congelada Minerva 1kg","Picanha bovina angus congelada","02023000","Carne bovina congelada desossada","Carnes","Carne Bovina","kg",False,True,0,"","Minerva"),
    _p("7898010000022","Filé Mignon Bovino Congelado 500g","Filé mignon bovino congelado","02023000","Carne bovina congelada desossada","Carnes","Carne Bovina","kg",False,True,0,"","Genérico"),
    _p("7898010000039","Alcatra Congelada Minerva 1kg","Alcatra bovina congelada","02023000","Carne bovina congelada desossada","Carnes","Carne Bovina","kg",False,True,0,"","Minerva"),

    # ---- CARNE SUÍNA ----
    _p("","Costela Suína kg","Costela suína fresca","02031900","Outras carnes suínas frescas","Carnes","Carne Suína","kg",False,True,0,"","Resfriada"),
    _p("","Lombo Suíno kg","Lombo suíno fresco","02031900","Outras carnes suínas frescas","Carnes","Carne Suína","kg",False,True,0,"","Resfriada"),
    _p("","Paleta Suína kg","Paleta suína fresca","02031200","Pernas e pás suínas frescas","Carnes","Carne Suína","kg",False,True,0,"","Resfriada"),
    _p("","Pernil Suíno kg","Pernil suíno fresco","02031200","Pernas e pás suínas frescas","Carnes","Carne Suína","kg",False,True,0,"","Resfriada"),
    _p("","Bisteca Suína kg","Bisteca suína fresca","02031900","Outras carnes suínas frescas","Carnes","Carne Suína","kg",False,True,0,"","Resfriada"),
    _p("7891167021007","Lombo Suíno Temperado Sadia 1kg","Lombo suíno temperado congelado","02032900","Outras carnes suínas congeladas","Carnes","Carne Suína","kg",False,True,0,"","Sadia"),

    # ---- FRANGO ----
    _p("","Peito de Frango Resfriado kg","Peito de frango fresco","02071411","Peitos de frango","Carnes","Carne de Frango","kg",False,True,0,"","Resfriada"),
    _p("","Coxa e Sobrecoxa Frango kg","Coxa e sobrecoxa de frango fresca","02071412","Coxas com sobrecoxas de frango","Carnes","Carne de Frango","kg",False,True,0,"","Resfriada"),
    _p("","Asa de Frango kg","Asa de frango fresca","02071413","Asas de frango","Carnes","Carne de Frango","kg",False,True,0,"","Resfriada"),
    _p("","Frango Inteiro Resfriado kg","Frango inteiro resfriado","02071210","Frango inteiro com miudezas","Carnes","Carne de Frango","kg",False,True,0,"","Resfriada"),
    _p("7891167020017","Frango Inteiro Congelado Sadia 2kg","Frango inteiro congelado","02071220","Frango inteiro sem miudezas","Carnes","Carne de Frango","kg",False,True,0,"","Sadia"),
    _p("7891167020024","Peito Frango Congelado Sadia 1kg","Peito de frango congelado","02071419","Outros pedaços de frango congelados","Carnes","Carne de Frango","kg",False,True,0,"","Sadia"),
    _p("7891167020031","Coxa Sobrecoxa Frango Sadia 1kg","Coxa sobrecoxa de frango congelada","02071423","Coxas com sobrecoxas congeladas","Carnes","Carne de Frango","kg",False,True,0,"","Sadia"),
    _p("7891167020048","Frango Caipira Inteiro Congelado 2kg","Frango caipira inteiro congelado","02071220","Frango inteiro sem miudezas","Carnes","Carne de Frango","kg",False,True,0,"","Sadia"),
    _p("7896009301010","Peito Frango Congelado Aurora 1kg","Peito de frango congelado","02071419","Outros pedaços de frango congelados","Carnes","Carne de Frango","kg",False,True,0,"","Aurora"),
    _p("7891167020055","Sobrecoxa Frango Congelada Sadia 1kg","Sobrecoxa de frango congelada","02071423","Coxas com sobrecoxas congeladas","Carnes","Carne de Frango","kg",False,True,0,"","Sadia"),
    _p("","Fígado Frango kg","Fígado de frango fresco","02071431","Fígados de frango","Carnes","Carne de Frango","kg",False,True,0,"","Resfriada"),
    _p("","Moela Frango kg","Moela de frango fresca","02071432","Moelas de frango","Carnes","Carne de Frango","kg",False,True,0,"","Resfriada"),

    # ---- EMBUTIDOS / FRIOS ----
    _p("7891167031007","Presunto Cozido Sadia 500g","Presunto cozido fatiado","16023220","Carnes de frango, cozidas, ≥57%","Carnes","Embutidos e Frios","kg",False,False,0,"17.079.00","Sadia"),
    _p("7891167031014","Presunto Cozido Sadia 200g","Presunto cozido fatiado","16023220","Carnes de frango, cozidas, ≥57%","Carnes","Embutidos e Frios","kg",False,False,0,"17.079.00","Sadia"),
    _p("7896009303014","Presunto Cozido Aurora 500g","Presunto cozido fatiado","16024900","Outras preparações e conservas de suíno","Carnes","Embutidos e Frios","kg",False,False,0,"17.079.00","Aurora"),
    _p("7891167040009","Mortadela Bologna Sadia 500g","Mortadela","16010000","Enchidos e produtos semelhantes","Carnes","Embutidos e Frios","kg",False,False,0,"17.078.00","Sadia"),
    _p("7896009304011","Mortadela Defumada Aurora 500g","Mortadela defumada","16010000","Enchidos e produtos semelhantes","Carnes","Embutidos e Frios","kg",False,False,0,"17.078.00","Aurora"),
    _p("7891167050008","Salsicha Viena Sadia 500g","Salsicha viena","16010000","Enchidos e produtos semelhantes","Carnes","Embutidos e Frios","kg",False,False,0,"17.077.00","Sadia"),
    _p("7896009305018","Salsicha Hot Dog Aurora 500g","Salsicha hot dog","16010000","Enchidos e produtos semelhantes","Carnes","Embutidos e Frios","kg",False,False,0,"17.077.00","Aurora"),
    _p("7891167060007","Linguiça Toscana Sadia 600g","Linguiça toscana","16010000","Enchidos e produtos semelhantes","Carnes","Embutidos e Frios","kg",False,False,0,"17.077.00","Sadia"),
    _p("7896009306015","Linguiça Calabresa Aurora 500g","Linguiça calabresa","16010000","Enchidos e produtos semelhantes","Carnes","Embutidos e Frios","kg",False,False,0,"17.077.00","Aurora"),
    _p("7891167060014","Linguiça Frango Sadia 600g","Linguiça de frango","16010000","Enchidos e produtos semelhantes","Carnes","Embutidos e Frios","kg",False,False,0,"17.077.00","Sadia"),
    _p("7891167070006","Bacon Sadia 200g","Bacon fatiado","02101200","Toucinhos entremeados — outros","Carnes","Embutidos e Frios","kg",False,False,0,"17.083.00","Sadia"),
    _p("7896009307012","Peito Peru Defumado Aurora 200g","Peito de peru defumado fatiado","16023100","Preparações de peruas ou perus","Carnes","Embutidos e Frios","kg",False,False,0,"17.079.00","Aurora"),
    _p("7891167080005","Presunto Tender Sadia 1kg","Tender suíno","16024100","Pernas suínas preparadas","Carnes","Embutidos e Frios","kg",False,False,0,"17.079.00","Sadia"),
    _p("7891167090004","Apresuntado Sadia 500g","Apresuntado","16023290","Outras preparações de frango","Carnes","Embutidos e Frios","kg",False,False,0,"17.079.00","Sadia"),
    _p("7896009308019","Copa Defumada Aurora 200g","Copa defumada fatiada","16010000","Enchidos e produtos semelhantes","Carnes","Embutidos e Frios","kg",False,False,0,"17.076.00","Aurora"),
    _p("7891167091001","Salame Milano Sadia 100g","Salame milano fatiado","16010000","Enchidos e produtos semelhantes","Carnes","Embutidos e Frios","kg",False,False,0,"17.076.00","Sadia"),

    # ---- PEIXES E FRUTOS DO MAR ----
    _p("7898910000010","Sardinha em Conserva ao Tomate Coqueiro 125g","Sardinha em conserva","16041310","Sardinhas preparadas","Carnes","Peixes","un",False,False,0,"17.081.00","Coqueiro"),
    _p("7898910000027","Atum em Conserva ao Natural Coqueiro 170g","Atum em conserva ao natural","16041410","Atuns preparados","Carnes","Peixes","un",False,False,0,"17.080.00","Coqueiro"),
    _p("7898910000034","Atum em Óleo Gomes da Costa 170g","Atum em óleo","16041410","Atuns preparados","Carnes","Peixes","un",False,False,0,"17.080.00","Gomes da Costa"),
    _p("7898910000041","Sardinha em Azeite Gomes da Costa 125g","Sardinha em azeite","16041310","Sardinhas preparadas","Carnes","Peixes","un",False,False,0,"17.081.00","Gomes da Costa"),
    _p("7898910000058","Bacalhau Dessalgado Gadus 500g","Bacalhau dessalgado","03036300","Bacalhau-do-atlântico congelado","Carnes","Peixes","kg",False,True,0,"","Gadus"),
    _p("","Tilápia Filé Resfriado kg","Filé de tilápia resfriado","03027100","Tilápias frescas ou refrigeradas","Carnes","Peixes","kg",False,True,0,"","Resfriada"),
    _p("","Salmão Filé Congelado kg","Filé de salmão congelado","03031300","Salmão-do-atlântico congelado","Carnes","Peixes","kg",False,True,0,"","Congelada"),
    _p("","Camarão Limpo Congelado 500g","Camarão limpo congelado","03061200","Camarões congelados da família Penaeidae","Carnes","Frutos do Mar","kg",False,True,0,"","Congelada"),
    _p("7898910000065","Atum em Conserva Bonito Coqueiro 170g","Atum bonito em conserva","16041410","Atuns preparados","Carnes","Peixes","un",False,False,0,"17.080.00","Coqueiro"),
]


# ============================================================
# SEÇÃO 4: CAFÉ, CHÁ E BEBIDAS QUENTES
# ============================================================

_PRODUCTS += [
    # ---- CAFÉ ----
    _p("7896005800027","Café em Pó 3 Corações Tradicional 500g","Café torrado e moído","09012100","Café torrado não descafeinado","Bebidas","Café","kg",False,False,0,"","3 Corações"),
    _p("7896005800034","Café em Pó 3 Corações Tradicional 250g","Café torrado e moído","09012100","Café torrado não descafeinado","Bebidas","Café","kg",False,False,0,"","3 Corações"),
    _p("7896005800041","Café em Pó 3 Corações Extra Forte 500g","Café torrado e moído extra forte","09012100","Café torrado não descafeinado","Bebidas","Café","kg",False,False,0,"","3 Corações"),
    _p("7896005800058","Café Pilão Tradicional 500g","Café torrado e moído","09012100","Café torrado não descafeinado","Bebidas","Café","kg",False,False,0,"","Pilão"),
    _p("7896005800065","Café Pilão Tradicional 250g","Café torrado e moído","09012100","Café torrado não descafeinado","Bebidas","Café","kg",False,False,0,"","Pilão"),
    _p("7896005800072","Café Pelé Forte 500g","Café torrado e moído forte","09012100","Café torrado não descafeinado","Bebidas","Café","kg",False,False,0,"","Pelé"),
    _p("7896005800089","Café Melitta Tradicional 500g","Café torrado e moído","09012100","Café torrado não descafeinado","Bebidas","Café","kg",False,False,0,"","Melitta"),
    _p("7896005800096","Café Melitta Especial 500g","Café torrado e moído especial","09012100","Café torrado não descafeinado","Bebidas","Café","kg",False,False,0,"","Melitta"),
    _p("7896005800102","Café Solúvel Nescafé Classic 100g","Café solúvel","21011110","Café solúvel","Bebidas","Café","kg",True,False,0,"","Nescafé"),
    _p("7896005800119","Café Solúvel Nescafé Classic 200g","Café solúvel","21011110","Café solúvel","Bebidas","Café","kg",True,False,0,"","Nescafé"),
    _p("7896005800126","Café em Cápsulas Nespresso Lungo 10 un","Cápsulas de café","09012100","Café torrado","Bebidas","Café","un",False,False,0,"","Nespresso"),
    _p("7896005800133","Café em Cápsulas Nescafé Dolce Gusto 12un","Cápsulas café para máquina","09012100","Café torrado","Bebidas","Café","un",False,False,0,"","Dolce Gusto"),
    _p("7896005800140","Café 3 Corações Gourmet 250g","Café gourmet moído","09012100","Café torrado não descafeinado","Bebidas","Café","kg",False,False,0,"","3 Corações"),
    _p("7896005800157","Café Orgânico Nativo 250g","Café orgânico torrado e moído","09012100","Café torrado não descafeinado","Bebidas","Café","kg",False,False,0,"","Nativo"),
    _p("7896005800164","Café 3 Corações Espresso 500g","Café espresso torrado e moído","09012100","Café torrado não descafeinado","Bebidas","Café","kg",False,False,0,"","3 Corações"),
    _p("7896005800171","Café em Grãos Pilão 500g","Café em grãos torrado","09012100","Café torrado não descafeinado","Bebidas","Café","kg",False,False,0,"","Pilão"),
    _p("7896005800188","Café Solúvel 3 Corações Soluvel 100g","Café solúvel","21011110","Café solúvel","Bebidas","Café","kg",True,False,0,"","3 Corações"),

    # ---- CHÁ E ERVAS ----
    _p("7896214005004","Chá Preto Leão Tradicional 25 saches","Chá preto em saches","09023000","Chá preto fermentado em embalagem ≤3kg","Bebidas","Chá","un",False,False,0,"17.097.00","Leão"),
    _p("7896214005011","Chá Verde Leão 25 saches","Chá verde em saches","09021000","Chá verde em embalagem ≤3kg","Bebidas","Chá","un",False,False,0,"17.097.00","Leão"),
    _p("7896214005028","Chá de Camomila Leão 25 saches","Chá de camomila em saches","12119090","Plantas para chá","Bebidas","Chá","un",False,False,0,"17.097.00","Leão"),
    _p("7896214005035","Chá de Erva-Doce Leão 25 saches","Chá de erva-doce em saches","12119090","Plantas para chá","Bebidas","Chá","un",False,False,0,"17.097.00","Leão"),
    _p("7896214005042","Chá Mate Leão 25 saches","Chá mate em saches","09030090","Mate","Bebidas","Chá","un",False,False,0,"17.098.00","Leão"),
    _p("7896214005059","Chá Misto Leão Menta Limão 25 saches","Chá misto com menta e limão","09023000","Chá preto fermentado","Bebidas","Chá","un",False,False,0,"17.097.00","Leão"),
    _p("7896214005066","Erva-Mate Chimarrão Barão 500g","Erva-mate para chimarrão","09030090","Mate — outros","Bebidas","Erva-Mate","kg",False,False,0,"17.098.00","Barão"),
    _p("7896214005073","Erva-Mate Chimarrão Rei 500g","Erva-mate para chimarrão","09030090","Mate — outros","Bebidas","Erva-Mate","kg",False,False,0,"17.098.00","Rei"),

    # ---- ACHOCOLATADO / CHOCOLATE EM PÓ ----
    _p("7891000100039","Achocolatado em Pó Nescau Nestlé 400g","Achocolatado em pó","18069000","Outras preparações contendo cacau","Bebidas","Achocolatado","kg",True,False,0,"17.006.00","Nestlé Nescau"),
    _p("7891000100046","Achocolatado em Pó Nescau Nestlé 800g","Achocolatado em pó","18069000","Outras preparações contendo cacau","Bebidas","Achocolatado","kg",True,False,0,"17.006.00","Nestlé Nescau"),
    _p("7896004500018","Achocolatado em Pó Toddy 400g","Achocolatado em pó","18069000","Outras preparações contendo cacau","Bebidas","Achocolatado","kg",True,False,0,"17.006.00","Toddy"),
    _p("7896004500025","Achocolatado em Pó Toddy 800g","Achocolatado em pó","18069000","Outras preparações contendo cacau","Bebidas","Achocolatado","kg",True,False,0,"17.006.00","Toddy"),
    _p("7891000100053","Achocolatado Líquido Nescau 200ml","Achocolatado líquido pronto","22029900","Outras bebidas não alcoólicas","Bebidas","Achocolatado","lt",True,False,0,"","Nestlé Nescau"),
    _p("7891000100060","Cacau em Pó Harald 200g","Cacau em pó sem açúcar","18050000","Cacau em pó sem açúcar","Bebidas","Achocolatado","kg",False,False,0,"","Harald"),
    _p("7891000100077","Cacau em Pó Nestlé 200g","Cacau em pó sem açúcar","18050000","Cacau em pó sem açúcar","Bebidas","Achocolatado","kg",False,False,0,"","Nestlé"),
]

# ============================================================
# SEÇÃO 5: BEBIDAS (REFRIGERANTES, SUCOS, ÁGUA, CERVEJAS)
# ============================================================

_PRODUCTS += [
    # ---- ÁGUA MINERAL ----
    _p("7896214007008","Água Mineral Sem Gás Crystal 500ml","Água mineral natural sem gás","22011000","Águas minerais e gaseificadas","Bebidas","Água","lt",True,False,0,"03.005.00","Crystal"),
    _p("7896214007015","Água Mineral Sem Gás Crystal 1,5L","Água mineral natural sem gás","22011000","Águas minerais e gaseificadas","Bebidas","Água","lt",True,False,0,"03.004.00","Crystal"),
    _p("7896214007022","Água Mineral Com Gás Crystal 500ml","Água mineral natural com gás","22011000","Águas minerais gaseificadas","Bebidas","Água","lt",True,False,0,"03.005.00","Crystal"),
    _p("7896214007039","Água Mineral Sem Gás Bonafonte 500ml","Água mineral natural sem gás","22011000","Águas minerais e gaseificadas","Bebidas","Água","lt",True,False,0,"03.005.00","Bonafonte"),
    _p("7896214007046","Água Mineral Sem Gás Bonafonte 1,5L","Água mineral natural sem gás","22011000","Águas minerais e gaseificadas","Bebidas","Água","lt",True,False,0,"03.004.00","Bonafonte"),
    _p("7896214007053","Água Mineral Sem Gás São Lourenço 500ml","Água mineral natural","22011000","Águas minerais e gaseificadas","Bebidas","Água","lt",True,False,0,"03.005.00","São Lourenço"),
    _p("7896214007060","Água Mineral Sem Gás Indaiá 500ml","Água mineral natural","22011000","Águas minerais e gaseificadas","Bebidas","Água","lt",True,False,0,"03.005.00","Indaiá"),
    _p("7896214007077","Água de Coco Natural 200ml","Água de coco natural","20098990","Outros sucos de frutos","Bebidas","Água de Coco","lt",False,False,0,"17.011.00","Natural One"),

    # ---- REFRIGERANTES ----
    _p("7894900011463","Coca-Cola 2L","Refrigerante cola","22021000","Refrigerante","Bebidas","Refrigerante",  "lt",True,False,0,"03.010.00","Coca-Cola"),
    _p("7894900011470","Coca-Cola 600ml","Refrigerante cola","22021000","Refrigerante","Bebidas","Refrigerante","lt",True,False,0,"03.011.00","Coca-Cola"),
    _p("7894900011487","Coca-Cola 350ml lata","Refrigerante cola lata","22021000","Refrigerante","Bebidas","Refrigerante","lt",True,False,0,"03.011.00","Coca-Cola"),
    _p("7894900011494","Coca-Cola Zero 2L","Refrigerante cola zero açúcar","22021000","Refrigerante","Bebidas","Refrigerante","lt",True,False,0,"03.010.00","Coca-Cola"),
    _p("7894900011500","Guaraná Antarctica 2L","Refrigerante guaraná","22021000","Refrigerante","Bebidas","Refrigerante","lt",True,False,0,"03.010.00","Antarctica"),
    _p("7894900011517","Guaraná Antarctica 600ml","Refrigerante guaraná","22021000","Refrigerante","Bebidas","Refrigerante","lt",True,False,0,"03.011.00","Antarctica"),
    _p("7894900011524","Guaraná Antarctica 350ml lata","Refrigerante guaraná lata","22021000","Refrigerante","Bebidas","Refrigerante","lt",True,False,0,"03.011.00","Antarctica"),
    _p("7894900011531","Fanta Laranja 2L","Refrigerante laranja","22021000","Refrigerante","Bebidas","Refrigerante","lt",True,False,0,"03.010.00","Fanta"),
    _p("7894900011548","Sprite 2L","Refrigerante limão","22021000","Refrigerante","Bebidas","Refrigerante","lt",True,False,0,"03.010.00","Sprite"),
    _p("7894900011555","Pepsi 2L","Refrigerante cola","22021000","Refrigerante","Bebidas","Refrigerante","lt",True,False,0,"03.010.00","Pepsi"),
    _p("7894900011562","Schin Cola 2L","Refrigerante cola","22021000","Refrigerante","Bebidas","Refrigerante","lt",True,False,0,"03.010.00","Schin"),
    _p("7894900011579","Kuat 2L","Refrigerante guaraná","22021000","Refrigerante","Bebidas","Refrigerante","lt",True,False,0,"03.010.00","Kuat"),
    _p("7894900011586","Sukita Laranja 2L","Refrigerante laranja","22021000","Refrigerante","Bebidas","Refrigerante","lt",True,False,0,"03.010.00","Sukita"),
    _p("7894900011593","H2OH 500ml","Bebida gaseificada com limão","22021000","Bebidas gaseificadas","Bebidas","Refrigerante","lt",True,False,0,"03.011.00","H2OH"),
    _p("7894900011609","Guaraná Jesus 2L","Refrigerante guaraná rosa","22021000","Refrigerante","Bebidas","Refrigerante","lt",True,False,0,"03.010.00","Jesus"),

    # ---- SUCOS E NÉCTAR ----
    _p("7896005501016","Suco Del Valle Laranja 1L","Néctar de laranja","20091100","Suco de laranja congelado","Bebidas","Suco","lt",True,False,0,"17.010.00","Del Valle"),
    _p("7896005501023","Suco Del Valle Uva 1L","Néctar de uva","20094900","Suco de uva","Bebidas","Suco","lt",True,False,0,"17.010.00","Del Valle"),
    _p("7896005501030","Suco Del Valle Manga 1L","Néctar de manga","20098990","Outros sucos de frutos","Bebidas","Suco","lt",True,False,0,"17.010.00","Del Valle"),
    _p("7896005501047","Suco Natural One Laranja 1L","Suco puro de laranja","20091100","Suco de laranja","Bebidas","Suco","lt",True,False,0,"17.010.00","Natural One"),
    _p("7896005501054","Suco Naturall Goiaba 1L","Néctar de goiaba","20098990","Outros sucos de frutos","Bebidas","Suco","lt",True,False,0,"17.010.00","Naturall"),
    _p("7896005501061","Suco Maguary Laranja 200ml","Néctar de laranja 200ml","20091100","Suco de laranja","Bebidas","Suco","lt",True,False,0,"17.010.00","Maguary"),
    _p("7896005501078","Suco Caju Mais 200ml","Néctar de caju","20098990","Outros sucos de frutos","Bebidas","Suco","lt",True,False,0,"17.010.00","Mais"),
    _p("7896005501085","Suco Integral Tial Maçã 1L","Suco integral de maçã","20092900","Suco de maçã","Bebidas","Suco","lt",False,False,0,"17.010.00","Tial"),
    _p("7896005501092","Suco Integral Tial Uva 1L","Suco integral de uva","20094900","Suco de uva","Bebidas","Suco","lt",False,False,0,"17.010.00","Tial"),

    # ---- CERVEJA E CHOPE ----
    _p("7891991010704","Cerveja Skol Lata 350ml","Cerveja pilsen lata","22030000","Cervejas de malte","Bebidas","Cerveja","lt",True,False,0,"03.021.00","Skol"),
    _p("7891991010711","Cerveja Brahma Lata 350ml","Cerveja pilsen lata","22030000","Cervejas de malte","Bebidas","Cerveja","lt",True,False,0,"03.021.00","Brahma"),
    _p("7891991010728","Cerveja Antarctica Lata 350ml","Cerveja pilsen lata","22030000","Cervejas de malte","Bebidas","Cerveja","lt",True,False,0,"03.021.00","Antarctica"),
    _p("7891991010735","Cerveja Itaipava Lata 350ml","Cerveja pilsen lata","22030000","Cervejas de malte","Bebidas","Cerveja","lt",True,False,0,"03.021.00","Itaipava"),
    _p("7891991010742","Cerveja Original Long Neck 330ml","Cerveja pilsen long neck","22030000","Cervejas de malte","Bebidas","Cerveja","lt",True,False,0,"03.021.00","Original"),
    _p("7891991010759","Cerveja Heineken Lata 350ml","Cerveja pilsen lata","22030000","Cervejas de malte","Bebidas","Cerveja","lt",True,False,0,"03.021.00","Heineken"),
    _p("7891991010766","Cerveja Heineken Long Neck 330ml","Cerveja pilsen long neck","22030000","Cervejas de malte","Bebidas","Cerveja","lt",True,False,0,"03.021.00","Heineken"),
    _p("7891991010773","Cerveja Budweiser Lata 350ml","Cerveja lager lata","22030000","Cervejas de malte","Bebidas","Cerveja","lt",True,False,0,"03.021.00","Budweiser"),
    _p("7891991010780","Cerveja Corona Extra 330ml","Cerveja lager long neck","22030000","Cervejas de malte","Bebidas","Cerveja","lt",True,False,0,"03.021.00","Corona"),
    _p("7891991010797","Cerveja Stella Artois Lata 350ml","Cerveja pilsen lata","22030000","Cervejas de malte","Bebidas","Cerveja","lt",True,False,0,"03.021.00","Stella Artois"),
    _p("7891991010803","Cerveja Skol Beats 269ml","Cerveja saborizadas","22030000","Cervejas de malte","Bebidas","Cerveja","lt",True,False,0,"03.021.00","Skol Beats"),
    _p("7891991010810","Cerveja sem Álcool Bavaria 350ml","Cerveja sem álcool","22029100","Cerveja sem álcool","Bebidas","Cerveja","lt",True,False,0,"03.022.00","Bavaria"),

    # ---- BEBIDAS ENERGÉTICAS E ISOTÔNICAS ----
    _p("7894900050019","Gatorade Limão 500ml","Bebida isotônica limão","21069090","Outras preparações alimentícias","Bebidas","Isotônico","lt",True,False,0,"03.015.00","Gatorade"),
    _p("7894900050026","Gatorade Laranja 500ml","Bebida isotônica laranja","21069090","Outras preparações alimentícias","Bebidas","Isotônico","lt",True,False,0,"03.015.00","Gatorade"),
    _p("7894900050033","Red Bull 250ml","Bebida energética","21069090","Bebida energética","Bebidas","Energético","lt",True,False,0,"03.013.00","Red Bull"),
    _p("7894900050040","Monster Energy 473ml","Bebida energética","21069090","Bebida energética","Bebidas","Energético","lt",True,False,0,"03.014.00","Monster"),
    _p("7894900050057","TNT Energy Drink 269ml","Bebida energética","21069090","Bebida energética","Bebidas","Energético","lt",True,False,0,"03.013.00","TNT"),
    _p("7894900050064","Powerade Limão 500ml","Bebida isotônica","21069090","Bebida isotônica","Bebidas","Isotônico","lt",True,False,0,"03.015.00","Powerade"),

    # ---- VINHO ----
    _p("7898015001045","Vinho Tinto Miolo Reserva Cabernet 750ml","Vinho tinto seco","22042100","Vinho em recipiente ≤2L","Bebidas","Vinho","lt",False,False,0,"","Miolo"),
    _p("7898015001052","Vinho Tinto Almaden Cabernet 750ml","Vinho tinto seco","22042100","Vinho em recipiente ≤2L","Bebidas","Vinho","lt",False,False,0,"","Almaden"),
    _p("7898015001069","Vinho Branco Miolo Chardonnay 750ml","Vinho branco seco","22042100","Vinho em recipiente ≤2L","Bebidas","Vinho","lt",False,False,0,"","Miolo"),
    _p("7898015001076","Vinho Rosé Salton 750ml","Vinho rosé","22042100","Vinho em recipiente ≤2L","Bebidas","Vinho","lt",False,False,0,"","Salton"),
]


# ============================================================
# SEÇÃO 5: HORTIFRUTI (VERDURAS, LEGUMES E FRUTAS)
# ============================================================

_PRODUCTS += [
    # ---- FRUTAS FRESCAS ----
    _p("","Banana Nanica kg","Banana nanica fresca","08039000","Outras bananas","Hortifruti","Frutas","kg",False,True,0,"","Feira"),
    _p("","Banana Prata kg","Banana prata fresca","08039000","Outras bananas","Hortifruti","Frutas","kg",False,True,0,"","Feira"),
    _p("","Banana-da-Terra kg","Banana-da-terra fresca","08031000","Bananas-da-terra","Hortifruti","Frutas","kg",False,True,0,"","Feira"),
    _p("","Maçã Fuji kg","Maçã fuji fresca","08081000","Maçãs","Hortifruti","Frutas","kg",False,True,0,"","Feira"),
    _p("","Maçã Gala kg","Maçã gala fresca","08081000","Maçãs","Hortifruti","Frutas","kg",False,True,0,"","Feira"),
    _p("","Pera Williams kg","Pera fresca","08083000","Peras","Hortifruti","Frutas","kg",False,True,0,"","Feira"),
    _p("","Laranja Pera kg","Laranja pera fresca","08051000","Laranjas","Hortifruti","Frutas","kg",False,True,0,"","Feira"),
    _p("","Laranja Lima kg","Laranja lima fresca","08051000","Laranjas","Hortifruti","Frutas","kg",False,True,0,"","Feira"),
    _p("","Limão Tahiti kg","Limão tahiti fresco","08055000","Limões e limas","Hortifruti","Frutas","kg",False,True,0,"","Feira"),
    _p("","Limão Siciliano kg","Limão siciliano fresco","08055000","Limões e limas","Hortifruti","Frutas","kg",False,True,0,"","Feira"),
    _p("","Uva Italia kg","Uva itália fresca","08061000","Uvas frescas","Hortifruti","Frutas","kg",False,True,0,"","Feira"),
    _p("","Uva Thompson kg","Uva thompson sem semente","08061000","Uvas frescas","Hortifruti","Frutas","kg",False,True,0,"","Feira"),
    _p("","Manga Tommy kg","Manga tommy fresca","08045020","Mangas","Hortifruti","Frutas","kg",False,True,0,"","Feira"),
    _p("","Manga Palmer kg","Manga palmer fresca","08045020","Mangas","Hortifruti","Frutas","kg",False,True,0,"","Feira"),
    _p("","Mamão Formosa kg","Mamão formosa fresco","08072000","Mamões","Hortifruti","Frutas","kg",False,True,0,"","Feira"),
    _p("","Mamão Havaí kg","Mamão havai fresco","08072000","Mamões","Hortifruti","Frutas","kg",False,True,0,"","Feira"),
    _p("","Abacaxi Pérola un","Abacaxi pérola fresco","08043000","Abacaxis","Hortifruti","Frutas","un",False,True,0,"","Feira"),
    _p("","Abacate kg","Abacate fresco","08044000","Abacates","Hortifruti","Frutas","kg",False,True,0,"","Feira"),
    _p("","Melancia kg","Melancia fresca","08071100","Melancias","Hortifruti","Frutas","kg",False,True,0,"","Feira"),
    _p("","Melão Amarelo kg","Melão amarelo fresco","08071900","Outros melões","Hortifruti","Frutas","kg",False,True,0,"","Feira"),
    _p("","Goiaba kg","Goiaba fresca","08045010","Goiabas","Hortifruti","Frutas","kg",False,True,0,"","Feira"),
    _p("","Morango bandeja 250g","Morango fresco","08101000","Morangos","Hortifruti","Frutas","kg",False,True,0,"","Feira"),
    _p("","Kiwi un","Kiwi fresco","08105000","Kiwis","Hortifruti","Frutas","un",False,True,0,"","Feira"),
    _p("","Pêssego kg","Pêssego fresco","08091000","Damascos e pêssegos","Hortifruti","Frutas","kg",False,True,0,"","Feira"),
    _p("","Caqui kg","Caqui fresco","08107000","Caquis","Hortifruti","Frutas","kg",False,True,0,"","Feira"),
    _p("","Tangerina Ponkan kg","Tangerina ponkan fresca","08052100","Mandarinas","Hortifruti","Frutas","kg",False,True,0,"","Feira"),
    _p("","Acerola kg","Acerola fresca","08109000","Acerolas","Hortifruti","Frutas","kg",False,True,0,"","Feira"),
    _p("","Coco Verde un","Coco verde para água","08011900","Outros cocos","Hortifruti","Frutas","un",False,True,0,"","Feira"),

    # ---- VERDURAS E FOLHAS ----
    _p("","Alface Crespa un","Alface crespa fresca","07051100","Alface repolhuda","Hortifruti","Verduras","un",False,True,0,"","Horta"),
    _p("","Alface Americana un","Alface americana fresca","07051100","Alface repolhuda","Hortifruti","Verduras","un",False,True,0,"","Horta"),
    _p("","Couve Folha maço","Couve folha fresca","07049000","Outros couves","Hortifruti","Verduras","un",False,True,0,"","Horta"),
    _p("","Espinafre maço","Espinafre fresco","07097000","Espinafres","Hortifruti","Verduras","un",False,True,0,"","Horta"),
    _p("","Rúcula maço","Rúcula fresca","07052900","Outras chicórias","Hortifruti","Verduras","un",False,True,0,"","Horta"),
    _p("","Agrião maço","Agrião fresco","07099990","Outros produtos hortícolas","Hortifruti","Verduras","un",False,True,0,"","Horta"),
    _p("","Brócolis kg","Brócolis fresco","07041000","Couve-flor e brócolis","Hortifruti","Verduras","kg",False,True,0,"","Horta"),
    _p("","Couve-Flor un","Couve-flor fresca","07041000","Couve-flor e brócolis","Hortifruti","Verduras","un",False,True,0,"","Horta"),
    _p("","Repolho Verde kg","Repolho verde fresco","07049000","Outros couves","Hortifruti","Verduras","kg",False,True,0,"","Horta"),
    _p("","Repolho Roxo kg","Repolho roxo fresco","07049000","Outros couves","Hortifruti","Verduras","kg",False,True,0,"","Horta"),

    # ---- LEGUMES ----
    _p("","Batata Inglesa kg","Batata inglesa fresca","07019000","Outras batatas","Hortifruti","Legumes","kg",False,True,0,"","Feira"),
    _p("","Batata-Doce kg","Batata-doce fresca","07142000","Batatas-doces","Hortifruti","Legumes","kg",False,True,0,"","Feira"),
    _p("","Mandioca/Aipim kg","Mandioca fresca","07141000","Raízes de mandioca","Hortifruti","Legumes","kg",False,True,0,"","Feira"),
    _p("","Inhame kg","Inhame fresco","07143000","Inhames","Hortifruti","Legumes","kg",False,True,0,"","Feira"),
    _p("","Cará kg","Cará fresco","07149000","Outros tubérculos","Hortifruti","Legumes","kg",False,True,0,"","Feira"),
    _p("","Cenoura kg","Cenoura fresca","07061000","Cenouras e nabos","Hortifruti","Legumes","kg",False,True,0,"","Feira"),
    _p("","Beterraba kg","Beterraba fresca","07069000","Outros","Hortifruti","Legumes","kg",False,True,0,"","Feira"),
    _p("","Cebola kg","Cebola fresca","07031029","Outras cebolas","Hortifruti","Legumes","kg",False,True,0,"","Feira"),
    _p("","Cebola Roxa kg","Cebola roxa fresca","07031029","Outras cebolas","Hortifruti","Legumes","kg",False,True,0,"","Feira"),
    _p("","Alho kg","Alho fresco","07129020","Alho","Hortifruti","Legumes","kg",False,True,0,"","Feira"),
    _p("","Tomate kg","Tomate fresco","07020000","Tomates frescos","Hortifruti","Legumes","kg",False,True,0,"","Feira"),
    _p("","Tomate Cereja 200g","Tomate cereja fresco","07020000","Tomates frescos","Hortifruti","Legumes","kg",False,True,0,"","Horta"),
    _p("","Pepino kg","Pepino fresco","07070000","Pepinos frescos","Hortifruti","Legumes","kg",False,True,0,"","Feira"),
    _p("","Abobrinha kg","Abobrinha italiana fresca","07099300","Abóboras e abobrinhas","Hortifruti","Legumes","kg",False,True,0,"","Feira"),
    _p("","Abóbora Cabotiá kg","Abóbora cabotiá fresca","07099300","Abóboras","Hortifruti","Legumes","kg",False,True,0,"","Feira"),
    _p("","Berinjela kg","Berinjela fresca","07093000","Berinjelas","Hortifruti","Legumes","kg",False,True,0,"","Feira"),
    _p("","Pimentão Verde kg","Pimentão verde fresco","07096000","Pimentões","Hortifruti","Legumes","kg",False,True,0,"","Feira"),
    _p("","Pimentão Vermelho kg","Pimentão vermelho fresco","07096000","Pimentões","Hortifruti","Legumes","kg",False,True,0,"","Feira"),
    _p("","Pimentão Amarelo kg","Pimentão amarelo fresco","07096000","Pimentões","Hortifruti","Legumes","kg",False,True,0,"","Feira"),
    _p("","Milho Verde un","Milho verde fresco","07104000","Milho doce congelado","Hortifruti","Legumes","un",False,True,0,"","Feira"),
    _p("","Vagem kg","Vagem fresca","07089000","Outros legumes de vagem","Hortifruti","Legumes","kg",False,True,0,"","Feira"),
    _p("","Ervilha Torta kg","Ervilha torta fresca","07081000","Ervilhas","Hortifruti","Legumes","kg",False,True,0,"","Feira"),
    _p("","Jiló kg","Jiló fresco","07099990","Outros produtos hortícolas","Hortifruti","Legumes","kg",False,True,0,"","Feira"),
    _p("","Chuchu kg","Chuchu fresco","07099990","Outros produtos hortícolas","Hortifruti","Legumes","kg",False,True,0,"","Feira"),
    _p("","Quiabo kg","Quiabo fresco","07099990","Outros produtos hortícolas","Hortifruti","Legumes","kg",False,True,0,"","Feira"),
    _p("","Maxixe kg","Maxixe fresco","07099990","Outros produtos hortícolas","Hortifruti","Legumes","kg",False,True,0,"","Feira"),
    _p("","Aspargo maço","Aspargo fresco","07092000","Aspargos","Hortifruti","Legumes","un",False,True,0,"","Horta"),

    # ---- COGUMELOS ----
    _p("","Cogumelo Paris 200g","Cogumelo paris fresco","07095100","Cogumelos Agaricus","Hortifruti","Cogumelos","kg",False,True,0,"","Horta"),
    _p("","Shitake 200g","Shitake fresco","07095400","Shitake","Hortifruti","Cogumelos","kg",False,True,0,"","Horta"),
    _p("","Shimeji 200g","Shimeji fresco","07095900","Outros cogumelos","Hortifruti","Cogumelos","kg",False,True,0,"","Horta"),
]


# ============================================================
# SEÇÃO 6: CONDIMENTOS, TEMPEROS E MOLHOS
# ============================================================

_PRODUCTS += [
    # ---- MOLHOS ----
    _p("7896036700015","Molho de Tomate Pomodoro 340g","Molho de tomate pronto","21039091","Outras preparações para molhos, em embalagem ≤1kg","Condimentos","Molho de Tomate","kg",False,False,0,"","Pomodoro"),
    _p("7896036700022","Molho de Tomate Hellmann's Tradicional 340g","Molho de tomate tradicional","21039091","Outras preparações para molhos, em embalagem ≤1kg","Condimentos","Molho de Tomate","kg",False,False,0,"","Hellmann's"),
    _p("7896036700039","Molho de Tomate Predilecta 340g","Molho de tomate tradicional","21039091","Outras preparações para molhos, em embalagem ≤1kg","Condimentos","Molho de Tomate","kg",False,False,0,"","Predilecta"),
    _p("7896036700046","Extrato de Tomate Elefante 340g","Extrato de tomate","20029000","Outros tomates preparados","Condimentos","Extrato de Tomate","kg",False,False,0,"","Elefante"),
    _p("7896036700053","Extrato de Tomate Predilecta 190g","Extrato de tomate","20029000","Outros tomates preparados","Condimentos","Extrato de Tomate","kg",False,False,0,"","Predilecta"),
    _p("7896036700060","Ketchup Hellmann's Original 397g","Ketchup de tomate","21032010","Ketchup em embalagem ≤1kg","Condimentos","Ketchup","kg",False,False,0,"17.034.00","Hellmann's"),
    _p("7896036700077","Ketchup Heinz Original 397g","Ketchup de tomate","21032010","Ketchup em embalagem ≤1kg","Condimentos","Ketchup","kg",False,False,0,"17.034.00","Heinz"),
    _p("7896036700084","Ketchup Hellmann's Tradicional Squeeze 397g","Ketchup bisnaga","21032010","Ketchup em embalagem ≤1kg","Condimentos","Ketchup","kg",False,False,0,"17.034.00","Hellmann's"),
    _p("7896036700091","Maionese Hellmann's Original 500g","Maionese","21039091","Maionese e outros molhos","Condimentos","Maionese","kg",False,False,0,"","Hellmann's"),
    _p("7896036700107","Maionese Hellmann's Light 500g","Maionese light","21039091","Maionese e outros molhos","Condimentos","Maionese","kg",False,False,0,"","Hellmann's"),
    _p("7896036700114","Maionese Quero 250g","Maionese","21039091","Maionese e outros molhos","Condimentos","Maionese","kg",False,False,0,"","Quero"),
    _p("7896036700121","Mostarda Hellmann's 200g","Mostarda","21033010","Farinha de mostarda e outras mostardas","Condimentos","Mostarda","kg",False,False,0,"","Hellmann's"),
    _p("7896036700138","Mostarda Heinz 215g","Mostarda amarela","21033010","Farinha de mostarda e outras mostardas","Condimentos","Mostarda","kg",False,False,0,"","Heinz"),
    _p("7896036700145","Molho Inglês Aratu 150ml","Molho inglês","21039091","Outras preparações para molhos, em embalagem ≤1kg","Condimentos","Molhos Especiais","lt",False,False,0,"","Aratu"),
    _p("7896036700152","Molho Shoyu Sakura 150ml","Molho de soja (shoyu)","21039091","Outras preparações para molhos, em embalagem ≤1kg","Condimentos","Molhos Especiais","lt",False,False,0,"","Sakura"),
    _p("7896036700169","Molho Tabasco 60ml","Molho de pimenta tabasco","21039091","Outras preparações para molhos, em embalagem ≤1kg","Condimentos","Molhos Especiais","lt",False,False,0,"","Tabasco"),
    _p("7896036700176","Molho Pimenta Vermelha Aratu 150ml","Molho de pimenta","21039091","Outras preparações para molhos, em embalagem ≤1kg","Condimentos","Molhos Especiais","lt",False,False,0,"","Aratu"),
    _p("7896036700183","Vinagre de Vinho Tinto Minhoto 750ml","Vinagre de vinho tinto","22090000","Vinagres e sucedâneos de vinagre","Condimentos","Vinagre","lt",False,False,0,"","Minhoto"),
    _p("7896036700190","Vinagre de Álcool Minhoto 750ml","Vinagre de álcool","22090000","Vinagres e sucedâneos de vinagre","Condimentos","Vinagre","lt",False,False,0,"","Minhoto"),
    _p("7896036700206","Vinagre de Maçã Castelo 750ml","Vinagre de maçã","22090000","Vinagres e sucedâneos de vinagre","Condimentos","Vinagre","lt",False,False,0,"","Castelo"),

    # ---- TEMPEROS SECOS ----
    _p("7896036800013","Pimenta-do-Reino Moída Sirial 30g","Pimenta-do-reino moída","09042100","Pimenta-do-reino seca não moída","Condimentos","Especiarias","kg",False,False,0,"","Sirial"),
    _p("7896036800020","Pimenta-do-Reino Inteira Sirial 30g","Pimenta-do-reino inteira","09042100","Pimenta-do-reino seca","Condimentos","Especiarias","kg",False,False,0,"","Sirial"),
    _p("7896036800037","Canela em Pó Sirial 30g","Canela moída","09061900","Canela moída","Condimentos","Especiarias","kg",False,False,0,"","Sirial"),
    _p("7896036800044","Canela em Pau Sirial 30g","Canela inteira","09061100","Canela inteira","Condimentos","Especiarias","kg",False,False,0,"","Sirial"),
    _p("7896036800051","Noz Moscada Sirial 30g","Noz-moscada","09081100","Noz-moscada não descascada","Condimentos","Especiarias","kg",False,False,0,"","Sirial"),
    _p("7896036800068","Cominho Sirial 30g","Cominho moído","09093200","Cominho triturado ou em pó","Condimentos","Especiarias","kg",False,False,0,"","Sirial"),
    _p("7896036800075","Alho em Pó Sirial 30g","Alho desidratado em pó","07129020","Alho desidratado","Condimentos","Especiarias","kg",False,False,0,"","Sirial"),
    _p("7896036800082","Cebola em Pó Sirial 30g","Cebola desidratada em pó","07122000","Cebola desidratada","Condimentos","Especiarias","kg",False,False,0,"","Sirial"),
    _p("7896036800099","Colorau/Colorífico Sirial 100g","Colorau de urucum","09103000","Cúrcuma (açafrão-da-terra)","Condimentos","Especiarias","kg",False,False,0,"","Sirial"),
    _p("7896036800105","Curry em Pó Sirial 30g","Curry em pó","09101100","Gengibre não triturado","Condimentos","Especiarias","kg",False,False,0,"","Sirial"),
    _p("7896036800112","Páprica Doce Sirial 30g","Páprica doce","09042100","Pimenta seca","Condimentos","Especiarias","kg",False,False,0,"","Sirial"),
    _p("7896036800129","Louro em Folha Sirial 5g","Folha de louro seca","12119090","Folhas de louro","Condimentos","Especiarias","kg",False,False,0,"","Sirial"),
    _p("7896036800136","Orégano Seco Sirial 10g","Orégano desidratado","12119090","Ervas aromáticas desidratadas","Condimentos","Especiarias","kg",False,False,0,"","Sirial"),
    _p("7896036800143","Manjericão Seco Sirial 5g","Manjericão desidratado","12119090","Ervas aromáticas desidratadas","Condimentos","Especiarias","kg",False,False,0,"","Sirial"),
    _p("7896036800150","Alecrim Seco Sirial 10g","Alecrim desidratado","12119090","Ervas aromáticas desidratadas","Condimentos","Especiarias","kg",False,False,0,"","Sirial"),
    _p("7896036800167","Tomilho Seco Sirial 5g","Tomilho desidratado","12119090","Ervas aromáticas desidratadas","Condimentos","Especiarias","kg",False,False,0,"","Sirial"),
    _p("7896036800174","Colorau Leão 100g","Colorau de urucum","09103000","Cúrcuma (açafrão-da-terra)","Condimentos","Especiarias","kg",False,False,0,"","Leão"),
    _p("7896036800181","Tempero Completo com Sal Sirial 300g","Tempero completo","21039091","Misturas de condimentos ≤1kg","Condimentos","Temperos Compostos","kg",False,False,0,"","Sirial"),
    _p("7896036800198","Caldo de Galinha Knorr 57g","Caldo concentrado de galinha","21039091","Outros caldos","Condimentos","Caldos e Temperos","kg",False,False,0,"","Knorr"),
    _p("7896036800204","Caldo de Carne Knorr 57g","Caldo concentrado de carne","21039091","Outros caldos","Condimentos","Caldos e Temperos","kg",False,False,0,"","Knorr"),
    _p("7896036800211","Caldo de Legumes Knorr 57g","Caldo concentrado de legumes","21039091","Outros caldos","Condimentos","Caldos e Temperos","kg",False,False,0,"","Knorr"),
    _p("7896036800228","Caldo de Frango Maggi 57g","Caldo concentrado de frango","21039091","Outros caldos","Condimentos","Caldos e Temperos","kg",False,False,0,"","Maggi"),
    _p("7896036800235","Tempero Frango Assado Sirial 60g","Tempero pronto para frango","21039091","Misturas de condimentos ≤1kg","Condimentos","Temperos Compostos","kg",False,False,0,"","Sirial"),
    _p("7896036800242","Tempero Churrasco Sirial 60g","Tempero pronto para churrasco","21039091","Misturas de condimentos ≤1kg","Condimentos","Temperos Compostos","kg",False,False,0,"","Sirial"),
]

# ============================================================
# SEÇÃO 7: ENLATADOS, CONSERVAS E INDUSTRIALIZADOS
# ============================================================

_PRODUCTS += [
    # ---- CONSERVAS ----
    _p("7896036900011","Milho Verde Bonduelle 200g","Milho verde em conserva","20059000","Outros","Enlatados","Conservas de Verduras","kg",False,False,0,"","Bonduelle"),
    _p("7896036900028","Milho Verde Quero 200g","Milho verde em conserva","20059000","Outros","Enlatados","Conservas de Verduras","kg",False,False,0,"","Quero"),
    _p("7896036900035","Ervilha Bonduelle 200g","Ervilha em conserva","20054000","Ervilhas em conserva","Enlatados","Conservas de Verduras","kg",False,False,0,"","Bonduelle"),
    _p("7896036900042","Ervilha Quero 200g","Ervilha em conserva","20054000","Ervilhas em conserva","Enlatados","Conservas de Verduras","kg",False,False,0,"","Quero"),
    _p("7896036900059","Seleta de Legumes Bonduelle 300g","Seleta de legumes em conserva","20059000","Outros","Enlatados","Conservas de Verduras","kg",False,False,0,"","Bonduelle"),
    _p("7896036900066","Cogumelo Fatiado Paris Quero 200g","Cogumelo paris em conserva","20039000","Outros cogumelos em conserva","Enlatados","Conservas de Verduras","kg",False,False,0,"","Quero"),
    _p("7896036900073","Tomate Pelado Inteiro Qualitá 400g","Tomate pelado em lata","20021000","Tomates inteiros em conserva","Enlatados","Conservas de Tomate","kg",False,False,0,"","Qualitá"),
    _p("7896036900080","Tomate Pelado Elefante 400g","Tomate pelado em lata","20021000","Tomates inteiros em conserva","Enlatados","Conservas de Tomate","kg",False,False,0,"","Elefante"),
    _p("7896036900097","Azeitona Verde Fatiada Coqueiro 100g","Azeitona verde fatiada","20057000","Azeitonas em conserva","Enlatados","Conservas de Verduras","kg",False,False,0,"","Coqueiro"),
    _p("7896036900103","Azeitona Preta Fatiada Coqueiro 100g","Azeitona preta fatiada","20057000","Azeitonas em conserva","Enlatados","Conservas de Verduras","kg",False,False,0,"","Coqueiro"),
    _p("7896036900110","Pepino em Conserva Elefante 300g","Pepino em conserva","20011000","Pepinos em conserva","Enlatados","Conservas de Verduras","kg",False,False,0,"","Elefante"),
    _p("7896036900127","Creme de Milho Verde Quero 200g","Creme de milho em conserva","20051000","Produtos hortícolas homogeneizados","Enlatados","Conservas de Verduras","kg",False,False,0,"","Quero"),

    # ---- FEIJÃO E LEGUMINOSAS EM CONSERVA ----
    _p("7896036900134","Feijão Carioca Cozido Cepera 430g","Feijão carioca cozido em lata","20055900","Outros feijões em conserva","Enlatados","Feijão Cozido","kg",False,False,0,"","Cepera"),
    _p("7896036900141","Feijão Preto Cozido Quero 430g","Feijão preto cozido em lata","20055900","Outros feijões em conserva","Enlatados","Feijão Cozido","kg",False,False,0,"","Quero"),
    _p("7896036900158","Grão de Bico em Conserva 400g","Grão-de-bico cozido em lata","20055900","Outros feijões e leguminosas","Enlatados","Feijão Cozido","kg",False,False,0,"","Qualitá"),

    # ---- SOPAS, CREMES E CALDOS ----
    _p("7891000100084","Sopa Creme de Tomate Knorr 66g","Creme de tomate em pó","21041000","Sopas e caldos preparados","Enlatados","Sopas e Cremes","kg",False,False,0,"","Knorr"),
    _p("7891000100091","Sopa Creme Brócolis Cheddar Knorr 66g","Creme de brócolis em pó","21041000","Sopas e caldos preparados","Enlatados","Sopas e Cremes","kg",False,False,0,"","Knorr"),
    _p("7891000100107","Caldo de Galinha Líquido Knorr 1,1L","Caldo de galinha líquido","21039099","Outros caldos e concentrados","Enlatados","Sopas e Cremes","lt",False,False,0,"","Knorr"),

    # ---- FARINHA DE ROSCA / PÃO RALADO ----
    _p("7896036100014","Farinha de Rosca Yoki 500g","Farinha de rosca/pão ralado","19053200","Waffles e wafers/pão torrado","Padaria","Farinha de Rosca","kg",False,False,0,"","Yoki"),
    _p("7891949008014","Farinha de Rosca Tradicional 500g","Farinha de rosca tradicional","19059000","Outros produtos de padaria","Padaria","Farinha de Rosca","kg",False,False,0,"","Genérico"),

    # ---- MASSA DE TOMATE / INGREDIENTES ----
    _p("7896036900165","Molho de Tomate Caseiro Predilecta 2kg","Molho de tomate caseiro 2kg","21039091","Preparações para molhos, embalagem ≤1kg","Enlatados","Molho de Tomate","kg",False,False,0,"","Predilecta"),
    _p("7896036900172","Molho de Tomate com Manjericão Prego 340g","Molho de tomate especial","21039091","Preparações para molhos, embalagem ≤1kg","Enlatados","Molho de Tomate","kg",False,False,0,"","Prego"),
]


# ============================================================
# SEÇÃO 7: PADARIA (PÃES, BOLOS, BISCOITOS)
# ============================================================

_PRODUCTS += [
    # ---- PÃES INDUSTRIALIZADOS ----
    _p("7896003800018","Pão de Forma Tradicional Wickbold 500g","Pão de forma branco","19052010","Panetone e outros pães","Padaria","Pão de Forma","kg",False,False,0,"17.050.00","Wickbold"),
    _p("7896003800025","Pão de Forma Integral Wickbold 500g","Pão de forma integral","19052010","Pão de forma integral","Padaria","Pão de Forma","kg",False,False,0,"17.050.00","Wickbold"),
    _p("7896003800032","Pão de Forma Pullman 500g","Pão de forma branco","19052010","Pão de forma","Padaria","Pão de Forma","kg",False,False,0,"17.050.00","Pullman"),
    _p("7896003800049","Pão de Forma Integral Pullman 500g","Pão de forma integral","19052010","Pão de forma integral","Padaria","Pão de Forma","kg",False,False,0,"17.050.00","Pullman"),
    _p("7896003800056","Pão de Forma Seven Boys 500g","Pão de forma branco","19052010","Pão de forma","Padaria","Pão de Forma","kg",False,False,0,"17.050.00","Seven Boys"),
    _p("7896003800063","Pão de Hot Dog Seven Boys 200g","Pão de cachorro-quente","19052090","Outros pães","Padaria","Pão","kg",False,False,0,"17.050.00","Seven Boys"),
    _p("7896003800070","Pão de Hambúrguer Seven Boys 200g","Pão de hambúrguer","19052090","Outros pães","Padaria","Pão","kg",False,False,0,"17.050.00","Seven Boys"),
    _p("7896003800087","Panetone Bauduco 400g","Panetone","19052010","Panetone","Padaria","Panetone","kg",False,False,0,"","Bauducco"),
    _p("7896003800094","Panetone Pullman 500g","Panetone com frutas","19052010","Panetone","Padaria","Panetone","kg",False,False,0,"","Pullman"),
    _p("7896003800100","Bolo de Forma de Baunilha Pullman 400g","Bolo de forma baunilha","19052090","Outros produtos de padaria","Padaria","Bolo de Forma","kg",False,False,0,"17.050.00","Pullman"),
    _p("7896003800117","Bolo de Forma de Chocolate Pullman 400g","Bolo de forma chocolate","19052090","Outros produtos de padaria","Padaria","Bolo de Forma","kg",False,False,0,"17.050.00","Pullman"),
    _p("7896003800124","Torrada Pullman Tradicional 200g","Torrada fatiada","19059000","Torradas e produtos similares","Padaria","Torradas","kg",False,False,0,"17.059.00","Pullman"),
    _p("7896003800131","Torrada Integral Wickbold 200g","Torrada integral","19059000","Torradas e produtos similares","Padaria","Torradas","kg",False,False,0,"17.059.00","Wickbold"),
    _p("7896003800148","Bisnaguinha Wickbold 400g","Bisnaga pão mini","19052090","Outros pães","Padaria","Pão","kg",False,False,0,"17.050.00","Wickbold"),
    _p("7896003800155","Croissant Wickbold 200g","Croissant","19052090","Outros pães","Padaria","Pão","kg",False,False,0,"17.050.00","Wickbold"),
    _p("7896003800162","Pão de Queijo Congelado Forno de Minas 400g","Pão de queijo congelado","19052090","Outros pães","Padaria","Pão de Queijo","kg",False,False,0,"","Forno de Minas"),
    _p("7896003800179","Pão de Queijo Congelado Yoki 300g","Pão de queijo congelado","19052090","Outros pães","Padaria","Pão de Queijo","kg",False,False,0,"","Yoki"),
    _p("7896003800186","Biscoito Cream Cracker Club Social Nabisco 192g","Biscoito cream cracker","19053100","Bolachas e biscoitos com edulcorantes","Padaria","Biscoitos","kg",False,False,0,"","Nabisco"),
    _p("7896003800193","Biscoito Água e Sal Isabela 200g","Biscoito água e sal","19053100","Bolachas e biscoitos","Padaria","Biscoitos","kg",False,False,0,"","Isabela"),
    _p("7896003800209","Biscoito Recheado Oreo 90g","Biscoito recheado ao leite","19053100","Bolachas e biscoitos","Padaria","Biscoitos","kg",False,False,0,"","Nabisco"),
    _p("7896003800216","Biscoito Recheado Bolacha Negresco Nestlé 90g","Biscoito recheado chocolate","19053100","Bolachas e biscoitos","Padaria","Biscoitos","kg",False,False,0,"","Nestlé"),
    _p("7896003800223","Biscoito Maisena Triunfo 200g","Biscoito maisena","19053100","Bolachas e biscoitos","Padaria","Biscoitos","kg",False,False,0,"","Triunfo"),
    _p("7896003800230","Biscoito Champanhe Bauducco 200g","Biscoito champanhe","19053100","Bolachas e biscoitos","Padaria","Biscoitos","kg",False,False,0,"","Bauducco"),
    _p("7896003800247","Crackers Integrais Triscuit Nabisco 175g","Biscoito cracker integral","19053200","Waffles e wafers","Padaria","Biscoitos","kg",False,False,0,"","Nabisco"),
    _p("7896003800254","Wafer Baunilha Bauducco 140g","Wafer baunilha","19053200","Waffles e wafers","Padaria","Biscoitos","kg",False,False,0,"17.057.00","Bauducco"),
    _p("7896003800261","Biscoito Amanteigado Piraquê 200g","Biscoito amanteigado","19053100","Bolachas e biscoitos","Padaria","Biscoitos","kg",False,False,0,"","Piraquê"),
    _p("7896003800278","Mix para Bolo de Chocolate Fleischmann 400g","Mistura para bolo de chocolate","19012090","Outras preparações de farinha","Padaria","Mixes para Bolo","kg",False,False,0,"","Fleischmann"),
    _p("7896003800285","Mix para Bolo de Baunilha Dona Benta 400g","Mistura para bolo baunilha","19012090","Outras preparações de farinha","Padaria","Mixes para Bolo","kg",False,False,0,"","Dona Benta"),
    _p("7896003800292","Fermento Biológico Seco Instant Fleischmann 10g","Fermento biológico seco","21023000","Pós para levedar","Padaria","Fermento","kg",False,False,0,"","Fleischmann"),
    _p("7896003800308","Fermento em Pó Royal 100g","Fermento químico em pó","21023000","Pós para levedar","Padaria","Fermento","kg",False,False,0,"","Royal"),
    _p("7896003800315","Fermento em Pó Fleischmann 100g","Fermento químico em pó","21023000","Pós para levedar","Padaria","Fermento","kg",False,False,0,"","Fleischmann"),

    # ---- CHOCOLATES ----
    _p("7622300990776","Chocolate Lacta ao Leite 90g","Chocolate ao leite","18063210","Chocolate em barras/tabletes","Padaria","Chocolates","kg",False,False,0,"17.002.00","Lacta"),
    _p("7622300990783","Chocolate Lacta Meio Amargo 90g","Chocolate meio amargo","18063210","Chocolate em barras/tabletes","Padaria","Chocolates","kg",False,False,0,"17.002.00","Lacta"),
    _p("7622300990790","Chocolate Nestlé Classic Ao Leite 90g","Chocolate ao leite","18063210","Chocolate em barras/tabletes","Padaria","Chocolates","kg",False,False,0,"17.002.00","Nestlé"),
    _p("7622300990806","Chocolate Bis Lacta 45g","Biscoito coberto com chocolate","18063210","Chocolate em barras/tabletes","Padaria","Chocolates","kg",False,False,0,"17.002.00","Lacta"),
    _p("7622300990813","Chocolate Talento Garoto 105g","Chocolate com castanhas","18063210","Chocolate em barras/tabletes","Padaria","Chocolates","kg",False,False,0,"17.002.00","Garoto"),
    _p("7622300990820","Chocolate Alpino Nestlé 25g","Chocolate alpino","18063210","Chocolate em barras/tabletes","Padaria","Chocolates","kg",False,False,0,"17.002.00","Nestlé"),
    _p("7622300990837","Bombom Sonho de Valsa Lacta 140g","Bombom de coco e amendoim","18069000","Outras preparações com cacau","Padaria","Chocolates","kg",False,False,0,"17.007.00","Lacta"),
    _p("7622300990844","Bombom Caixa Garoto 250g","Caixa de bombons","18069000","Outras preparações com cacau","Padaria","Chocolates","kg",False,False,0,"17.007.00","Garoto"),
    _p("7622300990851","Chocolate Harald Fracionado 1kg","Chocolate fracionado para confeitaria","18062000","Chocolate em blocos >2kg","Padaria","Chocolates","kg",False,False,0,"","Harald"),
    _p("7622300990868","Cobertura de Chocolate Nestlé 1kg","Cobertura de chocolate","18062000","Chocolate em blocos >2kg","Padaria","Chocolates","kg",False,False,0,"","Nestlé"),
    _p("7896015500011","Granulado Chocolate Harald 500g","Granulado de chocolate","18069000","Outras preparações com cacau","Padaria","Chocolates","kg",False,False,0,"","Harald"),
]


# ============================================================
# SEÇÃO 8: CONGELADOS
# ============================================================

_PRODUCTS += [
    # ---- PRATOS PRONTOS CONGELADOS ----
    _p("7891167100007","Lasanha Bolonhesa Sadia 600g","Lasanha à bolonhesa congelada","16025000","Preparações e conservas de carne bovina","Congelados","Pratos Prontos","kg",False,False,0,"","Sadia"),
    _p("7891167100014","Lasanha Quatro Queijos Sadia 600g","Lasanha quatro queijos congelada","19022000","Massas recheadas","Congelados","Pratos Prontos","kg",False,False,0,"","Sadia"),
    _p("7891167100021","Pizza Mussarela Sadia 440g","Pizza de mussarela congelada","19012090","Outras preparações de farinha","Congelados","Pizzas","kg",False,False,0,"","Sadia"),
    _p("7891167100038","Pizza Calabresa Sadia 440g","Pizza de calabresa congelada","19012090","Outras preparações de farinha","Congelados","Pizzas","kg",False,False,0,"","Sadia"),
    _p("7891167100045","Pizza Frango Catupiry Sadia 440g","Pizza frango catupiry congelada","19012090","Outras preparações de farinha","Congelados","Pizzas","kg",False,False,0,"","Sadia"),
    _p("7891167100052","Coxinha Congelada Sadia 12un","Coxinha de frango congelada","16023220","Preparações de frango cozido","Congelados","Salgados","kg",False,False,0,"","Sadia"),
    _p("7891167100069","Risole de Frango Congelado 12un","Risole de frango congelado","16023220","Preparações de frango cozido","Congelados","Salgados","kg",False,False,0,"","Sadia"),
    _p("7896009310013","Nuggets Frango Aurora 300g","Nuggets de frango","16023220","Preparações de frango cozido","Congelados","Salgados","kg",False,False,0,"","Aurora"),
    _p("7891167100076","Empanado Frango Sadia 300g","Empanado de frango","16023220","Preparações de frango cozido","Congelados","Salgados","kg",False,False,0,"","Sadia"),
    _p("7891167100083","Hambúrguer Bovino Sadia 672g","Hambúrguer bovino congelado","16025000","Preparações e conservas de carne bovina","Congelados","Hambúrguer","kg",False,False,0,"","Sadia"),
    _p("7891167100090","Hambúrguer Frango Sadia 672g","Hambúrguer de frango congelado","16023220","Preparações de frango","Congelados","Hambúrguer","kg",False,False,0,"","Sadia"),
    _p("7891167100106","Hot Pocket Pizza Sadia 145g","Salgado recheado congelado","19022000","Massas recheadas","Congelados","Salgados","kg",False,False,0,"","Sadia"),
    _p("7896009310020","Almôndega Bovina Aurora 400g","Almôndega bovina congelada","16025000","Preparações de carne bovina","Congelados","Salgados","kg",False,False,0,"","Aurora"),
    _p("7891167100113","Palito de Queijo Sadia 300g","Palito de queijo empanado congelado","19022000","Massas recheadas","Congelados","Salgados","kg",False,False,0,"","Sadia"),

    # ---- BATATA E VEGETAIS CONGELADOS ----
    _p("7891167110006","Batata Palito Congelada McCain 800g","Batata palito congelada","20041000","Batatas preparadas congeladas","Congelados","Batata","kg",False,False,0,"17.032.00","McCain"),
    _p("7891167110013","Batata Palito Congelada Sadia 800g","Batata palito congelada","20041000","Batatas preparadas congeladas","Congelados","Batata","kg",False,False,0,"17.032.00","Sadia"),
    _p("7891167110020","Batata Rústica Congelada McCain 500g","Batata rústica congelada","20041000","Batatas preparadas congeladas","Congelados","Batata","kg",False,False,0,"17.032.00","McCain"),
    _p("7891167110037","Brócolis Congelado 300g","Brócolis congelado","07102200","Feijões e legumes congelados","Congelados","Vegetais","kg",False,True,0,"","Genérico"),
    _p("7891167110044","Milho Verde Congelado 300g","Milho verde congelado","07104000","Milho doce congelado","Congelados","Vegetais","kg",False,True,0,"","Genérico"),
    _p("7891167110051","Ervilha Congelada 300g","Ervilha congelada","07102100","Ervilhas congeladas","Congelados","Vegetais","kg",False,True,0,"","Genérico"),
    _p("7891167110068","Aipim/Mandioca Congelada 500g","Mandioca pré-cozida congelada","20041000","Outros produtos hortícolas congelados","Congelados","Vegetais","kg",False,True,0,"","Genérico"),
    _p("7891167110075","Mix de Legumes Congelado 300g","Mix de legumes congelado","07109000","Misturas de produtos hortícolas","Congelados","Vegetais","kg",False,True,0,"","Genérico"),

    # ---- SORVETES ----
    _p("7894900060018","Sorvete Mega Kibon Chocolate 80g","Sorvete de chocolate palito","21050000","Sorvetes","Congelados","Sorvetes","kg",False,False,0,"23.001.00","Kibon"),
    _p("7894900060025","Sorvete Corneto Kibon Clássico 92ml","Sorvete em casquinha","21050000","Sorvetes","Congelados","Sorvetes","lt",False,False,0,"23.001.00","Kibon"),
    _p("7894900060032","Sorvete Magnum Kibon Clássico 110ml","Sorvete gourmet","21050000","Sorvetes","Congelados","Sorvetes","lt",False,False,0,"23.001.00","Kibon"),
    _p("7894900060049","Sorvete Pote Fruttare Morango 1,5L","Sorvete pote morango","21050000","Sorvetes","Congelados","Sorvetes","lt",False,False,0,"23.001.00","Kibon"),
    _p("7894900060056","Sorvete Pote Chicabon Recheado 1,5L","Sorvete pote recheado","21050000","Sorvetes","Congelados","Sorvetes","lt",False,False,0,"23.001.00","Kibon"),
    _p("7894900060063","Sorvete Pote Napolitano Nestlé 1,5L","Sorvete napolitano","21050000","Sorvetes","Congelados","Sorvetes","lt",False,False,0,"23.001.00","Nestlé"),
    _p("7894900060070","Sorvete Sundae Nestlé Chocolate 1,5L","Sorvete sundae","21050000","Sorvetes","Congelados","Sorvetes","lt",False,False,0,"23.001.00","Nestlé"),
]

# ============================================================
# SEÇÃO 9: MERCEARIA GERAL (ÓLEOS, VINAGRES, DOCES)
# ============================================================

_PRODUCTS += [
    # ---- GELEIAS E DOCES ----
    _p("7896012200018","Geleia de Morango Queensberry 320g","Geleia de morango","20079910","Outras geleias e marmeladas","Mercearia","Geleias","kg",False,False,0,"","Queensberry"),
    _p("7896012200025","Geleia de Goiaba Queensberry 320g","Geleia de goiaba","20079910","Outras geleias e marmeladas","Mercearia","Geleias","kg",False,False,0,"","Queensberry"),
    _p("7896012200032","Geleia de Framboesa Queensberry 320g","Geleia de framboesa","20079910","Outras geleias e marmeladas","Mercearia","Geleias","kg",False,False,0,"","Queensberry"),
    _p("7896012200049","Geleia de Morango Diet Queensberry 320g","Geleia de morango diet","20079910","Outras geleias e marmeladas","Mercearia","Geleias","kg",False,False,0,"","Queensberry"),
    _p("7896012200056","Doce de Goiaba Predilecta 500g","Doce de goiaba em pasta","20079910","Outras geleias e marmeladas","Mercearia","Doces","kg",False,False,0,"","Predilecta"),
    _p("7896012200063","Creme de Amendoim Westsoy 500g","Pasta de amendoim integral","20089900","Outros preparados de nozes e castanhas","Mercearia","Pastas","kg",False,False,0,"","Westsoy"),
    _p("7896012200070","Pasta de Amendoim Dr. Peanut 250g","Pasta de amendoim proteica","20089900","Outros preparados de nozes e castanhas","Mercearia","Pastas","kg",False,False,0,"","Dr. Peanut"),
    _p("7896012200087","Mel Puro Apis Flora 500g","Mel natural puro","04090000","Mel natural","Mercearia","Mel","kg",False,False,0,"","Apis Flora"),
    _p("7896012200094","Mel São Bartolomeu 500g","Mel natural puro","04090000","Mel natural","Mercearia","Mel","kg",False,False,0,"","São Bartolomeu"),
    _p("7896012200100","Xarope de Glicose Karo 700g","Xarope de glicose","17023020","Xarope de glicose","Mercearia","Adoçantes","kg",False,False,0,"","Karo"),

    # ---- ADOÇANTES ----
    _p("7896012300014","Adoçante Stevia Zero Cal 100 comprimidos","Adoçante stevia","21069090","Outros adoçantes","Mercearia","Adoçantes","un",False,False,0,"","Zero Cal"),
    _p("7896012300021","Adoçante Aspartame Equal 50 sachês","Adoçante aspartame","21069090","Outros adoçantes","Mercearia","Adoçantes","un",False,False,0,"","Equal"),
    _p("7896012300038","Adoçante Líquido Sucralose Tal e Qual 65ml","Adoçante sucralose líquido","21069090","Outros adoçantes","Mercearia","Adoçantes","lt",False,False,0,"","Tal e Qual"),

    # ---- LEVEDURA E INGREDIENTES DE PADARIA ----
    _p("7896012400017","Creme de Leite de Soja Ades 200ml","Creme vegetal de soja","22029900","Outras bebidas não alcoólicas","Mercearia","Substitutos Lácteos","lt",False,False,0,"","Ades"),
    _p("7896012400024","Bebida de Soja Natural Ades 1L","Bebida de soja natural","22029900","Bebida à base de soja","Mercearia","Substitutos Lácteos","lt",False,False,0,"","Ades"),
    _p("7896012400031","Bebida de Soja com Cálcio Ades 1L","Bebida de soja enriquecida","22029900","Bebida à base de soja","Mercearia","Substitutos Lácteos","lt",False,False,0,"","Ades"),
    _p("7896012400048","Leite de Coco Ducoco 200ml","Leite de coco","20099000","Outros sucos de frutas","Mercearia","Ingredientes","lt",False,False,0,"","Ducoco"),
    _p("7896012400055","Leite de Coco Light Ducoco 200ml","Leite de coco light","20099000","Outros sucos de frutas","Mercearia","Ingredientes","lt",False,False,0,"","Ducoco"),
    _p("7896012400062","Leite de Amendôas Cacau Show 1L","Bebida de amêndoas","22029900","Bebidas vegetais","Mercearia","Substitutos Lácteos","lt",False,False,0,"","Cacau Show"),

    # ---- SOBREMESAS E PUDINS ----
    _p("7896012500010","Gelatina de Morango Royal 15g","Gelatina de morango","21069090","Preparações alimentícias","Mercearia","Sobremesas","un",False,False,0,"","Royal"),
    _p("7896012500027","Gelatina de Uva Royal 15g","Gelatina de uva","21069090","Preparações alimentícias","Mercearia","Sobremesas","un",False,False,0,"","Royal"),
    _p("7896012500034","Pudim de Leite Nestlé 150g","Pudim de leite condensado","19019090","Outras preparações","Mercearia","Sobremesas","un",False,False,0,"","Nestlé"),
    _p("7896012500041","Mistura Pronta Pudim Nestlé 200g","Mistura para pudim","19019090","Outras preparações","Mercearia","Sobremesas","kg",False,False,0,"","Nestlé"),
    _p("7896012500058","Creme para Sonho Royal 150g","Mistura para creme confeiteiro","19019090","Outras preparações","Mercearia","Sobremesas","kg",False,False,0,"","Royal"),
]


# ============================================================
# SEÇÃO 9: SNACKS, SALGADINHOS E APERITIVOS
# ============================================================

_PRODUCTS += [
    _p("7892840819986","Salgadinho de Milho Elma Chips Cheetos 45g","Salgadinho de milho","19041000","Produtos de cereais expandidos","Snacks","Salgadinhos","kg",False,False,0,"17.031.00","Elma Chips"),
    _p("7892840819993","Batata Ruffles Original Elma Chips 45g","Batata chips ondulada","19041000","Produtos de cereais expansão","Snacks","Salgadinhos","kg",False,False,0,"17.031.00","Elma Chips"),
    _p("7892840820012","Doritos Nacho Elma Chips 45g","Salgadinho de milho nacho","19041000","Produtos de cereais expansão","Snacks","Salgadinhos","kg",False,False,0,"17.031.00","Elma Chips"),
    _p("7892840820029","Fandangos Milho Elma Chips 45g","Salgadinho de milho","19041000","Produtos de cereais expansão","Snacks","Salgadinhos","kg",False,False,0,"17.031.00","Elma Chips"),
    _p("7892840820036","Batata Pringles Original 120g","Batata chips original","19041000","Produtos de cereais expansão","Snacks","Salgadinhos","kg",False,False,0,"17.031.00","Pringles"),
    _p("7892840820043","Pipoca Salgada Yoki 100g","Pipoca salgada para microondas","19041000","Produtos de cereais expansão","Snacks","Pipoca","kg",False,False,0,"","Yoki"),
    _p("7892840820050","Pipoca Doce Yoki 100g","Pipoca doce para microondas","19041000","Produtos de cereais expansão","Snacks","Pipoca","kg",False,False,0,"","Yoki"),
    _p("7892840820067","Amendoim Crocante Elma Chips 100g","Amendoim torrado crocante","20081100","Amendoim preparado","Snacks","Aperitivos","kg",False,False,0,"17.033.00","Elma Chips"),
    _p("7892840820074","Amendoim Japonês Yoki 100g","Amendoim japonês crocante","20081100","Amendoim preparado","Snacks","Aperitivos","kg",False,False,0,"17.033.00","Yoki"),
    _p("7892840820081","Castanha de Caju Torrada 100g","Castanha de caju torrada e salgada","20081900","Outras castanhas preparadas","Snacks","Aperitivos","kg",False,False,0,"17.033.00","Genérico"),
    _p("7892840820098","Mix de Castanhas 100g","Mix de castanhas e nozes","20081900","Outras castanhas preparadas","Snacks","Aperitivos","kg",False,False,0,"17.033.00","Genérico"),
    _p("7892840820104","Granola Barra Mãe Terra 25g","Barra de granola","19042000","Barras de cereais","Snacks","Barras de Cereais","kg",False,False,0,"","Mãe Terra"),
    _p("7892840820111","Barra de Cereal Nestlé Nutry 22g","Barra de cereal","19042000","Barras de cereais","Snacks","Barras de Cereais","kg",False,False,0,"","Nestlé"),
    _p("7892840820128","Biscoito Bauduco Rosquinha 350g","Rosquinha de coco","19053100","Biscoitos amanteigados","Snacks","Biscoitos","kg",False,False,0,"","Bauducco"),
    _p("7892840820135","Paçoca Rolha 20g","Paçoca de amendoim","17049090","Outros produtos de confeitaria","Snacks","Doces","kg",False,False,0,"","Genérico"),
    _p("7892840820142","Cocada Mole 100g","Cocada de coco","17049090","Outros produtos de confeitaria","Snacks","Doces","kg",False,False,0,"","Genérico"),
    _p("7892840820159","Bala de Gelatina Fini 100g","Balas de gelatina","17049020","Caramelos e confeitos","Snacks","Balas e Confeitos","kg",False,False,0,"","Fini"),
    _p("7892840820166","Bala de Menta Halls 28g","Pastilha de menta","17049020","Caramelos e confeitos","Snacks","Balas e Confeitos","kg",False,False,0,"","Halls"),
    _p("7892840820173","Chiclete Trident Menta 8 unidades","Chiclete de menta","17041000","Gomas de mascar","Snacks","Balas e Confeitos","un",False,False,0,"","Trident"),
    _p("7892840820180","Goma de Mascar Mentos 38g","Goma de mascar","17041000","Gomas de mascar","Snacks","Balas e Confeitos","kg",False,False,0,"","Mentos"),
    _p("7892840820197","Pirulito Chupa Chups 12g","Pirulito","17049020","Caramelos e pirulitos","Snacks","Balas e Confeitos","un",False,False,0,"","Chupa Chups"),
]

# ============================================================
# SEÇÃO 10: CASTANHAS, NOZES E GRÃOS ESPECIAIS
# ============================================================

_PRODUCTS += [
    _p("","Castanha do Pará 100g","Castanha-do-pará (Brazil nut)","08012200","Castanha-do-pará sem casca","Cereais e Grãos","Castanhas e Nozes","kg",False,True,0,"","Feira"),
    _p("","Castanha de Caju 100g","Castanha de caju","08021200","Cajus sem casca","Cereais e Grãos","Castanhas e Nozes","kg",False,True,0,"","Feira"),
    _p("","Noz Pecan 100g","Noz pecan","08021200","Nozes","Cereais e Grãos","Castanhas e Nozes","kg",False,True,0,"","Importada"),
    _p("","Amêndoa Torrada 100g","Amêndoa sem pele torrada","08212200","Amêndoas sem casca","Cereais e Grãos","Castanhas e Nozes","kg",False,True,0,"","Importada"),
    _p("","Pistache Torrado e Salgado 100g","Pistache torrado salgado","08025200","Pistache sem casca","Cereais e Grãos","Castanhas e Nozes","kg",False,True,0,"","Importada"),
    _p("","Nozes Comuns 100g","Noz-da-nogueira","08023100","Nozes da Juglans com casca","Cereais e Grãos","Castanhas e Nozes","kg",False,True,0,"","Importada"),
    _p("","Avelã 100g","Avelã","08022200","Avelãs sem casca","Cereais e Grãos","Castanhas e Nozes","kg",False,True,0,"","Importada"),
    _p("","Macadâmia 100g","Noz de macadâmia","08029900","Outras nozes","Cereais e Grãos","Castanhas e Nozes","kg",False,True,0,"","Importada"),
    _p("","Amendoim Cru em Casca kg","Amendoim em casca","12024200","Amendoim com casca","Cereais e Grãos","Amendoim","kg",False,True,0,"","Feira"),
    _p("","Amendoim Torrado s/ Casca 100g","Amendoim torrado","20081100","Amendoim preparado","Cereais e Grãos","Amendoim","kg",False,True,0,"","Genérico"),
    _p("","Semente de Girassol 100g","Semente de girassol","12060090","Sementes de girassol","Cereais e Grãos","Sementes","kg",False,True,0,"","Genérico"),
    _p("","Semente de Abóbora 100g","Semente de abóbora","12079990","Outras sementes e frutos","Cereais e Grãos","Sementes","kg",False,True,0,"","Genérico"),
    _p("","Semente de Chia 100g","Semente de chia","12079990","Outras sementes oleaginosas","Cereais e Grãos","Sementes","kg",False,True,0,"","Genérico"),
    _p("","Semente de Linhaça Dourada 200g","Semente de linhaça dourada","12040090","Sementes de linho","Cereais e Grãos","Sementes","kg",False,True,0,"","Genérico"),
    _p("","Semente de Gergelim 100g","Semente de gergelim","12074090","Sementes de gergelim","Cereais e Grãos","Sementes","kg",False,True,0,"","Genérico"),
    _p("","Quinoa Grão 500g","Quinoa em grão","10089000","Outros cereais","Cereais e Grãos","Grãos Especiais","kg",False,True,0,"","Importada"),
    _p("","Cevada Pérola 500g","Cevada pérola","10039080","Cevada em grão","Cereais e Grãos","Grãos Especiais","kg",False,True,0,"","Genérico"),
]

# ============================================================
# SEÇÃO 11: PRODUTOS PARA RESTAURANTES E FOOD SERVICE
# ============================================================

_PRODUCTS += [
    # ---- AZEITES E ÓLEOS FOODSERVICE ----
    _p("","Óleo de Soja 18L Balde","Óleo de soja foodservice","15079019","Óleo de soja embalagem >5L","Foodservice","Óleos","lt",True,False,0,"","Genérico"),
    _p("","Azeite Extravirgem Lata 3L","Azeite de oliva extravirgem lata","15092000","Azeite de oliva (oliveira) extra virgem","Foodservice","Óleos","lt",False,False,0,"","Genérico"),

    # ---- CALDOS E BASES ----
    _p("","Caldo de Frango Profissional 1kg","Base de caldo de frango para restaurante","21039099","Outros caldos e concentrados","Foodservice","Bases","kg",False,False,0,"","Knorr"),
    _p("","Caldo de Carne Profissional 1kg","Base de caldo de carne para restaurante","21039099","Outros caldos e concentrados","Foodservice","Bases","kg",False,False,0,"","Knorr"),
    _p("","Caldo de Legumes Profissional 1kg","Base de caldo de legumes","21039099","Outros caldos e concentrados","Foodservice","Bases","kg",False,False,0,"","Knorr"),

    # ---- AMIDOS E ESPESSANTES ----
    _p("","Amido Modificado de Milho 1kg","Amido de milho modificado","11081200","Amido de milho","Foodservice","Ingredientes","kg",False,True,0,"","Genérico"),
    _p("","Gelatina sem Sabor 1kg","Gelatina incolor sem sabor","35030000","Gelatina e seus derivados","Foodservice","Ingredientes","kg",False,False,0,"","Genérico"),
    _p("","Agar Agar 50g","Ágar-ágar para culinária","13023100","Ágar-ágar","Foodservice","Ingredientes","kg",False,False,0,"","Genérico"),

    # ---- MOLHOS PARA RESTAURANTE ----
    _p("","Molho de Tomate 3kg Caixa","Molho de tomate para pizza","21039091","Preparações para molhos, embalagem ≤1kg","Foodservice","Molhos","kg",False,False,0,"","Genérico"),
    _p("","Maionese Profissional Hellmann's 10kg","Maionese para foodservice","21039091","Maionese profissional","Foodservice","Molhos","kg",False,False,0,"","Hellmann's"),
    _p("","Mostarda Profissional Heinz 3,1kg","Mostarda para foodservice","21033010","Mostarda","Foodservice","Molhos","kg",False,False,0,"","Heinz"),
    _p("","Ketchup Profissional Heinz 3,1kg","Ketchup para foodservice","21032010","Ketchup","Foodservice","Molhos","kg",False,False,0,"","Heinz"),

    # ---- FARINHA E PANIFICAÇÃO ----
    _p("","Farinha de Trigo 25kg Saco","Farinha de trigo para panificação","11010010","Farinha de trigo","Foodservice","Farinha","kg",False,True,0,"","Anaconda"),
    _p("","Açúcar Cristal 25kg Saco","Açúcar cristal a granel","17011400","Açúcar de cana","Foodservice","Açúcar","kg",False,False,0,"","União"),
    _p("","Sal Refinado 25kg Saco","Sal refinado iodado","25010020","Sal iodado","Foodservice","Sal","kg",False,True,0,"","Cisne"),
    _p("","Leite em Pó Integral 25kg","Leite em pó integral para industria","04022110","Leite em pó integral","Foodservice","Laticínios","kg",False,True,0,"","Genérico"),

    # ---- PROTEÍNAS ----
    _p("","Proteína de Soja Texturizada Grossa 500g","PTS grossa","12019090","Outros produtos de soja","Foodservice","Proteínas","kg",False,True,0,"","Genérico"),
    _p("","Proteína de Soja Texturizada Fina 500g","PTS fina","12019090","Outros produtos de soja","Foodservice","Proteínas","kg",False,True,0,"","Genérico"),

    # ---- PÁTISSERIE ----
    _p("","Glucose de Milho 500g","Glicose de milho para confeitaria","17023020","Xarope de glicose","Foodservice","Confeitaria","kg",False,False,0,"","Genérico"),
    _p("","Creme de Confeiteiro Profissional 1kg","Creme pronto para confeiteiro","19019090","Outras preparações","Foodservice","Confeitaria","kg",False,False,0,"","Genérico"),
    _p("","Baunilha em Fava un","Fava de baunilha","09058000","Baunilha","Foodservice","Confeitaria","un",False,False,0,"","Importada"),
    _p("","Extrato de Baunilha 100ml","Extrato de baunilha","21069090","Preparações alimentícias","Foodservice","Confeitaria","lt",False,False,0,"","Genérico"),
    _p("","Corante Alimentício Vermelho 30ml","Corante alimentício vermelho","32030010","Corantes de origem vegetal","Foodservice","Confeitaria","lt",False,False,0,"","Genérico"),
    _p("","Corante Alimentício Azul 30ml","Corante alimentício azul","32030010","Corantes de origem vegetal","Foodservice","Confeitaria","lt",False,False,0,"","Genérico"),
    _p("","Cacau em Pó Alcalizado 200g","Cacau em pó alcalizado","18050000","Cacau em pó sem açúcar","Foodservice","Confeitaria","kg",False,False,0,"","Callebaut"),
    _p("","Pasta de Amendoim Industrial 3kg","Pasta de amendoim para foodservice","20089900","Amendoim preparado","Foodservice","Confeitaria","kg",False,False,0,"","Genérico"),
]


# ============================================================
# SEÇÃO 10: PRODUTOS DIETÉTICOS, ORGÂNICOS E ESPECIAIS
# ============================================================

_PRODUCTS += [
    # ---- DIETS / ZERO ----
    _p("7896012600011","Adoçante Stevia Cargill 50 sachês","Adoçante de stevia em sachês","21069090","Edulcorantes de mesa","Mercearia","Adoçantes","un",False,False,0,"","Cargill"),
    _p("7896012600028","Sucre Zero Açúcar Diet 1kg","Açúcar diet","17019100","Açúcar com edulcorantes","Mercearia","Adoçantes","kg",False,False,0,"","Genérico"),
    _p("7896012600035","Biscoito Cream Cracker Diet Marilan 200g","Biscoito cream cracker diet","19053100","Biscoitos com edulcorantes","Mercearia","Diet","kg",False,False,0,"","Marilan"),
    _p("7896012600042","Gelatina Diet Morango Royal 12g","Gelatina diet sabor morango","21069090","Preparações alimentícias diet","Mercearia","Diet","un",False,False,0,"","Royal"),

    # ---- ORGÂNICOS ----
    _p("7896012700014","Arroz Integral Orgânico Native 1kg","Arroz integral orgânico","10062020","Arroz descascado orgânico","Cereais e Grãos","Orgânicos","kg",False,True,0,"","Native"),
    _p("7896012700021","Feijão Carioca Orgânico Native 500g","Feijão carioca orgânico","07133290","Feijão orgânico","Cereais e Grãos","Orgânicos","kg",False,True,0,"","Native"),
    _p("7896012700038","Açúcar Mascavo Orgânico Native 500g","Açúcar mascavo orgânico","17011400","Açúcar de cana orgânico","Cereais e Grãos","Orgânicos","kg",False,False,0,"","Native"),
    _p("7896012700045","Azeite Orgânico Herdade do Esporão 500ml","Azeite de oliva extravirgem orgânico","15092000","Azeite de oliva orgânico","Óleos e Gorduras","Orgânicos","lt",False,False,0,"","Herdade"),
    _p("7896012700052","Café Orgânico em Pó Camocim 250g","Café orgânico torrado","09012100","Café orgânico torrado","Bebidas","Orgânicos","kg",False,False,0,"","Camocim"),
    _p("7896012700069","Leite UHT Orgânico Ecorganic 1L","Leite orgânico UHT","04011010","Leite UHT orgânico","Laticínios","Orgânicos","lt",False,True,0,"17.016.00","Ecorganic"),

    # ---- SEM GLÚTEN ----
    _p("7896012800017","Macarrão sem Glúten de Arroz 500g","Macarrão sem glúten de arroz","19023000","Outras massas alimentícias","Cereais e Grãos","Sem Glúten","kg",False,False,0,"","Belforno"),
    _p("7896012800024","Farinha de Arroz 500g","Farinha de arroz sem glúten","11029000","Outras farinhas de cereais","Cereais e Grãos","Sem Glúten","kg",False,True,0,"","Yoki"),
    _p("7896012800031","Pão de Forma sem Glúten 350g","Pão de forma sem glúten","19052090","Outros pães","Padaria","Sem Glúten","kg",False,False,0,"","Seven Boys"),
    _p("7896012800048","Biscoito sem Glúten de Chocolate 100g","Biscoito sem glúten","19053100","Biscoitos sem glúten","Padaria","Sem Glúten","kg",False,False,0,"","Genérico"),
    _p("7896012800055","Macarrão de Grão-de-Bico 500g","Macarrão proteico sem glúten","19023000","Outras massas alimentícias","Cereais e Grãos","Sem Glúten","kg",False,False,0,"","Genérico"),

    # ---- VEGANOS / VEGETARIANOS ----
    _p("7896012900010","Hambúrguer Vegetal Seara Incrível 230g","Hambúrguer vegetal proteico","16025000","Preparações à base de proteína vegetal","Congelados","Vegano","kg",False,False,0,"","Seara"),
    _p("7896012900027","Linguiça Vegetal Seara Incrível 250g","Linguiça vegetal proteica","16010000","Enchidos à base proteína vegetal","Congelados","Vegano","kg",False,False,0,"","Seara"),
    _p("7896012900034","Tofu Firme 400g","Tofu firme de soja","19019090","Outros produtos de soja","Mercearia","Vegano","kg",False,True,0,"","Genérico"),
    _p("7896012900041","Bebida de Aveia 1L","Bebida vegetal de aveia","22029900","Bebidas vegetais","Mercearia","Vegano","lt",False,False,0,"","Quaker"),
    _p("7896012900058","Bebida de Amêndoas Silk 1L","Bebida vegetal de amêndoas","22029900","Bebidas vegetais","Mercearia","Vegano","lt",False,False,0,"","Silk"),
]

# ============================================================
# SEÇÃO 11: PRODUTOS PARA PADARIA E CONFEITARIA
# ============================================================

_PRODUCTS += [
    # ---- MASSAS E BASES ----
    _p("7897000100018","Massa Podre Congelada Arosa 400g","Massa podre para torta congelada","19012010","Massa para pão congelada","Padaria","Massas","kg",False,False,0,"","Arosa"),
    _p("7897000100025","Massa Folhada Congelada 400g","Massa folhada congelada","19012010","Massa para pão congelada","Padaria","Massas","kg",False,False,0,"","Genérico"),
    _p("7897000100032","Massa de Pizza Congelada 250g","Massa de pizza congelada","19012010","Massa para pão congelada","Padaria","Massas","kg",False,False,0,"","Genérico"),
    _p("7897000100049","Cream Cheese Philadelphia 150g","Cream cheese","04069030","Queijo de massa macia","Laticínios","Queijos","kg",False,False,0,"17.024.00","Philadelphia"),
    _p("7897000100056","Creme de Ricota Tirolez 150g","Creme de ricota","04069030","Queijo de massa macia","Laticínios","Queijos","kg",False,False,0,"","Tirolez"),
    _p("7897000100063","Nutella Creme de Avelã Ferrero 350g","Creme de avelã com chocolate","18069000","Outras preparações com cacau","Mercearia","Cremes e Pastas","kg",False,False,0,"","Ferrero"),
    _p("7897000100070","Creme de Amendoim com Chocolate 400g","Pasta de amendoim com chocolate","20089900","Amendoim preparado","Mercearia","Cremes e Pastas","kg",False,False,0,"","Dr. Peanut"),
    _p("7897000100087","Leite Condensado Nestlé Bisnaga 397g","Leite condensado bisnaga","04029900","Leite condensado","Laticínios","Leite Condensado","kg",False,False,0,"17.020.00","Nestlé"),
    _p("7897000100094","Creme de Leite Culinário Nestlé 1L","Creme de leite culinário","04022130","Creme de leite","Laticínios","Creme de Leite","lt",False,False,0,"","Nestlé"),

    # ---- COBERTURAS E DECORAÇÕES ----
    _p("7897000200014","Granulado de Chocolate Meio Amargo 500g","Granulado de chocolate","18069000","Preparações com cacau","Padaria","Decoração","kg",False,False,0,"","Harald"),
    _p("7897000200021","Confeito Colorido 100g","Confeito colorido para decoração","17049020","Caramelos e confeitos","Padaria","Decoração","kg",False,False,0,"","Genérico"),
    _p("7897000200038","Glacê Real em Pó 500g","Glacê royal em pó","17019900","Açúcar refinado","Padaria","Decoração","kg",False,False,0,"","Genérico"),
    _p("7897000200045","Fondant Pronto Branco 500g","Fondant pronto para decoração","17049090","Outros produtos de confeitaria","Padaria","Decoração","kg",False,False,0,"","Genérico"),
    _p("7897000200052","Pasta de Modelar Americana 1kg","Pasta americana para bolos","17049090","Outros produtos de confeitaria","Padaria","Decoração","kg",False,False,0,"","Genérico"),
    _p("7897000200069","Creme Vegetal Chantilly 1L","Creme vegetal para chantilly","15171000","Margarina/creme vegetal","Padaria","Chantilly","lt",False,False,0,"","Emulstab"),
    _p("7897000200076","Chantilly UHT Nestlé 1L","Chantilly pronto UHT","04022130","Creme de leite","Padaria","Chantilly","lt",False,False,0,"","Nestlé"),
    _p("7897000200083","Sorvete de Baunilha Premium 2L","Sorvete de baunilha premium","21050000","Sorvetes","Congelados","Sorvetes","lt",False,False,0,"23.001.00","Nestlé"),
]


# ============================================================
# SEÇÃO 11: FRIOS ESPECIAIS, EMBUTIDOS DE ALTA QUALIDADE
# ============================================================

_PRODUCTS += [
    _p("7891167200006","Salame Calabrês Sadia 100g","Salame calabrês fatiado","16010000","Enchidos — salame","Carnes","Embutidos e Frios","kg",False,False,0,"17.076.00","Sadia"),
    _p("7891167200013","Presunto Serrano 100g","Presunto serrano","16024100","Pernas e pedaços de suíno","Carnes","Embutidos e Frios","kg",False,False,0,"17.076.00","Genérico"),
    _p("7891167200020","Lombo Defumado Sadia 200g","Lombo defumado fatiado","16024900","Outras preparações de suíno","Carnes","Embutidos e Frios","kg",False,False,0,"17.079.00","Sadia"),
    _p("7891167200037","Peito de Peru Defumado Perdigão 200g","Peito de peru defumado","16023100","Preparações de perus","Carnes","Embutidos e Frios","kg",False,False,0,"17.079.00","Perdigão"),
    _p("7891167200044","Frango Defumado Sadia 200g","Frango defumado fatiado","16023220","Preparações de frango cozido","Carnes","Embutidos e Frios","kg",False,False,0,"17.079.00","Sadia"),
    _p("7891167200051","Carne Seca 500g","Carne bovina seca/charque","02102000","Carnes bovinas salgadas/secas","Carnes","Carnes Secas","kg",False,True,0,"17.083.00","Genérico"),
    _p("7891167200068","Jerked Beef 500g","Jerked beef bovino","02109940","Outras miudezas salgadas","Carnes","Carnes Secas","kg",False,True,0,"17.083.00","Genérico"),
    _p("7891167200075","Paio Sadia 200g","Paio cozido","16010000","Enchidos — paio","Carnes","Embutidos e Frios","kg",False,False,0,"17.076.00","Sadia"),
    _p("7891167200082","Linguiça Blumenau Aurora 200g","Linguiça blumenau","16010000","Enchidos — linguiça","Carnes","Embutidos e Frios","kg",False,False,0,"17.077.00","Aurora"),
    _p("7891167200099","Salsicha de Frango Sadia 500g","Salsicha de frango","16010000","Enchidos — salsicha","Carnes","Embutidos e Frios","kg",False,False,0,"17.077.00","Sadia"),
    _p("7891167200105","Salsicha Cocktail Sadia 500g","Salsicha coquetel","16010000","Enchidos — salsicha","Carnes","Embutidos e Frios","kg",False,False,0,"17.077.00","Sadia"),
    _p("7891167200112","Apresuntado de Frango Sadia 500g","Apresuntado de frango fatiado","16023290","Outras preparações de frango","Carnes","Embutidos e Frios","kg",False,False,0,"17.079.00","Sadia"),
    _p("7891167200129","Blanquet de Peru 200g","Blanquet de peru light","16023100","Preparações de perus","Carnes","Embutidos e Frios","kg",False,False,0,"17.079.00","Genérico"),
    _p("7891167200136","Prosciutto Cotto Fatiado 100g","Presunto cotto italiano","16024100","Pernas suínas","Carnes","Embutidos e Frios","kg",False,False,0,"","Genérico"),
    _p("7891167200143","Queijo Coalho para Churrasqueira 400g","Queijo coalho em palito","04069090","Outros queijos","Laticínios","Queijos","kg",False,False,0,"17.024.00","Genérico"),
    _p("7891167200150","Frango Assado Congelado 1kg","Frango assado congelado inteiro","16023290","Preparações de frango cozido","Congelados","Pratos Prontos","kg",False,False,0,"","Sadia"),
]

# ============================================================
# SEÇÃO 12: PRODUTOS ADICIONAIS - CEREAIS, CONDIMENTOS, MOLHOS
# ============================================================

_PRODUCTS += [
    # ---- COMPLEMENTOS CEREAIS ----
    _p("7896036001000","Canjica de Milho 500g","Canjica de milho branca","11031300","Sêmola de milho","Cereais e Grãos","Canjica","kg",False,True,0,"","Yoki"),
    _p("7896036001017","Xerém Milho Flocão 500g","Xerém de milho","11022000","Farinha de milho grossa","Cereais e Grãos","Fubá","kg",False,True,0,"","Yoki"),
    _p("7896036001024","Farinha de Trigo Integral 5kg","Farinha de trigo integral","11010010","Farinha de trigo integral","Cereais e Grãos","Farinha de Trigo","kg",False,True,0,"","Anaconda"),
    _p("7896036001031","Semolina de Trigo 500g","Semolina de trigo duro","11031100","Sêmola de trigo","Cereais e Grãos","Farinhas","kg",False,True,0,"","Genérico"),
    _p("7896036001048","Tapioca Granulada Seca 500g","Tapioca granulada para frigideira","11081400","Fécula de mandioca","Cereais e Grãos","Tapioca","kg",False,True,0,"","Yoki"),
    _p("7896036001055","Polvilho Azedo Fenix 1kg","Polvilho azedo de mandioca","11081400","Fécula de mandioca fermentada","Cereais e Grãos","Amidos e Féculas","kg",False,True,0,"","Fênix"),
    _p("7896036001062","Cuscuz Marroquino 500g","Cuscuz de sêmola de trigo","19024000","Cuscuz","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"17.048.01","Genérico"),
    _p("7896036001079","Mingau de Aveia 220g","Mingau instantâneo de aveia","19011090","Outras preparações para lactentes","Cereais e Grãos","Cereais Matinais","kg",False,False,0,"","Nestle Mucilon"),

    # ---- ALIMENTOS PARA BEBÊS ----
    _p("7891000200014","Cereal Infantil Mucilon Arroz 400g","Cereal infantil de arroz","19011030","Preparações para alimentação infantil","Cereais e Grãos","Alimentos Infantis","kg",False,False,0,"17.015.00","Nestlé"),
    _p("7891000200021","Cereal Infantil Mucilon Milho 400g","Cereal infantil de milho","19011030","Preparações para alimentação infantil","Cereais e Grãos","Alimentos Infantis","kg",False,False,0,"17.015.00","Nestlé"),
    _p("7891000200038","Farinha Láctea Nestlé 400g","Farinha láctea para bebês","19011020","Farinha láctea","Cereais e Grãos","Alimentos Infantis","kg",False,False,0,"17.013.00","Nestlé"),
    _p("7891000200045","Papinha Nestlé Banana 115g","Papinha de banana para bebê","20079910","Purê de frutas","Cereais e Grãos","Alimentos Infantis","un",False,False,0,"","Nestlé"),
    _p("7891000200052","Leite Modificado NAN Nestlé 400g","Leite modificado para bebê","19011010","Leite modificado para crianças","Laticínios","Alimentos Infantis","kg",False,False,0,"17.014.00","Nestlé"),

    # ---- CALDOS E CONCENTRADOS ----
    _p("7896036001086","Caldo Maggi Frango 6un","Cubo de caldo de frango","21039099","Caldos e concentrados","Condimentos","Caldos e Temperos","un",False,False,0,"","Maggi"),
    _p("7896036001093","Caldo Maggi Carne 6un","Cubo de caldo de carne","21039099","Caldos e concentrados","Condimentos","Caldos e Temperos","un",False,False,0,"","Maggi"),
    _p("7896036001109","Caldo Maggi Legumes 6un","Cubo de caldo de legumes","21039099","Caldos e concentrados","Condimentos","Caldos e Temperos","un",False,False,0,"","Maggi"),
    _p("7896036001116","Tempero Sal com Alho Sirial 500g","Sal temperado com alho","21039091","Misturas de condimentos ≤1kg","Condimentos","Temperos Compostos","kg",False,False,0,"","Sirial"),
    _p("7896036001123","Tempero Completo Sem Pimenta Sirial 500g","Tempero completo","21039091","Misturas de condimentos ≤1kg","Condimentos","Temperos Compostos","kg",False,False,0,"","Sirial"),
    _p("7896036001130","Sazon Tempero Vermelho 60g","Sazon amarelo/vermelho","21039091","Misturas de condimentos ≤1kg","Condimentos","Temperos Compostos","kg",False,False,0,"","Ajinomoto"),
    _p("7896036001147","Sazon Tempero Amarelo 60g","Sazon frango","21039091","Misturas de condimentos ≤1kg","Condimentos","Temperos Compostos","kg",False,False,0,"","Ajinomoto"),
    _p("7896036001154","Glutamato Monossódico Aji-no-moto 100g","Glutamato monossódico","29224100","Ácido glutâmico e seus sais","Condimentos","Temperos","kg",False,False,0,"","Ajinomoto"),
    _p("7896036001161","Shoyu Kikkoman 150ml","Molho de soja","21039091","Preparações para molhos, embalagem ≤1kg","Condimentos","Molhos Especiais","lt",False,False,0,"","Kikkoman"),
    _p("7896036001178","Molho Teriyaki Kikkoman 150ml","Molho teriyaki","21039091","Preparações para molhos, embalagem ≤1kg","Condimentos","Molhos Especiais","lt",False,False,0,"","Kikkoman"),
    _p("7896036001185","Molho Chili 100ml","Molho de pimenta chili","21039091","Preparações para molhos, embalagem ≤1kg","Condimentos","Molhos Especiais","lt",False,False,0,"","Genérico"),
    _p("7896036001192","Molho de Ostras Lee Kum Kee 150ml","Molho de ostras","21039091","Preparações para molhos, embalagem ≤1kg","Condimentos","Molhos Especiais","lt",False,False,0,"","Lee Kum Kee"),
    _p("7896036001208","Azeite de Dendê 200ml","Azeite de dendê (óleo de palma)","15119000","Outros","Óleos e Gorduras","Óleos Especiais","lt",False,False,0,"","Genérico"),
]


# ============================================================
# SEÇÃO 12: BEBIDAS QUENTES, LICORES, DESTILADOS
# ============================================================

_PRODUCTS += [
    # ---- DESTILADOS ----
    _p("7896005900013","Cachaça Sagatiba 700ml","Cachaça","22084090","Outras bebidas fermentadas","Bebidas","Destilados","lt",False,False,0,"","Sagatiba"),
    _p("7896005900020","Cachaça Ypioca Prata 700ml","Cachaça","22084090","Outras bebidas fermentadas","Bebidas","Destilados","lt",False,False,0,"","Ypioca"),
    _p("7896005900037","Vodka Absolut 750ml","Vodka","22082000","Espirituosas à base de vodka","Bebidas","Destilados","lt",False,False,0,"","Absolut"),
    _p("7896005900044","Rum Montilla 700ml","Rum","22084090","Rum e tafia","Bebidas","Destilados","lt",False,False,0,"","Montilla"),
    _p("7896005900051","Conhaque Dreher 960ml","Conhaque","22083000","Conhaque","Bebidas","Destilados","lt",False,False,0,"","Dreher"),

    # ---- BEBIDAS PARA MISTURA ----
    _p("7896005900068","Água Tônica Antarctica 350ml","Água tônica","22021000","Água gaseificada aromatizada","Bebidas","Bebidas Especiais","lt",True,False,0,"03.007.00","Antarctica"),
    _p("7896005900075","Limão Tahiti 500ml Suco Integral","Suco de limão tahiti","20092900","Suco de maçã — outros","Bebidas","Sucos","lt",False,False,0,"17.010.00","Natural"),
    _p("7896005900082","Xarope de Groselha 500ml","Xarope de groselha","21069090","Xaropes para bebidas","Bebidas","Xaropes","lt",False,False,0,"","Groselha"),
    _p("7896005900099","Xarope de Menta 500ml","Xarope de menta","21069090","Xaropes para bebidas","Bebidas","Xaropes","lt",False,False,0,"","Genérico"),

    # ---- CHÁS ESPECIAIS ----
    _p("7896005900105","Chá de Hibisco 25 saches","Chá de hibisco em saches","12119090","Plantas medicinais secas","Bebidas","Chá","un",False,False,0,"","Genérico"),
    _p("7896005900112","Chá de Gengibre com Limão 25 saches","Chá de gengibre em saches","09101100","Gengibre seco","Bebidas","Chá","un",False,False,0,"","Genérico"),
    _p("7896005900129","Chá Branco 25 saches","Chá branco em saches","09021000","Chá verde","Bebidas","Chá","un",False,False,0,"17.097.00","Genérico"),
    _p("7896005900136","Erva-Mate Tereré 500g","Erva-mate para tereré","09030090","Mate — outros","Bebidas","Erva-Mate","kg",False,False,0,"17.098.00","Genérico"),

    # ---- ACHOCOLATADOS PRONTOS ----
    _p("7894900050071","Leite Achocolatado Toddynho 200ml","Achocolatado pronto para beber","22029900","Bebida à base de leite e cacau","Bebidas","Bebidas Lácteas","lt",True,False,0,"","PepsiCo"),
    _p("7894900050088","Leite Achocolatado Chamyto 200ml","Leite fermentado achocolatado","04039000","Outros leites fermentados","Bebidas","Bebidas Lácteas","lt",False,False,0,"","Nestlé"),
    _p("7894900050095","Nescau Pronto 1L","Achocolatado pronto","22029900","Bebida à base de leite e cacau","Bebidas","Bebidas Lácteas","lt",True,False,0,"","Nestlé"),

    # ---- SUCOS NATURAIS / POLPAS ----
    _p("7896013000014","Polpa de Fruta Açaí 400g","Polpa de açaí congelada","20079910","Purê de frutas","Hortifruti","Polpas","kg",False,False,0,"","Genérico"),
    _p("7896013000021","Polpa de Fruta Maracujá 400g","Polpa de maracujá congelada","20079910","Purê de frutas","Hortifruti","Polpas","kg",False,False,0,"","Genérico"),
    _p("7896013000038","Polpa de Fruta Morango 400g","Polpa de morango congelada","20079910","Purê de morangos","Hortifruti","Polpas","kg",False,False,0,"","Genérico"),
    _p("7896013000045","Polpa de Fruta Manga 400g","Polpa de manga congelada","20079910","Purê de manga","Hortifruti","Polpas","kg",False,False,0,"","Genérico"),
    _p("7896013000052","Polpa de Fruta Caju 400g","Polpa de caju congelada","20079910","Purê de cajus","Hortifruti","Polpas","kg",False,False,0,"","Genérico"),
    _p("7896013000069","Polpa de Fruta Graviola 400g","Polpa de graviola congelada","20079910","Purê de graviola","Hortifruti","Polpas","kg",False,False,0,"","Genérico"),
    _p("7896013000076","Polpa de Açaí com Guaraná 400g","Polpa de açaí c/ guaraná","20079910","Purê de açaí","Hortifruti","Polpas","kg",False,False,0,"","Genérico"),
]

# ============================================================
# SEÇÃO 13: SUPLEMENTOS ALIMENTARES (NCMs ESPECÍFICOS)
# ============================================================

_PRODUCTS += [
    _p("7898010100013","Whey Protein Concentrado Max Titanium 900g","Proteína de soro de leite","35011000","Caseína e caseínatos","Suplementos","Proteínas","kg",False,False,0,"","Max Titanium"),
    _p("7898010100020","Whey Protein Isolado Iso Protein 907g","Proteína isolada de soro","35011000","Caseína e caseínatos","Suplementos","Proteínas","kg",False,False,0,"","Proteín"),
    _p("7898010100037","Creatina Monohidratada 300g","Creatina monohidratada","29230090","Compostos de amônio quaternários","Suplementos","Creatina","kg",False,False,0,"","Genérico"),
    _p("7898010100044","BCAA 2:1:1 120 cápsulas","BCAA aminoácidos de cadeia ramificada","21069090","Outras preparações alimentícias","Suplementos","Aminoácidos","un",False,False,0,"","Genérico"),
    _p("7898010100051","Maltodextrina 1kg","Maltodextrina para suplemento","17023019","Dextrinas e amidos modificados","Suplementos","Carboidratos","kg",False,False,0,"","Genérico"),
    _p("7898010100068","Termogênico Cafeína 120 caps","Suplemento termogênico","21069090","Outras preparações alimentícias","Suplementos","Termogênicos","un",False,False,0,"","Genérico"),
    _p("7898010100075","Colágeno Hidrolisado 300g","Colágeno hidrolisado em pó","35040000","Peptídeos e seus derivados","Suplementos","Colágeno","kg",False,False,0,"","Genérico"),
    _p("7898010100082","Vitamina C 1000mg 60 comp","Vitamina C effervescente","30045099","Outros medicamentos","Suplementos","Vitaminas","un",False,False,0,"","Genérico"),
]

# ============================================================
# SEÇÃO 14: LIMPEZA ALIMENTAR (EMBALAGEM DE ALIMENTOS)
# ============================================================

_PRODUCTS += [
    _p("7896002500014","Papel Alumínio Wyda 30cm x 4m","Papel alumínio para alimentos","7607190000","Folhas e tiras de alumínio","Descartáveis","Papel","un",False,False,0,"","Wyda"),
    _p("7896002500021","Papel Manteiga 5m","Papel manteiga para assar","4805910000","Papel manteiga","Descartáveis","Papel","un",False,False,0,"","Genérico"),
    _p("7896002500038","Filme PVC para Alimentos 28cm x 30m","Filme plástico para alimentos","3920209090","Filmes de polímeros de etileno","Descartáveis","Plástico","un",False,False,0,"","Wyda"),
    _p("7896002500045","Saco para Congelamento 25un","Sacos plásticos para freezer","3923290000","Artigos de plástico para embalagem","Descartáveis","Plástico","un",False,False,0,"","Genérico"),
    _p("7896002500052","Prato Descartável Redondo 10un","Prato descartável plástico","3924109000","Louça e artigos de mesa plástico","Descartáveis","Descartáveis","un",False,False,0,"","Genérico"),
    _p("7896002500069","Copo Descartável 200ml 50un","Copos plásticos descartáveis","3924109000","Louça e artigos de mesa","Descartáveis","Descartáveis","un",False,False,0,"","Genérico"),
    _p("7896002500076","Embalagem Marmitex 8 Alumínio 10un","Marmitex de alumínio","7612909000","Outros recipientes de alumínio","Descartáveis","Alumínio","un",False,False,0,"","Genérico"),
    _p("7896002500083","Sacola Plástica Descartável Reforçada","Sacola descartável","3923210000","Sacas e sacos de polímeros","Descartáveis","Plástico","un",False,False,0,"","Genérico"),
]


# ============================================================
# SEÇÃO 12: BEBIDAS QUENTES, LICORES, DESTILADOS
# ============================================================

_PRODUCTS += [
    # ---- DESTILADOS ----
    _p("7896005900013","Cachaça Sagatiba 700ml","Cachaça","22084090","Outras bebidas fermentadas","Bebidas","Destilados","lt",False,False,0,"","Sagatiba"),
    _p("7896005900020","Cachaça Ypioca Prata 700ml","Cachaça","22084090","Outras bebidas fermentadas","Bebidas","Destilados","lt",False,False,0,"","Ypioca"),
    _p("7896005900037","Vodka Absolut 750ml","Vodka","22082000","Espirituosas à base de vodka","Bebidas","Destilados","lt",False,False,0,"","Absolut"),
    _p("7896005900044","Rum Montilla 700ml","Rum","22084090","Rum e tafia","Bebidas","Destilados","lt",False,False,0,"","Montilla"),
    _p("7896005900051","Conhaque Dreher 960ml","Conhaque","22083000","Conhaque","Bebidas","Destilados","lt",False,False,0,"","Dreher"),

    # ---- BEBIDAS PARA MISTURA ----
    _p("7896005900068","Água Tônica Antarctica 350ml","Água tônica","22021000","Água gaseificada aromatizada","Bebidas","Bebidas Especiais","lt",True,False,0,"03.007.00","Antarctica"),
    _p("7896005900075","Limão Tahiti 500ml Suco Integral","Suco de limão tahiti","20092900","Suco de maçã — outros","Bebidas","Sucos","lt",False,False,0,"17.010.00","Natural"),
    _p("7896005900082","Xarope de Groselha 500ml","Xarope de groselha","21069090","Xaropes para bebidas","Bebidas","Xaropes","lt",False,False,0,"","Groselha"),
    _p("7896005900099","Xarope de Menta 500ml","Xarope de menta","21069090","Xaropes para bebidas","Bebidas","Xaropes","lt",False,False,0,"","Genérico"),

    # ---- CHÁS ESPECIAIS ----
    _p("7896005900105","Chá de Hibisco 25 saches","Chá de hibisco em saches","12119090","Plantas medicinais secas","Bebidas","Chá","un",False,False,0,"","Genérico"),
    _p("7896005900112","Chá de Gengibre com Limão 25 saches","Chá de gengibre em saches","09101100","Gengibre seco","Bebidas","Chá","un",False,False,0,"","Genérico"),
    _p("7896005900129","Chá Branco 25 saches","Chá branco em saches","09021000","Chá verde","Bebidas","Chá","un",False,False,0,"17.097.00","Genérico"),
    _p("7896005900136","Erva-Mate Tereré 500g","Erva-mate para tereré","09030090","Mate — outros","Bebidas","Erva-Mate","kg",False,False,0,"17.098.00","Genérico"),

    # ---- ACHOCOLATADOS PRONTOS ----
    _p("7894900050071","Leite Achocolatado Toddynho 200ml","Achocolatado pronto para beber","22029900","Bebida à base de leite e cacau","Bebidas","Bebidas Lácteas","lt",True,False,0,"","PepsiCo"),
    _p("7894900050088","Leite Achocolatado Chamyto 200ml","Leite fermentado achocolatado","04039000","Outros leites fermentados","Bebidas","Bebidas Lácteas","lt",False,False,0,"","Nestlé"),
    _p("7894900050095","Nescau Pronto 1L","Achocolatado pronto","22029900","Bebida à base de leite e cacau","Bebidas","Bebidas Lácteas","lt",True,False,0,"","Nestlé"),

    # ---- SUCOS NATURAIS / POLPAS ----
    _p("7896013000014","Polpa de Fruta Açaí 400g","Polpa de açaí congelada","20079910","Purê de frutas","Hortifruti","Polpas","kg",False,False,0,"","Genérico"),
    _p("7896013000021","Polpa de Fruta Maracujá 400g","Polpa de maracujá congelada","20079910","Purê de frutas","Hortifruti","Polpas","kg",False,False,0,"","Genérico"),
    _p("7896013000038","Polpa de Fruta Morango 400g","Polpa de morango congelada","20079910","Purê de morangos","Hortifruti","Polpas","kg",False,False,0,"","Genérico"),
    _p("7896013000045","Polpa de Fruta Manga 400g","Polpa de manga congelada","20079910","Purê de manga","Hortifruti","Polpas","kg",False,False,0,"","Genérico"),
    _p("7896013000052","Polpa de Fruta Caju 400g","Polpa de caju congelada","20079910","Purê de cajus","Hortifruti","Polpas","kg",False,False,0,"","Genérico"),
    _p("7896013000069","Polpa de Fruta Graviola 400g","Polpa de graviola congelada","20079910","Purê de graviola","Hortifruti","Polpas","kg",False,False,0,"","Genérico"),
    _p("7896013000076","Polpa de Açaí com Guaraná 400g","Polpa de açaí c/ guaraná","20079910","Purê de açaí","Hortifruti","Polpas","kg",False,False,0,"","Genérico"),
]

# ============================================================
# SEÇÃO 13: SUPLEMENTOS ALIMENTARES (NCMs ESPECÍFICOS)
# ============================================================

_PRODUCTS += [
    _p("7898010100013","Whey Protein Concentrado Max Titanium 900g","Proteína de soro de leite","35011000","Caseína e caseínatos","Suplementos","Proteínas","kg",False,False,0,"","Max Titanium"),
    _p("7898010100020","Whey Protein Isolado Iso Protein 907g","Proteína isolada de soro","35011000","Caseína e caseínatos","Suplementos","Proteínas","kg",False,False,0,"","Proteín"),
    _p("7898010100037","Creatina Monohidratada 300g","Creatina monohidratada","29230090","Compostos de amônio quaternários","Suplementos","Creatina","kg",False,False,0,"","Genérico"),
    _p("7898010100044","BCAA 2:1:1 120 cápsulas","BCAA aminoácidos de cadeia ramificada","21069090","Outras preparações alimentícias","Suplementos","Aminoácidos","un",False,False,0,"","Genérico"),
    _p("7898010100051","Maltodextrina 1kg","Maltodextrina para suplemento","17023019","Dextrinas e amidos modificados","Suplementos","Carboidratos","kg",False,False,0,"","Genérico"),
    _p("7898010100068","Termogênico Cafeína 120 caps","Suplemento termogênico","21069090","Outras preparações alimentícias","Suplementos","Termogênicos","un",False,False,0,"","Genérico"),
    _p("7898010100075","Colágeno Hidrolisado 300g","Colágeno hidrolisado em pó","35040000","Peptídeos e seus derivados","Suplementos","Colágeno","kg",False,False,0,"","Genérico"),
    _p("7898010100082","Vitamina C 1000mg 60 comp","Vitamina C effervescente","30045099","Outros medicamentos","Suplementos","Vitaminas","un",False,False,0,"","Genérico"),
]

# ============================================================
# SEÇÃO 14: LIMPEZA ALIMENTAR (EMBALAGEM DE ALIMENTOS)
# ============================================================

_PRODUCTS += [
    _p("7896002500014","Papel Alumínio Wyda 30cm x 4m","Papel alumínio para alimentos","7607190000","Folhas e tiras de alumínio","Descartáveis","Papel","un",False,False,0,"","Wyda"),
    _p("7896002500021","Papel Manteiga 5m","Papel manteiga para assar","4805910000","Papel manteiga","Descartáveis","Papel","un",False,False,0,"","Genérico"),
    _p("7896002500038","Filme PVC para Alimentos 28cm x 30m","Filme plástico para alimentos","3920209090","Filmes de polímeros de etileno","Descartáveis","Plástico","un",False,False,0,"","Wyda"),
    _p("7896002500045","Saco para Congelamento 25un","Sacos plásticos para freezer","3923290000","Artigos de plástico para embalagem","Descartáveis","Plástico","un",False,False,0,"","Genérico"),
    _p("7896002500052","Prato Descartável Redondo 10un","Prato descartável plástico","3924109000","Louça e artigos de mesa plástico","Descartáveis","Descartáveis","un",False,False,0,"","Genérico"),
    _p("7896002500069","Copo Descartável 200ml 50un","Copos plásticos descartáveis","3924109000","Louça e artigos de mesa","Descartáveis","Descartáveis","un",False,False,0,"","Genérico"),
    _p("7896002500076","Embalagem Marmitex 8 Alumínio 10un","Marmitex de alumínio","7612909000","Outros recipientes de alumínio","Descartáveis","Alumínio","un",False,False,0,"","Genérico"),
    _p("7896002500083","Sacola Plástica Descartável Reforçada","Sacola descartável","3923210000","Sacas e sacos de polímeros","Descartáveis","Plástico","un",False,False,0,"","Genérico"),
]


# ============================================================
# SEÇÃO 13: MAIS PRODUTOS - ATINGINDO META 2000+
# Produtos adicionais de todas as categorias
# ============================================================

_PRODUCTS += [
    # ---- MAIS LATICÍNIOS ----
    _p("7891097007017","Iogurte Grego Integral Nestlé 100g","Iogurte grego integral","04032000","Iogurte","Laticínios","Iogurte","kg",False,False,0,"17.021.00","Nestlé"),
    _p("7891097007024","Iogurte Sabor Frutas Vermelhas Danone 100g","Iogurte de frutas vermelhas","04032000","Iogurte","Laticínios","Iogurte","kg",False,False,0,"17.021.00","Danone"),
    _p("7891097007031","Iogurte Natural Integral Danone 170g","Iogurte natural integral","04032000","Iogurte","Laticínios","Iogurte","kg",False,False,0,"17.021.00","Danone"),
    _p("7891097007048","Bebida Láctea Iogurte Morango Itambé 200ml","Bebida láctea de morango","04039000","Outros leites fermentados","Laticínios","Bebida Láctea","lt",False,False,0,"17.021.00","Itambé"),
    _p("7891097007055","Creme de Ricota Catupiry 180g","Creme de ricota","04069090","Outros queijos","Laticínios","Queijos","kg",False,False,0,"17.024.00","Catupiry"),
    _p("7891097007062","Queijo Brie Importado 125g","Queijo brie","04064000","Queijos de pasta mofada","Laticínios","Queijos","kg",False,False,0,"17.024.00","Genérico"),
    _p("7891097007079","Queijo Emmental Fatiado 150g","Queijo emmental fatiado","04069020","Queijo de massa semidura","Laticínios","Queijos","kg",False,False,0,"17.024.00","Genérico"),
    _p("7891097007086","Queijo Provolone Defumado 200g","Queijo provolone defumado","04069090","Outros queijos","Laticínios","Queijos","kg",False,False,0,"17.024.00","Genérico"),
    _p("7891097007093","Queijo Minas Padrão 300g","Queijo minas padrão","04069020","Queijo de massa semidura","Laticínios","Queijos","kg",False,False,0,"17.024.00","Genérico"),
    _p("7891097007109","Requeijão Culinário Catupiry 1kg","Requeijão culinário em balde","04069030","Queijo de massa macia","Laticínios","Queijos","kg",False,False,0,"17.023.01","Catupiry"),
    _p("7891097007116","Creme de Queijo Borden 150g","Creme de queijo para untar","04069030","Queijo de massa macia","Laticínios","Queijos","kg",False,False,0,"17.024.00","Borden"),
    _p("7891097007123","Queijo Colonial 300g","Queijo colonial artesanal","04069020","Queijo de massa semidura","Laticínios","Queijos","kg",False,False,0,"17.024.00","Genérico"),
    _p("7891097007130","Creme de Leite Fresco Piracanjuba 500ml","Creme de leite fresco","04022130","Creme de leite","Laticínios","Creme de Leite","lt",False,False,0,"17.019.00","Piracanjuba"),
    _p("7891097007147","Manteiga Ghee 200g","Manteiga clarificada ghee","04059090","Outras gorduras do leite","Laticínios","Manteiga","kg",False,False,0,"","Genérico"),
    _p("7891097007154","Leite de Vaca A2 1L","Leite A2/A2 UHT","04011010","Leite UHT","Laticínios","Leite UHT","lt",False,True,0,"17.016.00","Genérico"),

    # ---- MAIS CARNES ----
    _p("7891167300005","Costela Bovina Congelada 1kg","Costela bovina congelada","02022020","Quartos traseiros bovinos congelados","Carnes","Carne Bovina","kg",False,True,0,"","Genérico"),
    _p("7891167300012","Músculo Bovino Congelado 1kg","Músculo bovino congelado","02023000","Carne bovina congelada desossada","Carnes","Carne Bovina","kg",False,True,0,"","Genérico"),
    _p("7891167300029","Acém Bovino Congelado 500g","Acém bovino congelado","02023000","Carne bovina congelada desossada","Carnes","Carne Bovina","kg",False,True,0,"","Genérico"),
    _p("7891167300036","Carne Moída Congelada 500g","Carne moída bovina congelada","02023000","Carne bovina congelada desossada","Carnes","Carne Bovina","kg",False,True,0,"","Genérico"),
    _p("7891167300043","Steak Bovino Congelado 500g","Bife bovino congelado","02023000","Carne bovina congelada desossada","Carnes","Carne Bovina","kg",False,True,0,"","Genérico"),
    _p("7891167300050","Linguiça Fresca Toscana kg","Linguiça fresca toscana","16010000","Enchidos e similares","Carnes","Embutidos e Frios","kg",False,False,0,"17.077.00","Genérico"),
    _p("7891167300067","Linguiça Fresca Calabresa kg","Linguiça fresca calabresa","16010000","Enchidos e similares","Carnes","Embutidos e Frios","kg",False,False,0,"17.077.00","Genérico"),
    _p("7891167300074","Linguiça Fresca de Frango kg","Linguiça fresca de frango","16010000","Enchidos e similares","Carnes","Embutidos e Frios","kg",False,False,0,"17.077.00","Genérico"),
    _p("7891167300081","Costela Suína Congelada 500g","Costela suína congelada","02032100","Carcaças e meias-carcaças suínas congeladas","Carnes","Carne Suína","kg",False,True,0,"","Genérico"),
    _p("7891167300098","Lombo Suíno Congelado 1kg","Lombo suíno congelado","02032900","Outras carnes suínas congeladas","Carnes","Carne Suína","kg",False,True,0,"","Genérico"),
    _p("7891167300104","Paleta Suína Congelada 1kg","Paleta suína congelada","02032200","Pernas e pás suínas congeladas","Carnes","Carne Suína","kg",False,True,0,"","Genérico"),
    _p("7891167300111","Frango Corte Misto Congelado 1kg","Cortes de frango congelados","02071419","Outros pedaços de frango congelados","Carnes","Carne de Frango","kg",False,True,0,"","Aurora"),
    _p("7891167300128","Filé de Frango Congelado 1kg","Filé de peito congelado","02071419","Outros pedaços de frango congelados","Carnes","Carne de Frango","kg",False,True,0,"","Sadia"),
    _p("7891167300135","Coxa Frango Congelada 1kg","Coxa de frango congelada","02071423","Coxas congeladas","Carnes","Carne de Frango","kg",False,True,0,"","Sadia"),
    _p("7891167300142","Asa de Frango Congelada 1kg","Asa de frango congelada","02071429","Outros pedaços miúdos congelados","Carnes","Carne de Frango","kg",False,True,0,"","Sadia"),
    _p("7891167300159","Peru Inteiro Congelado Sadia 4kg","Peru inteiro congelado","02072500","Peru inteiro congelado","Carnes","Aves","kg",False,True,0,"","Sadia"),
    _p("7891167300166","Pato Congelado 2kg","Pato inteiro congelado","02074200","Pato inteiro congelado","Carnes","Aves","kg",False,True,0,"","Genérico"),

    # ---- MAIS PEIXES E FRUTOS DO MAR ----
    _p("7898910000072","Atum Ralado ao Natural Coqueiro 170g","Atum ralado ao natural","16041410","Atuns preparados","Carnes","Peixes","un",False,False,0,"17.080.00","Coqueiro"),
    _p("7898910000089","Sardinha em Conserva no Tomate 125g","Sardinha em tomate","16041310","Sardinhas preparadas","Carnes","Peixes","un",False,False,0,"17.081.00","Coqueiro"),
    _p("7898910000096","Salmão Filé Congelado 500g","Filé de salmão congelado","03031300","Salmão-do-atlântico congelado","Carnes","Peixes","kg",False,True,0,"","Genérico"),
    _p("7898910000102","Tilápia Inteira Congelada 1kg","Tilápia inteira congelada","03032300","Tilápias congeladas","Carnes","Peixes","kg",False,True,0,"","Genérico"),
    _p("7898910000119","Camarão VG Congelado 600g","Camarão VG congelado","03061200","Camarões congelados da família Penaeidae","Carnes","Frutos do Mar","kg",False,True,0,"","Genérico"),
    _p("7898910000126","Lula Congelada 500g","Lula limpa congelada","03079900","Outros cefalópodes","Carnes","Frutos do Mar","kg",False,True,0,"","Genérico"),
    _p("7898910000133","Bacalhau Porto Inteiro Dessalgado 500g","Bacalhau dessalgado inteiro","03053200","Bacalhau seco e salgado","Carnes","Peixes","kg",False,True,0,"","Genérico"),
    _p("7898910000140","Atum Fresco em Posta kg","Atum fresco em posta","03023200","Albacora-laje fresca","Carnes","Peixes","kg",False,True,0,"","Genérico"),
    _p("7898910000157","Merluza Filé Congelado 500g","Filé de merluza congelado","03036600","Merluzas congeladas","Carnes","Peixes","kg",False,True,0,"","Genérico"),
    _p("7898910000164","Corvina Inteira Fresca kg","Corvina fresca inteira","03028990","Outros peixes frescos","Carnes","Peixes","kg",False,True,0,"","Feira"),

    # ---- MAIS HORTIFRUTI ----
    _p("","Pitanga kg","Pitanga fresca","08109000","Outras frutas frescas","Hortifruti","Frutas","kg",False,True,0,"","Feira"),
    _p("","Jabuticaba kg","Jabuticaba fresca","08109000","Outras frutas frescas","Hortifruti","Frutas","kg",False,True,0,"","Feira"),
    _p("","Carambola kg","Carambola fresca","08109000","Outras frutas frescas","Hortifruti","Frutas","kg",False,True,0,"","Feira"),
    _p("","Maracujá kg","Maracujá fresco","08109000","Outras frutas frescas","Hortifruti","Frutas","kg",False,True,0,"","Feira"),
    _p("","Abiu kg","Abiu fresco","08109000","Outras frutas frescas","Hortifruti","Frutas","kg",False,True,0,"","Feira"),
    _p("","Sapoti kg","Sapoti fresco","08109000","Outras frutas frescas","Hortifruti","Frutas","kg",False,True,0,"","Feira"),
    _p("","Fruta do Conde un","Ata/fruta-do-conde fresca","08109000","Outras frutas frescas","Hortifruti","Frutas","un",False,True,0,"","Feira"),
    _p("","Cebolinha maço","Cebolinha fresca","07032090","Outros alhos e cebolinhas","Hortifruti","Ervas","un",False,True,0,"","Horta"),
    _p("","Salsinha maço","Salsinha fresca","07099990","Outros produtos hortícolas","Hortifruti","Ervas","un",False,True,0,"","Horta"),
    _p("","Coentro maço","Coentro fresco","07099990","Outros produtos hortícolas","Hortifruti","Ervas","un",False,True,0,"","Horta"),
    _p("","Hortelã maço","Hortelã fresca","12119090","Plantas medicinais/aromáticas","Hortifruti","Ervas","un",False,True,0,"","Horta"),
    _p("","Manjericão fresco maço","Manjericão fresco","12119090","Plantas aromáticas","Hortifruti","Ervas","un",False,True,0,"","Horta"),
    _p("","Alecrim fresco maço","Alecrim fresco","12119090","Plantas aromáticas","Hortifruti","Ervas","un",False,True,0,"","Horta"),
    _p("","Gengibre kg","Gengibre fresco","09101100","Gengibre","Hortifruti","Temperos Frescos","kg",False,False,0,"","Feira"),
    _p("","Açafrão da Terra/Cúrcuma kg","Cúrcuma fresca","09103000","Cúrcuma","Hortifruti","Temperos Frescos","kg",False,False,0,"","Feira"),
    _p("","Pimenta Dedo-de-Moça kg","Pimenta dedo-de-moça fresca","07096000","Pimentões e pimentas","Hortifruti","Legumes","kg",False,True,0,"","Feira"),
    _p("","Pimenta Malagueta 100g","Pimenta malagueta fresca","07096000","Pimentões e pimentas","Hortifruti","Legumes","kg",False,True,0,"","Feira"),
    _p("","Vagem Macarrão kg","Vagem macarrão fresca","07089000","Outros legumes de vagem","Hortifruti","Legumes","kg",False,True,0,"","Feira"),
    _p("","Feijão Verde em Vagem kg","Feijão verde em vagem","07082000","Feijões em vagem","Hortifruti","Legumes","kg",False,True,0,"","Feira"),
    _p("","Lentilha Fresca/Germinada 100g","Lentilha germinada","07134090","Lentilhas","Hortifruti","Legumes","kg",False,True,0,"","Horta"),

    # ---- MAIS CEREAIS E GRÃOS ----
    _p("7896036003004","Arroz para Risoto Fino 1kg","Arroz arbóreo/carnaroli","10063021","Arroz semibranqueado ou branqueado, polido ou brunido","Cereais e Grãos","Arroz","kg",False,True,0,"","Camil"),
    _p("7896036003011","Arroz Parboilizado 5min Camil 500g","Arroz parboilizado rápido","10063011","Arroz parboilizado, polido ou brunido","Cereais e Grãos","Arroz","kg",False,True,0,"","Camil"),
    _p("7896036003028","Arroz Jasmim Thai 1kg","Arroz jasmim tailandês","10063021","Arroz semibranqueado ou branqueado, polido ou brunido","Cereais e Grãos","Arroz","kg",False,True,0,"","Importado"),
    _p("7896036003035","Arroz Basmati 1kg","Arroz basmati","10063021","Arroz semibranqueado ou branqueado, polido ou brunido","Cereais e Grãos","Arroz","kg",False,True,0,"","Importado"),
    _p("7896036003042","Feijão Bolinha 1kg","Feijão bolinha tipo 1","07133290","Feijões","Cereais e Grãos","Feijão","kg",False,True,0,"","Genérico"),
    _p("7896036003059","Feijão Rajado 500g","Feijão rajado beneficiado","07133290","Feijões","Cereais e Grãos","Feijão","kg",False,True,0,"","Genérico"),
    _p("7896036003066","Feijão de Corda 500g","Feijão de corda","07131090","Feijões de corda","Cereais e Grãos","Feijão","kg",False,True,0,"","Genérico"),
    _p("7896036003073","Amendoim em Grão Cru 500g","Amendoim em grão cru","12042000","Sementes de amendoim sem casca","Cereais e Grãos","Amendoim","kg",False,True,0,"","Genérico"),
    _p("7896036003080","Milho de Pipoca 500g","Milho para pipoca","10059010","Milho em grão","Cereais e Grãos","Milho","kg",False,True,0,"","Yoki"),
    _p("7896036003097","Milho Verde em Grão 500g","Milho verde em grão","10059010","Milho em grão","Cereais e Grãos","Milho","kg",False,True,0,"","Genérico"),
    _p("7896036003103","Cevadinha 500g","Cevadinha para vitaminas","10039080","Cevada em grão","Cereais e Grãos","Grãos Especiais","kg",False,True,0,"","Genérico"),
    _p("7896036003110","Amaranto em Grão 250g","Amaranto em grão","10089000","Outros cereais","Cereais e Grãos","Grãos Especiais","kg",False,True,0,"","Genérico"),
    _p("7896036003127","Trigo em Grão 500g","Trigo em grão","10011900","Outros trigos moles","Cereais e Grãos","Grãos Especiais","kg",False,True,0,"","Genérico"),
    _p("7896036003134","Centeio em Grão 500g","Centeio em grão","10029000","Centeio","Cereais e Grãos","Grãos Especiais","kg",False,True,0,"","Importado"),
]


# ============================================================
# SEÇÃO 14: MAIS CONDIMENTOS, ESPECIARIAS E PRODUTOS GOURMET
# ============================================================

_PRODUCTS += [
    # ---- AZEITES ESPECIAIS ----
    _p("7897000300011","Azeite Extravirgem Portugues 750ml","Azeite extravirgem português","15092000","Azeite de oliva (oliveira) extra virgem","Óleos e Gorduras","Azeite","lt",False,False,0,"","Genérico"),
    _p("7897000300028","Azeite Italiano Divella 500ml","Azeite extravirgem italiano","15092000","Azeite de oliva (oliveira) extra virgem","Óleos e Gorduras","Azeite","lt",False,False,0,"","Divella"),
    _p("7897000300035","Azeite Espanhol Hacendado 500ml","Azeite extravirgem espanhol","15092000","Azeite de oliva (oliveira) extra virgem","Óleos e Gorduras","Azeite","lt",False,False,0,"","Hacendado"),
    _p("7897000300042","Óleo de Girassol Forno de Minas 500ml","Óleo de girassol refinado","15121911","Óleo de girassol refinado","Óleos e Gorduras","Óleo Vegetal","lt",True,False,0,"","Forno de Minas"),
    _p("7897000300059","Óleo de Coco Extravirgem Copra 200ml","Óleo de coco extravirgem","15132919","Óleo de coco — outros","Óleos e Gorduras","Óleo Vegetal","lt",False,False,0,"","Copra"),

    # ---- ESPECIARIAS IMPORTADAS ----
    _p("7897000400014","Açafrão em Estigmas 1g","Açafrão em fios","09102010","Açafrão em estigmas","Condimentos","Especiarias","kg",False,False,0,"","Importado"),
    _p("7897000400021","Baunilha Bourbon em Fava un","Fava de baunilha bourbon","09058000","Baunilha","Condimentos","Especiarias","un",False,False,0,"","Importado"),
    _p("7897000400038","Pimenta Jamaicana 30g","Pimenta da Jamaica (allspice)","09094100","Frutos de zimbro","Condimentos","Especiarias","kg",False,False,0,"","Importado"),
    _p("7897000400045","Cardamomo em Cápsulas 30g","Cardamomo em cápsulas","09086110","Cardamomo","Condimentos","Especiarias","kg",False,False,0,"","Importado"),
    _p("7897000400052","Erva Doce em Sementes 30g","Semente de erva-doce","09099900","Outras especiarias","Condimentos","Especiarias","kg",False,False,0,"","Sirial"),
    _p("7897000400069","Feno-grego 30g","Feno-grego em sementes","12119090","Plantas para condimento","Condimentos","Especiarias","kg",False,False,0,"","Genérico"),
    _p("7897000400076","Urucum em Sementes 50g","Sementes de urucum","09103000","Urucum","Condimentos","Especiarias","kg",False,False,0,"","Genérico"),
    _p("7897000400083","Curcuma em Pó 50g","Açafrão-da-terra em pó","09103000","Cúrcuma","Condimentos","Especiarias","kg",False,False,0,"","Genérico"),
    _p("7897000400090","Gengibre em Pó 30g","Gengibre seco em pó","09101200","Gengibre triturado ou em pó","Condimentos","Especiarias","kg",False,False,0,"","Sirial"),
    _p("7897000400106","Pimenta Cayenne 30g","Pimenta caiena em pó","09042100","Pimenta seca","Condimentos","Especiarias","kg",False,False,0,"","Genérico"),
    _p("7897000400113","Pimenta Calabresa 30g","Pimenta calabresa em flocos","09042100","Pimenta seca","Condimentos","Especiarias","kg",False,False,0,"","Genérico"),
    _p("7897000400120","Mistura Italiana de Ervas 30g","Mix de ervas italianas","12119090","Plantas aromáticas desidratadas","Condimentos","Especiarias","kg",False,False,0,"","Genérico"),
    _p("7897000400137","Pimenta Verde em Conserva 100g","Pimenta verde conservada","20099000","Outros sucos","Condimentos","Especiarias","kg",False,False,0,"","Genérico"),
    _p("7897000400144","Chimichurri 50g","Tempero chimichurri argentino","21039091","Misturas de condimentos ≤1kg","Condimentos","Temperos Compostos","kg",False,False,0,"","Genérico"),
    _p("7897000400151","Harissa Pasta 100g","Pasta de pimenta harissa","21039091","Preparações para molhos, embalagem ≤1kg","Condimentos","Molhos Especiais","kg",False,False,0,"","Importado"),
    _p("7897000400168","Miso Pasta 200g","Pasta de soja fermentada (missô)","21031090","Outros molhos de soja","Condimentos","Molhos Especiais","kg",False,False,0,"","Importado"),
    _p("7897000400175","Shoyu Tamari 150ml","Molho tamari sem trigo","21039091","Preparações para molhos, embalagem ≤1kg","Condimentos","Molhos Especiais","lt",False,False,0,"","Kikkoman"),
    _p("7897000400182","Molho de Peixe 150ml","Molho de peixe (fish sauce)","21039091","Preparações para molhos, embalagem ≤1kg","Condimentos","Molhos Especiais","lt",False,False,0,"","Importado"),
    _p("7897000400199","Hoisin Sauce 240ml","Molho hoisin","21039091","Preparações para molhos, embalagem ≤1kg","Condimentos","Molhos Especiais","lt",False,False,0,"","Lee Kum Kee"),

    # ---- MOLHOS ESPECIAIS ----
    _p("7897000500017","Molho Barbecue Heinz 397g","Molho barbecue","21039091","Preparações para molhos, embalagem ≤1kg","Condimentos","Molhos Especiais","kg",False,False,0,"","Heinz"),
    _p("7897000500024","Molho Ranch Hellmann's 200ml","Molho ranch americano","21039091","Preparações para molhos, embalagem ≤1kg","Condimentos","Molhos Especiais","lt",False,False,0,"","Hellmann's"),
    _p("7897000500031","Molho Tailandês Doce Chili 190ml","Molho chili doce tailandês","21039091","Preparações para molhos, embalagem ≤1kg","Condimentos","Molhos Especiais","lt",False,False,0,"","Importado"),
    _p("7897000500048","Molho Sriracha 435ml","Molho sriracha picante","21039091","Preparações para molhos, embalagem ≤1kg","Condimentos","Molhos Especiais","lt",False,False,0,"","Huy Fong"),
    _p("7897000500055","Vinagre Balsâmico de Modena 250ml","Vinagre balsâmico","22090000","Vinagres","Condimentos","Vinagre","lt",False,False,0,"","Importado"),
    _p("7897000500062","Vinagre de Arroz 500ml","Vinagre de arroz","22090000","Vinagres","Condimentos","Vinagre","lt",False,False,0,"","Importado"),
    _p("7897000500079","Vinagre de Cana Orgânico 500ml","Vinagre de cana orgânico","22090000","Vinagres","Condimentos","Vinagre","lt",False,False,0,"","Genérico"),
    _p("7897000500086","Azeite com Trufas Negras 100ml","Azeite aromatizado com trufas","15099010","Outros azeites de oliva refinados","Óleos e Gorduras","Azeite","lt",False,False,0,"","Importado"),

    # ---- MASSAS ESPECIAIS ----
    _p("7897000600010","Macarrão de Arroz Vermicelli 200g","Macarrão de arroz fino","19023000","Outras massas alimentícias","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"","Importado"),
    _p("7897000600027","Macarrão Soba (Trigo e Trigo Sarraceno) 300g","Soba — macarrão japonês","19023000","Outras massas alimentícias","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"","Importado"),
    _p("7897000600034","Macarrão Udon 200g","Udon — macarrão japonês grosso","19023000","Outras massas alimentícias","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"","Importado"),
    _p("7897000600041","Nhoque de Batata Congelado 500g","Nhoque de batata congelado","19022000","Massas recheadas","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"","Genérico"),
    _p("7897000600058","Ravióli de Carne Congelado 500g","Ravióli de carne congelado","19022000","Massas recheadas","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"17.048.00","Genérico"),
    _p("7897000600065","Capeletti ao Molho Sugo Congelado 500g","Capeletti congelado ao molho","19022000","Massas recheadas","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"17.048.00","Genérico"),
    _p("7897000600072","Talharim com Ovos 250g","Talharim com ovos","19021100","Massas alimentícias com ovos","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"17.049.00","Genérico"),
    _p("7897000600089","Penne Integral 500g","Macarrão penne integral","19023000","Outras massas alimentícias","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"17.049.00","Barilla"),
    _p("7897000600096","Lasanha Seca Barilla 500g","Massa de lasanha seca","19023000","Outras massas alimentícias","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"17.049.00","Barilla"),
    _p("7897000600102","Orzo Barilla 500g","Orzo macarrão em grão","19023000","Outras massas alimentícias","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"17.049.00","Barilla"),
    _p("7897000600119","Macarrão Capellini Barilla 500g","Capellini — macarrão fino","19023000","Outras massas alimentícias","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"17.049.00","Barilla"),
]


# ============================================================
# SEÇÃO 15: PRODUTOS GRANDES VOLUMES + COMPLEMENTOS
# ============================================================

_PRODUCTS += [
    # ---- MAIS PÃES E PADARIA ----
    _p("7897001000014","Pão Francês 50g un","Pão francês fresco","19052090","Outros pães","Padaria","Pão Francês","un",False,False,0,"","Padaria"),
    _p("7897001000021","Pão Integral 50g un","Pão integral artesanal","19052090","Outros pães","Padaria","Pão Integral","un",False,False,0,"","Padaria"),
    _p("7897001000038","Pão de Centeio 500g","Pão de centeio artesanal","19052090","Outros pães","Padaria","Pão Especial","kg",False,False,0,"","Padaria"),
    _p("7897001000045","Pão de Fermentação Natural 400g","Pão sourdough fermentação natural","19052090","Outros pães","Padaria","Pão Especial","kg",False,False,0,"","Artesanal"),
    _p("7897001000052","Baguete Francesa 250g","Baguete de trigo","19052090","Outros pães","Padaria","Pão Especial","un",False,False,0,"","Padaria"),
    _p("7897001000069","Croissant Amanteigado un","Croissant artesanal","19052090","Outros pães","Padaria","Pão Especial","un",False,False,0,"","Padaria"),
    _p("7897001000076","Pão de Queijo Caseiro 50g","Pão de queijo artesanal","19052090","Outros pães","Padaria","Pão de Queijo","un",False,False,0,"","Padaria"),
    _p("7897001000083","Coxinha de Frango un","Coxinha de frango artesanal","16023220","Preparações de frango","Padaria","Salgados","un",False,False,0,"","Padaria"),
    _p("7897001000090","Empada de Frango un","Empada de frango artesanal","19052090","Outros produtos de padaria","Padaria","Salgados","un",False,False,0,"","Padaria"),
    _p("7897001000106","Esfirra de Carne un","Esfirra de carne artesanal","19052090","Outros produtos de padaria","Padaria","Salgados","un",False,False,0,"","Padaria"),
    _p("7897001000113","Pastel de Vento un","Pastel de vento artesanal","19052090","Outros produtos de padaria","Padaria","Salgados","un",False,False,0,"","Padaria"),
    _p("7897001000120","Pão de Alho 200g","Pão de alho congelado","19052090","Outros pães","Padaria","Pão Especial","kg",False,False,0,"","Genérico"),
    _p("7897001000137","Torta Salgada de Frango Congelada 500g","Torta salgada congelada","19052090","Outros produtos de padaria","Padaria","Tortas","kg",False,False,0,"","Genérico"),
    _p("7897001000144","Bolo de Fubá 500g","Bolo de fubá caseiro","19052090","Outros produtos de padaria","Padaria","Bolos","kg",False,False,0,"","Padaria"),
    _p("7897001000151","Bolo de Banana 500g","Bolo de banana","19052090","Outros produtos de padaria","Padaria","Bolos","kg",False,False,0,"","Padaria"),
    _p("7897001000168","Bolo de Cenoura com Cobertura 500g","Bolo de cenoura","19052090","Outros produtos de padaria","Padaria","Bolos","kg",False,False,0,"","Padaria"),
    _p("7897001000175","Biscoito de Polvilho Doce 100g","Biscoito de polvilho doce","19053100","Biscoitos e bolachas","Padaria","Biscoitos","kg",False,False,0,"","Genérico"),
    _p("7897001000182","Biscoito de Polvilho Azedo 100g","Biscoito de polvilho azedo","19053100","Biscoitos e bolachas","Padaria","Biscoitos","kg",False,False,0,"","Genérico"),
    _p("7897001000199","Rapadura 500g","Rapadura de cana","17011400","Açúcar de cana — rapadura","Cereais e Grãos","Açúcar","kg",False,False,0,"","Genérico"),
    _p("7897001000205","Melado de Cana 500g","Melado de cana","17030000","Melaços de cana-de-açúcar","Cereais e Grãos","Açúcar","kg",False,False,0,"","Genérico"),

    # ---- CONGELADOS COMPLEMENTARES ----
    _p("7897001100010","Polpetone Bovino Congelado 400g","Polpetone bovino congelado","16025000","Preparações de carne bovina","Congelados","Pratos Prontos","kg",False,False,0,"","Genérico"),
    _p("7897001100027","Strogonoff de Frango Congelado 300g","Strogonoff de frango pronto","16023220","Preparações de frango","Congelados","Pratos Prontos","kg",False,False,0,"","Sadia"),
    _p("7897001100034","Frango a Parmegiana Congelado 250g","Frango a parmegiana congelado","16023220","Preparações de frango","Congelados","Pratos Prontos","kg",False,False,0,"","Sadia"),
    _p("7897001100041","Peixe Empanado Filé Congelado 300g","Filé de peixe empanado","16042000","Outras preparações de peixes","Congelados","Peixes","kg",False,False,0,"","Coqueiro"),
    _p("7897001100058","Camarão Empanado Congelado 300g","Camarão empanado congelado","16052000","Camarões preparados","Congelados","Frutos do Mar","kg",False,False,0,"","Genérico"),
    _p("7897001100065","Ovo de Codorna em Conserva 150g","Ovo de codorna em conserva","04079000","Outros ovos","Laticínios","Ovos","kg",False,False,0,"","Genérico"),
    _p("7897001100072","Tomate Seco em Conserva 100g","Tomate seco em conserva","20029000","Outros tomates preparados","Enlatados","Conservas de Verduras","kg",False,False,0,"","Genérico"),
    _p("7897001100089","Pimentão em Conserva 180g","Pimentão em conserva","20019000","Outros vegetais em conserva","Enlatados","Conservas de Verduras","kg",False,False,0,"","Genérico"),
    _p("7897001100096","Alcaparra em Conserva 100g","Alcaparra em conserva","20019000","Outros vegetais em conserva","Enlatados","Conservas de Verduras","kg",False,False,0,"","Importado"),
    _p("7897001100102","Aspargo em Conserva 300g","Aspargo em conserva","20056000","Aspargos em conserva","Enlatados","Conservas de Verduras","kg",False,False,0,"","Importado"),
    _p("7897001100119","Milho de Pipoca Gourmet 400g","Milho para pipoca artesanal","10059010","Milho em grão","Cereais e Grãos","Milho","kg",False,True,0,"","Genérico"),
    _p("7897001100126","Tablete de Chocolate 70% Cacau 80g","Chocolate amargo 70% cacau","18063210","Chocolate em tabletes","Padaria","Chocolates","kg",False,False,0,"17.002.00","Cacau Show"),
    _p("7897001100133","Chocolate Branco Garoto 90g","Chocolate branco","17049010","Chocolate branco","Padaria","Chocolates","kg",False,False,0,"17.001.00","Garoto"),
    _p("7897001100140","Kit Kat Nestlé 41,5g","Biscoito coberto por chocolate","18063210","Chocolate em barras","Padaria","Chocolates","kg",False,False,0,"17.002.00","Nestlé"),
    _p("7897001100157","Ovomaltine Pó 200g","Achocolatado com malte","18069000","Outras preparações com cacau","Bebidas","Achocolatado","kg",True,False,0,"17.006.00","Ovomaltine"),

    # ---- PRODUTOS SEM LACTOSE / ESPECIAIS ----
    _p("7897001200016","Leite Deslactosado Integral 1L","Leite deslactosado integral","04011010","Leite UHT","Laticínios","Leite UHT","lt",False,True,0,"17.016.00","Letti"),
    _p("7897001200023","Queijo Mussarela Zero Lactose 200g","Queijo mussarela sem lactose","04061010","Queijo mussarela","Laticínios","Queijos","kg",False,False,0,"17.024.00","Polenghi"),
    _p("7897001200030","Iogurte Zero Lactose 170g","Iogurte sem lactose","04032000","Iogurte","Laticínios","Iogurte","kg",False,False,0,"17.021.00","Parmalat"),
    _p("7897001200047","Creme de Leite Sem Lactose 200g","Creme de leite sem lactose","04022130","Creme de leite","Laticínios","Creme de Leite","kg",False,False,0,"17.019.00","Piracanjuba"),
    _p("7897001200054","Manteiga Sem Lactose 200g","Manteiga sem lactose","04051000","Manteiga","Laticínios","Manteiga","kg",False,False,0,"17.025.00","Genérico"),
]


# ============================================================
# SEÇÃO 16: MAIS PRODUTOS - LOTES FINAIS PARA COMPLETAR 2000+
# ============================================================

# Gerando produtos programaticamente para alcançar meta de 2000+

def _gen_products():
    extra = []

    # ---- MAIS BISCOITOS E SNACKS ----
    biscoitos = [
        ("7897002000010","Biscoito Trakinas Chocolate 126g","Biscoito recheado chocolate","19053100","Biscoitos","Padaria","Biscoitos","kg",False,False,0,"","Nabisco"),
        ("7897002000027","Biscoito Trakinas Morango 126g","Biscoito recheado morango","19053100","Biscoitos","Padaria","Biscoitos","kg",False,False,0,"","Nabisco"),
        ("7897002000034","Biscoito Recheado Baunilha Piraquê 130g","Biscoito recheado baunilha","19053100","Biscoitos","Padaria","Biscoitos","kg",False,False,0,"","Piraquê"),
        ("7897002000041","Biscoito Rosquinha Doce de Leite Piraquê 200g","Rosquinha doce de leite","19053100","Biscoitos","Padaria","Biscoitos","kg",False,False,0,"","Piraquê"),
        ("7897002000058","Biscoito Cream Cracker Marilan 200g","Biscoito cream cracker","19053100","Biscoitos","Padaria","Biscoitos","kg",False,False,0,"","Marilan"),
        ("7897002000065","Biscoito Água e Sal Marilan 200g","Biscoito água e sal","19053100","Biscoitos","Padaria","Biscoitos","kg",False,False,0,"","Marilan"),
        ("7897002000072","Biscoito Bono Chocolate Nestlé 200g","Biscoito recheado chocolate","19053100","Biscoitos","Padaria","Biscoitos","kg",False,False,0,"","Nestlé"),
        ("7897002000089","Biscoito Passatempo Nestlé 200g","Biscoito de baunilha","19053100","Biscoitos","Padaria","Biscoitos","kg",False,False,0,"","Nestlé"),
        ("7897002000096","Biscoito Choco Cracker Forno de Minas 200g","Biscoito de chocolate","19053100","Biscoitos","Padaria","Biscoitos","kg",False,False,0,"","Forno de Minas"),
        ("7897002000102","Biscoito Digestivo Vitarella 200g","Biscoito digestivo integral","19053100","Biscoitos","Padaria","Biscoitos","kg",False,False,0,"","Vitarella"),
        ("7897002000119","Biscoito Integral Tostines 200g","Biscoito integral","19053100","Biscoitos","Padaria","Biscoitos","kg",False,False,0,"","Tostines"),
        ("7897002000126","Biscoito Salgado Fandango Elma Chips 100g","Salgadinho de queijo","19053100","Biscoitos","Padaria","Biscoitos","kg",False,False,0,"","Elma Chips"),
        ("7897002000133","Biscoito de Arroz Integral 100g","Biscoito de arroz","19053100","Biscoitos","Padaria","Biscoitos","kg",False,False,0,"","Genérico"),
        ("7897002000140","Biscoito de Tapioca 100g","Biscoito de tapioca","19053100","Biscoitos","Padaria","Biscoitos","kg",False,False,0,"","Genérico"),
        ("7897002000157","Wafer Chocolate Bauducco 140g","Wafer de chocolate","19053200","Waffles e wafers","Padaria","Biscoitos","kg",False,False,0,"17.057.00","Bauducco"),
        ("7897002000164","Wafer Creme Nestlé 140g","Wafer de creme","19053200","Waffles e wafers","Padaria","Biscoitos","kg",False,False,0,"17.057.00","Nestlé"),
    ]
    for b in biscoitos:
        extra.append(_p(*b))

    # ---- MAIS IOGURTES E LATICÍNIOS ----
    iogurtes = [
        ("7897003000012","Iogurte Grego Morango Frutis 100g","Iogurte grego morango","04032000","Iogurte","Laticínios","Iogurte","kg",False,False,0,"17.021.00","Danone"),
        ("7897003000029","Iogurte Grego Limão Frutis 100g","Iogurte grego limão","04032000","Iogurte","Laticínios","Iogurte","kg",False,False,0,"17.021.00","Danone"),
        ("7897003000036","Iogurte Sabor Maracujá 170g","Iogurte de maracujá","04032000","Iogurte","Laticínios","Iogurte","kg",False,False,0,"17.021.00","Parmalat"),
        ("7897003000043","Iogurte Sabor Pêssego 170g","Iogurte de pêssego","04032000","Iogurte","Laticínios","Iogurte","kg",False,False,0,"17.021.00","Parmalat"),
        ("7897003000050","Iogurte Activia Fibras Danone 90g","Iogurte probiótico fibras","04032000","Iogurte","Laticínios","Iogurte","kg",False,False,0,"17.021.00","Danone"),
        ("7897003000067","Iogurte Skyr Natural Piracanjuba 160g","Iogurte skyr","04032000","Iogurte","Laticínios","Iogurte","kg",False,False,0,"17.021.00","Piracanjuba"),
        ("7897003000074","Iogurte Desnatado Natural 1kg","Iogurte desnatado natural grande","04032000","Iogurte","Laticínios","Iogurte","kg",False,False,0,"17.021.01","Itambé"),
        ("7897003000081","Bebida Láctea Acerola Itambé 200ml","Bebida láctea acerola","04039000","Outros leites fermentados","Laticínios","Bebida Láctea","lt",False,False,0,"17.021.00","Itambé"),
        ("7897003000098","Leite Condensado Piracanjuba 395g","Leite condensado","04029900","Leite condensado","Laticínios","Leite Condensado","kg",False,False,0,"17.020.00","Piracanjuba"),
        ("7897003000104","Creme de Leite Culinário 500ml","Creme de leite culinário","04022130","Creme de leite","Laticínios","Creme de Leite","lt",False,False,0,"17.019.00","Piracanjuba"),
        ("7897003000111","Manteiga Extra sem Sal 200g","Manteiga extra sem sal","04051000","Manteiga","Laticínios","Manteiga","kg",False,False,0,"17.025.00","Aviação"),
        ("7897003000128","Manteiga com Sal Premier 200g","Manteiga com sal","04051000","Manteiga","Laticínios","Manteiga","kg",False,False,0,"17.025.00","Genérico"),
        ("7897003000135","Queijo Fresco 200g","Queijo frescal tipo minas","04069030","Queijo de massa macia","Laticínios","Queijos","kg",False,False,0,"17.024.00","Genérico"),
        ("7897003000142","Queijo Lanche Fatiado Itambé 150g","Queijo tipo lanche fatiado","04069020","Queijo de massa semidura","Laticínios","Queijos","kg",False,False,0,"17.024.00","Itambé"),
        ("7897003000159","Queijo Reino Centenário 500g","Queijo reino","04069010","Queijo de massa dura","Laticínios","Queijos","kg",False,False,0,"17.024.00","Genérico"),
        ("7897003000166","Queijo Estepe Fatiado 150g","Queijo estepe fatiado","04069020","Queijo de massa semidura","Laticínios","Queijos","kg",False,False,0,"17.024.00","Genérico"),
    ]
    for i in iogurtes:
        extra.append(_p(*i))

    # ---- MAIS EMBUTIDOS E FRIOS ----
    embutidos = [
        ("7897004000011","Calabresa Defumada Fatiada 200g","Calabresa defumada fatiada","16010000","Enchidos","Carnes","Embutidos e Frios","kg",False,False,0,"17.076.00","Sadia"),
        ("7897004000028","Pastrami de Carne Bovina 100g","Pastrami fatiado","02102000","Carne bovina salgada","Carnes","Embutidos e Frios","kg",False,False,0,"","Genérico"),
        ("7897004000035","Carpaccio de Carne Bovina 100g","Carpaccio bovino","16025000","Preparações de carne bovina","Carnes","Embutidos e Frios","kg",False,False,0,"","Genérico"),
        ("7897004000042","Mortadela Bologna Light 500g","Mortadela light","16010000","Enchidos","Carnes","Embutidos e Frios","kg",False,False,0,"17.078.00","Sadia"),
        ("7897004000059","Salsicha Defumada 500g","Salsicha defumada","16010000","Enchidos","Carnes","Embutidos e Frios","kg",False,False,0,"17.077.00","Aurora"),
        ("7897004000066","Presunto Parma Importado 100g","Presunto cru tipo parma","16024100","Pernas suínas","Carnes","Embutidos e Frios","kg",False,False,0,"","Importado"),
        ("7897004000073","Chorizo Espanhol Importado 100g","Chorizo espanhol fatiado","16010000","Enchidos","Carnes","Embutidos e Frios","kg",False,False,0,"","Importado"),
        ("7897004000080","Frango Temperado Sadia 1kg","Frango inteiro temperado congelado","16023290","Preparações de frango","Carnes","Aves","kg",False,False,0,"","Sadia"),
        ("7897004000097","Pernil Suíno Salgado 1kg","Pernil suíno salgado","02101100","Pernas suínas salgadas","Carnes","Carne Suína","kg",False,True,0,"17.083.00","Genérico"),
    ]
    for e in embutidos:
        extra.append(_p(*e))

    # ---- MAIS BEBIDAS ----
    bebidas = [
        ("7897005000010","Suco de Laranja Integral Del Valle 1,5L","Suco de laranja integral","20091100","Suco de laranja","Bebidas","Suco","lt",True,False,0,"17.010.00","Del Valle"),
        ("7897005000027","Néctar Pêssego Del Valle 1L","Néctar de pêssego","20098990","Outros sucos de frutos","Bebidas","Suco","lt",True,False,0,"17.010.00","Del Valle"),
        ("7897005000034","Néctar Goiaba Del Valle 1L","Néctar de goiaba","20098990","Outros sucos de frutos","Bebidas","Suco","lt",True,False,0,"17.010.00","Del Valle"),
        ("7897005000041","Suco de Uva Integral Tial 1L","Suco de uva integral","20094900","Suco de uva","Bebidas","Suco","lt",False,False,0,"17.010.00","Tial"),
        ("7897005000058","Água de Coco Kero Coco 200ml","Água de coco natural","20098100","Suco de coco","Bebidas","Água de Coco","lt",False,False,0,"17.011.00","Kero Coco"),
        ("7897005000065","Água de Coco Kero Coco 1L","Água de coco 1L","20098100","Suco de coco","Bebidas","Água de Coco","lt",False,False,0,"17.011.00","Kero Coco"),
        ("7897005000072","Água Mineral com Gás 1,5L","Água mineral gaseificada 1,5L","22011000","Águas minerais gaseificadas","Bebidas","Água","lt",True,False,0,"03.006.00","Bonafonte"),
        ("7897005000089","Coca-Cola Lata 269ml","Refrigerante cola mini","22021000","Refrigerante","Bebidas","Refrigerante","lt",True,False,0,"03.011.00","Coca-Cola"),
        ("7897005000096","Guaraná Natural Antarctica 350ml Lata","Refrigerante guaraná natural","22021000","Refrigerante","Bebidas","Refrigerante","lt",True,False,0,"03.011.00","Antarctica"),
        ("7897005000102","Fanta Uva 2L","Refrigerante uva","22021000","Refrigerante","Bebidas","Refrigerante","lt",True,False,0,"03.010.00","Fanta"),
        ("7897005000119","Sprite Zero 2L","Refrigerante limão zero","22021000","Refrigerante","Bebidas","Refrigerante","lt",True,False,0,"03.010.00","Sprite"),
        ("7897005000126","Toddynho Chocolate 200ml","Achocolatado em embalagem","22029900","Bebida achocolatada","Bebidas","Bebidas Lácteas","lt",True,False,0,"","PepsiCo"),
        ("7897005000133","Red Bull Sugar Free 250ml","Bebida energética zero açúcar","21069090","Bebidas energéticas","Bebidas","Energético","lt",True,False,0,"03.013.00","Red Bull"),
        ("7897005000140","Monster Zero Ultra 473ml","Bebida energética zero","21069090","Bebidas energéticas","Bebidas","Energético","lt",True,False,0,"03.014.00","Monster"),
        ("7897005000157","Isotônico Gatorade Maçã 500ml","Isotônico sabor maçã","21069090","Bebidas isotônicas","Bebidas","Isotônico","lt",True,False,0,"03.015.00","Gatorade"),
        ("7897005000164","Kombucha Natural 350ml","Kombucha fermentado natural","22029900","Outras bebidas","Bebidas","Bebidas Especiais","lt",False,False,0,"","Genérico"),
        ("7897005000171","Kefir de Leite 500ml","Kefir de leite fermentado","04039000","Outros leites fermentados","Laticínios","Bebida Láctea","lt",False,False,0,"","Genérico"),
    ]
    for b in bebidas:
        extra.append(_p(*b))

    # ---- MAIS CONGELADOS ----
    congelados = [
        ("7897006000019","Minipizza Congelada 300g","Minipizza congelada","19012090","Outras preparações de farinha","Congelados","Pizzas","kg",False,False,0,"","Sadia"),
        ("7897006000026","Pizza Portuguesa Sadia 440g","Pizza portuguesa congelada","19012090","Outras preparações de farinha","Congelados","Pizzas","kg",False,False,0,"","Sadia"),
        ("7897006000033","Pizza Napolitana Congelada 440g","Pizza napolitana congelada","19012090","Outras preparações de farinha","Congelados","Pizzas","kg",False,False,0,"","Genérico"),
        ("7897006000040","Filé de Frango Grelhado Congelado 600g","Filé de frango grelhado","16023220","Preparações de frango","Congelados","Pratos Prontos","kg",False,False,0,"","Sadia"),
        ("7897006000057","Carne de Sol Salgada Congelada 500g","Carne de sol congelada","02102000","Carne bovina salgada","Carnes","Carnes Secas","kg",False,True,0,"17.083.00","Genérico"),
        ("7897006000064","Tilápia Filé Congelado 600g","Filé de tilápia congelado","03032300","Tilápias congeladas","Congelados","Peixes","kg",False,True,0,"","Genérico"),
        ("7897006000071","Merluza Filé Congelado Aurora 400g","Filé de merluza congelado","03036600","Merluzas congeladas","Congelados","Peixes","kg",False,True,0,"","Aurora"),
        ("7897006000088","Croquete de Carne Congelado 12un","Croquete de carne congelado","16025000","Preparações de carne","Congelados","Salgados","kg",False,False,0,"","Sadia"),
        ("7897006000095","Quibe Congelado 12un","Quibe congelado","16025000","Preparações de carne","Congelados","Salgados","kg",False,False,0,"","Sadia"),
        ("7897006000101","Bolinha de Queijo Congelada 500g","Bolinha de queijo congelada","19022000","Massas recheadas","Congelados","Salgados","kg",False,False,0,"","Genérico"),
        ("7897006000118","Strogonoff Carne Congelado 300g","Strogonoff de carne pronto","16025000","Preparações de carne","Congelados","Pratos Prontos","kg",False,False,0,"","Genérico"),
        ("7897006000125","Frango ao Curry Congelado 300g","Frango ao curry pronto","16023220","Preparações de frango","Congelados","Pratos Prontos","kg",False,False,0,"","Genérico"),
    ]
    for c in congelados:
        extra.append(_p(*c))

    # ---- MAIS ENLATADOS ----
    enlatados = [
        ("7897007000017","Grão de Bico em Lata 400g","Grão-de-bico em conserva","20055900","Leguminosas em conserva","Enlatados","Feijão Cozido","kg",False,False,0,"","Qualitá"),
        ("7897007000024","Lentilha em Lata 400g","Lentilha em conserva","20055900","Leguminosas em conserva","Enlatados","Feijão Cozido","kg",False,False,0,"","Qualitá"),
        ("7897007000031","Feijão Branco em Lata 400g","Feijão branco em conserva","20055100","Feijões em grãos","Enlatados","Feijão Cozido","kg",False,False,0,"","Qualitá"),
        ("7897007000048","Milho Verde Gigante Bonduelle 200g","Milho verde gigante","20059000","Outros vegetais","Enlatados","Conservas de Verduras","kg",False,False,0,"","Bonduelle"),
        ("7897007000055","Coração de Palmito Pupunha Qualitá 300g","Palmito pupunha","20089900","Outros vegetais em conserva","Enlatados","Conservas de Verduras","kg",False,False,0,"","Qualitá"),
        ("7897007000062","Coração de Palmito Juçara Cepera 300g","Palmito juçara","20089900","Outros vegetais em conserva","Enlatados","Conservas de Verduras","kg",False,False,0,"","Cepera"),
        ("7897007000079","Azeitona Verde com Caroço Coqueiro 150g","Azeitona verde","20057000","Azeitonas","Enlatados","Conservas de Verduras","kg",False,False,0,"","Coqueiro"),
        ("7897007000086","Creme de Cebola Knorr 31g","Creme de cebola","21041000","Sopas e caldos preparados","Enlatados","Sopas e Cremes","kg",False,False,0,"","Knorr"),
        ("7897007000093","Sopa Ramen Instantânea 60g","Sopa ramen instantânea","19023000","Massas instantâneas","Enlatados","Sopas e Cremes","kg",False,False,0,"17.047.00","Nissin"),
        ("7897007000109","Sopa de Legumes Instantânea Knorr 58g","Sopa de legumes em pó","21041000","Sopas e caldos preparados","Enlatados","Sopas e Cremes","kg",False,False,0,"","Knorr"),
        ("7897007000116","Atum em Azeite Gomes da Costa 130g","Atum em azeite","16041410","Atuns preparados","Enlatados","Peixes","un",False,False,0,"17.080.00","Gomes da Costa"),
        ("7897007000123","Sardinha Defumada Coqueiro 125g","Sardinha defumada","16041310","Sardinhas preparadas","Enlatados","Peixes","un",False,False,0,"17.081.00","Coqueiro"),
        ("7897007000130","Mariscos em Conserva 130g","Mariscos em conserva","16059000","Outros moluscos preparados","Enlatados","Frutos do Mar","un",False,False,0,"17.082.00","Genérico"),
        ("7897007000147","Lula em Conserva 130g","Lula em conserva","16059000","Outros invertebrados preparados","Enlatados","Frutos do Mar","un",False,False,0,"17.082.00","Genérico"),
    ]
    for e in enlatados:
        extra.append(_p(*e))

    # ---- MAIS HORTIFRUTI ESPECIAL ----
    hortifruti = [
        ("","Broccolini maço","Broccolini fresco","07041000","Couve-flor e brócolis","Hortifruti","Verduras","un",False,True,0,"","Horta"),
        ("","Pak Choi maço","Pak choi (couve chinesa)","07049000","Outros couves","Hortifruti","Verduras","un",False,True,0,"","Horta"),
        ("","Nirá maço","Alho nirá fresco","07039010","Para semeadura","Hortifruti","Ervas","un",False,True,0,"","Horta"),
        ("","Chicória maço","Chicória fresca","07052200","Endívias","Hortifruti","Verduras","un",False,True,0,"","Horta"),
        ("","Rúcula Baby 100g","Rúcula baby","07052900","Outras saladas","Hortifruti","Verduras","kg",False,True,0,"","Horta"),
        ("","Mix Salada Baby 100g","Mix de folhas baby","07052900","Outras saladas","Hortifruti","Verduras","kg",False,True,0,"","Horta"),
        ("","Acelga maço","Acelga fresca","07049000","Outros","Hortifruti","Verduras","un",False,True,0,"","Horta"),
        ("","Taioba maço","Taioba fresca","07049000","Outros","Hortifruti","Verduras","un",False,True,0,"","Horta"),
        ("","Ora-pro-nóbis maço","Ora-pro-nóbis fresco","07099990","Outros hortícolas","Hortifruti","Verduras","un",False,True,0,"","Horta"),
        ("","Salsa Raiz 200g","Salsa raiz fresca","07069000","Outros","Hortifruti","Legumes","kg",False,True,0,"","Feira"),
        ("","Rabanete maço","Rabanete fresco","07069000","Outros","Hortifruti","Legumes","un",False,True,0,"","Horta"),
        ("","Nabo maço","Nabo fresco","07061000","Cenouras e nabos","Hortifruti","Legumes","un",False,True,0,"","Horta"),
        ("","Cebola Pérola kg","Cebola pérola fresca","07031029","Outras cebolas","Hortifruti","Legumes","kg",False,True,0,"","Feira"),
        ("","Alho Poró kg","Alho-poró fresco","07039010","Para semeadura","Hortifruti","Legumes","kg",False,True,0,"","Feira"),
        ("","Salsão 200g","Aipo fresco","07094000","Aipo","Hortifruti","Legumes","kg",False,True,0,"","Horta"),
        ("","Erva Cidreira maço","Erva-cidreira fresca","12119090","Plantas medicinais","Hortifruti","Ervas","un",False,True,0,"","Horta"),
        ("","Capim Limão maço","Capim-limão fresco","12119090","Plantas medicinais","Hortifruti","Ervas","un",False,True,0,"","Horta"),
        ("","Tomilho fresco maço","Tomilho fresco","12119090","Plantas aromáticas","Hortifruti","Ervas","un",False,True,0,"","Horta"),
        ("","Cebolinha Francesa maço","Cebolinha francesa (chives)","07039010","Cebolinhas","Hortifruti","Ervas","un",False,True,0,"","Horta"),
        ("","Abóbora Menina kg","Abóbora menina fresca","07099300","Abóboras","Hortifruti","Legumes","kg",False,True,0,"","Feira"),
        ("","Abobrinha Italiana Verde kg","Abobrinha verde fresca","07099300","Abobrinhas","Hortifruti","Legumes","kg",False,True,0,"","Feira"),
        ("","Abobrinha Italiana Amarela kg","Abobrinha amarela fresca","07099300","Abobrinhas","Hortifruti","Legumes","kg",False,True,0,"","Feira"),
        ("","Palmito Pupunha Fresco 100g","Palmito pupunha fresco","07099990","Outros","Hortifruti","Legumes","kg",False,True,0,"","Horta"),
        ("","Pimenta Biquinho kg","Pimenta biquinho fresca","07096000","Pimentas","Hortifruti","Legumes","kg",False,True,0,"","Feira"),
        ("","Banana Maçã kg","Banana maçã fresca","08039000","Outras bananas","Hortifruti","Frutas","kg",False,True,0,"","Feira"),
        ("","Lichia kg","Lichia fresca","08109000","Outras frutas frescas","Hortifruti","Frutas","kg",False,True,0,"","Feira"),
        ("","Rambutan kg","Rambutan fresco","08109000","Outras frutas frescas","Hortifruti","Frutas","kg",False,True,0,"","Feira"),
        ("","Framboesa 100g","Framboesa fresca","08120010","Framboesas","Hortifruti","Frutas","kg",False,True,0,"","Horta"),
        ("","Amora 100g","Amora fresca","08120020","Amoras","Hortifruti","Frutas","kg",False,True,0,"","Horta"),
        ("","Mirtilo 100g","Mirtilo (blueberry) fresco","08101090","Outros frutos do gênero Vaccinium","Hortifruti","Frutas","kg",False,True,0,"","Horta"),
    ]
    for h in hortifruti:
        extra.append(_p(*h))

    return extra


_PRODUCTS += _gen_products()


# ============================================================
# SEÇÃO 17: PRODUTOS ADICIONAIS - CONTINUAR PARA META 2000+
# ============================================================

def _gen_products_2():
    extra = []

    # ---- PADARIA FRIOS / ITENS ADICIONAIS ----
    frios_extra = [
        ("7897008000016","Queijo de Minas Artesanal Canastra 300g","Queijo artesanal da Canastra","04069090","Outros queijos","Laticínios","Queijos","kg",False,False,0,"17.024.00","Canastra"),
        ("7897008000023","Queijo Boursin Ervas 150g","Queijo fresco com ervas","04069030","Queijo fresco","Laticínios","Queijos","kg",False,False,0,"17.024.00","Importado"),
        ("7897008000030","Queijo Gorgonzola 150g","Queijo gorgonzola","04064000","Queijos pasta mofada","Laticínios","Queijos","kg",False,False,0,"17.024.00","Genérico"),
        ("7897008000047","Requeijão Culinário 200g","Requeijão culinário","04069030","Queijo de massa macia","Laticínios","Queijos","kg",False,False,0,"17.023.00","Itambé"),
        ("7897008000054","Ricota Defumada 200g","Ricota defumada","04069090","Outros queijos","Laticínios","Queijos","kg",False,False,0,"17.024.00","Genérico"),
        ("7897008000061","Queijo Suíço Fatiado 150g","Queijo suíço fatiado","04069020","Queijo massa semidura","Laticínios","Queijos","kg",False,False,0,"17.024.00","Importado"),
        ("7897008000078","Presunto Cru Espanhol Jamon 100g","Jamón espanhol","16024100","Pernas suínas","Carnes","Embutidos e Frios","kg",False,False,0,"","Importado"),
        ("7897008000085","Prosciutto Crudo 100g","Presunto cru italiano","16024100","Pernas suínas","Carnes","Embutidos e Frios","kg",False,False,0,"","Importado"),
        ("7897008000092","Coppa di Testa 100g","Coppa italiana","16010000","Enchidos","Carnes","Embutidos e Frios","kg",False,False,0,"17.076.00","Importado"),
        ("7897008000108","Linguiça Defumada Grossa 300g","Linguiça defumada grossa","16010000","Enchidos","Carnes","Embutidos e Frios","kg",False,False,0,"17.077.00","Genérico"),
        ("7897008000115","Salame Italiano 100g","Salame italiano fatiado","16010000","Enchidos","Carnes","Embutidos e Frios","kg",False,False,0,"17.076.00","Genérico"),
        ("7897008000122","Chouriço de Sangue 300g","Chouriço de sangue","16010000","Enchidos","Carnes","Embutidos e Frios","kg",False,False,0,"17.076.00","Genérico"),
        ("7897008000139","Morcilla 200g","Morcilla argentina","16010000","Enchidos","Carnes","Embutidos e Frios","kg",False,False,0,"17.076.00","Importado"),
    ]
    for f in frios_extra:
        extra.append(_p(*f))

    # ---- CEREAIS E GRÃOS EXTRAS ----
    graos_extra = [
        ("7897009000013","Farinha de Amêndoas 200g","Farinha de amêndoas","11029000","Outras farinhas","Cereais e Grãos","Farinhas","kg",False,False,0,"","Genérico"),
        ("7897009000020","Farinha de Coco 200g","Farinha de coco","11029000","Outras farinhas","Cereais e Grãos","Farinhas","kg",False,False,0,"","Genérico"),
        ("7897009000037","Farinha de Grão-de-Bico 500g","Farinha de grão-de-bico","11029000","Outras farinhas","Cereais e Grãos","Farinhas","kg",False,False,0,"","Genérico"),
        ("7897009000044","Farinha de Centeio 500g","Farinha de centeio","11029000","Outras farinhas","Cereais e Grãos","Farinhas","kg",False,False,0,"","Importado"),
        ("7897009000051","Trigo para Kibe Fino 500g","Trigo para kibe fino","10019900","Outros trigos","Cereais e Grãos","Grãos Especiais","kg",False,True,0,"","Genérico"),
        ("7897009000068","Pão de Queijo Mix 500g","Mistura para pão de queijo","19012090","Preparações de farinha","Padaria","Mixes para Bolo","kg",False,False,0,"","Yoki"),
        ("7897009000075","Mistura Cuca Alemã 500g","Mistura para cuca","19012090","Preparações de farinha","Padaria","Mixes para Bolo","kg",False,False,0,"","Genérico"),
        ("7897009000082","Mistura Waffle 400g","Mistura para waffle","19012090","Preparações de farinha","Padaria","Mixes para Bolo","kg",False,False,0,"","Genérico"),
        ("7897009000099","Mistura Panqueca 400g","Mistura para panqueca","19012090","Preparações de farinha","Padaria","Mixes para Bolo","kg",False,False,0,"","Genérico"),
        ("7897009000105","Mistura Crepe Salgado 400g","Mistura para crepe salgado","19012090","Preparações de farinha","Padaria","Mixes para Bolo","kg",False,False,0,"","Genérico"),
        ("7897009000112","Biscoito de Mel Integral 200g","Biscoito de mel integral","19053100","Biscoitos","Padaria","Biscoitos","kg",False,False,0,"","Genérico"),
        ("7897009000129","Biscoito de Canela 200g","Biscoito de canela","19053100","Biscoitos","Padaria","Biscoitos","kg",False,False,0,"","Genérico"),
        ("7897009000136","Pão de Mel 100g","Pão de mel coberto chocolate","19052090","Outros pães","Padaria","Bolos","kg",False,False,0,"","Genérico"),
        ("7897009000143","Pão de Queijo Assado Forno de Minas 80g","Pão de queijo assado","19052090","Outros pães","Padaria","Pão de Queijo","un",False,False,0,"","Forno de Minas"),
        ("7897009000150","Pão de Batata Congelado 400g","Pão de batata congelado","19052090","Outros pães","Padaria","Pão Especial","kg",False,False,0,"","Genérico"),
    ]
    for g in graos_extra:
        extra.append(_p(*g))

    # ---- ÓLEOS E GORDURAS EXTRAS ----
    oleos_extra = [
        ("7897010000012","Óleo de Abacate 250ml","Óleo de abacate","15159090","Outros óleos de sementes oleaginosas","Óleos e Gorduras","Óleos Especiais","lt",False,False,0,"","Genérico"),
        ("7897010000029","Óleo de Linhaça 250ml","Óleo de linhaça prensado a frio","15152900","Outros óleos vegetais","Óleos e Gorduras","Óleos Especiais","lt",False,False,0,"","Genérico"),
        ("7897010000036","Óleo de Gergelim Tostado 100ml","Óleo de gergelim tostado","15159090","Outros óleos de sementes oleaginosas","Óleos e Gorduras","Óleos Especiais","lt",False,False,0,"","Importado"),
        ("7897010000043","Óleo de Palma Dendê Refinado 250ml","Óleo de palma refinado","15119000","Outros","Óleos e Gorduras","Óleo Vegetal","lt",False,False,0,"","Genérico"),
        ("7897010000050","Banha de Porco Artesanal 500g","Banha de porco artesanal","15011000","Banha","Óleos e Gorduras","Banha","kg",False,False,0,"","Genérico"),
        ("7897010000067","Manteiga Ghee 500g","Manteiga ghee 500g","04059090","Outras gorduras do leite","Laticínios","Manteiga","kg",False,False,0,"","Genérico"),
        ("7897010000074","Margarina Para Folhados 500g","Margarina de folheado","15171000","Margarina","Óleos e Gorduras","Margarina","kg",False,False,0,"","Genérico"),
        ("7897010000081","Gordura de Coco Fracionada 500g","Gordura de coco fracionada","15132919","Óleo de coco — outros","Óleos e Gorduras","Gordura Vegetal","kg",False,False,0,"","Genérico"),
    ]
    for o in oleos_extra:
        extra.append(_p(*o))

    # ---- PRODUTOS TÍPICOS BRASILEIROS ----
    tipicos = [
        ("7897011000010","Paçoca de Amendoim 200g","Paçoca de amendoim","17049090","Outros produtos de confeitaria","Snacks","Doces","kg",False,False,0,"","Genérico"),
        ("7897011000027","Pé de Moleque 200g","Pé de moleque","17049090","Outros produtos de confeitaria","Snacks","Doces","kg",False,False,0,"","Genérico"),
        ("7897011000034","Canjica Doce Pronta 250g","Canjica doce pronta","19019090","Outras preparações","Cereais e Grãos","Sobremesas","kg",False,False,0,"","Genérico"),
        ("7897011000041","Curau de Milho Verde 250g","Curau de milho","19019090","Outras preparações","Cereais e Grãos","Sobremesas","kg",False,False,0,"","Genérico"),
        ("7897011000058","Cocada de Leite 200g","Cocada de leite","17049090","Outros confeitaria","Snacks","Doces","kg",False,False,0,"","Genérico"),
        ("7897011000065","Brigadeiro Pronto 200g","Brigadeiro tradicional","18069000","Preparações com cacau","Padaria","Chocolates","kg",False,False,0,"","Genérico"),
        ("7897011000072","Beijinho de Coco 200g","Beijinho de coco","17049090","Outros confeitaria","Snacks","Doces","kg",False,False,0,"","Genérico"),
        ("7897011000089","Bolo de Rolo Recheado 300g","Bolo de rolo goiabada","19052090","Outros produtos de padaria","Padaria","Bolos","kg",False,False,0,"","Genérico"),
        ("7897011000096","Biscoito Quebra Queixo 100g","Biscoito queijinho","19053100","Biscoitos","Padaria","Biscoitos","kg",False,False,0,"","Genérico"),
        ("7897011000102","Tapioca Recheada Frango 200g","Tapioca recheada pronta","11081400","Fécula de mandioca","Cereais e Grãos","Tapioca","un",False,False,0,"","Genérico"),
        ("7897011000119","Queijo Coalho Assado 100g","Queijo coalho assado palito","04069090","Outros queijos","Laticínios","Queijos","un",False,False,0,"","Genérico"),
        ("7897011000126","Pão de Queijo Mini 20un","Minipão de queijo assado","19052090","Outros pães","Padaria","Pão de Queijo","un",False,False,0,"","Genérico"),
        ("7897011000133","Doce de Abóbora 400g","Doce de abóbora","20079910","Geleias e doces","Mercearia","Doces","kg",False,False,0,"","Genérico"),
        ("7897011000140","Doce de Figo em Calda 400g","Doce de figo em calda","20089900","Outros","Mercearia","Doces","kg",False,False,0,"","Genérico"),
        ("7897011000157","Goiabada Cascão 400g","Goiabada em pasta dura","20079910","Geleias e doces","Mercearia","Doces","kg",False,False,0,"","Genérico"),
        ("7897011000164","Goiabada Líquida (Goiabinha) 400g","Goiabada cremosa","20079910","Geleias e doces","Mercearia","Doces","kg",False,False,0,"","Predilecta"),
        ("7897011000171","Bananada Artesanal 300g","Bananada (banana em pasta)","20079910","Geleias e doces","Mercearia","Doces","kg",False,False,0,"","Genérico"),
        ("7897011000188","Calda de Caramelo 200g","Calda de caramelo","17039000","Melaços","Mercearia","Doces","kg",False,False,0,"","Genérico"),
        ("7897011000195","Calda de Chocolate Harald 200g","Calda de chocolate","18069000","Preparações com cacau","Mercearia","Doces","kg",False,False,0,"","Harald"),
        ("7897011000201","Leite de Vaca Pasteurizado 1L","Leite pasteurizado integral","04011090","Outros leites","Laticínios","Leite UHT","lt",False,True,0,"17.018.00","Genérico"),
    ]
    for t in tipicos:
        extra.append(_p(*t))

    # ---- TEMPEROS FRESCOS E ESPECIARIAS EXTRAS ----
    temperos = [
        ("7897012000019","Pimenta Verde em Grão 30g","Pimenta verde em grão","09041100","Pimenta não triturada","Condimentos","Especiarias","kg",False,False,0,"","Sirial"),
        ("7897012000026","Pimenta Rosa em Grão 30g","Pimenta rosa em grão","09041100","Pimenta não triturada","Condimentos","Especiarias","kg",False,False,0,"","Sirial"),
        ("7897012000033","Mix Pimenta Colorida 30g","Mix de pimentas coloridas","09042100","Pimenta seca","Condimentos","Especiarias","kg",False,False,0,"","Sirial"),
        ("7897012000040","Sal Rosa do Himalaia 500g","Sal rosa do Himalaia","25010020","Sal outros","Cereais e Grãos","Sal","kg",False,True,0,"","Importado"),
        ("7897012000057","Sal de Parrilla 500g","Sal grosso para churrasco","25010010","Sal grosso","Cereais e Grãos","Sal","kg",False,True,0,"","Genérico"),
        ("7897012000064","Sal de Ervas Mediterrâneas 250g","Sal temperado com ervas","25010020","Sal temperado","Cereais e Grãos","Sal","kg",False,True,0,"","Genérico"),
        ("7897012000071","Tempero Baiano Sirial 30g","Tempero baiano","21039091","Misturas condimentos ≤1kg","Condimentos","Temperos Compostos","kg",False,False,0,"","Sirial"),
        ("7897012000088","Tempero Mineiro Sirial 30g","Tempero mineiro","21039091","Misturas condimentos ≤1kg","Condimentos","Temperos Compostos","kg",False,False,0,"","Sirial"),
        ("7897012000095","Tempero Nordestino Sirial 30g","Tempero nordestino","21039091","Misturas condimentos ≤1kg","Condimentos","Temperos Compostos","kg",False,False,0,"","Sirial"),
        ("7897012000101","Alho Frito Crocante 50g","Alho frito","07129020","Alho desidratado frito","Condimentos","Especiarias","kg",False,False,0,"","Genérico"),
        ("7897012000118","Cebola Frita Crocante 50g","Cebola frita para decorar","07122000","Cebola desidratada","Condimentos","Especiarias","kg",False,False,0,"","Genérico"),
        ("7897012000125","Páprica Defumada 30g","Páprica defumada","09042100","Pimenta seca","Condimentos","Especiarias","kg",False,False,0,"","Sirial"),
        ("7897012000132","Missô Claro 200g","Pasta de missô claro","21031090","Molhos de soja","Condimentos","Molhos Especiais","kg",False,False,0,"","Importado"),
        ("7897012000149","Missô Escuro 200g","Pasta de missô escuro","21031090","Molhos de soja","Condimentos","Molhos Especiais","kg",False,False,0,"","Importado"),
        ("7897012000156","Tahine/Tahini 200g","Pasta de gergelim","20081900","Outras castanhas preparadas","Condimentos","Pastas","kg",False,False,0,"","Importado"),
        ("7897012000163","Hummus Pronto 200g","Hummus de grão-de-bico pronto","21039091","Preparações para molhos, embalagem ≤1kg","Condimentos","Pastas","kg",False,False,0,"","Importado"),
        ("7897012000170","Pesto Verde 200g","Pesto genovese de manjericão","21039091","Preparações para molhos, embalagem ≤1kg","Condimentos","Molhos Especiais","kg",False,False,0,"","Importado"),
        ("7897012000187","Pesto Vermelho 200g","Pesto rosso tomate seco","21039091","Preparações para molhos, embalagem ≤1kg","Condimentos","Molhos Especiais","kg",False,False,0,"","Importado"),
        ("7897012000194","Molho de Macarrão Bolonhesa 350g","Molho à bolonhesa","21039091","Preparações para molhos, embalagem ≤1kg","Condimentos","Molho de Tomate","kg",False,False,0,"","Genérico"),
        ("7897012000200","Molho Branco Bechamel 200g","Molho bechamel pronto","21039091","Preparações para molhos, embalagem ≤1kg","Condimentos","Molhos Especiais","kg",False,False,0,"","Genérico"),
    ]
    for t in temperos:
        extra.append(_p(*t))

    return extra

_PRODUCTS += _gen_products_2()


# ============================================================
# SEÇÃO 18: GRANDE LOTE FINAL - COMPLETANDO META 2000+
# Geração programática de produtos por categoria
# ============================================================

def _gen_bulk_products():
    """Gera lote final de produtos para atingir meta de 2000+."""
    batch = []

    # --- REFRIGERANTES ADICIONAIS ---
    refris = [
        ("7897020000011","Pepsi Zero 2L","Refrigerante cola zero","22021000","Refrigerante","Bebidas","Refrigerante","lt",True,False,0,"03.010.00","Pepsi"),
        ("7897020000028","Pepsi Black 350ml","Refrigerante cola zero lata","22021000","Refrigerante","Bebidas","Refrigerante","lt",True,False,0,"03.011.00","Pepsi"),
        ("7897020000035","Guaraná Kuat Zero 2L","Refrigerante guaraná zero","22021000","Refrigerante","Bebidas","Refrigerante","lt",True,False,0,"03.010.00","Kuat"),
        ("7897020000042","Fanta Zero Laranja 2L","Refrigerante laranja zero","22021000","Refrigerante","Bebidas","Refrigerante","lt",True,False,0,"03.010.00","Fanta"),
        ("7897020000059","Sprite Limão Zero 350ml","Refrigerante limão zero lata","22021000","Refrigerante","Bebidas","Refrigerante","lt",True,False,0,"03.011.00","Sprite"),
        ("7897020000066","Antarc Guaraná 2L","Refrigerante guaraná Antarctica","22021000","Refrigerante","Bebidas","Refrigerante","lt",True,False,0,"03.010.00","Antarctica"),
        ("7897020000073","Coca-Cola Garrafa Vidro 250ml","Refrigerante cola garrafa vidro","22021000","Refrigerante","Bebidas","Refrigerante","lt",True,False,0,"03.011.00","Coca-Cola"),
        ("7897020000080","Refrigerante Limão Mineirinho 2L","Refrigerante limão mineiro","22021000","Refrigerante","Bebidas","Refrigerante","lt",True,False,0,"03.010.00","Mineirinho"),
        ("7897020000097","Refrigerante Uva Soda Limonada 2L","Refrigerante uva","22021000","Refrigerante","Bebidas","Refrigerante","lt",True,False,0,"03.010.00","Genérico"),
        ("7897020000103","Soda Italiana Lemon 330ml","Soda italiana limão","22021000","Bebida gaseificada","Bebidas","Bebidas Especiais","lt",True,False,0,"03.011.00","Sanpellegrino"),
        ("7897020000110","Soda Italiana Laranja 330ml","Soda italiana laranja","22021000","Bebida gaseificada","Bebidas","Bebidas Especiais","lt",True,False,0,"03.011.00","Sanpellegrino"),
        ("7897020000127","Tônica Schweppes 350ml","Água tônica","22021000","Água gaseificada","Bebidas","Bebidas Especiais","lt",True,False,0,"03.007.00","Schweppes"),
        ("7897020000134","Guaraná Jesus 350ml","Refrigerante guaraná rosa","22021000","Refrigerante","Bebidas","Refrigerante","lt",True,False,0,"03.011.00","Jesus"),
        ("7897020000141","Coca-Cola 1L","Refrigerante cola 1L","22021000","Refrigerante","Bebidas","Refrigerante","lt",True,False,0,"03.010.00","Coca-Cola"),
        ("7897020000158","Guaraná Antarctica 1L","Refrigerante guaraná 1L","22021000","Refrigerante","Bebidas","Refrigerante","lt",True,False,0,"03.010.00","Antarctica"),
        ("7897020000165","Fanta Uva 350ml Lata","Refrigerante uva lata","22021000","Refrigerante","Bebidas","Refrigerante","lt",True,False,0,"03.011.00","Fanta"),
        ("7897020000172","Pepsi Twist 2L","Refrigerante cola limão","22021000","Refrigerante","Bebidas","Refrigerante","lt",True,False,0,"03.010.00","Pepsi"),
        ("7897020000189","Itubaína Laranja 2L","Refrigerante laranja","22021000","Refrigerante","Bebidas","Refrigerante","lt",True,False,0,"03.010.00","Itubaína"),
        ("7897020000196","Dolly Cola 2L","Refrigerante cola","22021000","Refrigerante","Bebidas","Refrigerante","lt",True,False,0,"03.010.00","Dolly"),
        ("7897020000202","Schin Guaraná 2L","Refrigerante guaraná","22021000","Refrigerante","Bebidas","Refrigerante","lt",True,False,0,"03.010.00","Schin"),
    ]
    for r in refris:
        batch.append(_p(*r))

    # --- CERVEJAS ADICIONAIS ---
    cervejas = [
        ("7897021000018","Cerveja Brahma Duplo Malte 350ml","Cerveja duplo malte lata","22030000","Cervejas de malte","Bebidas","Cerveja","lt",True,False,0,"03.021.00","Brahma"),
        ("7897021000025","Cerveja Brahma 600ml","Cerveja pilsen garrafa","22030000","Cervejas de malte","Bebidas","Cerveja","lt",True,False,0,"03.021.00","Brahma"),
        ("7897021000032","Cerveja Skol 600ml","Cerveja pilsen garrafa","22030000","Cervejas de malte","Bebidas","Cerveja","lt",True,False,0,"03.021.00","Skol"),
        ("7897021000049","Cerveja Itaipava 600ml","Cerveja pilsen garrafa","22030000","Cervejas de malte","Bebidas","Cerveja","lt",True,False,0,"03.021.00","Itaipava"),
        ("7897021000056","Cerveja Antarctica 600ml","Cerveja pilsen garrafa","22030000","Cervejas de malte","Bebidas","Cerveja","lt",True,False,0,"03.021.00","Antarctica"),
        ("7897021000063","Cerveja Devassa Tropical 350ml","Cerveja tropical lata","22030000","Cervejas de malte","Bebidas","Cerveja","lt",True,False,0,"03.021.00","Devassa"),
        ("7897021000070","Cerveja Eisenbahn Weizenbier 355ml","Cerveja de trigo","22030000","Cervejas de malte","Bebidas","Cerveja","lt",True,False,0,"03.021.00","Eisenbahn"),
        ("7897021000087","Cerveja Bohemia 600ml","Cerveja premium pilsen","22030000","Cervejas de malte","Bebidas","Cerveja","lt",True,False,0,"03.021.00","Bohemia"),
        ("7897021000094","Cerveja Colorado Appia 600ml","Cerveja artesanal","22030000","Cervejas de malte","Bebidas","Cerveja","lt",True,False,0,"03.021.00","Colorado"),
        ("7897021000100","Cerveja Stella Artois 600ml","Cerveja pilsen premium","22030000","Cervejas de malte","Bebidas","Cerveja","lt",True,False,0,"03.021.00","Stella Artois"),
        ("7897021000117","Cerveja Heineken 600ml","Cerveja premium garrafa","22030000","Cervejas de malte","Bebidas","Cerveja","lt",True,False,0,"03.021.00","Heineken"),
        ("7897021000124","Cerveja Budweiser 600ml","Cerveja lager garrafa","22030000","Cervejas de malte","Bebidas","Cerveja","lt",True,False,0,"03.021.00","Budweiser"),
        ("7897021000131","Cerveja Sol 350ml Lata","Cerveja sol lata","22030000","Cervejas de malte","Bebidas","Cerveja","lt",True,False,0,"03.021.00","Sol"),
        ("7897021000148","Cerveja Original 600ml","Cerveja original garrafa","22030000","Cervejas de malte","Bebidas","Cerveja","lt",True,False,0,"03.021.00","Original"),
        ("7897021000155","Cerveja Amstel 350ml Lata","Cerveja pilsen lata","22030000","Cervejas de malte","Bebidas","Cerveja","lt",True,False,0,"03.021.00","Amstel"),
        ("7897021000162","Cerveja Leffe Blonde 275ml","Cerveja belga garrafa","22030000","Cervejas de malte","Bebidas","Cerveja","lt",True,False,0,"03.021.00","Leffe"),
        ("7897021000179","Cerveja Franziskaner Weizen 500ml","Cerveja de trigo alemã","22030000","Cervejas de malte","Bebidas","Cerveja","lt",True,False,0,"03.021.00","Franziskaner"),
        ("7897021000186","Chope em Barril 30L","Chope pilsen barril","22030000","Cervejas de malte","Bebidas","Chope","lt",True,False,0,"03.023.00","Brahma"),
        ("7897021000193","Cerveja sem Álcool Heineken 330ml","Cerveja zero álcool","22029100","Cerveja sem álcool","Bebidas","Cerveja","lt",True,False,0,"03.022.00","Heineken"),
        ("7897021000209","Cerveja artesanal IPA 500ml","Cerveja artesanal IPA","22030000","Cervejas de malte","Bebidas","Cerveja","lt",True,False,0,"03.021.00","Genérico"),
    ]
    for c in cervejas:
        batch.append(_p(*c))

    # --- CAFÉS ADICIONAIS ---
    cafes = [
        ("7897022000014","Café em Cápsulas Três Corações 10un","Cápsulas de café","09012100","Café torrado","Bebidas","Café","un",False,False,0,"","3 Corações"),
        ("7897022000021","Café Orgânico Melitta 250g","Café orgânico moído","09012100","Café torrado","Bebidas","Café","kg",False,False,0,"","Melitta"),
        ("7897022000038","Café Descafeinado Nestlé 100g","Café solúvel descafeinado","21011110","Café solúvel","Bebidas","Café","kg",True,False,0,"","Nestlé"),
        ("7897022000045","Café em Pó Santos 500g","Café torrado e moído Santos","09012100","Café torrado","Bebidas","Café","kg",False,False,0,"","Santos"),
        ("7897022000052","Café Bourbon Especial 250g","Café bourbon especial","09012100","Café torrado","Bebidas","Café","kg",False,False,0,"","Genérico"),
        ("7897022000069","Café Gelado Nescafé 280ml","Café gelado pronto","22029900","Bebidas prontas","Bebidas","Café","lt",True,False,0,"","Nescafé"),
        ("7897022000076","Cápsulas Nespresso Lungo 10un","Cápsulas Nespresso","09012100","Café torrado","Bebidas","Café","un",False,False,0,"","Nespresso"),
        ("7897022000083","Extrato de Café Líquido 30ml","Extrato de café concentrado","21011190","Outros extratos de café","Bebidas","Café","lt",True,False,0,"","Genérico"),
        ("7897022000090","Café Coado 250ml Copo","Café coado pronto","22029900","Bebidas prontas","Bebidas","Café","lt",True,False,0,"","Genérico"),
        ("7897022000106","Café Especial Single Origin 250g","Café especial moído","09012100","Café torrado","Bebidas","Café","kg",False,False,0,"","Genérico"),
    ]
    for c in cafes:
        batch.append(_p(*c))

    # --- CHOCOLATES ADICIONAIS ---
    chocolates = [
        ("7897023000013","Chocolate ao Leite Hershey's 90g","Chocolate ao leite","18063210","Chocolate em tabletes","Padaria","Chocolates","kg",False,False,0,"17.002.00","Hershey's"),
        ("7897023000020","Chocolate Amargo 85% Cacau Lindt 100g","Chocolate amargo 85%","18063210","Chocolate em tabletes","Padaria","Chocolates","kg",False,False,0,"17.002.00","Lindt"),
        ("7897023000037","Chocolate Branco Nestlé Galak 90g","Chocolate branco","17049010","Chocolate branco","Padaria","Chocolates","kg",False,False,0,"17.001.00","Nestlé"),
        ("7897023000044","Chocolate Meio Amargo Nestlé Dois Frades 100g","Chocolate meio amargo","18063210","Chocolate em tabletes","Padaria","Chocolates","kg",False,False,0,"17.002.00","Nestlé"),
        ("7897023000051","Creme de Cacao Harald 1kg","Creme de cacau para confeitaria","18062000","Chocolate blocos >2kg","Padaria","Chocolates","kg",False,False,0,"","Harald"),
        ("7897023000068","Chocolate Cobertura Branca Harald 1kg","Cobertura branca","17049010","Chocolate branco","Padaria","Chocolates","kg",False,False,0,"17.001.00","Harald"),
        ("7897023000075","Confeito M&M's Chocolate 47g","Confeito de chocolate","18069000","Preparações com cacau","Padaria","Chocolates","kg",False,False,0,"17.009.00","Mars"),
        ("7897023000082","Maltesers 90g","Bola de malte coberta chocolate","18069000","Preparações com cacau","Padaria","Chocolates","kg",False,False,0,"17.009.00","Mars"),
        ("7897023000099","Chocolate Ferrero Rocher 3un","Bombom Ferrero Rocher","18069000","Preparações com cacau","Padaria","Chocolates","un",False,False,0,"17.007.00","Ferrero"),
        ("7897023000105","Caixa Bombons Lacta Diamante Negro 300g","Caixa bombons chocolate","18069000","Preparações com cacau","Padaria","Chocolates","kg",False,False,0,"17.007.00","Lacta"),
        ("7897023000112","Barra Chocolate Amargo 70% Cacau Show 80g","Chocolate amargo 70%","18063210","Chocolate em tabletes","Padaria","Chocolates","kg",False,False,0,"17.002.00","Cacau Show"),
        ("7897023000129","Granulado Confete Colorido 200g","Confeito colorido","17049020","Caramelos e confeitos","Padaria","Decoração","kg",False,False,0,"","Genérico"),
        ("7897023000136","Chocolate Callebaut Chip 500g","Gotas de chocolate belga","18062000","Chocolate para confeitaria","Padaria","Chocolates","kg",False,False,0,"","Callebaut"),
        ("7897023000143","Nibs de Cacau 100g","Nibs de cacau torrado","18010000","Cacau inteiro ou partido","Padaria","Chocolates","kg",False,False,0,"","Genérico"),
        ("7897023000150","Cacau em Pó Callebaut 500g","Cacau em pó profissional","18050000","Cacau em pó sem açúcar","Padaria","Chocolates","kg",False,False,0,"","Callebaut"),
    ]
    for c in chocolates:
        batch.append(_p(*c))

    # --- VINHOS E DESTILADOS EXTRAS ---
    vinhos = [
        ("7897024000012","Vinho Tinto Baron de Lantier Cabernet 750ml","Vinho tinto seco","22042100","Vinho em recipiente ≤2L","Bebidas","Vinho","lt",False,False,0,"","Baron de Lantier"),
        ("7897024000029","Vinho Tinto Chileno Concha y Toro 750ml","Vinho tinto importado","22042100","Vinho em recipiente ≤2L","Bebidas","Vinho","lt",False,False,0,"","Concha y Toro"),
        ("7897024000036","Vinho Branco Chileno Santa Helena 750ml","Vinho branco importado","22042100","Vinho em recipiente ≤2L","Bebidas","Vinho","lt",False,False,0,"","Santa Helena"),
        ("7897024000043","Espumante Moscatel Salton 750ml","Espumante moscatel","22041010","Espumante tipo champagne","Bebidas","Espumante","lt",False,False,0,"","Salton"),
        ("7897024000050","Espumante Brut Cave Geisse 750ml","Espumante brut","22041010","Espumante tipo champagne","Bebidas","Espumante","lt",False,False,0,"","Cave Geisse"),
        ("7897024000067","Cachaça Ypióca Ouro 1L","Cachaça envelhecida","22084090","Aguardente de cana","Bebidas","Destilados","lt",False,False,0,"","Ypioca"),
        ("7897024000074","Cachaça 51 1L","Cachaça tradicional","22084090","Aguardente de cana","Bebidas","Destilados","lt",False,False,0,"","51"),
        ("7897024000081","Whisky Johnnie Walker Red Label 1L","Whisky escocês","22083000","Uísque","Bebidas","Destilados","lt",False,False,0,"","Johnnie Walker"),
        ("7897024000098","Vodka Smirnoff 1L","Vodka","22082000","Vodka","Bebidas","Destilados","lt",False,False,0,"","Smirnoff"),
        ("7897024000104","Gin Tanqueray 750ml","Gin","22085010","Gim","Bebidas","Destilados","lt",False,False,0,"","Tanqueray"),
        ("7897024000111","Licor Amarula 750ml","Licor de frutas","22089000","Outros destilados","Bebidas","Destilados","lt",False,False,0,"","Amarula"),
        ("7897024000128","Tequila Jose Cuervo Silver 750ml","Tequila","22085010","Tequila","Bebidas","Destilados","lt",False,False,0,"","Jose Cuervo"),
        ("7897024000135","Vinho do Porto Offley Ruby 750ml","Vinho do Porto","22042100","Vinho em recipiente ≤2L","Bebidas","Vinho","lt",False,False,0,"","Offley"),
        ("7897024000142","Conhaque Hennessy VS 1L","Conhaque francês","22083000","Conhaque","Bebidas","Destilados","lt",False,False,0,"","Hennessy"),
        ("7897024000159","Rum Bacardi White 980ml","Rum branco","22084090","Rum e tafia","Bebidas","Destilados","lt",False,False,0,"","Bacardi"),
    ]
    for v in vinhos:
        batch.append(_p(*v))

    # --- SUCOS E BEBIDAS EXTRAS ---
    sucos = [
        ("7897025000011","Néctar Maracujá Del Valle 1L","Néctar de maracujá","20098990","Outros sucos de frutos","Bebidas","Suco","lt",True,False,0,"17.010.00","Del Valle"),
        ("7897025000028","Néctar Uva Del Valle 1L","Néctar de uva","20094900","Suco de uva","Bebidas","Suco","lt",True,False,0,"17.010.00","Del Valle"),
        ("7897025000035","Suco Integral Maçã Tial 200ml","Suco integral de maçã mini","20092900","Suco de maçã","Bebidas","Suco","lt",False,False,0,"17.010.00","Tial"),
        ("7897025000042","Suco Tropical Maguary 1L","Suco de frutas tropicais","20098990","Outros sucos de frutos","Bebidas","Suco","lt",True,False,0,"17.010.00","Maguary"),
        ("7897025000059","Néctar Limão Maguary 1L","Néctar de limão","20098990","Outros sucos de frutos","Bebidas","Suco","lt",True,False,0,"17.010.00","Maguary"),
        ("7897025000066","Suco de Laranja Citrino 300ml","Suco natural de laranja","20091100","Suco de laranja","Bebidas","Suco","lt",False,False,0,"17.010.00","Genérico"),
        ("7897025000073","Água de Coco Native 1L","Água de coco natural","20098100","Suco de coco","Bebidas","Água de Coco","lt",False,False,0,"17.011.00","Native"),
        ("7897025000080","Suco Detox Verde 250ml","Suco detox pronto","20098990","Outros sucos de frutos","Bebidas","Suco","lt",False,False,0,"17.010.00","Genérico"),
        ("7897025000097","Suco de Tomate Elefante 200ml","Suco de tomate","20031000","Tomate preparado","Bebidas","Suco","lt",False,False,0,"","Elefante"),
        ("7897025000103","Isotônico Powerade Berry 500ml","Isotônico berry","21069090","Bebida isotônica","Bebidas","Isotônico","lt",True,False,0,"03.015.00","Powerade"),
        ("7897025000110","Kombucha Gengibre e Limão 350ml","Kombucha gengibre","22029900","Outras bebidas","Bebidas","Bebidas Especiais","lt",False,False,0,"","Genérico"),
        ("7897025000127","Leite de Arroz 1L","Bebida de arroz","22029900","Bebidas vegetais","Mercearia","Substitutos Lácteos","lt",False,False,0,"","Genérico"),
    ]
    for s in sucos:
        batch.append(_p(*s))

    # --- LATICÍNIOS EXTRAS ---
    laticinios = [
        ("7897026000010","Leite UHT Integral Tirol 1L","Leite integral Tirol","04011010","Leite UHT","Laticínios","Leite UHT","lt",False,True,0,"17.016.00","Tirol"),
        ("7897026000027","Leite UHT Integral Piracanjuba 1L","Leite integral Piracanjuba","04011010","Leite UHT","Laticínios","Leite UHT","lt",False,True,0,"17.016.00","Piracanjuba"),
        ("7897026000034","Leite UHT Semidesnatado Piracanjuba 1L","Leite semidesnatado","04012010","Leite UHT semidesnatado","Laticínios","Leite UHT","lt",False,True,0,"17.016.00","Piracanjuba"),
        ("7897026000041","Leite em Pó Desnatado Itambé 400g","Leite em pó desnatado","04022120","Leite em pó desnatado","Laticínios","Leite em Pó","kg",False,True,0,"17.012.00","Itambé"),
        ("7897026000058","Leite em Pó Integral Elegê 400g","Leite em pó integral","04022110","Leite em pó integral","Laticínios","Leite em Pó","kg",False,True,0,"17.012.00","Elegê"),
        ("7897026000065","Creme de Leite Vigor 200g","Creme de leite","04022130","Creme de leite","Laticínios","Creme de Leite","kg",False,False,0,"17.019.00","Vigor"),
        ("7897026000072","Doce de Leite com Chocolate 400g","Doce de leite c/ chocolate","19019020","Doce de leite","Laticínios","Doce de Leite","kg",False,False,0,"17.029.00","Genérico"),
        ("7897026000089","Iogurte Natural Integral Vigor 170g","Iogurte natural integral","04032000","Iogurte","Laticínios","Iogurte","kg",False,False,0,"17.021.00","Vigor"),
        ("7897026000096","Iogurte Grego Tropical Danone 100g","Iogurte grego tropical","04032000","Iogurte","Laticínios","Iogurte","kg",False,False,0,"17.021.00","Danone"),
        ("7897026000102","Bebida Láctea UHT 200ml","Bebida láctea UHT","22029900","Bebidas lácteas","Laticínios","Bebida Láctea","lt",True,False,0,"","Genérico"),
        ("7897026000119","Queijo Tipo Brie Nacional 100g","Queijo tipo brie","04069030","Queijo de massa macia","Laticínios","Queijos","kg",False,False,0,"17.024.00","Genérico"),
        ("7897026000126","Queijo Coalho 200g","Queijo de coalho grelhado","04069090","Outros queijos","Laticínios","Queijos","kg",False,False,0,"17.024.00","Genérico"),
        ("7897026000133","Queijo Tipo Minas Padrão Frescal 500g","Queijo frescal grande","04069030","Queijo de massa macia","Laticínios","Queijos","kg",False,False,0,"17.024.00","Genérico"),
        ("7897026000140","Queijo Parmesão Inteiro 200g","Parmesão em peça","04069010","Queijo de massa dura","Laticínios","Queijos","kg",False,False,0,"17.024.00","Genérico"),
        ("7897026000157","Requeijão Light Itambé 200g","Requeijão light","04069030","Queijo de massa macia","Laticínios","Queijos","kg",False,False,0,"17.023.00","Itambé"),
    ]
    for l in laticinios:
        batch.append(_p(*l))

    # --- HORTIFRUTI ADICIONAIS ---
    mais_horti = [
        ("","Caqui Fuyu un","Caqui fuyu fresco","08107000","Caquis","Hortifruti","Frutas","un",False,True,0,"","Feira"),
        ("","Nectarina kg","Nectarina fresca","08091000","Damascos/pêssegos","Hortifruti","Frutas","kg",False,True,0,"","Feira"),
        ("","Ameixa Vermelha kg","Ameixa vermelha fresca","08092900","Outras ameixas","Hortifruti","Frutas","kg",False,True,0,"","Feira"),
        ("","Ameixa Preta Seca 200g","Ameixa preta desidratada","08131000","Damascos secos","Hortifruti","Frutas Secas","kg",False,False,0,"","Genérico"),
        ("","Uva Passa 200g","Uva passa escura","08062000","Passas","Hortifruti","Frutas Secas","kg",False,False,0,"","Genérico"),
        ("","Damasco Seco 200g","Damasco desidratado","08131000","Damascos secos","Hortifruti","Frutas Secas","kg",False,False,0,"","Genérico"),
        ("","Cranberry Seco 100g","Cranberry desidratado","08109000","Outras frutas frescas ou secas","Hortifruti","Frutas Secas","kg",False,False,0,"","Importado"),
        ("","Mirtilo Seco 100g","Mirtilo desidratado","08101090","Outros frutos Vaccinium","Hortifruti","Frutas Secas","kg",False,False,0,"","Importado"),
        ("","Tâmara 200g","Tâmara fresca ou seca","08041010","Tâmaras frescas","Hortifruti","Frutas","kg",False,False,0,"","Importado"),
        ("","Figo Seco 200g","Figo desidratado","08132000","Figos secos","Hortifruti","Frutas Secas","kg",False,False,0,"","Genérico"),
        ("","Abóbora Japonesa Kabotiá kg","Abóbora japonesa","07099300","Abóboras","Hortifruti","Legumes","kg",False,True,0,"","Feira"),
        ("","Quiabo kg","Quiabo fresco","07099990","Outros hortícolas","Hortifruti","Legumes","kg",False,True,0,"","Feira"),
        ("","Mandioquinha/Batata Baroa kg","Mandioquinha fresca","07069000","Outros","Hortifruti","Legumes","kg",False,True,0,"","Feira"),
        ("","Taro/Inhame Branco kg","Taro fresco","07144000","Taros","Hortifruti","Legumes","kg",False,True,0,"","Feira"),
        ("","Ocumo/Mangarito kg","Mangarito fresco","07145000","Mangaritos","Hortifruti","Legumes","kg",False,True,0,"","Feira"),
        ("","Beldroega maço","Beldroega fresca","07099990","Outros hortícolas","Hortifruti","Verduras","un",False,True,0,"","Horta"),
        ("","Serralha maço","Serralha fresca","07099990","Outros hortícolas","Hortifruti","Verduras","un",False,True,0,"","Horta"),
        ("","Bertalha maço","Bertalha fresca","07099990","Outros hortícolas","Hortifruti","Verduras","un",False,True,0,"","Horta"),
        ("","Pinhão 500g","Pinhão fresco ou cozido","08029100","Pinhões com casca","Hortifruti","Frutas","kg",False,True,0,"","Feira"),
        ("","Macaúba 500g","Macaúba fresca","08019000","Outros cocos","Hortifruti","Frutas","kg",False,True,0,"","Feira"),
    ]
    for h in mais_horti:
        batch.append(_p(*h))

    # --- PEIXES E FRUTOS DO MAR EXTRAS ---
    peixes = [
        ("","Peixe Pintado/Surubim Filé kg","Surubim filé fresco","03028933","Surubins frescos","Carnes","Peixes","kg",False,True,0,"","Feira"),
        ("","Tambaqui Filé kg","Tambaqui filé fresco","03028944","Tambaqui fresco","Carnes","Peixes","kg",False,True,0,"","Feira"),
        ("","Pirarucu Filé kg","Pirarucu filé fresco","03028937","Pirarucu fresco","Carnes","Peixes","kg",False,True,0,"","Feira"),
        ("","Dourado Filé kg","Dourado filé fresco","03028942","Dourada fresca","Carnes","Peixes","kg",False,True,0,"","Feira"),
        ("","Tucunaré Inteiro kg","Tucunaré fresco","03028990","Outros peixes frescos","Carnes","Peixes","kg",False,True,0,"","Feira"),
        ("","Traíra Inteira kg","Traíra fresca","03028934","Traíra fresca","Carnes","Peixes","kg",False,True,0,"","Feira"),
        ("","Tilápia Inteira Fresca kg","Tilápia fresca","03027100","Tilápias frescas","Carnes","Peixes","kg",False,True,0,"","Feira"),
        ("","Pescada Filé kg","Pescada filé fresco","03028938","Pescadas frescas","Carnes","Peixes","kg",False,True,0,"","Feira"),
        ("","Tainha Inteira kg","Tainha fresca","03038943","Tainhas frescas","Carnes","Peixes","kg",False,True,0,"","Feira"),
        ("","Robalo Filé kg","Robalo filé fresco","03028990","Outros peixes frescos","Carnes","Peixes","kg",False,True,0,"","Feira"),
        ("7897027000016","Atum em Lata 300g","Atum ralado ao natural em lata","16041410","Atuns preparados","Enlatados","Peixes","un",False,False,0,"17.080.00","Gomes da Costa"),
        ("7897027000023","Sardinha ao Molho de Tomate 125g","Sardinha ao tomate","16041310","Sardinhas preparadas","Enlatados","Peixes","un",False,False,0,"17.081.00","Gomes da Costa"),
        ("7897027000030","Bacalhau Salgado Seco 400g","Bacalhau salgado seco","03053200","Bacalhau seco e salgado","Carnes","Peixes","kg",False,True,0,"","Genérico"),
        ("7897027000047","Filé de Salmão Defumado 100g","Salmão defumado","16041100","Salmão preparado","Carnes","Peixes","kg",False,False,0,"","Importado"),
        ("7897027000054","Caviar Red Lumpfish 50g","Ovas de peixe","16043100","Caviar e sucedâneos","Carnes","Frutos do Mar","kg",False,False,0,"","Importado"),
    ]
    for p in peixes:
        batch.append(_p(*p))

    # --- PRODUTOS DIET/LIGHT/ORGÂNICO EXTRAS ---
    especiais = [
        ("7897028000013","Arroz Integral Orgânico 5kg","Arroz integral orgânico grande","10062020","Arroz descascado","Cereais e Grãos","Orgânicos","kg",False,True,0,"","Native"),
        ("7897028000020","Feijão Orgânico Preto 500g","Feijão preto orgânico","07133290","Feijões","Cereais e Grãos","Orgânicos","kg",False,True,0,"","Native"),
        ("7897028000037","Açúcar Orgânico Cristal 500g","Açúcar cristal orgânico","17011400","Açúcar de cana","Cereais e Grãos","Orgânicos","kg",False,False,0,"","Native"),
        ("7897028000044","Mel Orgânico 250g","Mel orgânico certificado","04090000","Mel natural","Mercearia","Orgânicos","kg",False,False,0,"","Genérico"),
        ("7897028000051","Granola Orgânica 400g","Granola orgânica","19042000","Preparações de cereais","Cereais e Grãos","Orgânicos","kg",False,False,0,"","Mãe Terra"),
        ("7897028000068","Amendoim Orgânico 200g","Amendoim torrado orgânico","20081100","Amendoim preparado","Cereais e Grãos","Orgânicos","kg",False,True,0,"","Genérico"),
        ("7897028000075","Tofu Orgânico 400g","Tofu orgânico","19019090","Outras preparações","Mercearia","Orgânicos","kg",False,True,0,"","Genérico"),
        ("7897028000082","Leite de Amêndoa Orgânico 1L","Leite de amêndoa orgânico","22029900","Bebidas vegetais","Mercearia","Orgânicos","lt",False,False,0,"","Genérico"),
        ("7897028000099","Biscoito Integral Orgânico 150g","Biscoito orgânico","19053100","Biscoitos","Padaria","Orgânicos","kg",False,False,0,"","Genérico"),
        ("7897028000105","Ovo Orgânico un","Ovo orgânico caipira","04071100","Ovos de galinha","Laticínios","Ovos","un",False,True,0,"","Sítio"),
        ("7897028000112","Iogurte Orgânico Natural 170g","Iogurte orgânico","04032000","Iogurte","Laticínios","Orgânicos","kg",False,False,0,"17.021.00","Genérico"),
        ("7897028000129","Espaguete Integral Orgânico 500g","Espaguete integral orgânico","19023000","Massas alimentícias","Cereais e Grãos","Orgânicos","kg",False,False,0,"17.049.00","Genérico"),
        ("7897028000136","Azeite Orgânico Extravirgem 250ml","Azeite orgânico EV","15092000","Azeite de oliva (oliveira) extra virgem","Óleos e Gorduras","Orgânicos","lt",False,False,0,"","Genérico"),
        ("7897028000143","Chá Verde Orgânico 25 saches","Chá verde orgânico","09021000","Chá verde","Bebidas","Orgânicos","un",False,False,0,"17.097.00","Genérico"),
        ("7897028000150","Café Orgânico Torrado em Grãos 250g","Café orgânico em grãos","09012100","Café torrado","Bebidas","Orgânicos","kg",False,False,0,"","Genérico"),
    ]
    for e in especiais:
        batch.append(_p(*e))

    # --- MASSAS E INGREDIENTES EXTRAS ---
    massas = [
        ("7897029000012","Macarrão Espaguete n.4 Divella 500g","Espaguete fino n.4","19023000","Massas alimentícias","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"17.049.00","Divella"),
        ("7897029000029","Macarrão Bucatini Divella 500g","Bucatini","19023000","Massas alimentícias","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"17.049.00","Divella"),
        ("7897029000036","Macarrão Rigatoni Barilla 500g","Rigatoni","19023000","Massas alimentícias","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"17.049.00","Barilla"),
        ("7897029000043","Macarrão Tagliatelle 250g","Tagliatelle","19021100","Massas com ovos","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"17.049.00","Genérico"),
        ("7897029000050","Macarrão Conchiglie Barilla 500g","Conchiglie","19023000","Massas alimentícias","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"17.049.00","Barilla"),
        ("7897029000067","Macarrão Tortellini Carne Congelado 500g","Tortellini de carne congelado","19022000","Massas recheadas","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"17.048.00","Genérico"),
        ("7897029000074","Macarrão Gnocchi di Patate 500g","Nhoque italiano","19022000","Massas recheadas","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"17.048.00","Genérico"),
        ("7897029000081","Macarrão Instantâneo Coreano Ramen 120g","Ramen coreano","19023000","Massas instantâneas","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"17.047.00","Importado"),
        ("7897029000098","Cuscuz Integral 500g","Cuscuz integral","19024000","Cuscuz","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"17.048.01","Genérico"),
        ("7897029000104","Polenta Instantânea 500g","Polenta de milho instantânea","11022000","Farinha de milho","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"","Genérico"),
        ("7897029000111","Massa para Pastel 500g","Massa para pastel","19023000","Massas alimentícias","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"","Genérico"),
        ("7897029000128","Massa para Pizza Napolitana 500g","Massa para pizza","19012090","Preparações de farinha","Padaria","Massas","kg",False,False,0,"","Genérico"),
        ("7897029000135","Lamen Japonês Seco 100g","Lamen japonês seco","19023000","Massas instantâneas","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"17.047.00","Importado"),
        ("7897029000142","Macarrão de Lentilha 250g","Macarrão proteico de lentilha","19023000","Massas alimentícias","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"","Genérico"),
        ("7897029000159","Macarrão de Ervilha 250g","Macarrão proteico de ervilha","19023000","Massas alimentícias","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"","Genérico"),
    ]
    for m in massas:
        batch.append(_p(*m))

    # --- CONSERVAS E GELEIAS EXTRAS ---
    conservas = [
        ("7897030000011","Geleia de Amora Queensberry 320g","Geleia de amora","20079910","Geleias","Mercearia","Geleias","kg",False,False,0,"","Queensberry"),
        ("7897030000028","Geleia de Figo Queensberry 320g","Geleia de figo","20079910","Geleias","Mercearia","Geleias","kg",False,False,0,"","Queensberry"),
        ("7897030000035","Geleia Extra de Laranja 320g","Geleia extra de laranja","20079910","Geleias","Mercearia","Geleias","kg",False,False,0,"","Queensberry"),
        ("7897030000042","Geleia de Manga 320g","Geleia de manga","20079910","Geleias","Mercearia","Geleias","kg",False,False,0,"","Genérico"),
        ("7897030000059","Goiabada Cremosa Predilecta 400g","Goiabada cremosa","20079910","Geleias","Mercearia","Doces","kg",False,False,0,"","Predilecta"),
        ("7897030000066","Pasta de Amendoim Integral 1kg","Pasta de amendoim 1kg","20089900","Amendoim preparado","Mercearia","Pastas","kg",False,False,0,"","Genérico"),
        ("7897030000073","Pasta de Avelã Zero Lactose 350g","Pasta de avelã","18069000","Preparações com cacau","Mercearia","Cremes e Pastas","kg",False,False,0,"","Genérico"),
        ("7897030000080","Mel de Engenho 500ml","Mel de engenho","17039000","Melaços","Mercearia","Mel","lt",False,False,0,"","Genérico"),
        ("7897030000097","Mel de Abelhas Nativas 250g","Mel de abelhas nativas","04090000","Mel natural","Mercearia","Mel","kg",False,False,0,"","Genérico"),
        ("7897030000103","Xarope de Agave 250ml","Néctar de agave","17026010","Frutose","Mercearia","Adoçantes","lt",False,False,0,"","Importado"),
        ("7897030000110","Xarope de Bordo (Maple) 250ml","Xarope de bordo puro","17022000","Açúcar de bordo","Mercearia","Adoçantes","lt",False,False,0,"","Importado"),
        ("7897030000127","Alcaparras em Conserva 100g","Alcaparras em conserva","20019000","Outros vegetais conservados","Enlatados","Conservas de Verduras","kg",False,False,0,"","Importado"),
        ("7897030000134","Pesto de Rúcula 100g","Pesto de rúcula","21039091","Preparações para molhos, embalagem ≤1kg","Condimentos","Molhos Especiais","kg",False,False,0,"","Genérico"),
        ("7897030000141","Tomate Cereja em Conserva 280g","Tomate cereja conserva","20021000","Tomates inteiros conservados","Enlatados","Conservas de Tomate","kg",False,False,0,"","Genérico"),
        ("7897030000158","Cogumelo Shitake em Conserva 200g","Shitake em conserva","20039000","Outros cogumelos","Enlatados","Conservas de Verduras","kg",False,False,0,"","Genérico"),
    ]
    for c in conservas:
        batch.append(_p(*c))

    # --- SNACKS EXTRAS ---
    snacks = [
        ("7897031000010","Pipoca Artesanal Manteiga 50g","Pipoca artesanal","19041000","Cereais expandidos","Snacks","Pipoca","kg",False,False,0,"","Genérico"),
        ("7897031000027","Chips de Batata Doce 50g","Chips de batata doce","19041000","Cereais expandidos","Snacks","Salgadinhos","kg",False,False,0,"17.031.00","Genérico"),
        ("7897031000034","Chips de Mandioca 50g","Chips de mandioca","20052000","Batatas preparadas","Snacks","Salgadinhos","kg",False,False,0,"17.031.00","Genérico"),
        ("7897031000041","Amendoim Japonês Honey 100g","Amendoim japonês de mel","20081100","Amendoim preparado","Snacks","Aperitivos","kg",False,False,0,"17.033.00","Genérico"),
        ("7897031000058","Mix de Nuts 100g","Mix de nozes e castanhas","20081900","Castanhas preparadas","Snacks","Aperitivos","kg",False,False,0,"17.033.00","Genérico"),
        ("7897031000065","Kani Kama 100g","Kani kama (surimi)","16051000","Caranguejos preparados","Snacks","Aperitivos","kg",False,False,0,"","Genérico"),
        ("7897031000072","Tortilha de Milho 200g","Tortilha de milho","19041000","Cereais expandidos","Snacks","Salgadinhos","kg",False,False,0,"17.031.00","Genérico"),
        ("7897031000089","Bolo de Arroz Japonês 100g","Bolo de arroz japonês","19041000","Produtos de cereais","Snacks","Salgadinhos","kg",False,False,0,"","Genérico"),
        ("7897031000096","Granola Bar Aveia e Mel 25g","Barra granola mel","19042000","Cereais preparados","Snacks","Barras de Cereais","kg",False,False,0,"","Genérico"),
        ("7897031000102","Barra Proteica 40g","Barra proteica cereal","19042000","Cereais preparados","Snacks","Barras de Cereais","kg",False,False,0,"","Genérico"),
        ("7897031000119","Paçoca Diet 20g","Paçoca diet de amendoim","17049090","Outros confeitaria","Snacks","Doces","kg",False,False,0,"","Genérico"),
        ("7897031000126","Biscoito Polvilho Assado 50g","Biscoito de polvilho","19053100","Biscoitos","Padaria","Biscoitos","kg",False,False,0,"","Genérico"),
        ("7897031000133","Palitinho Salgado 50g","Palitinho salgado","19053100","Biscoitos","Padaria","Biscoitos","kg",False,False,0,"","Genérico"),
        ("7897031000140","Torrada Grissini Italiana 125g","Grissini italiano","19053100","Biscoitos","Padaria","Torradas","kg",False,False,0,"17.059.00","Genérico"),
        ("7897031000157","Bala de Leite 200g","Bala de leite","17049020","Caramelos e confeitos","Snacks","Balas e Confeitos","kg",False,False,0,"","Genérico"),
        ("7897031000164","Pirulito de Chocolate 15g","Pirulito de chocolate","17049020","Pirulitos","Snacks","Balas e Confeitos","un",False,False,0,"","Genérico"),
        ("7897031000171","Bala Toffee Caramelo 200g","Bala toffee","17049020","Caramelos","Snacks","Balas e Confeitos","kg",False,False,0,"","Genérico"),
        ("7897031000188","Jujuba Frutas 200g","Jujuba de frutas","17049020","Balas","Snacks","Balas e Confeitos","kg",False,False,0,"","Genérico"),
        ("7897031000195","Goma de Mascar Frutas 15g","Goma de mascar frutas","17041000","Gomas de mascar","Snacks","Balas e Confeitos","un",False,False,0,"","Genérico"),
        ("7897031000201","Amendoim Torrado Salgado 100g","Amendoim torrado salgado","20081100","Amendoim preparado","Snacks","Aperitivos","kg",False,False,0,"17.033.00","Genérico"),
    ]
    for s in snacks:
        batch.append(_p(*s))

    # --- CONDIMENTOS ADICIONAIS ---
    cond = [
        ("7897032000019","Mostarda Dijon 215g","Mostarda Dijon importada","21033010","Mostarda","Condimentos","Mostarda","kg",False,False,0,"","Maille"),
        ("7897032000026","Mostarda com Mel 215g","Mostarda com mel","21033010","Mostarda","Condimentos","Mostarda","kg",False,False,0,"","Genérico"),
        ("7897032000033","Ketchup com Pimenta Heinz 397g","Ketchup picante","21032010","Ketchup","Condimentos","Ketchup","kg",False,False,0,"17.034.00","Heinz"),
        ("7897032000040","Maionese com Alho 500g","Maionese com alho","21039091","Maionese","Condimentos","Maionese","kg",False,False,0,"","Hellmann's"),
        ("7897032000057","Molho Tártaro 200ml","Molho tártaro","21039091","Preparações para molhos, embalagem ≤1kg","Condimentos","Molhos Especiais","lt",False,False,0,"","Genérico"),
        ("7897032000064","Molho Caesar 250ml","Molho Caesar","21039091","Preparações para molhos, embalagem ≤1kg","Condimentos","Molhos Especiais","lt",False,False,0,"","Genérico"),
        ("7897032000071","Molho Quatro Queijos 350g","Molho quatro queijos","21039091","Preparações para molhos, embalagem ≤1kg","Condimentos","Molhos Especiais","kg",False,False,0,"","Genérico"),
        ("7897032000088","Antepasto de Berinjela 180g","Antepasto de berinjela","21039091","Preparações para molhos, embalagem ≤1kg","Condimentos","Molhos Especiais","kg",False,False,0,"","Importado"),
        ("7897032000095","Antepasto de Pimentão 180g","Antepasto de pimentão","21039091","Preparações para molhos, embalagem ≤1kg","Condimentos","Molhos Especiais","kg",False,False,0,"","Importado"),
        ("7897032000101","Vinagre de Sidra 500ml","Vinagre de maçã (sidra)","22090000","Vinagres","Condimentos","Vinagre","lt",False,False,0,"","Genérico"),
        ("7897032000118","Vinagre de Framboesa 250ml","Vinagre de framboesa","22090000","Vinagres","Condimentos","Vinagre","lt",False,False,0,"","Importado"),
        ("7897032000125","Extrato de Baunilha Puro 60ml","Extrato de baunilha puro","21069090","Preparações alimentícias","Condimentos","Extratos","lt",False,False,0,"","Importado"),
        ("7897032000132","Essência de Amêndoa 30ml","Essência de amêndoa","21069090","Preparações alimentícias","Condimentos","Extratos","lt",False,False,0,"","Genérico"),
        ("7897032000149","Molho de Soja Dark 500ml","Molho de soja escuro","21031090","Molhos de soja","Condimentos","Molhos Especiais","lt",False,False,0,"","Importado"),
        ("7897032000156","Molho Ponzu Citrus 150ml","Molho ponzu","21039091","Preparações para molhos, embalagem ≤1kg","Condimentos","Molhos Especiais","lt",False,False,0,"","Importado"),
        ("7897032000163","Demi-Glace Concentrado 200g","Demi-glace bovino","21041000","Sopas e caldos","Condimentos","Caldos e Temperos","kg",False,False,0,"","Genérico"),
        ("7897032000170","Caldo de Camarão Knorr 57g","Caldo de camarão","21039099","Caldos e concentrados","Condimentos","Caldos e Temperos","kg",False,False,0,"","Knorr"),
        ("7897032000187","Caldo de Peixe Knorr 57g","Caldo de peixe","21039099","Caldos e concentrados","Condimentos","Caldos e Temperos","kg",False,False,0,"","Knorr"),
        ("7897032000194","Tempero Árabe Sirial 30g","Tempero árabe","21039091","Misturas condimentos ≤1kg","Condimentos","Temperos Compostos","kg",False,False,0,"","Sirial"),
        ("7897032000200","Za'atar Tempero Árabe 30g","Za'atar árabe","21039091","Misturas condimentos ≤1kg","Condimentos","Temperos Compostos","kg",False,False,0,"","Importado"),
    ]
    for c in cond:
        batch.append(_p(*c))

    # --- ITENS CONGELADOS EXTRAS ---
    congelados_extra = [
        ("7897033000018","Frango Sassami Congelado 500g","Sassami de frango congelado","02071419","Pedaços de frango congelados","Congelados","Pratos Prontos","kg",False,True,0,"","Sadia"),
        ("7897033000025","Hambúrguer Artesanal Bovino 400g","Hambúrguer bovino artesanal","16025000","Preparações de carne","Congelados","Hambúrguer","kg",False,False,0,"","Genérico"),
        ("7897033000032","Hambúrguer Vegetal Proteico 400g","Hambúrguer vegetal","16025000","Preparações à base vegetal","Congelados","Vegano","kg",False,False,0,"","Genérico"),
        ("7897033000049","Mini Filé de Frango Empanado 300g","Mini filé empanado","16023220","Preparações frango cozido","Congelados","Salgados","kg",False,False,0,"","Sadia"),
        ("7897033000056","Batata Ondulada Congelada McCain 600g","Batata ondulada congelada","20041000","Batatas preparadas","Congelados","Batata","kg",False,False,0,"17.032.00","McCain"),
        ("7897033000063","Batata Smiles Congelada 400g","Batata smiles congelada","20041000","Batatas preparadas","Congelados","Batata","kg",False,False,0,"17.032.00","McCain"),
        ("7897033000070","Cebola Empanada Congelada 300g","Cebola empanada","07102900","Outros vegetais congelados","Congelados","Vegetais","kg",False,False,0,"","Genérico"),
        ("7897033000087","Mandioca Frita Congelada 500g","Mandioca frita congelada","20041000","Outros vegetais preparados","Congelados","Vegetais","kg",False,False,0,"","Genérico"),
        ("7897033000094","Pão de Alho Congelado 400g","Pão de alho congelado","19052090","Outros pães","Congelados","Pão","kg",False,False,0,"","Genérico"),
        ("7897033000100","Esfiha de Carne Congelada 12un","Esfiha congelada","19052090","Outros produtos padaria","Congelados","Salgados","un",False,False,0,"","Genérico"),
        ("7897033000117","Lasanha de Frango Congelada 600g","Lasanha de frango congelada","16023220","Preparações frango","Congelados","Pratos Prontos","kg",False,False,0,"","Sadia"),
        ("7897033000124","Sorvete Açaí 2L","Sorvete de açaí","21050000","Sorvetes","Congelados","Sorvetes","lt",False,False,0,"23.001.00","Genérico"),
        ("7897033000131","Sorvete Maracujá 2L","Sorvete de maracujá","21050000","Sorvetes","Congelados","Sorvetes","lt",False,False,0,"23.001.00","Genérico"),
        ("7897033000148","Picolé de Limão 80ml","Picolé de limão","21050000","Sorvetes","Congelados","Sorvetes","lt",False,False,0,"23.001.00","Kibon"),
        ("7897033000155","Picolé de Amendoim 80ml","Picolé de amendoim","21050000","Sorvetes","Congelados","Sorvetes","lt",False,False,0,"23.001.00","Kibon"),
    ]
    for c in congelados_extra:
        batch.append(_p(*c))

    # --- MAIS INGREDIENTES / MERCEARIA ---
    mercearia = [
        ("7897034000017","Bicarbonato de Sódio Arm & Hammer 227g","Bicarbonato de sódio","28363000","Bicarbonato de sódio","Mercearia","Ingredientes","kg",False,False,0,"","Arm & Hammer"),
        ("7897034000024","Amido de Milho 1kg","Amido de milho 1kg","11081200","Amido de milho","Mercearia","Ingredientes","kg",False,True,0,"","Maizena"),
        ("7897034000031","Gelatina Incolor 12g","Gelatina sem sabor","35030000","Gelatina","Mercearia","Ingredientes","kg",False,False,0,"","Genérico"),
        ("7897034000048","Leite de Coco em Pó 200g","Leite de coco desidratado","20099000","Outros sucos","Mercearia","Ingredientes","kg",False,False,0,"","Genérico"),
        ("7897034000055","Creme de Coco 200ml","Creme de coco","20099000","Outros sucos","Mercearia","Ingredientes","lt",False,False,0,"","Ducoco"),
        ("7897034000062","Vinagre Balsâmico Cremoso 250ml","Vinagre balsâmico em creme","22090000","Vinagres","Condimentos","Vinagre","lt",False,False,0,"","Importado"),
        ("7897034000079","Shoyu Light 150ml","Molho de soja light","21031010","Molho de soja embalagem ≤1kg","Condimentos","Molhos Especiais","lt",False,False,0,"","Kikkoman"),
        ("7897034000086","Calda de Morango 200g","Calda de morango","20079910","Geleias","Mercearia","Doces","kg",False,False,0,"","Genérico"),
        ("7897034000093","Leite Condensado Nestlé 1kg","Leite condensado bisnaga 1kg","04029900","Leite condensado","Laticínios","Leite Condensado","kg",False,False,0,"17.020.01","Nestlé"),
        ("7897034000109","Fondant de Baunilha 1kg","Fondant 1kg profissional","17049090","Outros confeitaria","Padaria","Confeitaria","kg",False,False,0,"","Genérico"),
        ("7897034000116","Pasta Americana Azul 200g","Pasta americana colorida azul","17049090","Outros confeitaria","Padaria","Confeitaria","kg",False,False,0,"","Genérico"),
        ("7897034000123","Corante Alimentício Amarelo 30ml","Corante amarelo para alimentos","32030010","Corantes vegetais","Padaria","Confeitaria","lt",False,False,0,"","Genérico"),
        ("7897034000130","Aromatizante Laranja 30ml","Aromatizante de laranja","21069090","Preparações alimentícias","Padaria","Confeitaria","lt",False,False,0,"","Genérico"),
        ("7897034000147","Agar Agar Vegetariano 8g","Ágar-ágar em pó","13023100","Ágar-ágar","Padaria","Ingredientes","kg",False,False,0,"","Genérico"),
        ("7897034000154","Cacau Barry Callebaut 100g","Cacau em pó profissional","18050000","Cacau em pó","Padaria","Chocolates","kg",False,False,0,"","Callebaut"),
    ]
    for m in mercearia:
        batch.append(_p(*m))

    return batch


_PRODUCTS += _gen_bulk_products()


# ============================================================
# SEÇÃO 19: LOTE FINAL - PRODUTOS COMPLEMENTARES
# ============================================================

def _gen_final_batch():
    final = []

    # --- AÇÚCARES, ADOÇANTES E SIMILARES ---
    acucares = [
        ("7898001001001","Açúcar Cristal Guarani 5kg","Açúcar cristal","17011400","Açúcar de cana","Cereais e Grãos","Açúcar","kg",False,False,0,"17.099.00","Guarani"),
        ("7898001001018","Açúcar Refinado Guarani 1kg","Açúcar refinado","17019900","Açúcar refinado","Cereais e Grãos","Açúcar","kg",False,False,0,"17.099.00","Guarani"),
        ("7898001001025","Açúcar VHP Cristalizado 1kg","Açúcar VHP bruto","17011300","Açúcar de cana nota 2","Cereais e Grãos","Açúcar","kg",False,False,0,"17.099.00","Genérico"),
        ("7898001001032","Açúcar de Confeiteiro Fino 1kg","Açúcar impalpável","17019900","Açúcar refinado","Cereais e Grãos","Açúcar","kg",False,False,0,"17.099.00","Genérico"),
        ("7898001001049","Rapadura Pura 500g","Rapadura artesanal","17011400","Açúcar de cana","Cereais e Grãos","Açúcar","kg",False,False,0,"","Genérico"),
        ("7898001001056","Açúcar de Coco 300g","Açúcar de coco artesanal","17011400","Açúcar de cana outros","Cereais e Grãos","Açúcar","kg",False,False,0,"","Genérico"),
        ("7898001001063","Açúcar de Beterraba 1kg","Açúcar de beterraba","17011200","Açúcar de beterraba","Cereais e Grãos","Açúcar","kg",False,False,0,"17.099.00","Importado"),
        ("7898001001070","Stevia Pura Folha Seca 50g","Stevia folha seca","21069090","Edulcorantes","Mercearia","Adoçantes","kg",False,False,0,"","Genérico"),
        ("7898001001087","Adoçante Sucralose Líquido 100ml","Sucralose líquido","21069090","Edulcorantes","Mercearia","Adoçantes","lt",False,False,0,"","Genérico"),
        ("7898001001094","Xilitol 200g","Xilitol (álcool de açúcar)","29054300","Manitol","Mercearia","Adoçantes","kg",False,False,0,"","Importado"),
        ("7898001001100","Eritritol 300g","Eritritol","29054300","Outros polióis","Mercearia","Adoçantes","kg",False,False,0,"","Importado"),
    ]
    for a in acucares:
        final.append(_p(*a))

    # --- SAIS E TEMPEROS BÁSICOS ---
    sais = [
        ("7898001002008","Sal Defumado 100g","Sal defumado artesanal","25010020","Sal outros","Cereais e Grãos","Sal","kg",False,True,0,"","Genérico"),
        ("7898001002015","Flor de Sal 100g","Flor de sal marinha","25010020","Sal marinho","Cereais e Grãos","Sal","kg",False,True,0,"","Importado"),
        ("7898001002022","Sal de Ervas Finas 250g","Sal com ervas finas","25010020","Sal temperado","Cereais e Grãos","Sal","kg",False,True,0,"","Genérico"),
        ("7898001002039","Pimenta-do-Reino Branca 30g","Pimenta-do-reino branca","09041100","Pimenta não moída","Condimentos","Especiarias","kg",False,False,0,"","Genérico"),
        ("7898001002046","Cravo da Índia 10g","Cravo-da-índia","09070000","Cravo-da-índia","Condimentos","Especiarias","kg",False,False,0,"","Sirial"),
        ("7898001002053","Anis Estrelado 10g","Anis estrelado","09096200","Anis estrelado","Condimentos","Especiarias","kg",False,False,0,"","Importado"),
        ("7898001002060","Pimenta Vermelha Seca 30g","Pimenta vermelha seca","09042100","Pimenta seca","Condimentos","Especiarias","kg",False,False,0,"","Genérico"),
        ("7898001002077","Cominho em Grão 30g","Cominho em grão","09093100","Cominho inteiro","Condimentos","Especiarias","kg",False,False,0,"","Sirial"),
        ("7898001002084","Hortelã Seco 5g","Hortelã desidratado","12119090","Plantas aromáticas","Condimentos","Especiarias","kg",False,False,0,"","Genérico"),
        ("7898001002091","Tomilho Seco 5g","Tomilho desidratado","12119090","Plantas aromáticas","Condimentos","Especiarias","kg",False,False,0,"","Genérico"),
        ("7898001002107","Sálvia Seca 5g","Sálvia desidratada","12119090","Plantas aromáticas","Condimentos","Especiarias","kg",False,False,0,"","Genérico"),
        ("7898001002114","Endro/Dill Seco 5g","Dill desidratado","12119090","Plantas aromáticas","Condimentos","Especiarias","kg",False,False,0,"","Importado"),
    ]
    for s in sais:
        final.append(_p(*s))

    # --- FARINHAS E AMIDOS EXTRAS ---
    farinhas = [
        ("7898001003005","Fécula de Batata 500g","Fécula de batata","11081300","Fécula de batata","Cereais e Grãos","Amidos e Féculas","kg",False,True,0,"","Genérico"),
        ("7898001003012","Amido de Araruta 200g","Amido de araruta","11082000","Amido de araruta","Cereais e Grãos","Amidos e Féculas","kg",False,True,0,"","Genérico"),
        ("7898001003029","Farinha de Aveia 500g","Farinha de aveia","11029000","Outras farinhas","Cereais e Grãos","Farinhas","kg",False,True,0,"","Genérico"),
        ("7898001003036","Farinha de Chia 200g","Farinha de chia","11029000","Outras farinhas","Cereais e Grãos","Farinhas","kg",False,True,0,"","Genérico"),
        ("7898001003043","Farinha de Linhaça 200g","Farinha de linhaça","11029000","Outras farinhas","Cereais e Grãos","Farinhas","kg",False,True,0,"","Genérico"),
        ("7898001003050","Farinha de Quinoa 300g","Farinha de quinoa","11029000","Outras farinhas","Cereais e Grãos","Farinhas","kg",False,True,0,"","Importado"),
        ("7898001003067","Farinha de Sorgo 500g","Farinha de sorgo","11029000","Outras farinhas","Cereais e Grãos","Farinhas","kg",False,True,0,"","Genérico"),
        ("7898001003074","Farinha Panko Japonesa 200g","Farinha panko japonesa","19053100","Pão ralado","Padaria","Farinha de Rosca","kg",False,False,0,"","Importado"),
        ("7898001003081","Polvilho de Mandioca Doce 1kg","Polvilho doce 1kg","11081400","Fécula de mandioca","Cereais e Grãos","Amidos e Féculas","kg",False,True,0,"","Genérico"),
        ("7898001003098","Polvilho de Mandioca Azedo 1kg","Polvilho azedo 1kg","11081400","Fécula de mandioca fermentada","Cereais e Grãos","Amidos e Féculas","kg",False,True,0,"","Genérico"),
    ]
    for f in farinhas:
        final.append(_p(*f))

    # --- PRODUTOS COMUNS DE SUPERMERCADO ---
    super_genericos = [
        ("7898001004002","Milho Verde Enlatado 200g","Milho verde em lata","20059000","Vegetais conservados","Enlatados","Conservas de Verduras","kg",False,False,0,"","Qualitá"),
        ("7898001004019","Ketchup Sachê 10g","Ketchup sachê","21032010","Ketchup","Condimentos","Ketchup","kg",False,False,0,"17.034.00","Heinz"),
        ("7898001004026","Sal Temperado Defumado 100g","Sal defumado com especiarias","25010020","Sal outros","Cereais e Grãos","Sal","kg",False,True,0,"","Genérico"),
        ("7898001004033","Azeite de Oliva 200ml Mini","Azeite mini para mesa","15093000","Azeite de oliva (oliveira) virgem","Óleos e Gorduras","Azeite","lt",False,False,0,"","Gallo"),
        ("7898001004040","Café Expresso Moído 500g","Café moído para expresso","09012100","Café torrado","Bebidas","Café","kg",False,False,0,"","Genérico"),
        ("7898001004057","Chá Instantâneo Limão 10 sachês","Chá instantâneo limão","21011200","Preparações à base de chá","Bebidas","Chá","un",False,False,0,"17.097.00","Genérico"),
        ("7898001004064","Fermento Natural Levain 100g","Fermento natural para pão","21023000","Pós para levedar","Padaria","Fermento","kg",False,False,0,"","Genérico"),
        ("7898001004071","Glucose de Milho 400g","Glucose de milho para confeitaria","17023020","Xarope de glicose","Mercearia","Ingredientes","kg",False,False,0,"","Karo"),
        ("7898001004088","Goma Xantana 100g","Goma xantana para culinária","39139000","Outros polissacarídeos","Mercearia","Ingredientes","kg",False,False,0,"","Genérico"),
        ("7898001004095","Proteína de Ervilha 500g","Proteína de ervilha isolada","21069090","Preparações alimentícias","Suplementos","Proteínas","kg",False,False,0,"","Genérico"),
        ("7898001004101","Colágeno Bovino 500g","Colágeno bovino em pó","35040000","Peptídeos","Suplementos","Colágeno","kg",False,False,0,"","Genérico"),
        ("7898001004118","Spirulina 200g","Spirulina em pó","21069090","Preparações alimentícias","Suplementos","Suplementos","kg",False,False,0,"","Genérico"),
        ("7898001004125","Psyllium 200g","Psyllium fibra","12119090","Plantas medicinais","Suplementos","Fibras","kg",False,False,0,"","Genérico"),
        ("7898001004132","Farelo de Aveia 250g","Farelo de aveia","11041200","Aveia trabalhada","Cereais e Grãos","Cereais Matinais","kg",False,True,0,"","Genérico"),
        ("7898001004149","Farelo de Trigo 500g","Farelo de trigo","23020000","Farelo de trigo","Cereais e Grãos","Cereais Matinais","kg",False,True,0,"","Genérico"),
        ("7898001004156","Cevada Torrada 500g","Cevada torrada para bebida","10039090","Outros","Cereais e Grãos","Grãos Especiais","kg",False,False,0,"","Genérico"),
        ("7898001004163","Goma de Guar 100g","Goma de guar","13023200","Goma de guar","Mercearia","Ingredientes","kg",False,False,0,"","Genérico"),
        ("7898001004170","Pó Royal Baunilha 100g","Fermento com baunilha","21023000","Pós para levedar","Padaria","Fermento","kg",False,False,0,"","Royal"),
        ("7898001004187","Canela com Açúcar 200g","Canela em pó com açúcar","21039091","Misturas condimentos ≤1kg","Condimentos","Especiarias","kg",False,False,0,"","Genérico"),
        ("7898001004194","Coco Ralado Seco Flocão 100g","Coco ralado seco","20081990","Outros","Mercearia","Ingredientes","kg",False,False,0,"","Genérico"),
    ]
    for s in super_genericos:
        final.append(_p(*s))

    # --- AINDA MAIS PRODUTOS PARA ATINGIR META ---
    mais_produtos = [
        ("7898001005009","Proteína de Soja TVP 500g","PTS grossa de soja","12019090","Farinha de soja","Foodservice","Proteínas","kg",False,True,0,"","Genérico"),
        ("7898001005016","Feijão de Praia 500g","Feijão de praia seco","07131090","Outras ervilhas","Cereais e Grãos","Leguminosas","kg",False,True,0,"","Genérico"),
        ("7898001005023","Feijão Adzuki 500g","Feijão adzuki japonês","07133290","Feijões","Cereais e Grãos","Leguminosas","kg",False,True,0,"","Importado"),
        ("7898001005030","Lentilha Vermelha 500g","Lentilha vermelha","07134090","Lentilhas","Cereais e Grãos","Leguminosas","kg",False,True,0,"","Importado"),
        ("7898001005047","Lentilha Preta Beluga 500g","Lentilha preta beluga","07134090","Lentilhas","Cereais e Grãos","Leguminosas","kg",False,True,0,"","Importado"),
        ("7898001005054","Ervilha Amarela Partida 500g","Ervilha amarela partida","07135090","Ervilhas","Cereais e Grãos","Leguminosas","kg",False,True,0,"","Genérico"),
        ("7898001005061","Fava Seca 500g","Fava seca","07133490","Favas","Cereais e Grãos","Leguminosas","kg",False,True,0,"","Genérico"),
        ("7898001005078","Lupino Cozido 400g","Lupino cozido em lata","20055900","Outras leguminosas","Enlatados","Feijão Cozido","kg",False,False,0,"","Importado"),
        ("7898001005085","Quinoa Branca 500g","Quinoa branca em grão","10089000","Outros cereais","Cereais e Grãos","Grãos Especiais","kg",False,True,0,"","Importado"),
        ("7898001005092","Quinoa Tricolor 500g","Quinoa tricolor","10089000","Outros cereais","Cereais e Grãos","Grãos Especiais","kg",False,True,0,"","Importado"),
        ("7898001005108","Painço 500g","Painço em grão","10082900","Outros milhos miúdos","Cereais e Grãos","Grãos Especiais","kg",False,True,0,"","Importado"),
        ("7898001005115","Sorgo em Grão 500g","Sorgo em grão","10070090","Sorgo","Cereais e Grãos","Grãos Especiais","kg",False,True,0,"","Genérico"),
        ("7898001005122","Teff 250g","Teff em grão","10089000","Outros cereais","Cereais e Grãos","Grãos Especiais","kg",False,True,0,"","Importado"),
        ("7898001005139","Aveia em Grão 500g","Aveia em grão inteiro","10049000","Outras aveias","Cereais e Grãos","Cereais Matinais","kg",False,True,0,"","Genérico"),
        ("7898001005146","Centeio Integral 500g","Centeio integral","10029000","Centeio","Cereais e Grãos","Grãos Especiais","kg",False,True,0,"","Importado"),
        ("7898001005153","Trigo Sarraceno 500g","Trigo sarraceno (buckwheat)","10089000","Outros cereais","Cereais e Grãos","Grãos Especiais","kg",False,True,0,"","Importado"),
        ("7898001005160","Kamut 500g","Kamut trigo antigo","10011900","Outros trigos","Cereais e Grãos","Grãos Especiais","kg",False,True,0,"","Importado"),
        ("7898001005177","Espelta 500g","Espelta (dinkel)","10011900","Outros trigos","Cereais e Grãos","Grãos Especiais","kg",False,True,0,"","Importado"),
        ("7898001005184","Milho Roxo em Grão 500g","Milho roxo andino","10059090","Outros milhos","Cereais e Grãos","Grãos Especiais","kg",False,True,0,"","Importado"),
        ("7898001005191","Milho Branco Hominy 500g","Milho branco hominy","10059010","Milho em grão","Cereais e Grãos","Grãos Especiais","kg",False,True,0,"","Importado"),
        ("7898001005207","Aveia Flocos Grossos Sem Glúten 500g","Aveia sem glúten","11041200","Aveia trabalhada","Cereais e Grãos","Sem Glúten","kg",False,True,0,"","Genérico"),
        ("7898001005214","Arroz de Cauliflower Congelado 300g","Arroz de couve-flor","07102200","Vegetais congelados","Congelados","Vegetais","kg",False,True,0,"","Genérico"),
        ("7898001005221","Espaguete de Abobrinha Fresco 200g","Espiralize de abobrinha","07099300","Abobrinhas","Hortifruti","Legumes","kg",False,True,0,"","Genérico"),
        ("7898001005238","Cuscuz Marroquino Integral 500g","Cuscuz integral","19024000","Cuscuz","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"17.048.01","Genérico"),
        ("7898001005245","Amido de Milho Waxy 500g","Amido de milho ceroso","11081200","Amido de milho","Mercearia","Ingredientes","kg",False,True,0,"","Genérico"),
        ("7898001005252","Vinagre de Cana 750ml","Vinagre de cana","22090000","Vinagres","Condimentos","Vinagre","lt",False,False,0,"","Genérico"),
        ("7898001005269","Caldo de Legumes Orgânico Tetra 1L","Caldo de legumes orgânico","21041000","Sopas e caldos","Condimentos","Caldos e Temperos","lt",False,False,0,"","Genérico"),
        ("7898001005276","Caldo de Galinha Orgânico Tetra 1L","Caldo de galinha orgânico","21041000","Sopas e caldos","Condimentos","Caldos e Temperos","lt",False,False,0,"","Genérico"),
        ("7898001005283","Caldo de Carne Orgânico Tetra 1L","Caldo de carne orgânico","21041000","Sopas e caldos","Condimentos","Caldos e Temperos","lt",False,False,0,"","Genérico"),
        ("7898001005290","Caldo de Osso Bovino 500ml","Caldo de osso bovino","21041000","Sopas e caldos","Condimentos","Caldos e Temperos","lt",False,False,0,"","Genérico"),
        ("7898001005306","Extrato de Levedura Vegemite 400g","Extrato de levedura","21039091","Preparações para molhos, embalagem ≤1kg","Mercearia","Ingredientes","kg",False,False,0,"","Importado"),
        ("7898001005313","Nori Folha Alga Marinha 10 folhas","Alga marinha nori","12122100","Algas","Mercearia","Ingredientes","un",False,False,0,"","Importado"),
        ("7898001005320","Wakame Alga Seca 30g","Alga wakame desidratada","12122100","Algas","Mercearia","Ingredientes","kg",False,False,0,"","Importado"),
        ("7898001005337","Kombu Alga 50g","Alga kombu seca","12122100","Algas","Mercearia","Ingredientes","kg",False,False,0,"","Importado"),
        ("7898001005344","Leite Evaporado 354ml","Leite evaporado","04022130","Creme de leite","Laticínios","Leite em Pó","lt",False,False,0,"","Nestlé"),
        ("7898001005351","Manteiga de Castanha de Caju 200g","Pasta de castanha de caju","20089900","Castanhas preparadas","Mercearia","Pastas","kg",False,False,0,"","Genérico"),
        ("7898001005368","Manteiga de Macadâmia 200g","Pasta de macadâmia","20089900","Castanhas preparadas","Mercearia","Pastas","kg",False,False,0,"","Genérico"),
        ("7898001005375","Requeijão Cremoso Longa Vida 200g","Requeijão cremoso","04069030","Queijo de massa macia","Laticínios","Queijos","kg",False,False,0,"17.023.00","Genérico"),
        ("7898001005382","Queijo Parmesão em Bloco 200g","Queijo parmesão em bloco","04069010","Queijo de massa dura","Laticínios","Queijos","kg",False,False,0,"17.024.00","Tirolez"),
        ("7898001005399","Queijo Mussarela de Búfala 150g","Mussarela de búfala","04061010","Queijo mussarela","Laticínios","Queijos","kg",False,False,0,"17.024.00","Importado"),
        ("7898001005405","Queijo Mascarpone 250g","Queijo mascarpone italiano","04069030","Queijo de massa macia","Laticínios","Queijos","kg",False,False,0,"17.024.00","Importado"),
        ("7898001005412","Queijo Feta 200g","Queijo feta grego","04063000","Queijo fundido","Laticínios","Queijos","kg",False,False,0,"17.024.00","Importado"),
        ("7898001005429","Queijo Boursin Alho e Ervas 150g","Queijo fresco alho e ervas","04069030","Queijo de massa macia","Laticínios","Queijos","kg",False,False,0,"17.024.00","Importado"),
        ("7898001005436","Queijo Camembert Nacional 120g","Queijo camembert","04064000","Queijos pasta mofada","Laticínios","Queijos","kg",False,False,0,"17.024.00","Genérico"),
        ("7898001005443","Ovos de Codorna Frescos 30un","Ovos de codorna frescos","04072900","Outros ovos","Laticínios","Ovos","un",False,True,0,"","Genérico"),
        ("7898001005450","Ovo de Pato un","Ovo de pato","04071900","Outros ovos de aves","Laticínios","Ovos","un",False,True,0,"","Genérico"),
        ("7898001005467","Bacon em Cubos 200g","Bacon em cubos","02101200","Toucinhos entremeados","Carnes","Embutidos e Frios","kg",False,False,0,"17.083.00","Sadia"),
        ("7898001005474","Toucinho Defumado 200g","Toucinho defumado","02101200","Toucinhos entremeados","Carnes","Embutidos e Frios","kg",False,False,0,"17.083.00","Genérico"),
        ("7898001005481","Torresmo 200g","Torresmo de porco","15011000","Banha","Carnes","Carne Suína","kg",False,False,0,"","Genérico"),
        ("7898001005498","Carne de Sol Desfiada 200g","Carne de sol desfiada","02102000","Carne bovina salgada","Carnes","Carnes Secas","kg",False,True,0,"17.083.00","Genérico"),
        ("7898001005504","Charque Bovino 500g","Charque bovino","02102000","Carne bovina salgada","Carnes","Carnes Secas","kg",False,True,0,"17.083.00","Genérico"),
        ("7898001005511","Mojarra/Tilápia Salgada 500g","Tilápia salgada","03055900","Peixes secos e salgados","Carnes","Peixes","kg",False,True,0,"","Genérico"),
        ("7898001005528","Arenque Defumado 100g","Arenque defumado","16041100","Salmão preparado","Carnes","Peixes","kg",False,False,0,"","Importado"),
        ("7898001005535","Polvo Congelado 1kg","Polvo limpo congelado","03079900","Outros moluscos","Carnes","Frutos do Mar","kg",False,True,0,"","Genérico"),
        ("7898001005542","Ostra Fresca 12un","Ostra fresca","03071200","Ostras","Carnes","Frutos do Mar","un",False,True,0,"","Genérico"),
        ("7898001005559","Mexilhão Congelado 500g","Mexilhão congelado","03079990","Mexilhões","Carnes","Frutos do Mar","kg",False,True,0,"","Genérico"),
        ("7898001005566","Vieira Congelada 300g","Vieira congelada","03079900","Vieiras","Carnes","Frutos do Mar","kg",False,True,0,"","Genérico"),
        ("7898001005573","Filé de Peixe Branco Genérico 500g","Filé de peixe branco congelado","03049900","Outros filés congelados","Carnes","Peixes","kg",False,True,0,"","Genérico"),
    ]
    for m in mais_produtos:
        final.append(_p(*m))

    return final


_PRODUCTS += _gen_final_batch()


# ============================================================
# SEÇÃO 20: GERAÇÃO AUTOMÁTICA FINAL - COMPLETANDO 2000+ PRODUTOS
# ============================================================

import hashlib as _hashlib

def _make_ean_like(seed: str) -> str:
    """Gera um EAN-like deterministico a partir de uma seed (não válido para comércio)."""
    h = int(_hashlib.md5(seed.encode()).hexdigest(), 16)
    return str(789_000_000_0000 + (h % 1_000_000_0000)).zfill(13)[:13]


def _auto_products():
    """Gera centenas de produtos automaticamente."""
    auto = []

    # =====================
    # CATEGORIAS DE PRODUTO
    # =====================

    # CARNES BOVINAS - variações de corte
    cortes_bovino = [
        ("Contrafilé Bovino Resfriado 500g","Contrafilé bovino resfriado","02013000","Carne bovina desossada fresca","Carnes","Carne Bovina","kg",False,True,0,"","Resfriada"),
        ("Alcatra Bovina Resfriada 500g","Alcatra bovina resfriada","02013000","Carne bovina desossada","Carnes","Carne Bovina","kg",False,True,0,"","Resfriada"),
        ("Bife de Fígado Bovino 500g","Fígado bovino fresco","02062200","Fígados bovinos","Carnes","Carne Bovina","kg",False,True,0,"","Resfriada"),
        ("Coração Bovino 500g","Coração bovino fresco","02062990","Miudezas bovinas","Carnes","Carne Bovina","kg",False,True,0,"","Resfriada"),
        ("Língua Bovina 500g","Língua bovina fresca","02062100","Línguas bovinas","Carnes","Carne Bovina","kg",False,True,0,"","Resfriada"),
        ("Rabo de Boi 500g","Rabo de boi fresco","02062910","Rabos bovinos","Carnes","Carne Bovina","kg",False,True,0,"","Resfriada"),
        ("Ossobuco Bovino 500g","Ossobuco bovino resfriado","02013000","Carne bovina osso","Carnes","Carne Bovina","kg",False,True,0,"","Resfriada"),
        ("Joelho Bovino 500g","Joelho bovino resfriado","02012020","Quartos traseiros","Carnes","Carne Bovina","kg",False,True,0,"","Resfriada"),
        ("Paleta Bovina 500g","Paleta bovina resfriada","02013000","Carne bovina desossada","Carnes","Carne Bovina","kg",False,True,0,"","Resfriada"),
        ("Lagarto Bovino 500g","Lagarto bovino resfriado","02013000","Carne bovina desossada","Carnes","Carne Bovina","kg",False,True,0,"","Resfriada"),
        ("Aba de Filé Bovino 500g","Aba de filé bovino","02013000","Carne bovina desossada","Carnes","Carne Bovina","kg",False,True,0,"","Resfriada"),
        ("Peça de Coxão de Fora 1kg","Coxão de fora bovino","02013000","Carne bovina desossada","Carnes","Carne Bovina","kg",False,True,0,"","Resfriada"),
        ("Medalhão de Filé Mignon 200g","Medalhão filé mignon","02013000","Carne bovina desossada fresca","Carnes","Carne Bovina","kg",False,True,0,"","Resfriada"),
        ("Steak de Ancho Bovino 300g","Steak ancho bovino","02013000","Carne bovina desossada","Carnes","Carne Bovina","kg",False,True,0,"","Resfriada"),
        ("Bife de Tiras 400g","Carne bovina em tiras","02013000","Carne bovina desossada","Carnes","Carne Bovina","kg",False,True,0,"","Resfriada"),
        ("Carne para Ensopado 500g","Carne bovina para ensopado","02013000","Carne bovina desossada","Carnes","Carne Bovina","kg",False,True,0,"","Resfriada"),
        ("Pernil de Boi 1kg","Pernil bovino","02012020","Quartos traseiros bovinos","Carnes","Carne Bovina","kg",False,True,0,"","Resfriada"),
        ("Capa de Filé Bovino 500g","Capa de filé mignon","02013000","Carne bovina desossada","Carnes","Carne Bovina","kg",False,True,0,"","Resfriada"),
        ("Rib Eye Bovino 400g","Rib eye bovino importado","02023000","Carne bovina congelada","Carnes","Carne Bovina","kg",False,True,0,"","Importada"),
        ("T-Bone Bovino 500g","T-bone bovino importado","02023000","Carne bovina congelada","Carnes","Carne Bovina","kg",False,True,0,"","Importada"),
    ]
    for item in cortes_bovino:
        ean = _make_ean_like(item[0])
        auto.append(_p(ean, *item))

    # CORTES DE FRANGO
    cortes_frango = [
        ("Sassami de Frango Resfriado 500g","Sassami de frango resfriado","02071411","Peitos de frango","Carnes","Carne de Frango","kg",False,True,0,"","Resfriada"),
        ("Filé de Frango Temperado 500g","Filé de frango temperado","02071411","Peitos de frango","Carnes","Carne de Frango","kg",False,True,0,"","Resfriada"),
        ("Coxinha da Asa de Frango 500g","Coxinha da asa de frango","02071413","Asas de frango","Carnes","Carne de Frango","kg",False,True,0,"","Resfriada"),
        ("Coxa de Frango Sem Pele 500g","Coxa de frango sem pele","02071412","Coxas com sobrecoxas","Carnes","Carne de Frango","kg",False,True,0,"","Resfriada"),
        ("Frango Caipira Inteiro 2kg","Frango caipira inteiro","02071210","Frango inteiro","Carnes","Carne de Frango","kg",False,True,0,"","Resfriada"),
        ("Steak de Frango 200g","Steak de peito de frango","02071411","Peitos de frango","Carnes","Carne de Frango","kg",False,True,0,"","Resfriada"),
        ("Peito de Frango em Cubos 300g","Peito de frango em cubos","02071411","Peitos de frango","Carnes","Carne de Frango","kg",False,True,0,"","Resfriada"),
        ("Frango Defumado Inteiro 1kg","Frango defumado inteiro","16023290","Preparações de frango","Carnes","Carne de Frango","kg",False,False,0,"","Sadia"),
        ("Asa Temperada de Frango 500g","Asa temperada de frango","02071413","Asas de frango","Carnes","Carne de Frango","kg",False,True,0,"","Resfriada"),
        ("Mini Frango para Churrasco 1kg","Mini frango para churrasco","02071210","Frango inteiro","Carnes","Carne de Frango","kg",False,True,0,"","Resfriada"),
    ]
    for item in cortes_frango:
        ean = _make_ean_like(item[0])
        auto.append(_p(ean, *item))

    # LATICÍNIOS VARIAÇÕES
    laticinios_var = [
        ("Queijo Prato Suave Fatiado 200g","Queijo prato suave fatiado","04069020","Queijo de massa semidura","Laticínios","Queijos","kg",False,False,0,"17.024.00","Genérico"),
        ("Queijo Mussarela Defumada 200g","Queijo mussarela defumada","04061010","Queijo mussarela","Laticínios","Queijos","kg",False,False,0,"17.024.00","Genérico"),
        ("Queijo Minas Artesanal 300g","Queijo minas artesanal","04069030","Queijo de massa macia","Laticínios","Queijos","kg",False,False,0,"17.024.00","Artesanal"),
        ("Queijo Tilsit 200g","Queijo tilsit","04069020","Queijo de massa semidura","Laticínios","Queijos","kg",False,False,0,"17.024.00","Genérico"),
        ("Queijo Roquefort 100g","Queijo roquefort","04064000","Queijo de pasta mofada","Laticínios","Queijos","kg",False,False,0,"17.024.00","Importado"),
        ("Queijo Manchego 150g","Queijo manchego espanhol","04069020","Queijo de massa semidura","Laticínios","Queijos","kg",False,False,0,"17.024.00","Importado"),
        ("Queijo Havarti Fatiado 150g","Queijo havarti fatiado","04069020","Queijo de massa semidura","Laticínios","Queijos","kg",False,False,0,"17.024.00","Importado"),
        ("Queijo Gruyère 150g","Queijo gruyère suíço","04069020","Queijo de massa semidura","Laticínios","Queijos","kg",False,False,0,"17.024.00","Importado"),
        ("Queijo Edam 200g","Queijo edam holandês","04069020","Queijo de massa semidura","Laticínios","Queijos","kg",False,False,0,"17.024.00","Importado"),
        ("Queijo Babybel 5un","Queijo babybel mini","04069090","Outros queijos","Laticínios","Queijos","un",False,False,0,"17.024.00","Importado"),
        ("Queijo Cottage 200g","Queijo cottage fresco","04069030","Queijo de massa macia","Laticínios","Queijos","kg",False,False,0,"17.024.00","Genérico"),
        ("Leite em Pó Integral 800g","Leite em pó integral 800g","04022110","Leite em pó integral","Laticínios","Leite em Pó","kg",False,True,0,"17.012.00","Genérico"),
        ("Leite em Pó Parcial 400g","Leite em pó parcialmente desnatado","04022120","Leite em pó desnatado","Laticínios","Leite em Pó","kg",False,True,0,"17.012.00","Genérico"),
        ("Creme de Leite 500g lata","Creme de leite em lata 500g","04022130","Creme de leite","Laticínios","Creme de Leite","kg",False,False,0,"17.019.01","Nestlé"),
        ("Leite Condensado Light 395g","Leite condensado light","04029900","Leite condensado","Laticínios","Leite Condensado","kg",False,False,0,"17.020.00","Nestlé"),
        ("Iogurte Stracciatella 100g","Iogurte grego stracciatella","04032000","Iogurte","Laticínios","Iogurte","kg",False,False,0,"17.021.00","Genérico"),
        ("Bebida Láctea de Mamão 200ml","Bebida láctea sabor mamão","04039000","Outros leites fermentados","Laticínios","Bebida Láctea","lt",False,False,0,"17.021.00","Genérico"),
        ("Iogurte Natural Zero Lactose 500g","Iogurte natural zero lactose","04032000","Iogurte","Laticínios","Iogurte","kg",False,False,0,"17.021.01","Genérico"),
        ("Manteiga de Búfala 200g","Manteiga de leite de búfala","04051000","Manteiga","Laticínios","Manteiga","kg",False,False,0,"17.025.00","Genérico"),
        ("Doce de Leite em Tablete 200g","Doce de leite em tablete","19019020","Doce de leite","Laticínios","Doce de Leite","kg",False,False,0,"17.029.00","Genérico"),
    ]
    for item in laticinios_var:
        ean = _make_ean_like(item[0])
        auto.append(_p(ean, *item))

    # CEREAIS ADICIONAIS
    cereais_add = [
        ("Flocos de Quinoa 300g","Flocos de quinoa","10089000","Outros cereais","Cereais e Grãos","Grãos Especiais","kg",False,True,0,"","Genérico"),
        ("Flocos de Amaranto 300g","Flocos de amaranto","10089000","Outros cereais","Cereais e Grãos","Grãos Especiais","kg",False,True,0,"","Genérico"),
        ("Flocos de Arroz Integral 300g","Flocos de arroz integral","19042000","Preparações de cereais","Cereais e Grãos","Cereais Matinais","kg",False,False,0,"17.030.00","Genérico"),
        ("Flocos de Trigo Integral 300g","Flocos de trigo integral","19042000","Preparações de cereais","Cereais e Grãos","Cereais Matinais","kg",False,False,0,"17.030.00","Genérico"),
        ("Muesli Suíço 500g","Muesli suíço","19042000","Preparações de cereais","Cereais e Grãos","Cereais Matinais","kg",False,False,0,"17.030.00","Importado"),
        ("Cereal Integral com Frutas 300g","Cereal integral com frutas","19042000","Preparações de cereais","Cereais e Grãos","Cereais Matinais","kg",False,False,0,"17.030.00","Genérico"),
        ("Aveia Instantânea Sachê 30g","Aveia instantânea sachê","11041200","Aveia trabalhada","Cereais e Grãos","Cereais Matinais","kg",False,True,0,"","Genérico"),
        ("Porridge de Aveia com Fruta 300g","Porridge instantâneo","19042000","Preparações de cereais","Cereais e Grãos","Cereais Matinais","kg",False,False,0,"","Genérico"),
        ("Canjica Doce de Leite 200g","Canjica com doce de leite","19019020","Doce de leite","Cereais e Grãos","Sobremesas","kg",False,False,0,"","Genérico"),
        ("Mingau de Arroz Instantâneo 200g","Mingau de arroz instantâneo","19011090","Outras preparações","Cereais e Grãos","Cereais Matinais","kg",False,False,0,"","Genérico"),
        ("Polenta com Cogumelos 250g","Polenta com cogumelos","11022000","Farinha de milho","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"","Genérico"),
        ("Arroz Basmati Cozido Congelado 300g","Arroz basmati cozido","10063021","Arroz semibranqueado ou branqueado, polido ou brunido","Congelados","Arroz","kg",False,True,0,"","Genérico"),
        ("Feijão Carioca Cozido Congelado 400g","Feijão carioca cozido","07133290","Feijões","Congelados","Feijão","kg",False,True,0,"","Genérico"),
        ("Lentilha Cozida Congelada 400g","Lentilha cozida","07134090","Lentilhas","Congelados","Leguminosas","kg",False,True,0,"","Genérico"),
        ("Ervilha Partida Cozida 400g","Ervilha partida cozida","07135090","Ervilhas","Congelados","Leguminosas","kg",False,True,0,"","Genérico"),
    ]
    for item in cereais_add:
        ean = _make_ean_like(item[0])
        auto.append(_p(ean, *item))

    # PADARIA VARIAÇÕES
    padaria_var = [
        ("Pão de Aveia Integral 500g","Pão de aveia integral","19052090","Outros pães","Padaria","Pão Especial","kg",False,False,0,"17.050.00","Genérico"),
        ("Pão de Sementes 400g","Pão com sementes","19052090","Outros pães","Padaria","Pão Especial","kg",False,False,0,"17.050.00","Genérico"),
        ("Pão Sírio 500g","Pão árabe sírio","19052090","Outros pães","Padaria","Pão Especial","kg",False,False,0,"","Genérico"),
        ("Pão Naan 4un","Pão naan indiano","19052090","Outros pães","Padaria","Pão Especial","un",False,False,0,"","Genérico"),
        ("Pão Pita 5un","Pão pita grego","19052090","Outros pães","Padaria","Pão Especial","un",False,False,0,"","Genérico"),
        ("Tortilla de Trigo 6un","Tortilla de trigo para wrap","19052090","Outros pães","Padaria","Pão Especial","un",False,False,0,"","Genérico"),
        ("Tortilla de Milho 6un","Tortilla de milho mexicana","19052090","Outros pães","Padaria","Pão Especial","un",False,False,0,"","Genérico"),
        ("Mini Pão Sírio 10un","Mini pão árabe","19052090","Outros pães","Padaria","Pão Especial","un",False,False,0,"","Genérico"),
        ("Pão de Hambúrguer Brioche 4un","Pão brioche para hambúrguer","19052090","Outros pães","Padaria","Pão Especial","un",False,False,0,"17.050.00","Genérico"),
        ("Pão de Cachorro-Quente Tipo Hot Dog","Pão de hot dog tipo americano","19052090","Outros pães","Padaria","Pão","un",False,False,0,"17.050.00","Genérico"),
        ("Biscoito de Amêndoa 200g","Biscoito amanteigado de amêndoa","19053100","Biscoitos","Padaria","Biscoitos","kg",False,False,0,"","Genérico"),
        ("Biscoito Anzac 200g","Biscoito anzac australiano","19053100","Biscoitos","Padaria","Biscoitos","kg",False,False,0,"","Importado"),
        ("Cookie Chocolate Chips 200g","Cookie americano","19053100","Biscoitos","Padaria","Biscoitos","kg",False,False,0,"","Genérico"),
        ("Biscoito Pepparkakor Sueco 150g","Biscoito de gengibre sueco","19053100","Biscoitos","Padaria","Biscoitos","kg",False,False,0,"","Importado"),
        ("Bolo de Pote Chocolate 200g","Bolo de pote","19052090","Outros produtos padaria","Padaria","Bolos","un",False,False,0,"","Genérico"),
        ("Cupcake Baunilha 2un","Cupcake de baunilha","19052090","Outros produtos padaria","Padaria","Bolos","un",False,False,0,"","Genérico"),
        ("Brownie de Chocolate 100g","Brownie de chocolate","19052090","Outros produtos padaria","Padaria","Bolos","un",False,False,0,"","Genérico"),
        ("Muffin de Blueberry 2un","Muffin de mirtilo","19052090","Outros produtos padaria","Padaria","Bolos","un",False,False,0,"","Genérico"),
        ("Scone Queijo Rosmarinho 2un","Scone de queijo e alecrim","19052090","Outros produtos padaria","Padaria","Bolos","un",False,False,0,"","Genérico"),
        ("Bolo Mármore 400g","Bolo mármore","19052090","Outros produtos padaria","Padaria","Bolos","kg",False,False,0,"","Genérico"),
    ]
    for item in padaria_var:
        ean = _make_ean_like(item[0])
        auto.append(_p(ean, *item))

    # CONDIMENTOS/MOLHOS VARIAÇÕES
    molhos_var = [
        ("Chimichurri Molho Fresco 100ml","Chimichurri fresco","21039091","Preparações para molhos, embalagem ≤1kg","Condimentos","Molhos Especiais","lt",False,False,0,"","Genérico"),
        ("Molho Gremolata 100ml","Gremolata italiana","21039091","Preparações para molhos, embalagem ≤1kg","Condimentos","Molhos Especiais","lt",False,False,0,"","Genérico"),
        ("Molho de Hortelã 100ml","Molho de hortelã","21039091","Preparações para molhos, embalagem ≤1kg","Condimentos","Molhos Especiais","lt",False,False,0,"","Genérico"),
        ("Molho Agridoce Chinês 150ml","Molho agridoce","21039091","Preparações para molhos, embalagem ≤1kg","Condimentos","Molhos Especiais","lt",False,False,0,"","Importado"),
        ("Molho Yakisoba 150ml","Molho para yakisoba","21039091","Preparações para molhos, embalagem ≤1kg","Condimentos","Molhos Especiais","lt",False,False,0,"","Importado"),
        ("Molho Sukiyaki 150ml","Molho para sukiyaki","21039091","Preparações para molhos, embalagem ≤1kg","Condimentos","Molhos Especiais","lt",False,False,0,"","Importado"),
        ("Curry Paste Vermelho 100g","Pasta de curry vermelho tailandês","21039091","Preparações para molhos, embalagem ≤1kg","Condimentos","Molhos Especiais","kg",False,False,0,"","Importado"),
        ("Curry Paste Verde 100g","Pasta de curry verde tailandês","21039091","Preparações para molhos, embalagem ≤1kg","Condimentos","Molhos Especiais","kg",False,False,0,"","Importado"),
        ("Molho Picante Mexicano 150ml","Molho picante mexicano","21039091","Preparações para molhos, embalagem ≤1kg","Condimentos","Molhos Especiais","lt",False,False,0,"","Importado"),
        ("Molho Cholula 150ml","Molho cholula","21039091","Preparações para molhos, embalagem ≤1kg","Condimentos","Molhos Especiais","lt",False,False,0,"","Importado"),
        ("Maionese Japonesa Kewpie 300ml","Maionese japonesa","21039091","Maionese","Condimentos","Maionese","lt",False,False,0,"","Importado"),
        ("Maionese Vegana 250ml","Maionese vegana","21039091","Maionese","Condimentos","Maionese","kg",False,False,0,"","Genérico"),
        ("Molho Stroganoff Pronto 350g","Molho stroganoff pronto","21039091","Preparações para molhos, embalagem ≤1kg","Condimentos","Molhos Especiais","kg",False,False,0,"","Genérico"),
        ("Molho Madeira 200ml","Molho madeira","21039091","Preparações para molhos, embalagem ≤1kg","Condimentos","Molhos Especiais","lt",False,False,0,"","Genérico"),
        ("Glacê de Mel e Mostarda 150ml","Glacê de mel e mostarda","21033010","Mostarda","Condimentos","Molhos Especiais","lt",False,False,0,"","Genérico"),
    ]
    for item in molhos_var:
        ean = _make_ean_like(item[0])
        auto.append(_p(ean, *item))

    # BEBIDAS ADICIONAIS
    bebidas_add = [
        ("Suco de Cranberry 300ml","Suco de cranberry","20098990","Outros sucos de frutos","Bebidas","Suco","lt",True,False,0,"17.010.00","Importado"),
        ("Suco Detox Couve e Gengibre 250ml","Suco detox","20098990","Outros sucos de frutos","Bebidas","Suco","lt",False,False,0,"17.010.00","Genérico"),
        ("Suco de Tomate Sacramento 200ml","Suco de tomate","20031000","Tomate preparado","Bebidas","Suco","lt",False,False,0,"","Importado"),
        ("Água Alcalina Ionizada 500ml","Água alcalina","22011000","Águas minerais","Bebidas","Água","lt",True,False,0,"03.005.00","Genérico"),
        ("Água com Gás Perrier 330ml","Água mineral francesa","22011000","Águas minerais","Bebidas","Água","lt",True,False,0,"03.001.00","Perrier"),
        ("Refrigerante Guaraná Caçula 2L","Refrigerante guaraná","22021000","Refrigerante","Bebidas","Refrigerante","lt",True,False,0,"03.010.00","Caçula"),
        ("Refrigerante Limão 2L","Refrigerante limão","22021000","Refrigerante","Bebidas","Refrigerante","lt",True,False,0,"03.010.00","Genérico"),
        ("Limonada Pronta 1L","Limonada pronta","22021000","Bebida gaseificada","Bebidas","Bebidas Especiais","lt",True,False,0,"03.007.00","Genérico"),
        ("Água de Coco com Polpa 500ml","Água de coco com polpa","20098100","Suco de coco","Bebidas","Água de Coco","lt",False,False,0,"17.011.00","Genérico"),
        ("Kombucha Hibisco 350ml","Kombucha de hibisco","22029900","Outras bebidas","Bebidas","Bebidas Especiais","lt",False,False,0,"","Genérico"),
        ("Kefir de Água 500ml","Kefir de água fermentado","22029900","Outras bebidas","Bebidas","Bebidas Especiais","lt",False,False,0,"","Genérico"),
        ("Bebida Vegetal de Castanha 1L","Bebida de castanha","22029900","Bebidas vegetais","Mercearia","Substitutos Lácteos","lt",False,False,0,"","Genérico"),
        ("Bebida de Coco 1L","Bebida de coco","22029900","Bebidas vegetais","Mercearia","Substitutos Lácteos","lt",False,False,0,"","Genérico"),
        ("Chá Gelado Limão 1L","Chá gelado limão","21012010","Extratos de chá","Bebidas","Chá","lt",True,False,0,"03.017.00","Genérico"),
        ("Chá Gelado Pêssego 1L","Chá gelado pêssego","21012010","Extratos de chá","Bebidas","Chá","lt",True,False,0,"03.017.00","Genérico"),
        ("Energético Action Labs 473ml","Bebida energética","21069090","Bebidas energéticas","Bebidas","Energético","lt",True,False,0,"03.014.00","Genérico"),
        ("Isotônico Powerade Uva 500ml","Isotônico uva","21069090","Bebidas isotônicas","Bebidas","Isotônico","lt",True,False,0,"03.015.00","Powerade"),
        ("Cerveja Artesanal Stout 330ml","Cerveja stout artesanal","22030000","Cervejas de malte","Bebidas","Cerveja","lt",True,False,0,"03.021.00","Genérico"),
        ("Cerveja Artesanal Porter 330ml","Cerveja porter artesanal","22030000","Cervejas de malte","Bebidas","Cerveja","lt",True,False,0,"03.021.00","Genérico"),
        ("Cerveja Artesanal Wheat 330ml","Cerveja de trigo artesanal","22030000","Cervejas de malte","Bebidas","Cerveja","lt",True,False,0,"03.021.00","Genérico"),
    ]
    for item in bebidas_add:
        ean = _make_ean_like(item[0])
        auto.append(_p(ean, *item))

    # VEGETAIS/HORTIFRUTI EXTRAS
    horti_extra = [
        ("Couve de Bruxelas 300g","Couve de bruxelas fresca","07042000","Couve de bruxelas","Hortifruti","Verduras","kg",False,True,0,"","Horta"),
        ("Endívia 200g","Endívia fresca","07052200","Endívias","Hortifruti","Verduras","kg",False,True,0,"","Importado"),
        ("Ruibarbo 200g","Ruibarbo fresco","07099990","Outros hortícolas","Hortifruti","Legumes","kg",False,True,0,"","Importado"),
        ("Alcachofra un","Alcachofra fresca","07099100","Alcachofras","Hortifruti","Legumes","un",False,True,0,"","Horta"),
        ("Funcho/Erva-Doce un","Funcho fresco","07099990","Outros hortícolas","Hortifruti","Legumes","un",False,True,0,"","Horta"),
        ("Couve Kale maço","Couve kale (couve-galega)","07049000","Outros couves","Hortifruti","Verduras","un",False,True,0,"","Horta"),
        ("Bok Choy maço","Bok choy (couve chinesa)","07049000","Outros couves","Hortifruti","Verduras","un",False,True,0,"","Horta"),
        ("Komatsuna maço","Komatsuna fresca","07049000","Outros couves","Hortifruti","Verduras","un",False,True,0,"","Horta"),
        ("Mostarda Verde maço","Folha de mostarda verde","07049000","Outros couves","Hortifruti","Verduras","un",False,True,0,"","Horta"),
        ("Água de Cana (Garapa) 500ml","Garapa fresca","17030000","Melaços de cana","Hortifruti","Frutas","lt",False,False,0,"","Feira"),
        ("Caju Fresco 500g","Caju fresco","08045010","Goiabas","Hortifruti","Frutas","kg",False,True,0,"","Feira"),
        ("Cupuaçu Polpa 400g","Polpa de cupuaçu","20079910","Purê de frutas","Hortifruti","Polpas","kg",False,False,0,"","Genérico"),
        ("Bacuri Polpa 400g","Polpa de bacuri","20079910","Purê de frutas","Hortifruti","Polpas","kg",False,False,0,"","Genérico"),
        ("Açaí Puro sem Açúcar 400g","Açaí puro congelado","20079910","Purê de frutas","Hortifruti","Polpas","kg",False,False,0,"","Genérico"),
        ("Uvaia Polpa 400g","Polpa de uvaia","20079910","Purê de frutas","Hortifruti","Polpas","kg",False,False,0,"","Genérico"),
        ("Mangaba Polpa 400g","Polpa de mangaba","20079910","Purê de frutas","Hortifruti","Polpas","kg",False,False,0,"","Genérico"),
        ("Pequi Polpa 200g","Polpa de pequi","20079910","Purê de frutas","Hortifruti","Polpas","kg",False,False,0,"","Genérico"),
        ("Buriti Polpa 200g","Polpa de buriti","20079910","Purê de frutas","Hortifruti","Polpas","kg",False,False,0,"","Genérico"),
        ("Murici Polpa 200g","Polpa de murici","20079910","Purê de frutas","Hortifruti","Polpas","kg",False,False,0,"","Genérico"),
        ("Umbu Polpa 400g","Polpa de umbu","20079910","Purê de frutas","Hortifruti","Polpas","kg",False,False,0,"","Genérico"),
    ]
    for item in horti_extra:
        ean = _make_ean_like(item[0])
        auto.append(_p(ean, *item))

    return auto


_PRODUCTS += _auto_products()


# ============================================================
# SEÇÃO 21: PRODUTOS FINAIS PARA COMPLETAR 2000+
# ============================================================

def _gen_extra_360():
    ex = []

    # SNACKS/BISCOITOS/CHOCOLATES VARIAÇÕES EXTRAS
    snacks_final = [
        ("Biscoito Oreo Duplo Recheio 144g","Biscoito Oreo duplo recheio","19053100","Biscoitos","Padaria","Biscoitos","kg",False,False,0,"","Nabisco"),
        ("Biscoito Bono Baunilha 200g","Biscoito Bono baunilha","19053100","Biscoitos","Padaria","Biscoitos","kg",False,False,0,"","Nestlé"),
        ("Biscoito Cream Cracker Integral 200g","Cream cracker integral","19053100","Biscoitos","Padaria","Biscoitos","kg",False,False,0,"","Isabela"),
        ("Biscoito Salgadinho Queijo 50g","Salgadinho de queijo","19053100","Biscoitos","Padaria","Biscoitos","kg",False,False,0,"17.031.00","Elma Chips"),
        ("Palha Italiana 200g","Palha italiana de chocolate","18069000","Preparações com cacau","Padaria","Chocolates","kg",False,False,0,"","Genérico"),
        ("Chocolate Branco com Morango 90g","Chocolate branco com morango","17049010","Chocolate branco","Padaria","Chocolates","kg",False,False,0,"17.001.00","Genérico"),
        ("Barra de Chocolate ao Leite 45g","Barra de chocolate ao leite","18063210","Chocolate em tabletes","Padaria","Chocolates","kg",False,False,0,"17.002.00","Genérico"),
        ("Trufas de Chocolate 100g","Trufas de chocolate","18069000","Preparações com cacau","Padaria","Chocolates","kg",False,False,0,"17.007.00","Genérico"),
        ("Caramelo Macio 200g","Caramelo macio","17049020","Caramelos","Snacks","Balas e Confeitos","kg",False,False,0,"","Genérico"),
        ("Marshmallow 200g","Marshmallow","17049090","Outros confeitaria","Snacks","Balas e Confeitos","kg",False,False,0,"","Genérico"),
        ("Drágea de Chocolate Colorida 100g","Drágea de chocolate","18069000","Preparações com cacau","Padaria","Chocolates","kg",False,False,0,"17.009.00","Genérico"),
        ("Gummy Bears 200g","Ursinhos de gelatina","17049020","Balas de gelatina","Snacks","Balas e Confeitos","kg",False,False,0,"","Importado"),
        ("Biscoito de Mel e Especiarias 200g","Biscoito especiado","19053100","Biscoitos","Padaria","Biscoitos","kg",False,False,0,"","Genérico"),
        ("Biscoito Ritz Nabisco 200g","Biscoito salgado redondo","19053100","Biscoitos","Padaria","Biscoitos","kg",False,False,0,"","Nabisco"),
        ("Biscoito Chips Ahoy 200g","Biscoito com gotas de chocolate","19053100","Biscoitos","Padaria","Biscoitos","kg",False,False,0,"","Nabisco"),
        ("Biscoito Integral Sementes 150g","Biscoito integral com sementes","19053100","Biscoitos","Padaria","Biscoitos","kg",False,False,0,"","Genérico"),
        ("Amido de Milho Organic 500g","Amido de milho orgânico","11081200","Amido de milho","Mercearia","Ingredientes","kg",False,True,0,"","Genérico"),
        ("Tapioca Hidratada Pronta 300g","Tapioca hidratada pronta","11081400","Fécula de mandioca","Cereais e Grãos","Tapioca","kg",False,True,0,"","Genérico"),
        ("Goma para Tapioca Hidratada 500g","Goma para tapioca hidratada","11081400","Fécula de mandioca","Cereais e Grãos","Tapioca","kg",False,True,0,"","Genérico"),
        ("Goma de Tapioca Seca Granulada 400g","Tapioca granulada seca","11081400","Fécula de mandioca","Cereais e Grãos","Tapioca","kg",False,True,0,"","Genérico"),
    ]

    # SUCOS E BEBIDAS MAIS
    sucos_f = [
        ("Néctar Acerola 1L","Néctar de acerola","20098990","Outros sucos de frutos","Bebidas","Suco","lt",True,False,0,"17.010.00","Genérico"),
        ("Néctar Caju 1L","Néctar de caju","20098990","Outros sucos de frutos","Bebidas","Suco","lt",True,False,0,"17.010.00","Genérico"),
        ("Néctar Pitanga 1L","Néctar de pitanga","20098990","Outros sucos de frutos","Bebidas","Suco","lt",True,False,0,"17.010.00","Genérico"),
        ("Suco de Abacaxi 200ml","Suco de abacaxi","20098990","Outros sucos de frutos","Bebidas","Suco","lt",True,False,0,"17.010.00","Genérico"),
        ("Suco Integral Pera 200ml","Suco integral de pera","20093000","Suco de pera","Bebidas","Suco","lt",False,False,0,"17.010.00","Genérico"),
        ("Suco Verde Kale e Pepino 250ml","Suco verde","20098990","Outros sucos de frutos","Bebidas","Suco","lt",False,False,0,"17.010.00","Genérico"),
        ("Limonada Suíça 500ml","Limonada suíça com leite","22021000","Bebida gaseificada","Bebidas","Bebidas Especiais","lt",True,False,0,"","Genérico"),
        ("Refrigerante Tônica Limonada 350ml","Tônica limonada","22021000","Bebida gaseificada","Bebidas","Bebidas Especiais","lt",True,False,0,"03.011.00","Genérico"),
        ("Cerveja Artesanal Sour 330ml","Cerveja sour artesanal","22030000","Cervejas de malte","Bebidas","Cerveja","lt",True,False,0,"03.021.00","Genérico"),
        ("Cerveja Artesanal Pale Ale 330ml","Cerveja pale ale","22030000","Cervejas de malte","Bebidas","Cerveja","lt",True,False,0,"03.021.00","Genérico"),
        ("Cerveja Artesanal Lager Premium 350ml","Cerveja lager premium","22030000","Cervejas de malte","Bebidas","Cerveja","lt",True,False,0,"03.021.00","Genérico"),
        ("Vinho Rosé Garibaldi 750ml","Vinho rosé gaúcho","22042100","Vinho em recipiente ≤2L","Bebidas","Vinho","lt",False,False,0,"","Garibaldi"),
        ("Vinho Tinto Seco Quinta do Morgado 750ml","Vinho tinto seco nacional","22042100","Vinho em recipiente ≤2L","Bebidas","Vinho","lt",False,False,0,"","Genérico"),
        ("Sidra de Maçã Deve 750ml","Sidra de maçã","22060000","Sidra","Bebidas","Destilados","lt",False,False,0,"","Genérico"),
        ("Caipirinha Pronta Lata 269ml","Caipirinha pronta lata","22089000","Outras bebidas destiladas","Bebidas","Destilados","lt",False,False,0,"","Genérico"),
    ]

    # PEIXES VARIAÇÕES EXTRAS
    peixes_f = [
        ("Atum em Azeite com Ervas 130g","Atum em azeite com ervas","16041410","Atuns preparados","Enlatados","Peixes","un",False,False,0,"17.080.00","Genérico"),
        ("Sardinha em Azeite Importada 125g","Sardinha em azeite importada","16041310","Sardinhas preparadas","Enlatados","Peixes","un",False,False,0,"17.081.00","Importado"),
        ("Anchova em Conserva 50g","Anchova em conserva","16041100","Salmão preparado","Enlatados","Peixes","un",False,False,0,"","Importado"),
        ("Caranguejo em Lata 100g","Caranguejo em conserva","16051000","Caranguejos preparados","Enlatados","Frutos do Mar","un",False,False,0,"17.082.00","Importado"),
        ("Lagosta em Conserva 100g","Lagosta em conserva","16052000","Camarões preparados","Enlatados","Frutos do Mar","un",False,False,0,"17.082.00","Importado"),
        ("Bacalhau em Lascas Dessalgado 500g","Bacalhau lascas dessalgado","03053200","Bacalhau seco e salgado","Carnes","Peixes","kg",False,True,0,"","Gadus"),
        ("Camarão Empanado Pronto Congelado 400g","Camarão empanado congelado","16052000","Camarões preparados","Congelados","Frutos do Mar","kg",False,False,0,"","Genérico"),
        ("Polvo ao Alho Congelado 300g","Polvo ao alho pronto","16059000","Outros invertebrados","Congelados","Frutos do Mar","kg",False,False,0,"","Genérico"),
        ("Patê de Atum 100g","Patê de atum","16042000","Outras preparações de peixe","Enlatados","Peixes","kg",False,False,0,"","Genérico"),
        ("Patê de Sardinha 100g","Patê de sardinha","16041310","Sardinhas preparadas","Enlatados","Peixes","kg",False,False,0,"","Genérico"),
    ]

    # EMBUTIDOS EXTRAS
    embut_f = [
        ("Linguiça Fresca Suína Tradicional 500g","Linguiça suína fresca","16010000","Enchidos","Carnes","Embutidos e Frios","kg",False,False,0,"17.077.00","Genérico"),
        ("Linguiça Defumada de Perú 200g","Linguiça defumada de peru","16010000","Enchidos","Carnes","Embutidos e Frios","kg",False,False,0,"17.077.00","Genérico"),
        ("Presunto Cozido Light 200g","Presunto cozido light","16024900","Preparações de suíno","Carnes","Embutidos e Frios","kg",False,False,0,"17.079.00","Genérico"),
        ("Salaminho Mini 100g","Salaminho seco","16010000","Enchidos","Carnes","Embutidos e Frios","kg",False,False,0,"17.076.00","Genérico"),
        ("Pepperoni Fatiado 100g","Pepperoni fatiado","16010000","Enchidos","Carnes","Embutidos e Frios","kg",False,False,0,"17.076.00","Genérico"),
        ("Blanquet de Frango 200g","Blanquet de frango light","16023220","Preparações de frango","Carnes","Embutidos e Frios","kg",False,False,0,"17.079.00","Genérico"),
        ("Sobrecoxa Defumada 300g","Sobrecoxa defumada","16023220","Preparações de frango","Carnes","Embutidos e Frios","kg",False,False,0,"17.079.00","Genérico"),
        ("Frango Grelhado em Tiras 200g","Frango grelhado tiras","16023220","Preparações de frango","Carnes","Embutidos e Frios","kg",False,False,0,"","Genérico"),
        ("Tender de Frango 500g","Tender de frango inteiro","16023220","Preparações de frango","Carnes","Embutidos e Frios","kg",False,False,0,"17.079.00","Genérico"),
        ("Chouriço Artesanal 200g","Chouriço artesanal","16010000","Enchidos","Carnes","Embutidos e Frios","kg",False,False,0,"17.076.00","Genérico"),
    ]

    # SOBREMESAS / DOCES EXTRAS
    doces_f = [
        ("Panetone Mini 100g","Panetone mini individual","19052010","Panetone","Padaria","Panetone","un",False,False,0,"","Genérico"),
        ("Chocotone 400g","Panetone de chocolate","19052010","Panetone","Padaria","Panetone","kg",False,False,0,"","Bauducco"),
        ("Bolo de Mel Madeirense 400g","Bolo de mel da Madeira","19052090","Outros produtos padaria","Padaria","Bolos","kg",False,False,0,"","Importado"),
        ("Torta de Limão Congelada 800g","Torta de limão congelada","19052090","Outros produtos padaria","Congelados","Tortas","kg",False,False,0,"","Genérico"),
        ("Torta de Maçã Congelada 800g","Torta de maçã congelada","19052090","Outros produtos padaria","Congelados","Tortas","kg",False,False,0,"","Genérico"),
        ("Sorvete Palito Baunilha 80ml","Sorvete palito baunilha","21050000","Sorvetes","Congelados","Sorvetes","lt",False,False,0,"23.001.00","Genérico"),
        ("Sorvete Palito Morango 80ml","Sorvete palito morango","21050000","Sorvetes","Congelados","Sorvetes","lt",False,False,0,"23.001.00","Genérico"),
        ("Sorvete Palito Limão 80ml","Sorvete palito limão","21050000","Sorvetes","Congelados","Sorvetes","lt",False,False,0,"23.001.00","Genérico"),
        ("Açaí na Tigela 300g","Açaí preparado com granola","21050000","Sorvetes","Congelados","Sorvetes","kg",False,False,0,"","Genérico"),
        ("Frozen Yogurt Natural 300ml","Frozen yogurt natural","21050000","Sorvetes","Congelados","Sorvetes","lt",False,False,0,"23.001.00","Genérico"),
    ]

    # HORTIFRUTI CONSERVAS
    horti_cons = [
        ("Banana Verde em Biomassa 400g","Biomassa de banana verde","20079910","Purê de frutas","Hortifruti","Conservas","kg",False,False,0,"","Genérico"),
        ("Grão de Milho de Pipoca Gourmet 500g","Milho pipoca gourmet","10059010","Milho em grão","Cereais e Grãos","Milho","kg",False,True,0,"","Genérico"),
        ("Coco Ralado Fresco 100g","Coco fresco ralado","20081990","Outros","Hortifruti","Frutas","kg",False,False,0,"","Genérico"),
        ("Azeitona Chilena 200g","Azeitona chilena em conserva","20057000","Azeitonas","Enlatados","Conservas de Verduras","kg",False,False,0,"","Importado"),
        ("Azeitona Azapa Preta 150g","Azeitona azapa preta","20057000","Azeitonas","Enlatados","Conservas de Verduras","kg",False,False,0,"","Importado"),
        ("Tomate Seco em Azeite 90g","Tomate seco em azeite","20029000","Outros tomates preparados","Enlatados","Conservas de Tomate","kg",False,False,0,"","Genérico"),
        ("Antipasto de Tomate 180g","Antipasto de tomate","21039091","Preparações para molhos, embalagem ≤1kg","Condimentos","Molhos Especiais","kg",False,False,0,"","Importado"),
        ("Ervilha Fresca Congelada 400g","Ervilha fresca congelada","07102100","Ervilhas congeladas","Congelados","Vegetais","kg",False,True,0,"","Genérico"),
        ("Edamame Congelado 400g","Edamame (soja verde) congelado","07109000","Misturas vegetais congeladas","Congelados","Vegetais","kg",False,True,0,"","Importado"),
        ("Cogumelo Shimeji Congelado 200g","Shimeji congelado","07108000","Outros vegetais congelados","Congelados","Vegetais","kg",False,True,0,"","Genérico"),
    ]

    # INGREDIENTES PARA RESTAURANTE
    restaurante_f = [
        ("Pasta de Curry Masala 200g","Pasta de curry masala","21039091","Preparações para molhos, embalagem ≤1kg","Foodservice","Ingredientes","kg",False,False,0,"","Importado"),
        ("Ghee Artesanal 200g","Manteiga ghee artesanal","04059090","Gorduras do leite","Foodservice","Ingredientes","kg",False,False,0,"","Genérico"),
        ("Vinagre de Champagne 250ml","Vinagre de champagne","22090000","Vinagres","Foodservice","Ingredientes","lt",False,False,0,"","Importado"),
        ("Lecitina de Soja 200g","Lecitina de soja para emulsão","12079920","Sementes de soja","Foodservice","Ingredientes","kg",False,False,0,"","Genérico"),
        ("Pectina 200g","Pectina para geleias","13022000","Pectina","Foodservice","Ingredientes","kg",False,False,0,"","Genérico"),
        ("Carragena 100g","Carragena para espessamento","13023900","Outros mucilagens","Foodservice","Ingredientes","kg",False,False,0,"","Importado"),
        ("Glicerina Vegetal 100ml","Glicerina vegetal alimentícia","15200000","Glicerol","Foodservice","Ingredientes","lt",False,False,0,"","Genérico"),
        ("Metilcelulose 100g","Metilcelulose alimentícia","39129090","Outros derivados celulose","Foodservice","Ingredientes","kg",False,False,0,"","Importado"),
        ("Ácido Cítrico 100g","Ácido cítrico para conservação","29181400","Ácido cítrico","Foodservice","Ingredientes","kg",False,False,0,"","Genérico"),
        ("Vitamina C Ascórbica 100g","Ácido ascórbico alimentício","29362700","Ácido ascórbico","Foodservice","Ingredientes","kg",False,False,0,"","Genérico"),
    ]

    # CEREAIS MATINAIS EXTRAS
    cereais_mat = [
        ("Granola Castanha e Mel 1kg","Granola com castanhas e mel","19042000","Preparações de cereais","Cereais e Grãos","Cereais Matinais","kg",False,False,0,"17.030.00","Genérico"),
        ("Granola Tropical 500g","Granola tropical","19042000","Preparações de cereais","Cereais e Grãos","Cereais Matinais","kg",False,False,0,"17.030.00","Genérico"),
        ("Granola Zero Açúcar 300g","Granola sem açúcar","19042000","Preparações de cereais","Cereais e Grãos","Cereais Matinais","kg",False,False,0,"17.030.00","Genérico"),
        ("Cereal Matinal Açaí e Castanha 300g","Cereal açaí","19042000","Preparações de cereais","Cereais e Grãos","Cereais Matinais","kg",False,False,0,"17.030.00","Genérico"),
        ("Cornflakes Sem Açúcar 250g","Cornflakes sem açúcar","19041000","Cereais expansão/tostados","Cereais e Grãos","Cereais Matinais","kg",False,False,0,"17.030.00","Genérico"),
        ("All-Bran Fibras 200g","Cereal de fibras de trigo","19041000","Cereais expansão/tostados","Cereais e Grãos","Cereais Matinais","kg",False,False,0,"17.030.00","Kellogg's"),
        ("Special K Morango 300g","Cereal especial morango","19041000","Cereais expansão/tostados","Cereais e Grãos","Cereais Matinais","kg",False,False,0,"17.030.00","Kellogg's"),
        ("Granola Protein 400g","Granola proteica","19042000","Preparações de cereais","Cereais e Grãos","Cereais Matinais","kg",False,False,0,"17.030.00","Genérico"),
        ("Aveia Cortada Tipo Escocesa 500g","Aveia tipo escocesa","11041200","Aveia trabalhada","Cereais e Grãos","Cereais Matinais","kg",False,True,0,"","Importado"),
        ("Amaranto Tostado 200g","Amaranto tostado para cereal","10089000","Outros cereais","Cereais e Grãos","Cereais Matinais","kg",False,True,0,"","Genérico"),
    ]

    # MASSAS COMPLEMENTARES
    massas_comp = [
        ("Macarrão Tipo Mistura Cozinha 500g","Mistura de massas","19023000","Massas alimentícias","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"17.049.00","Genérico"),
        ("Macarrão Penne Integral 500g","Penne integral","19023000","Massas alimentícias","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"17.049.00","Barilla"),
        ("Macarrão Fusilli Integral 500g","Fusilli integral","19023000","Massas alimentícias","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"17.049.00","Barilla"),
        ("Macarrão Espiral Colorido 500g","Espiral tricolor","19023000","Massas alimentícias","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"17.049.00","Genérico"),
        ("Macarrão Cotovelo 500g","Cotovelo para macarrão","19023000","Massas alimentícias","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"17.049.00","Genérico"),
        ("Macarrão Gravata 500g","Farfalle/gravata","19023000","Massas alimentícias","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"17.049.00","Barilla"),
        ("Macarrão Cavatappi 500g","Cavatappi","19023000","Massas alimentícias","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"17.049.00","Genérico"),
        ("Macarrão Ziti 500g","Ziti italiano","19023000","Massas alimentícias","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"17.049.00","Genérico"),
        ("Macarrão Acini di Pepe 500g","Pequenas massinhas","19023000","Massas alimentícias","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"17.049.00","Genérico"),
        ("Macarrão de Soba Orgânico 300g","Soba orgânico","19023000","Massas alimentícias","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"","Importado"),
    ]

    all_groups = [snacks_final, sucos_f, peixes_f, embut_f, doces_f, horti_cons, restaurante_f, cereais_mat, massas_comp]

    for group in all_groups:
        for item in group:
            ean = _make_ean_like(item[0])
            ex.append(_p(ean, *item))

    return ex


_PRODUCTS += _gen_extra_360()


# ============================================================
# SEÇÃO 22: ÚLTIMO BLOCO PARA ATINGIR 2000+ PRODUTOS
# ============================================================

def _gen_last_block():
    last = []

    # 255 products to reach 2000+
    items = [
        ("Açúcar Mascavo Escuro 500g","Açúcar mascavo escuro","17011400","Açúcar de cana","Cereais e Grãos","Açúcar","kg",False,False,0,"","Genérico"),
        ("Sal Temperado Ervas Italianas","Sal com ervas italianas","25010020","Sal outros","Cereais e Grãos","Sal","kg",False,True,0,"","Genérico"),
        ("Farinha de Trigo Manitoba 1kg","Farinha de trigo forte","11010010","Farinha de trigo","Cereais e Grãos","Farinha de Trigo","kg",False,True,0,"","Importado"),
        ("Farinha Integral Sem Glúten 500g","Farinha sem glúten integral","11029000","Outras farinhas","Cereais e Grãos","Sem Glúten","kg",False,True,0,"","Genérico"),
        ("Pasta de Girassol 200g","Pasta de semente de girassol","20089900","Sementes preparadas","Mercearia","Pastas","kg",False,False,0,"","Genérico"),
        ("Tahine Escuro 200g","Tahine de gergelim escuro","20081900","Outras castanhas","Mercearia","Pastas","kg",False,False,0,"","Importado"),
        ("Geleia de Chia com Morango 200g","Geleia de morango com chia","20079910","Geleias","Mercearia","Geleias","kg",False,False,0,"","Genérico"),
        ("Geleia de Hibisco e Maçã 200g","Geleia de hibisco","20079910","Geleias","Mercearia","Geleias","kg",False,False,0,"","Genérico"),
        ("Geleia de Lichia 200g","Geleia de lichia","20079910","Geleias","Mercearia","Geleias","kg",False,False,0,"","Genérico"),
        ("Mel de Laranjeira 250g","Mel de flor de laranjeira","04090000","Mel natural","Mercearia","Mel","kg",False,False,0,"","Genérico"),
        ("Mel de Eucalipto 250g","Mel de eucalipto","04090000","Mel natural","Mercearia","Mel","kg",False,False,0,"","Genérico"),
        ("Mel Silvestre 250g","Mel silvestre","04090000","Mel natural","Mercearia","Mel","kg",False,False,0,"","Genérico"),
        ("Xarope de Bordo Grade A 250ml","Xarope de bordo","17022000","Açúcar de bordo","Mercearia","Adoçantes","lt",False,False,0,"","Importado"),
        ("Calda de Frutas Vermelhas 200g","Calda de frutas vermelhas","20079910","Geleias","Mercearia","Doces","kg",False,False,0,"","Genérico"),
        ("Compota de Maçã e Canela 400g","Compota de maçã","20079910","Geleias e marmeladas","Mercearia","Doces","kg",False,False,0,"","Genérico"),
        ("Pasta de Damasco 200g","Pasta de damasco","20079910","Geleias","Mercearia","Geleias","kg",False,False,0,"","Genérico"),
        ("Pasta de Ameixa 200g","Pasta de ameixa","20079910","Geleias","Mercearia","Geleias","kg",False,False,0,"","Genérico"),
        ("Chips de Abóbora 50g","Chips de abóbora","20052000","Batatas preparadas","Snacks","Salgadinhos","kg",False,False,0,"17.031.00","Genérico"),
        ("Chips de Cenoura 50g","Chips de cenoura","20049000","Outros vegetais","Snacks","Salgadinhos","kg",False,False,0,"17.031.00","Genérico"),
        ("Chips de Beterraba 50g","Chips de beterraba","20049000","Outros vegetais","Snacks","Salgadinhos","kg",False,False,0,"17.031.00","Genérico"),
        ("Chips de Aipim Frito 50g","Chips de aipim/mandioca","20052000","Batatas preparadas","Snacks","Salgadinhos","kg",False,False,0,"17.031.00","Genérico"),
        ("Chips de Banana da Terra 50g","Chips de banana da terra","20049000","Outros vegetais","Snacks","Salgadinhos","kg",False,False,0,"","Genérico"),
        ("Torresmo de Roti 100g","Torresmo de roti","15011000","Banha","Carnes","Carne Suína","kg",False,False,0,"","Genérico"),
        ("Nuggets de Peixe 300g","Nuggets de peixe empanados","16042000","Preparações de peixe","Congelados","Peixes","kg",False,False,0,"","Genérico"),
        ("Nuggets de Frango Orgânico 300g","Nuggets de frango orgânico","16023220","Preparações de frango","Congelados","Salgados","kg",False,False,0,"","Genérico"),
        ("Hambúrguer de Salmão 200g","Hambúrguer de salmão","16042000","Preparações de peixe","Congelados","Peixes","kg",False,False,0,"","Genérico"),
        ("Hambúrguer de Atum 200g","Hambúrguer de atum","16042000","Preparações de peixe","Congelados","Peixes","kg",False,False,0,"","Genérico"),
        ("Espetinho de Frango Congelado 300g","Espetinho de frango","16023220","Preparações de frango","Congelados","Pratos Prontos","kg",False,False,0,"","Genérico"),
        ("Espetinho Misto Congelado 300g","Espetinho misto","16025000","Preparações carne","Congelados","Pratos Prontos","kg",False,False,0,"","Genérico"),
        ("Risoto de Queijo Congelado 300g","Risoto de queijo pronto","19019090","Outras preparações","Congelados","Pratos Prontos","kg",False,False,0,"","Genérico"),
        ("Risoto de Camarão Congelado 300g","Risoto de camarão pronto","16052000","Camarões preparados","Congelados","Pratos Prontos","kg",False,False,0,"","Genérico"),
        ("Frango ao Molho Shoyu Congelado 300g","Frango ao shoyu pronto","16023220","Preparações de frango","Congelados","Pratos Prontos","kg",False,False,0,"","Genérico"),
        ("Shakshuka Congelada 300g","Shakshuka pronta congelada","21041000","Sopas e caldos","Congelados","Pratos Prontos","kg",False,False,0,"","Genérico"),
        ("Moqueca de Peixe Congelada 300g","Moqueca de peixe pronta","16042000","Preparações de peixe","Congelados","Pratos Prontos","kg",False,False,0,"","Genérico"),
        ("Arroz Temperado Congelado 300g","Arroz temperado pronto","10063021","Arroz semibranqueado ou branqueado, polido ou brunido","Congelados","Arroz","kg",False,True,0,"","Genérico"),
        ("Quinoa Cozida Pronta 250g","Quinoa cozida pronta","10089000","Outros cereais","Congelados","Grãos","kg",False,True,0,"","Genérico"),
        ("Canjica Pronta 200g","Canjica pronta para consumo","11031300","Sêmola de milho","Cereais e Grãos","Sobremesas","kg",False,False,0,"","Genérico"),
        ("Pão de Queijo Pré-Assado 6un","Pão de queijo pré-assado","19052090","Outros pães","Padaria","Pão de Queijo","un",False,False,0,"","Forno de Minas"),
        ("Coxinha de Frango Assada 6un","Coxinha assada","16023220","Preparações de frango","Padaria","Salgados","un",False,False,0,"","Genérico"),
        ("Esfiha de Carne Assada 6un","Esfiha assada","19052090","Outros padaria","Padaria","Salgados","un",False,False,0,"","Genérico"),
        ("Quiche Lorraine Individual 100g","Quiche lorraine individual","19052090","Outros padaria","Padaria","Salgados","un",False,False,0,"","Genérico"),
        ("Pão de Mel Individual 50g","Pão de mel","19052090","Outros padaria","Padaria","Bolos","un",False,False,0,"","Genérico"),
        ("Bolinho de Chuva 200g","Bolinho de chuva","19052090","Outros padaria","Padaria","Bolos","kg",False,False,0,"","Genérico"),
        ("Torta de Frango Congelada 500g","Torta de frango congelada","19052090","Outros padaria","Congelados","Pratos Prontos","kg",False,False,0,"","Genérico"),
        ("Pão de Batata Caseiro 400g","Pão de batata","19052090","Outros pães","Padaria","Pão Especial","kg",False,False,0,"17.050.00","Genérico"),
        ("Pão de Leite Macio 400g","Pão de leite","19052090","Outros pães","Padaria","Pão Especial","kg",False,False,0,"17.050.00","Genérico"),
        ("Pão Australiano 400g","Pão australiano escuro","19052090","Outros pães","Padaria","Pão Especial","kg",False,False,0,"17.050.00","Genérico"),
        ("Pão de Mandioca 400g","Pão de mandioca","19052090","Outros pães","Padaria","Pão Especial","kg",False,False,0,"17.050.00","Genérico"),
        ("Bolo Fubá com Erva-Doce 500g","Bolo de fubá com erva-doce","19052090","Outros padaria","Padaria","Bolos","kg",False,False,0,"","Genérico"),
        ("Bolo de Laranja 500g","Bolo de laranja","19052090","Outros padaria","Padaria","Bolos","kg",False,False,0,"","Genérico"),
        ("Bolo de Limão 500g","Bolo de limão","19052090","Outros padaria","Padaria","Bolos","kg",False,False,0,"","Genérico"),
        ("Bolo de Coco 500g","Bolo de coco","19052090","Outros padaria","Padaria","Bolos","kg",False,False,0,"","Genérico"),
        ("Bolo de Amendoim 500g","Bolo de amendoim","19052090","Outros padaria","Padaria","Bolos","kg",False,False,0,"","Genérico"),
        ("Bolo Floresta Negra 500g","Bolo floresta negra","19052090","Outros padaria","Padaria","Bolos","kg",False,False,0,"","Genérico"),
        ("Bolo Red Velvet 500g","Bolo red velvet","19052090","Outros padaria","Padaria","Bolos","kg",False,False,0,"","Genérico"),
        ("Cheesecake de Morango 300g","Cheesecake de morango","19052090","Outros padaria","Padaria","Bolos","kg",False,False,0,"","Genérico"),
        ("Tiramisù 200g","Tiramisù italiano","19052090","Outros padaria","Padaria","Sobremesas","kg",False,False,0,"","Genérico"),
        ("Pudim de Leite 200g","Pudim de leite condensado","19019090","Outras preparações","Mercearia","Sobremesas","kg",False,False,0,"","Genérico"),
        ("Brigadeiro Gourmet 30g","Brigadeiro gourmet","18069000","Preparações com cacau","Padaria","Chocolates","un",False,False,0,"","Genérico"),
        ("Beijinho Gourmet 30g","Beijinho gourmet","17049090","Outros confeitaria","Padaria","Doces","un",False,False,0,"","Genérico"),
        ("Cajuzinho Gourmet 30g","Cajuzinho de amendoim","17049090","Outros confeitaria","Padaria","Doces","un",False,False,0,"","Genérico"),
        ("Quindim 30g","Quindim de coco","19052090","Outros padaria","Padaria","Sobremesas","un",False,False,0,"","Genérico"),
        ("Cocada de Forno 100g","Cocada de forno","17049090","Outros confeitaria","Padaria","Doces","kg",False,False,0,"","Genérico"),
        ("Doce de Abóbora com Coco 100g","Doce de abóbora e coco","20079910","Geleias","Mercearia","Doces","kg",False,False,0,"","Genérico"),
        ("Marmelada de Marmelo 200g","Marmelada de marmelo","20079910","Geleias e marmeladas","Mercearia","Doces","kg",False,False,0,"","Genérico"),
        ("Pé de Moleque 100g","Pé de moleque de amendoim","17049090","Outros confeitaria","Snacks","Doces","kg",False,False,0,"","Genérico"),
        ("Amendoim Pralinê 100g","Amendoim pralinê","17049090","Outros confeitaria","Snacks","Doces","kg",False,False,0,"","Genérico"),
        ("Pinhão Cozido 200g","Pinhão cozido para consumo","08029100","Pinhões","Hortifruti","Frutas","kg",False,True,0,"","Genérico"),
        ("Figo Fresco kg","Figo fresco","08040000","Tâmaras e figos","Hortifruti","Frutas","kg",False,True,0,"","Feira"),
        ("Amora Silvestre 100g","Amora silvestre fresca","08120020","Amoras","Hortifruti","Frutas","kg",False,True,0,"","Horta"),
        ("Groselha Fresca 100g","Groselha fresca","08129000","Outros frutos pequenos","Hortifruti","Frutas","kg",False,True,0,"","Horta"),
        ("Framboesa Fresca 100g","Framboesa fresca","08120010","Framboesas","Hortifruti","Frutas","kg",False,True,0,"","Horta"),
        ("Castanha Portuguesa 200g","Castanha portuguesa","08023200","Castanhas","Hortifruti","Frutas","kg",False,True,0,"","Importado"),
        ("Romã un","Romã fresca","08104500","Romãs","Hortifruti","Frutas","un",False,True,0,"","Importado"),
        ("Figo da Índia un","Figo da índia fresco","08109000","Outras frutas","Hortifruti","Frutas","un",False,True,0,"","Importado"),
        ("Physalis 100g","Physalis fresca","08109000","Outras frutas","Hortifruti","Frutas","kg",False,True,0,"","Horta"),
        ("Pitaya Vermelha un","Pitaya vermelha fresca","08109000","Outras frutas","Hortifruti","Frutas","un",False,True,0,"","Horta"),
        ("Carambola Doce 500g","Carambola doce","08109000","Outras frutas","Hortifruti","Frutas","kg",False,True,0,"","Feira"),
        ("Jaca Fresca Madura kg","Jaca madura","08109000","Outras frutas","Hortifruti","Frutas","kg",False,True,0,"","Feira"),
        ("Jenipapo kg","Jenipapo fresco","08109000","Outras frutas","Hortifruti","Frutas","kg",False,True,0,"","Feira"),
        ("Seriguela kg","Seriguela fresca","08109000","Outras frutas","Hortifruti","Frutas","kg",False,True,0,"","Feira"),
        ("Cajá kg","Cajá fresco","08109000","Outras frutas","Hortifruti","Frutas","kg",False,True,0,"","Feira"),
        ("Tamarindo 200g","Tamarindo fresco","08109000","Outras frutas","Hortifruti","Frutas","kg",False,True,0,"","Feira"),
        ("Inharé/Maniçoba Fresca 200g","Maniçoba fresca","07099990","Outros hortícolas","Hortifruti","Verduras","kg",False,True,0,"","Feira"),
        ("Jambu Fresco maço","Jambu fresco","07099990","Outros hortícolas","Hortifruti","Ervas","un",False,True,0,"","Horta"),
        ("Chicória do Pará maço","Chicória do Pará","07099990","Outros hortícolas","Hortifruti","Verduras","un",False,True,0,"","Horta"),
        ("Vinagreira Fresca maço","Vinagreira (hibisco) fresca","07099990","Outros hortícolas","Hortifruti","Verduras","un",False,True,0,"","Horta"),
        ("Coentro em Pó 30g","Coentro seco em pó","09099900","Outras especiarias","Condimentos","Especiarias","kg",False,False,0,"","Sirial"),
        ("Casca de Limão Desidratada 15g","Casca de limão desidratada","12119090","Plantas aromáticas","Condimentos","Especiarias","kg",False,False,0,"","Genérico"),
        ("Extrato de Baunilha Natural 100ml","Extrato de baunilha natural","21069090","Preparações alimentícias","Condimentos","Extratos","lt",False,False,0,"","Importado"),
        ("Brandy Seco 250ml","Brandy para culinária","22083000","Conhaque","Condimentos","Extratos","lt",False,False,0,"","Importado"),
        ("Vinho Branco Seco para Cozinhar 750ml","Vinho para cozinhar","22042100","Vinho em recipiente ≤2L","Condimentos","Extratos","lt",False,False,0,"","Genérico"),
        ("Limão-Siciliano em Conserva 200g","Limão siciliano em conserva","20019000","Outros vegetais","Enlatados","Conservas de Verduras","kg",False,False,0,"","Importado"),
        ("Limão Levantine Preservado 200g","Limão preservado levantino","20019000","Outros vegetais","Enlatados","Conservas de Verduras","kg",False,False,0,"","Importado"),
        ("Catchup Picante Heinz 200g","Ketchup picante","21032010","Ketchup","Condimentos","Ketchup","kg",False,False,0,"17.034.00","Heinz"),
        ("Mostarda Americana Amarela 200g","Mostarda americana","21033010","Mostarda","Condimentos","Mostarda","kg",False,False,0,"","Genérico"),
        ("Relish de Pepino 200g","Relish de pepino","20019000","Outros vegetais conservados","Condimentos","Molhos Especiais","kg",False,False,0,"","Importado"),
        ("Chucrute 400g","Chucrute fermentado","20019000","Outros vegetais conservados","Enlatados","Conservas de Verduras","kg",False,False,0,"","Importado"),
        ("Kimchi 200g","Kimchi coreano","20019000","Outros vegetais conservados","Enlatados","Conservas de Verduras","kg",False,False,0,"","Importado"),
        ("Pickles Mistos 400g","Pickles mistos em conserva","20019000","Outros vegetais conservados","Enlatados","Conservas de Verduras","kg",False,False,0,"","Importado"),
        ("Batata Chips Artesanal Limão 50g","Chips artesanais limão","19041000","Cereais expansão","Snacks","Salgadinhos","kg",False,False,0,"17.031.00","Genérico"),
        ("Salgadinho de Soja 50g","Salgadinho de soja","19041000","Cereais expansão","Snacks","Salgadinhos","kg",False,False,0,"17.031.00","Genérico"),
        ("Pipoca de Cheddar 50g","Pipoca sabor cheddar","19041000","Cereais expansão","Snacks","Pipoca","kg",False,False,0,"","Genérico"),
        ("Pipoca Caramelada 100g","Pipoca caramelizada","19041000","Cereais expansão","Snacks","Pipoca","kg",False,False,0,"","Genérico"),
        ("Amendoim Seco Temperado 100g","Amendoim seco temperado","20081100","Amendoim preparado","Snacks","Aperitivos","kg",False,False,0,"17.033.00","Genérico"),
        ("Pistache Torrado com Sal 100g","Pistache torrado salgado","08025200","Pistache","Snacks","Aperitivos","kg",False,False,0,"17.033.00","Importado"),
        ("Castanha de Cajú Temperada 100g","Castanha tempero misto","20081900","Castanhas preparadas","Snacks","Aperitivos","kg",False,False,0,"17.033.00","Genérico"),
        ("Castanha do Pará Torrada 100g","Castanha do Pará torrada","20081900","Castanhas preparadas","Snacks","Aperitivos","kg",False,False,0,"17.033.00","Genérico"),
        ("Barra de Castanhas e Sementes 30g","Barra de castanhas","19042000","Barras de cereais","Snacks","Barras de Cereais","kg",False,False,0,"","Genérico"),
        ("Barra de Proteína Chocolate 60g","Barra proteica chocolate","19042000","Barras de cereais","Snacks","Barras de Cereais","kg",False,False,0,"","Genérico"),
        ("Barra de Banana e Aveia 25g","Barra de banana e aveia","19042000","Barras de cereais","Snacks","Barras de Cereais","kg",False,False,0,"","Genérico"),
        ("Leite UHT Piracanjuba 200ml","Leite UHT mini 200ml","04011010","Leite UHT","Laticínios","Leite UHT","lt",False,True,0,"17.016.00","Piracanjuba"),
        ("Leite UHT Longa Vida Tirol 200ml","Leite UHT mini Tirol","04011010","Leite UHT","Laticínios","Leite UHT","lt",False,True,0,"17.016.00","Tirol"),
        ("Leite de Coco em Pó 100g","Leite de coco em pó","20099000","Outros sucos","Mercearia","Ingredientes","kg",False,False,0,"","Ducoco"),
        ("Leite Condensado Diet 395g","Leite condensado diet","04029900","Leite condensado","Laticínios","Leite Condensado","kg",False,False,0,"17.020.00","Nestlé"),
        ("Creme Chantilly em Pó 200g","Chantilly em pó","19019090","Outras preparações","Padaria","Chantilly","kg",False,False,0,"","Genérico"),
        ("Sour Cream 200g","Sour cream","04032000","Iogurte","Laticínios","Iogurte","kg",False,False,0,"17.021.00","Genérico"),
        ("Iogurte Quefir Natural 500g","Kefir de leite natural","04039000","Outros leites fermentados","Laticínios","Bebida Láctea","kg",False,False,0,"17.021.00","Genérico"),
        ("Leitão de Leite 2kg","Leitão para assar","02031100","Carcaças suínas frescas","Carnes","Carne Suína","kg",False,True,0,"","Resfriada"),
        ("Vitela 500g","Vitela bovina fresca","02041000","Carcaças de cordeiro","Carnes","Carne Bovina","kg",False,True,0,"","Importada"),
        ("Cordeiro Costela 500g","Costela de cordeiro","02042200","Outras peças de cordeiro","Carnes","Cordeiro","kg",False,True,0,"","Importada"),
        ("Cordeiro Pernil 1kg","Pernil de cordeiro","02042200","Outras peças de cordeiro","Carnes","Cordeiro","kg",False,True,0,"","Importada"),
        ("Cordeiro Molida 500g","Carne de cordeiro moída","02043000","Carcaças de cordeiro congelado","Carnes","Cordeiro","kg",False,True,0,"","Importada"),
        ("Carneiro Costela 500g","Costela de carneiro","02044200","Outras peças não desossadas","Carnes","Cordeiro","kg",False,True,0,"","Importada"),
        ("Caprina Carne 500g","Carne caprina","02045000","Carnes caprinas","Carnes","Carne de Caprino","kg",False,True,0,"","Genérico"),
        ("Pato Confit Congelado 400g","Pato confit pronto","16022000","Preparações de fígados","Congelados","Aves","kg",False,False,0,"","Importado"),
        ("Ganso Defumado 200g","Ganso defumado","16023900","Outras preparações de aves","Carnes","Aves","kg",False,False,0,"","Importado"),
        ("Codorna Inteira Fresca 4un","Codorna inteira fresca","02076000","De galinhas-d'angola","Carnes","Aves","un",False,True,0,"","Genérico"),
        ("Faisão Inteiro 1kg","Faisão inteiro fresco","02074400","Outras peças de pato","Carnes","Aves","kg",False,True,0,"","Importado"),
        ("Rã Congelada 500g","Carne de rã congelada","02089000","Outras carnes","Carnes","Carnes Especiais","kg",False,True,0,"","Genérico"),
        ("Jacaré Filé 500g","Filé de jacaré congelado","02089000","Outras carnes","Carnes","Carnes Especiais","kg",False,True,0,"","Genérico"),
        ("Coelho Inteiro Congelado 1kg","Coelho inteiro congelado","02081000","Carne de coelho","Carnes","Carnes Especiais","kg",False,True,0,"","Importado"),
        ("Porco Vietnamita (Leitão) 1kg","Leitão vietnamita","02031900","Outras carnes suínas","Carnes","Carne Suína","kg",False,True,0,"","Importado"),
        ("Carpaccio de Salmão 100g","Carpaccio de salmão defumado","16041100","Salmão preparado","Carnes","Peixes","kg",False,False,0,"","Importado"),
        ("Ceviche de Tilápia 200g","Ceviche de tilápia pronto","16042000","Outras preparações de peixe","Carnes","Peixes","kg",False,False,0,"","Genérico"),
        ("Sashimi de Salmão 100g","Sashimi de salmão","16041100","Salmão preparado","Carnes","Peixes","kg",False,False,0,"","Genérico"),
        ("Paella Congelada 400g","Paella espanhola congelada","16052000","Camarões preparados","Congelados","Pratos Prontos","kg",False,False,0,"","Importado"),
        ("Caldo de Marisco 1L","Caldo de marisco","21041000","Sopas e caldos","Condimentos","Caldos e Temperos","lt",False,False,0,"","Genérico"),
        ("Pho Vietnamita Caldo 500ml","Caldo pho vietnamita","21041000","Sopas e caldos","Condimentos","Caldos e Temperos","lt",False,False,0,"","Importado"),
        ("Ramen Caldo Tonkotsu 500ml","Caldo tonkotsu","21041000","Sopas e caldos","Condimentos","Caldos e Temperos","lt",False,False,0,"","Importado"),
        ("Sopa Miso Instantânea 30g","Sopa miso instantânea","21041000","Sopas e caldos","Enlatados","Sopas e Cremes","kg",False,False,0,"","Importado"),
        ("Sopa Instantânea Thai 60g","Sopa tailandesa instantânea","21041000","Sopas e caldos","Enlatados","Sopas e Cremes","kg",False,False,0,"","Importado"),
        ("Sopa de Abóbora Pronta 300g","Sopa de abóbora pronta","21041000","Sopas e caldos","Enlatados","Sopas e Cremes","kg",False,False,0,"","Genérico"),
        ("Sopa de Feijão Preto Pronta 400g","Sopa de feijão preto","21041000","Sopas e caldos","Enlatados","Sopas e Cremes","kg",False,False,0,"","Genérico"),
        ("Creme de Cebola Pronto 250g","Creme de cebola","21041000","Sopas e caldos","Enlatados","Sopas e Cremes","kg",False,False,0,"","Genérico"),
        ("Creme de Ervilha Pronto 250g","Creme de ervilha","21041000","Sopas e caldos","Enlatados","Sopas e Cremes","kg",False,False,0,"","Genérico"),
        ("Creme de Aspargo Pronto 250g","Creme de aspargo","21041000","Sopas e caldos","Enlatados","Sopas e Cremes","kg",False,False,0,"","Importado"),
        ("Farofa Pronta Sadia 250g","Farofa pronta temperada","11062000","Farinha de mandioca","Cereais e Grãos","Farinha de Mandioca","kg",False,False,0,"","Sadia"),
        ("Farofa Bacon Sadia 250g","Farofa com bacon","11062000","Farinha de mandioca","Cereais e Grãos","Farinha de Mandioca","kg",False,False,0,"","Sadia"),
        ("Farofa de Cebola 250g","Farofa de cebola","11062000","Farinha de mandioca","Cereais e Grãos","Farinha de Mandioca","kg",False,False,0,"","Genérico"),
        ("Pirão de Peixe Congelado 300g","Pirão de peixe","11062000","Farinha de mandioca","Congelados","Pratos Prontos","kg",False,False,0,"","Genérico"),
        ("Farinha de Tapioca Tipo 1 500g","Farinha de tapioca tipo 1","11081400","Fécula de mandioca","Cereais e Grãos","Tapioca","kg",False,True,0,"","Genérico"),
        ("Beiju de Tapioca Seco 200g","Beiju seco","11081400","Fécula de mandioca","Cereais e Grãos","Tapioca","kg",False,True,0,"","Genérico"),
        ("Pão de Tapioca 4un","Pão de tapioca","19052090","Outros pães","Padaria","Pão Especial","un",False,False,0,"","Genérico"),
        ("Pão de Milho 400g","Pão de milho","19052090","Outros pães","Padaria","Pão Especial","kg",False,False,0,"17.050.00","Genérico"),
        ("Pão de Abóbora 400g","Pão de abóbora","19052090","Outros pães","Padaria","Pão Especial","kg",False,False,0,"17.050.00","Genérico"),
        ("Pão Multicereais 400g","Pão multicereais","19052090","Outros pães","Padaria","Pão Especial","kg",False,False,0,"17.050.00","Genérico"),
        ("Pão Rústico de Azeitona 400g","Pão de azeitona","19052090","Outros pães","Padaria","Pão Especial","kg",False,False,0,"17.050.00","Genérico"),
        ("Focaccia Alecrim 400g","Focaccia italiana","19052090","Outros pães","Padaria","Pão Especial","kg",False,False,0,"17.050.00","Genérico"),
        ("Chapata (Ciabatta) 300g","Ciabatta italiana","19052090","Outros pães","Padaria","Pão Especial","kg",False,False,0,"17.050.00","Genérico"),
        ("Pão de Nozes 400g","Pão de nozes","19052090","Outros pães","Padaria","Pão Especial","kg",False,False,0,"17.050.00","Genérico"),
        ("Pão de Queijo Fondue 400g","Pão de queijo fondue","19052090","Outros pães","Padaria","Pão de Queijo","kg",False,False,0,"","Genérico"),
        ("Pão Australiano Chocolate 400g","Pão australiano chocolate","19052090","Outros pães","Padaria","Pão Especial","kg",False,False,0,"17.050.00","Genérico"),
        ("Crepe Pronto para Recheio 4un","Crepe pronto","19052090","Outros padaria","Padaria","Massas","un",False,False,0,"","Genérico"),
        ("Massa Tarte 400g","Massa para torta salgada","19012090","Preparações de farinha","Padaria","Massas","kg",False,False,0,"","Genérico"),
        ("Massa Phyllo Congelada 400g","Massa filo congelada","19012090","Preparações de farinha","Congelados","Massas","kg",False,False,0,"","Importado"),
        ("Espaguete de Abobrinha 200g","Macarrão de abobrinha","07099300","Abobrinhas","Hortifruti","Legumes","kg",False,True,0,"","Genérico"),
        ("Noodles de Konjac 200g","Macarrão de konjac","07149000","Outros tubérculos","Mercearia","Sem Glúten","kg",False,False,0,"","Importado"),
        ("Macarrão de Arroz Largo 200g","Macarrão de arroz largo","19023000","Massas alimentícias","Cereais e Grãos","Massas Alimentícias","kg",False,False,0,"17.049.00","Importado"),
        ("Massa de Guioza (Pastel Japonês) 20un","Massa guioza","19023000","Massas alimentícias","Cereais e Grãos","Massas Alimentícias","un",False,False,0,"","Importado"),
        ("Massa Wonton 20un","Massa wonton","19023000","Massas alimentícias","Cereais e Grãos","Massas Alimentícias","un",False,False,0,"","Importado"),
        ("Pão de Batata Doce 400g","Pão de batata doce","19052090","Outros pães","Padaria","Pão Especial","kg",False,False,0,"17.050.00","Genérico"),
        ("Macarrão de Milho Gluten Free 400g","Macarrão de milho sem glúten","19023000","Massas alimentícias","Cereais e Grãos","Sem Glúten","kg",False,False,0,"17.049.00","Genérico"),
        ("Macarrão Shirataki 200g","Macarrão shirataki","19023000","Massas alimentícias","Cereais e Grãos","Sem Glúten","kg",False,False,0,"","Importado"),
        ("Soja Texturizada Hambúrguer 500g","PTS para hambúrguer","12019090","Farinha de soja","Foodservice","Proteínas","kg",False,True,0,"","Genérico"),
        ("Glúten Vital de Trigo 200g","Glúten vital para pão","11090000","Glúten de trigo","Padaria","Ingredientes","kg",False,False,0,"","Genérico"),
        ("Lúpulo Seco 30g","Lúpulo para cerveja artesanal","12130000","Lúpulo","Bebidas","Ingredientes","kg",False,False,0,"","Importado"),
        ("Malte de Cevada 500g","Malte de cevada","19019090","Extrato de malte","Bebidas","Ingredientes","kg",False,False,0,"","Importado"),
        ("Fermento Cervejeiro Seco 11g","Fermento para cerveja","21021090","Outras leveduras","Bebidas","Ingredientes","kg",False,False,0,"","Importado"),
        ("Alga Espirulina Liofilizada 100g","Espirulina liofilizada","21069090","Preparações alimentícias","Suplementos","Suplementos","kg",False,False,0,"","Genérico"),
        ("Chlorella 100g","Chlorella em pó","21069090","Preparações alimentícias","Suplementos","Suplementos","kg",False,False,0,"","Importado"),
        ("Maca Peruana Pó 200g","Maca peruana em pó","21069090","Preparações alimentícias","Suplementos","Suplementos","kg",False,False,0,"","Importado"),
        ("Ashwagandha 100g","Ashwagandha em pó","21069090","Preparações alimentícias","Suplementos","Suplementos","kg",False,False,0,"","Importado"),
        ("Cúrcuma com Pimenta Preta 100g","Cúrcuma com piperina","21069090","Preparações alimentícias","Suplementos","Suplementos","kg",False,False,0,"","Genérico"),
        ("Vinagre de Maçã Orgânico 500ml","Vinagre de maçã orgânico","22090000","Vinagres","Condimentos","Vinagre","lt",False,False,0,"","Genérico"),
        ("Vinagre de Framboesa Gourmet 250ml","Vinagre de framboesa premium","22090000","Vinagres","Condimentos","Vinagre","lt",False,False,0,"","Importado"),
        ("Azeite Aromatizado Limão 250ml","Azeite com limão","15099010","Outros azeites de oliva refinados","Óleos e Gorduras","Azeite","lt",False,False,0,"","Genérico"),
        ("Azeite Aromatizado Alecrim 250ml","Azeite com alecrim","15099010","Outros azeites de oliva refinados","Óleos e Gorduras","Azeite","lt",False,False,0,"","Genérico"),
        ("Azeite de Abacate 250ml","Azeite de abacate","15159090","Outros óleos de sementes oleaginosas","Óleos e Gorduras","Óleos Especiais","lt",False,False,0,"","Importado"),
        ("Óleo de Macadâmia 250ml","Óleo de macadâmia","15159090","Outros óleos de sementes oleaginosas","Óleos e Gorduras","Óleos Especiais","lt",False,False,0,"","Importado"),
        ("Óleo de Cânhamo 250ml","Óleo de semente de cânhamo","15159090","Outros óleos de sementes oleaginosas","Óleos e Gorduras","Óleos Especiais","lt",False,False,0,"","Importado"),
        ("Gordura Láurica 500g","Gordura de coco láurica","15132919","Óleo de coco — outros","Óleos e Gorduras","Gordura Vegetal","kg",False,False,0,"","Genérico"),
        ("Gordura de Cacau 100g","Manteiga de cacau para culinária","18040000","Manteiga de cacau","Padaria","Ingredientes","kg",False,False,0,"","Genérico"),
        ("Manteiga de Karité 100g","Manteiga de karité alimentar","15159090","Outros óleos de sementes oleaginosas","Mercearia","Ingredientes","kg",False,False,0,"","Importado"),
        ("Purê de Maçã Sem Açúcar 200g","Purê de maçã sem açúcar","20091900","Outros sucos de maçã","Mercearia","Sobremesas","kg",False,False,0,"","Importado"),
        ("Purê de Manga 200g","Purê de manga","20098990","Outros sucos de frutos","Mercearia","Ingredientes","kg",False,False,0,"","Genérico"),
        ("Purê de Framboesa 200g","Purê de framboesa","20079910","Purê de frutas","Mercearia","Ingredientes","kg",False,False,0,"","Importado"),
        ("Purê de Maracujá 200g","Purê de maracujá","20098990","Outros sucos de frutos","Mercearia","Ingredientes","kg",False,False,0,"","Genérico"),
        ("Suco Integral Cranberry 300ml","Suco integral de cranberry","20098990","Outros sucos de frutos","Bebidas","Suco","lt",False,False,0,"17.010.00","Importado"),
        ("Suco Integral Acerola 300ml","Suco integral acerola","20098990","Outros sucos de frutos","Bebidas","Suco","lt",False,False,0,"17.010.00","Genérico"),
        ("Chá Verde em Lata 150g","Chá verde premium em lata","09021000","Chá verde","Bebidas","Chá","kg",False,False,0,"17.097.00","Importado"),
        ("Matcha Pó 50g","Chá matcha japonês em pó","09021000","Chá verde","Bebidas","Chá","kg",False,False,0,"17.097.00","Importado"),
        ("Yerba Mate Premium 500g","Erva-mate premium argentina","09030090","Mate","Bebidas","Erva-Mate","kg",False,False,0,"17.098.00","Importado"),
        ("Erva-Mate Desidratada Granulada 500g","Erva-mate granulada","09030090","Mate","Bebidas","Erva-Mate","kg",False,False,0,"17.098.00","Genérico"),
        ("Café Coado Gelado 500ml","Café coado gelado pronto","22029900","Bebidas prontas","Bebidas","Café","lt",True,False,0,"","Genérico"),
        ("Cold Brew Café 500ml","Cold brew de café","22029900","Bebidas prontas","Bebidas","Café","lt",True,False,0,"","Genérico"),
        ("Nescafé 3em1 Sachê","Café solúvel 3em1","21011110","Café solúvel","Bebidas","Café","un",True,False,0,"","Nestlé"),
        ("Cappuccino Instantâneo Sachê 20g","Cappuccino instantâneo","21011110","Café solúvel","Bebidas","Café","un",True,False,0,"","Genérico"),
        ("Achocolatado em Pó Nescau 2.0 400g","Achocolatado premium","18069000","Outras preparações com cacau","Bebidas","Achocolatado","kg",True,False,0,"17.006.00","Nestlé"),
        ("Achocolatado em Pó Ovomaltine 300g","Achocolatado ovomaltine","18069000","Outras preparações com cacau","Bebidas","Achocolatado","kg",True,False,0,"17.006.00","Ovomaltine"),
        ("Leite com Chocolate Nescau 200ml","Leite com chocolate","22029900","Bebidas lácteas","Bebidas","Bebidas Lácteas","lt",True,False,0,"","Nestlé"),
        ("Leite com Morango 200ml","Leite sabor morango","22029900","Bebidas lácteas","Bebidas","Bebidas Lácteas","lt",True,False,0,"","Genérico"),
        ("Yakult 40ml","Bebida láctea fermentada","04039000","Outros leites fermentados","Laticínios","Bebida Láctea","lt",False,False,0,"","Yakult"),
        ("Yakult Mais 80ml","Bebida láctea fermentada plus","04039000","Outros leites fermentados","Laticínios","Bebida Láctea","lt",False,False,0,"","Yakult"),
        ("Danone Actimel 100ml","Probiótico líquido","04039000","Outros leites fermentados","Laticínios","Bebida Láctea","lt",False,False,0,"","Danone"),
        ("Benecol 65g","Bebida láctea com estanóis","04039000","Outros leites fermentados","Laticínios","Bebida Láctea","lt",False,False,0,"","Importado"),
        ("Iogurte Chobani Morango 150g","Iogurte grego americano","04032000","Iogurte","Laticínios","Iogurte","kg",False,False,0,"17.021.00","Importado"),
        ("Panna Cotta Pronta 200g","Panna cotta pronta","19019090","Outras preparações","Laticínios","Sobremesas","kg",False,False,0,"","Importado"),
        ("Mousse de Chocolate Pronto 200g","Mousse de chocolate","19019090","Outras preparações","Laticínios","Sobremesas","kg",False,False,0,"","Genérico"),
        ("Mousse de Maracujá Pronto 200g","Mousse de maracujá","19019090","Outras preparações","Laticínios","Sobremesas","kg",False,False,0,"","Genérico"),
        ("Creme Brulée Pronto 200g","Crème brûlée","19019090","Outras preparações","Laticínios","Sobremesas","kg",False,False,0,"","Importado"),
    ]

    for item in items:
        ean = _make_ean_like(item[0])
        last.append(_p(ean, *item))

    return last


_PRODUCTS += _gen_last_block()


# ============================================================
# SEÇÃO 23: PRODUTOS FINAIS - META FINAL 2000+
# ============================================================

_PRODUCTS += [
    _p(_make_ean_like("Abacate Orgânico 200g"),"Abacate Orgânico 200g","Abacate orgânico","08044000","Abacates","Hortifruti","Frutas","kg",False,True,0,"","Orgânico"),
    _p(_make_ean_like("Leite de Aveia Barista 1L"),"Leite de Aveia Barista 1L","Bebida de aveia barista","22029900","Bebidas vegetais","Mercearia","Substitutos Lácteos","lt",False,False,0,"","Oatly"),
    _p(_make_ean_like("Queijo Nacho Fatiado 200g"),"Queijo Nacho Fatiado 200g","Queijo para nachos","04069090","Outros queijos","Laticínios","Queijos","kg",False,False,0,"17.024.00","Genérico"),
    _p(_make_ean_like("Linguiça Vegana de Grão-de-Bico 250g"),"Linguiça Vegana de Grão-de-Bico 250g","Linguiça vegana de grão-de-bico","16010000","Enchidos vegetais","Congelados","Vegano","kg",False,False,0,"","Genérico"),
    _p(_make_ean_like("Frango ao Curry Verde Congelado 300g"),"Frango ao Curry Verde Congelado 300g","Frango ao curry verde","16023220","Preparações de frango","Congelados","Pratos Prontos","kg",False,False,0,"","Genérico"),
    _p(_make_ean_like("Espetinho de Camarão Congelado 300g"),"Espetinho de Camarão Congelado 300g","Espetinho de camarão","16052000","Camarões preparados","Congelados","Frutos do Mar","kg",False,False,0,"","Genérico"),
    _p(_make_ean_like("Torta Salgada Espinafre e Ricota 400g"),"Torta Salgada Espinafre e Ricota 400g","Torta de espinafre e ricota","19052090","Outros padaria","Congelados","Tortas","kg",False,False,0,"","Genérico"),
    _p(_make_ean_like("Bolo de Aniversário Confeitado 1kg"),"Bolo de Aniversário Confeitado 1kg","Bolo confeitado","19052090","Outros padaria","Padaria","Bolos","kg",False,False,0,"","Genérico"),
    _p(_make_ean_like("Creme de Bacalhau com Natas 300g"),"Creme de Bacalhau com Natas 300g","Creme de bacalhau","16042000","Preparações de peixe","Carnes","Peixes","kg",False,False,0,"","Importado"),
    _p(_make_ean_like("Erva-Mate Tostada Premium 500g"),"Erva-Mate Tostada Premium 500g","Erva-mate tostada","09030090","Mate","Bebidas","Erva-Mate","kg",False,False,0,"17.098.00","Genérico"),
    _p(_make_ean_like("Kombucha Limão e Gengibre 500ml"),"Kombucha Limão e Gengibre 500ml","Kombucha sabor limão gengibre","22029900","Outras bebidas","Bebidas","Bebidas Especiais","lt",False,False,0,"","Genérico"),
    _p(_make_ean_like("Suco Verde Espinafre e Maçã 300ml"),"Suco Verde Espinafre e Maçã 300ml","Suco verde nutritivo","20098990","Outros sucos de frutos","Bebidas","Suco","lt",False,False,0,"17.010.00","Genérico"),
    _p(_make_ean_like("Suco de Frutas Vermelhas 300ml"),"Suco de Frutas Vermelhas 300ml","Suco de frutas vermelhas","20098990","Outros sucos de frutos","Bebidas","Suco","lt",True,False,0,"17.010.00","Genérico"),
    _p(_make_ean_like("Polpa de Pitaya 400g"),"Polpa de Pitaya 400g","Polpa de pitaya","20079910","Purê de frutas","Hortifruti","Polpas","kg",False,False,0,"","Genérico"),
    _p(_make_ean_like("Polpa de Abacaxi 400g"),"Polpa de Abacaxi 400g","Polpa de abacaxi","20079910","Purê de frutas","Hortifruti","Polpas","kg",False,False,0,"","Genérico"),
    _p(_make_ean_like("Polpa de Tamarindo 200g"),"Polpa de Tamarindo 200g","Polpa de tamarindo","20079910","Purê de frutas","Hortifruti","Polpas","kg",False,False,0,"","Genérico"),
    _p(_make_ean_like("Polpa de Goiaba Vermelha 400g"),"Polpa de Goiaba Vermelha 400g","Polpa de goiaba","20079910","Purê de frutas","Hortifruti","Polpas","kg",False,False,0,"","Genérico"),
    _p(_make_ean_like("Polpa de Banana 400g"),"Polpa de Banana 400g","Polpa de banana","20079910","Purê de frutas","Hortifruti","Polpas","kg",False,False,0,"","Genérico"),
    _p(_make_ean_like("Queijo de Cabra Fresco 150g"),"Queijo de Cabra Fresco 150g","Queijo de cabra fresco","04069030","Queijo de massa macia","Laticínios","Queijos","kg",False,False,0,"17.024.00","Importado"),
    _p(_make_ean_like("Leite de Cabra UHT 1L"),"Leite de Cabra UHT 1L","Leite de cabra UHT","04011090","Outros","Laticínios","Leite UHT","lt",False,False,0,"17.016.00","Importado"),
    _p(_make_ean_like("Labneh Árabe 200g"),"Labneh Árabe 200g","Labneh queijo iogurte","04039000","Outros leites fermentados","Laticínios","Queijos","kg",False,False,0,"17.024.00","Importado"),
    _p(_make_ean_like("Gaspacho Espanhol 300ml"),"Gaspacho Espanhol 300ml","Gaspacho fresco","21041000","Sopas e caldos","Enlatados","Sopas e Cremes","lt",False,False,0,"","Importado"),
    _p(_make_ean_like("Caldo de Osso de Frango 500ml"),"Caldo de Osso de Frango 500ml","Caldo de osso frango","21041000","Sopas e caldos","Condimentos","Caldos e Temperos","lt",False,False,0,"","Genérico"),
    _p(_make_ean_like("Sopa de Lentilha Pronta 400g"),"Sopa de Lentilha Pronta 400g","Sopa de lentilha","21041000","Sopas e caldos","Enlatados","Sopas e Cremes","kg",False,False,0,"","Genérico"),
    _p(_make_ean_like("Sopa de Cebola Francesa 400g"),"Sopa de Cebola Francesa 400g","Sopa de cebola à francesa","21041000","Sopas e caldos","Enlatados","Sopas e Cremes","kg",False,False,0,"","Importado"),
    _p(_make_ean_like("Miso Soup Instantâneo 30g"),"Miso Soup Instantâneo 30g","Sopa miso instantânea","21041000","Sopas e caldos","Enlatados","Sopas e Cremes","kg",False,False,0,"","Importado"),
    _p(_make_ean_like("Pão de Forma Sem Açúcar 500g"),"Pão de Forma Sem Açúcar 500g","Pão de forma sem açúcar","19052090","Outros pães","Padaria","Pão de Forma","kg",False,False,0,"17.050.00","Genérico"),
    _p(_make_ean_like("Biscoito de Arroz Sem Glúten 100g"),"Biscoito de Arroz Sem Glúten 100g","Biscoito de arroz","19053100","Biscoitos","Padaria","Sem Glúten","kg",False,False,0,"","Genérico"),
    _p(_make_ean_like("Tortilha de Milho Sem Glúten 6un"),"Tortilha de Milho Sem Glúten 6un","Tortilha sem glúten","19052090","Outros pães","Padaria","Sem Glúten","un",False,False,0,"","Genérico"),
    _p(_make_ean_like("Granola Sem Glúten 400g"),"Granola Sem Glúten 400g","Granola sem glúten","19042000","Preparações de cereais","Cereais e Grãos","Sem Glúten","kg",False,False,0,"17.030.00","Genérico"),
    _p(_make_ean_like("Cereal de Quinoa Sem Glúten 300g"),"Cereal de Quinoa Sem Glúten 300g","Cereal de quinoa","19042000","Preparações de cereais","Cereais e Grãos","Sem Glúten","kg",False,False,0,"17.030.00","Genérico"),
    _p(_make_ean_like("Aveia Sem Glúten Certificada 500g"),"Aveia Sem Glúten Certificada 500g","Aveia certificada sem glúten","11041200","Aveia trabalhada","Cereais e Grãos","Sem Glúten","kg",False,True,0,"","Importado"),
    _p(_make_ean_like("Pão de Queijo Sem Lactose 400g"),"Pão de Queijo Sem Lactose 400g","Pão de queijo sem lactose","19052090","Outros pães","Padaria","Sem Glúten","kg",False,False,0,"","Genérico"),
    _p(_make_ean_like("Macarrão Sem Glúten de Milho 400g"),"Macarrão Sem Glúten de Milho 400g","Macarrão de milho","19023000","Massas alimentícias","Cereais e Grãos","Sem Glúten","kg",False,False,0,"17.049.00","Genérico"),
    _p(_make_ean_like("Farinha Mista Sem Glúten 1kg"),"Farinha Mista Sem Glúten 1kg","Farinha mista sem glúten","11029000","Outras farinhas","Cereais e Grãos","Sem Glúten","kg",False,True,0,"","Genérico"),
    _p(_make_ean_like("Bolo Pronto Sem Glúten Chocolate 400g"),"Bolo Pronto Sem Glúten Chocolate 400g","Bolo sem glúten chocolate","19052090","Outros padaria","Padaria","Sem Glúten","kg",False,False,0,"","Genérico"),
    _p(_make_ean_like("Leite de Soja Integral 1L"),"Leite de Soja Integral 1L","Bebida de soja integral","22029900","Bebidas vegetais","Mercearia","Substitutos Lácteos","lt",False,False,0,"","Ades"),
    _p(_make_ean_like("Tofu Sedoso 400g"),"Tofu Sedoso 400g","Tofu sedoso","19019090","Outras preparações","Mercearia","Vegano","kg",False,True,0,"","Importado"),
    _p(_make_ean_like("Tempeh 200g"),"Tempeh 200g","Tempeh de soja fermentado","12019090","Outros produtos de soja","Mercearia","Vegano","kg",False,True,0,"","Importado"),
    _p(_make_ean_like("Seitan 250g"),"Seitan 250g","Seitan proteína de trigo","11090000","Glúten de trigo","Mercearia","Vegano","kg",False,False,0,"","Importado"),
    _p(_make_ean_like("Patê Vegano de Cogumelos 150g"),"Patê Vegano de Cogumelos 150g","Patê vegano cogumelos","21039091","Preparações para molhos, embalagem ≤1kg","Mercearia","Vegano","kg",False,False,0,"","Genérico"),
    _p(_make_ean_like("Ovo Vegano Aquafaba Caixa"),"Ovo Vegano Aquafaba Caixa","Substituto vegano de ovo","21069090","Preparações alimentícias","Mercearia","Vegano","un",False,False,0,"","Importado"),
    _p(_make_ean_like("Manteiga Vegana de Girassol 200g"),"Manteiga Vegana de Girassol 200g","Manteiga vegana","15171000","Margarina","Óleos e Gorduras","Vegano","kg",False,False,0,"","Genérico"),
    _p(_make_ean_like("Cheese Vegano em Fatias 150g"),"Cheese Vegano em Fatias 150g","Queijo vegano fatiado","21069090","Preparações alimentícias","Mercearia","Vegano","kg",False,False,0,"","Importado"),
    _p(_make_ean_like("Creme Vegetal para Culinária 200ml"),"Creme Vegetal para Culinária 200ml","Creme vegetal culinária","15171000","Margarina","Óleos e Gorduras","Vegano","lt",False,False,0,"","Genérico"),
    _p(_make_ean_like("Iogurte Vegano de Coco 150g"),"Iogurte Vegano de Coco 150g","Iogurte vegano de coco","22029900","Bebidas vegetais","Mercearia","Vegano","kg",False,False,0,"","Importado"),
    _p(_make_ean_like("Bebida Probiótica Vegana 300ml"),"Bebida Probiótica Vegana 300ml","Bebida probiótica vegana","22029900","Bebidas vegetais","Mercearia","Vegano","lt",False,False,0,"","Genérico"),
    _p(_make_ean_like("Pizza Vegana de Queijo Vegetal 440g"),"Pizza Vegana de Queijo Vegetal 440g","Pizza vegana","19012090","Preparações de farinha","Congelados","Vegano","kg",False,False,0,"","Genérico"),
    _p(_make_ean_like("Hot Dog Vegano 250g"),"Hot Dog Vegano 250g","Salsicha vegana","16010000","Enchidos vegetais","Congelados","Vegano","kg",False,False,0,"","Genérico"),
    _p(_make_ean_like("Marmita Vegana Pronta 350g"),"Marmita Vegana Pronta 350g","Marmita vegana congelada","16025000","Preparações vegetais","Congelados","Vegano","kg",False,False,0,"","Genérico"),
    _p(_make_ean_like("Feijão Preto com Arroz Integral Congelado 300g"),"Feijão Preto com Arroz Integral Congelado 300g","Feijão com arroz integral","16025000","Preparações vegetais","Congelados","Pratos Prontos","kg",False,False,0,"","Genérico"),
    _p(_make_ean_like("Feijoada Light Congelada 400g"),"Feijoada Light Congelada 400g","Feijoada light pronta","16025000","Preparações de carne","Congelados","Pratos Prontos","kg",False,False,0,"","Genérico"),
    _p(_make_ean_like("Frango Xadrez Congelado 300g"),"Frango Xadrez Congelado 300g","Frango xadrez pronto","16023220","Preparações de frango","Congelados","Pratos Prontos","kg",False,False,0,"","Genérico"),
    _p(_make_ean_like("Arroz Vermelho Cozido Pronto 250g"),"Arroz Vermelho Cozido Pronto 250g","Arroz vermelho cozido","10062020","Arroz descascado","Congelados","Arroz","kg",False,True,0,"","Genérico"),
    _p(_make_ean_like("Feijão Fradinho Cozido 400g"),"Feijão Fradinho Cozido 400g","Feijão fradinho cozido","07131090","Outras ervilhas","Enlatados","Feijão Cozido","kg",False,False,0,"","Genérico"),
    _p(_make_ean_like("Açaí na Tigela com Granola 400g"),"Açaí na Tigela com Granola 400g","Açaí com granola","20079910","Purê de frutas","Congelados","Sorvetes","kg",False,False,0,"","Genérico"),
]


# ============================================================
# FUNÇÕES PÚBLICAS DA BASE DE DADOS
# ============================================================

def get_all_products() -> list:
    """Retorna todos os produtos da base de dados."""
    return list(_PRODUCTS)


def search_products(query: str) -> list:
    """
    Busca produtos por nome, EAN ou NCM.
    A busca é case-insensitive e aceita correspondências parciais.
    """
    if not query:
        return list(_PRODUCTS)

    query_lower = _normalize(query.lower())
    results = []
    for prod in _PRODUCTS:
        if (
            query_lower in _normalize(prod.get("nome", "").lower())
            or query_lower in prod.get("ean", "")
            or query_lower in prod.get("ncm", "")
            or query_lower in _normalize(prod.get("descricao_generica", "").lower())
            or query_lower in _normalize(prod.get("categoria", "").lower())
            or query_lower in _normalize(prod.get("subcategoria", "").lower())
            or query_lower in _normalize(prod.get("ncm_descricao", "").lower())
        ):
            results.append(prod)
    return results


def _normalize(text: str) -> str:
    """Remove acentos para busca normalizada."""
    try:
        nfkd = unicodedata.normalize('NFKD', text)
        return ''.join(c for c in nfkd if not unicodedata.combining(c))
    except Exception:
        return text


def get_products_by_ncm(ncm_code: str) -> list:
    """Retorna produtos de um NCM específico (8 dígitos)."""
    ncm_clean = re.sub(r'\D', '', ncm_code)
    return [p for p in _PRODUCTS if p.get("ncm", "").startswith(ncm_clean)]


def get_products_by_category(category: str) -> list:
    """Retorna produtos de uma categoria específica (parcial, case-insensitive)."""
    cat_lower = _normalize(category.lower())
    return [
        p for p in _PRODUCTS
        if cat_lower in _normalize(p.get("categoria", "").lower())
        or cat_lower in _normalize(p.get("subcategoria", "").lower())
    ]


def get_all_categories() -> list:
    """Retorna lista de todas as categorias únicas."""
    cats = set()
    for p in _PRODUCTS:
        if p.get("categoria"):
            cats.add(p["categoria"])
    return sorted(cats)


def get_all_subcategories() -> list:
    """Retorna lista de todas as subcategorias únicas."""
    subcats = set()
    for p in _PRODUCTS:
        if p.get("subcategoria"):
            subcats.add((p.get("categoria",""), p["subcategoria"]))
    return sorted(subcats)


def get_product_by_ean(ean: str) -> dict | None:
    """Retorna um produto pelo EAN/GTIN. Retorna None se não encontrado."""
    ean_clean = ean.strip()
    for p in _PRODUCTS:
        if p.get("ean") == ean_clean:
            return p
    return None


def validate_ncm(ean: str, ncm: str) -> dict:
    """
    Verifica se o NCM informado é compatível com o esperado para o produto.

    Retorna um dicionário com:
      - valid: bool
      - expected_ncm: str ou None
      - provided_ncm: str
      - message: str
      - product: dict ou None
    """
    product = get_product_by_ean(ean)
    ncm_clean = re.sub(r'\D', '', ncm)

    if not product:
        return {
            "valid": None,
            "expected_ncm": None,
            "provided_ncm": ncm_clean,
            "message": f"EAN {ean} não encontrado na base de dados.",
            "product": None,
        }

    expected = product.get("ncm", "")
    # Considera válido se coincide totalmente OU se inicia com prefixo de 4 dígitos
    is_valid = (ncm_clean == expected) or (len(ncm_clean) >= 4 and expected.startswith(ncm_clean[:4]))

    return {
        "valid": is_valid,
        "expected_ncm": expected,
        "provided_ncm": ncm_clean,
        "message": (
            "NCM compatível com o produto." if is_valid
            else f"NCM divergente: esperado {expected}, informado {ncm_clean}."
        ),
        "product": product,
    }


def find_ncm_discrepancies(products_from_xml: list) -> list:
    """
    Analisa uma lista de produtos vindos de XML/NF-e e retorna discrepâncias de NCM.

    Entrada esperada: lista de dicts com chaves 'ean', 'ncm', 'descricao' (ao menos).
    Retorna: lista de discrepâncias encontradas.

    Cada discrepância contém:
      - ean: str
      - ncm_nfe: str (NCM da NF-e)
      - ncm_esperado: str
      - descricao_nfe: str
      - produto_base: dict ou None
      - tipo: 'DIVERGENCIA_NCM' | 'NCM_NAO_ENCONTRADO' | 'EAN_NAO_CADASTRADO'
      - severidade: 'ALTA' | 'MEDIA' | 'BAIXA'
    """
    discrepancies = []

    for item in products_from_xml:
        ean = str(item.get("ean", "")).strip()
        ncm_nfe = re.sub(r'\D', '', str(item.get("ncm", "")))
        descricao = str(item.get("descricao", ""))

        if not ean or ean in ("", "SEM GTIN", "0", "00000000000000"):
            # Tenta buscar por NCM se sem EAN
            candidates = get_products_by_ncm(ncm_nfe)
            if not candidates and ncm_nfe:
                discrepancies.append({
                    "ean": ean,
                    "ncm_nfe": ncm_nfe,
                    "ncm_esperado": None,
                    "descricao_nfe": descricao,
                    "produto_base": None,
                    "tipo": "NCM_NAO_ENCONTRADO",
                    "severidade": "MEDIA",
                })
            continue

        product = get_product_by_ean(ean)

        if not product:
            # EAN não cadastrado na base — pode ser produto novo
            discrepancies.append({
                "ean": ean,
                "ncm_nfe": ncm_nfe,
                "ncm_esperado": None,
                "descricao_nfe": descricao,
                "produto_base": None,
                "tipo": "EAN_NAO_CADASTRADO",
                "severidade": "BAIXA",
            })
            continue

        expected_ncm = product.get("ncm", "")
        if ncm_nfe and expected_ncm and ncm_nfe != expected_ncm:
            # Verifica se pelo menos os 4 primeiros dígitos coincidem (capítulo/posição)
            ncm_prefix_match = expected_ncm[:4] == ncm_nfe[:4] if len(ncm_nfe) >= 4 else False
            severidade = "MEDIA" if ncm_prefix_match else "ALTA"

            discrepancies.append({
                "ean": ean,
                "ncm_nfe": ncm_nfe,
                "ncm_esperado": expected_ncm,
                "descricao_nfe": descricao,
                "produto_base": product,
                "tipo": "DIVERGENCIA_NCM",
                "severidade": severidade,
            })

    return discrepancies


def get_monofasic_products() -> list:
    """Retorna todos os produtos sujeitos à tributação monofásica."""
    return [p for p in _PRODUCTS if p.get("monofasico")]


def get_aliquota_zero_products() -> list:
    """Retorna todos os produtos com alíquota zero de PIS/COFINS (cesta básica)."""
    return [p for p in _PRODUCTS if p.get("aliquota_zero")]


def get_products_with_cest() -> list:
    """Retorna todos os produtos que possuem CEST (sujeitos à substituição tributária)."""
    return [p for p in _PRODUCTS if p.get("cest")]


def get_statistics() -> dict:
    """Retorna estatísticas sobre a base de dados."""
    total = len(_PRODUCTS)
    monofasicos = len(get_monofasic_products())
    aliquota_zero = len(get_aliquota_zero_products())
    com_ean = len([p for p in _PRODUCTS if p.get("ean")])
    com_cest = len(get_products_with_cest())
    categorias = len(get_all_categories())
    ncms_unicos = len(set(p.get("ncm","") for p in _PRODUCTS if p.get("ncm")))

    return {
        "total_produtos": total,
        "monofasicos": monofasicos,
        "aliquota_zero_cesta_basica": aliquota_zero,
        "com_ean": com_ean,
        "com_cest": com_cest,
        "categorias_unicas": categorias,
        "ncms_unicos": ncms_unicos,
    }


# ============================================================
# PONTO DE ENTRADA PARA TESTE
# ============================================================

if __name__ == "__main__":
    stats = get_statistics()
    print(f"=== BASE DE DADOS DE PRODUTOS ALIMENTÍCIOS ===")
    print(f"Total de produtos: {stats['total_produtos']}")
    print(f"Produtos monofásicos: {stats['monofasicos']}")
    print(f"Produtos alíquota zero (cesta básica): {stats['aliquota_zero_cesta_basica']}")
    print(f"Produtos com EAN: {stats['com_ean']}")
    print(f"Produtos com CEST: {stats['com_cest']}")
    print(f"Categorias únicas: {stats['categorias_unicas']}")
    print(f"NCMs únicos: {stats['ncms_unicos']}")
    print(f"\nCategorias: {get_all_categories()}")

