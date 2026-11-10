"""Pacote climatizacao_nbr16401 - Dimensionamento de Climatização (ABNT NBR 16401:2008).

Aritmética estritamente racional exata (Fraction e inteiros). Zero float.
Lofrano Tecnologia 2026.
"""

from __future__ import annotations

from climatizacao_nbr16401.calculator import calcular_climatizacao_nbr16401
from climatizacao_nbr16401.codecs import (
    codificar_resultado_json,
    decodificar_espaco_json,
    espaco_para_dict,
    parse_fracao_ou_int,
    resultado_para_dict,
)
from climatizacao_nbr16401.constants import (
    ATIVIDADES_METABOLICAS,
    BTU_POR_TR,
    CALOR_LATENTE_AR_KCAL_M3_G_KG,
    CALOR_VOLUMETRICO_AR_KCAL_M3_C,
    CAPACIDADES_COMERCIAIS_BTU,
    CIDADES_CLIMATICAS_PROJETO,
    COEFICIENTES_TRANSMISSAO_U_W_M2_K,
    FATOR_KCAL_PARA_BTU,
    FATOR_SOLAR_VIDROS,
    FATOR_W_PARA_KCAL_H,
    KCAL_POR_TR,
    RADIACAO_SOLAR_FACHADA_W_M2,
    TAXAS_RENOVACAO_AR_EXTERIOR,
    TBS_INTERNA_CONFORTO_PADRAO_C,
    UMIDADE_INTERNA_CONFORTO_PADRAO_G_KG,
)
from climatizacao_nbr16401.exporters import (
    criar_pacote_zip_deterministico,
    formatar_fracao_decimal,
    gerar_csv_elementos,
    gerar_relatorio_texto,
    sanitizar_campo_csv,
)
from climatizacao_nbr16401.models import (
    CargaEquipamentos,
    CargaIluminacao,
    CargaOcupantes,
    ElementoEnvoltoria,
    EspacoClimatizado,
    ResultadoCargaTermica,
    ResultadoElementoEnvoltoria,
)
from climatizacao_nbr16401.svg_generator import gerar_painel_svg

__version__ = "1.0.0"

__all__ = [
    "__version__",
    "ElementoEnvoltoria",
    "CargaOcupantes",
    "CargaIluminacao",
    "CargaEquipamentos",
    "EspacoClimatizado",
    "ResultadoElementoEnvoltoria",
    "ResultadoCargaTermica",
    "calcular_climatizacao_nbr16401",
    "decodificar_espaco_json",
    "codificar_resultado_json",
    "espaco_para_dict",
    "resultado_para_dict",
    "parse_fracao_ou_int",
    "gerar_relatorio_texto",
    "gerar_csv_elementos",
    "criar_pacote_zip_deterministico",
    "formatar_fracao_decimal",
    "sanitizar_campo_csv",
    "gerar_painel_svg",
    "CIDADES_CLIMATICAS_PROJETO",
    "TAXAS_RENOVACAO_AR_EXTERIOR",
    "ATIVIDADES_METABOLICAS",
    "COEFICIENTES_TRANSMISSAO_U_W_M2_K",
    "RADIACAO_SOLAR_FACHADA_W_M2",
    "FATOR_SOLAR_VIDROS",
    "CAPACIDADES_COMERCIAIS_BTU",
    "FATOR_KCAL_PARA_BTU",
    "FATOR_W_PARA_KCAL_H",
    "BTU_POR_TR",
    "KCAL_POR_TR",
    "CALOR_VOLUMETRICO_AR_KCAL_M3_C",
    "CALOR_LATENTE_AR_KCAL_M3_G_KG",
    "TBS_INTERNA_CONFORTO_PADRAO_C",
    "UMIDADE_INTERNA_CONFORTO_PADRAO_G_KG",
]
