"""Constantes e parâmetros normativos da ABNT NBR 16401:2008.

Instalações de ar-condicionado - Sistemas centrais e unitários:
- Parte 1: Projeto das instalações e condições climáticas de projeto;
- Parte 2: Parâmetros de conforto térmico;
- Parte 3: Qualidade do ar interior e taxas mínimas de renovação.

Aritmética estritamente racional exata (Fraction e inteiros). Zero float.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Final

# Conversões termodinâmicas exatas expressas em frações racionais
# 1 kcal = 3,96825 BTU => Fraction(396825, 100000) = Fraction(15873, 4000)
FATOR_KCAL_PARA_BTU: Final[Fraction] = Fraction(15873, 4000)

# 1 TR (Tonelada de Refrigeração) = 12.000 BTU/h = 3024 kcal/h = 3516,85 W
BTU_POR_TR: Final[int] = 12000
KCAL_POR_TR: Final[int] = 3024

# 1 W = 0,859845 kcal/h => Fraction(859845, 1000000) = Fraction(171969, 200000)
FATOR_W_PARA_KCAL_H: Final[Fraction] = Fraction(171969, 200000)

# Calor volumétrico do ar padrão rho * cp = 1,2 kg/m³ * 0,24 kcal/(kg.°C) = 0,288 kcal/(m³.°C)
CALOR_VOLUMETRICO_AR_KCAL_M3_C: Final[Fraction] = Fraction(288, 1000)

# Calor latente volumétrico do ar para umidade absoluta (kcal / (m³ * (g/kg)))
CALOR_LATENTE_AR_KCAL_M3_G_KG: Final[Fraction] = Fraction(70, 100)

# Condições climáticas de verão para capitais brasileiras (NBR 16401-1 Tabela A.1)
# TBS externa (°C), umidade absoluta w_ext (g vapor / kg ar seco), radiação solar de referência
CIDADES_CLIMATICAS_PROJETO: Final[dict[str, dict[str, Fraction | int | str]]] = {
    "sao_paulo": {
        "codigo": "sao_paulo",
        "nome": "São Paulo - SP",
        "tbs_externa_c": Fraction(32, 1),
        "umidade_externa_g_kg": Fraction(15, 1),
        "delta_t_diario_c": Fraction(9, 1),
    },
    "rio_de_janeiro": {
        "codigo": "rio_de_janeiro",
        "nome": "Rio de Janeiro - RJ",
        "tbs_externa_c": Fraction(35, 1),
        "umidade_externa_g_kg": Fraction(18, 1),
        "delta_t_diario_c": Fraction(7, 1),
    },
    "belo_horizonte": {
        "codigo": "belo_horizonte",
        "nome": "Belo Horizonte - MG",
        "tbs_externa_c": Fraction(31, 1),
        "umidade_externa_g_kg": Fraction(14, 1),
        "delta_t_diario_c": Fraction(10, 1),
    },
    "brasilia": {
        "codigo": "brasilia",
        "nome": "Brasília - DF",
        "tbs_externa_c": Fraction(32, 1),
        "umidade_externa_g_kg": Fraction(13, 1),
        "delta_t_diario_c": Fraction(11, 1),
    },
    "curitiba": {
        "codigo": "curitiba",
        "nome": "Curitiba - PR",
        "tbs_externa_c": Fraction(30, 1),
        "umidade_externa_g_kg": Fraction(14, 1),
        "delta_t_diario_c": Fraction(10, 1),
    },
    "salvador": {
        "codigo": "salvador",
        "nome": "Salvador - BA",
        "tbs_externa_c": Fraction(33, 1),
        "umidade_externa_g_kg": Fraction(19, 1),
        "delta_t_diario_c": Fraction(6, 1),
    },
    "recife": {
        "codigo": "recife",
        "nome": "Recife - PE",
        "tbs_externa_c": Fraction(33, 1),
        "umidade_externa_g_kg": Fraction(18, 1),
        "delta_t_diario_c": Fraction(6, 1),
    },
    "porto_alegre": {
        "codigo": "porto_alegre",
        "nome": "Porto Alegre - RS",
        "tbs_externa_c": Fraction(34, 1),
        "umidade_externa_g_kg": Fraction(17, 1),
        "delta_t_diario_c": Fraction(9, 1),
    },
    "fortaleza": {
        "codigo": "fortaleza",
        "nome": "Fortaleza - CE",
        "tbs_externa_c": Fraction(33, 1),
        "umidade_externa_g_kg": Fraction(18, 1),
        "delta_t_diario_c": Fraction(5, 1),
    },
    "manaus": {
        "codigo": "manaus",
        "nome": "Manaus - AM",
        "tbs_externa_c": Fraction(35, 1),
        "umidade_externa_g_kg": Fraction(21, 1),
        "delta_t_diario_c": Fraction(8, 1),
    },
}

# Condições internas de conforto térmico padrão de verão (NBR 16401-2)
TBS_INTERNA_CONFORTO_PADRAO_C: Final[Fraction] = Fraction(24, 1)  # 24 °C
UMIDADE_INTERNA_CONFORTO_PADRAO_G_KG: Final[Fraction] = Fraction(10, 1)  # ~50% UR a 24°C

# Calor metabólico emitido por pessoa segundo o tipo de atividade (NBR 16401-2)
# Valores em Watts por pessoa convertidos para fração
ATIVIDADES_METABOLICAS: Final[dict[str, dict[str, Fraction | str]]] = {
    "escritorio_sentado": {
        "nome": "Trabalho de escritório leve (sentado)",
        "calor_sensivel_w": Fraction(70, 1),
        "calor_latente_w": Fraction(60, 1),
    },
    "comercio_moderado": {
        "nome": "Comércio / Lojas (em pé / caminhando)",
        "calor_sensivel_w": Fraction(75, 1),
        "calor_latente_w": Fraction(75, 1),
    },
    "restaurante": {
        "nome": "Restaurante / Sala de refeições",
        "calor_sensivel_w": Fraction(75, 1),
        "calor_latente_w": Fraction(85, 1),
    },
    "sala_aula": {
        "nome": "Sala de aula / Treinamento",
        "calor_sensivel_w": Fraction(70, 1),
        "calor_latente_w": Fraction(55, 1),
    },
    "academia_musculacao": {
        "nome": "Atividade esportiva moderada / Academia",
        "calor_sensivel_w": Fraction(90, 1),
        "calor_latente_w": Fraction(180, 1),
    },
    "teatro_cinema": {
        "nome": "Auditório / Cinema / Teatro (repouso)",
        "calor_sensivel_w": Fraction(65, 1),
        "calor_latente_w": Fraction(50, 1),
    },
}

# Taxas mínimas de renovação de ar exterior por ocupante e por área (NBR 16401-3 Tabela 1)
# m³/h por pessoa e m³/h por m² de piso
TAXAS_RENOVACAO_AR_EXTERIOR: Final[dict[str, dict[str, Fraction | str]]] = {
    "escritorio_geral": {
        "nome": "Escritórios e salas de reunião",
        "vazao_por_pessoa_m3_h": Fraction(27, 1),   # 7,5 L/s/pessoa
        "vazao_por_area_m3_h_m2": Fraction(18, 10), # 0,5 L/s/m²
    },
    "loja_comercial": {
        "nome": "Lojas de departamentos e centros comerciais",
        "vazao_por_pessoa_m3_h": Fraction(20, 1),
        "vazao_por_area_m3_h_m2": Fraction(15, 10),
    },
    "restaurante_refeitorio": {
        "nome": "Restaurantes, refeitórios e praças de alimentação",
        "vazao_por_pessoa_m3_h": Fraction(30, 1),
        "vazao_por_area_m3_h_m2": Fraction(25, 10),
    },
    "sala_aula": {
        "nome": "Salas de aula e laboratórios de ensino",
        "vazao_por_pessoa_m3_h": Fraction(27, 1),
        "vazao_por_area_m3_h_m2": Fraction(20, 10),
    },
    "academia": {
        "nome": "Academias de ginástica e salas aeróbicas",
        "vazao_por_pessoa_m3_h": Fraction(40, 1),
        "vazao_por_area_m3_h_m2": Fraction(30, 10),
    },
    "hotel_quarto": {
        "nome": "Quartos de hotéis e pousadas",
        "vazao_por_pessoa_m3_h": Fraction(25, 1),
        "vazao_por_area_m3_h_m2": Fraction(12, 10),
    },
}

# Coeficientes globais de transferência térmica U típicos (W/(m².K)) e fatores solares
# U_w_m2_k convertido para kcal/(h.m².°C) via U * 0,859845
COEFICIENTES_TRANSMISSAO_U_W_M2_K: Final[dict[str, Fraction]] = {
    "alvenaria_tijolo_furado_reboco": Fraction(22, 10),   # 2,2 W/(m².K)
    "alvenaria_bloco_concreto": Fraction(25, 10),         # 2,5 W/(m².K)
    "drywall_isolamento_la": Fraction(12, 10),            # 1,2 W/(m².K)
    "cobertura_telha_fibrocimento_laje": Fraction(18, 10),# 1,8 W/(m².K)
    "cobertura_telha_termica_pir": Fraction(8, 10),       # 0,8 W/(m².K)
    "vidro_simples_incolor_4mm": Fraction(58, 10),        # 5,8 W/(m².K)
    "vidro_duplo_insulado_6mm": Fraction(28, 10),         # 2,8 W/(m².K)
    "piso_sobre_solo_ou_garagem": Fraction(15, 10),       # 1,5 W/(m².K)
    "divisoria_interna_leve": Fraction(19, 10),           # 1,9 W/(m².K)
}

# Radiação solar máxima de projeto incidente em superfícies envidraçadas (W/m²)
RADIACAO_SOLAR_FACHADA_W_M2: Final[dict[str, Fraction]] = {
    "norte": Fraction(220, 1),
    "sul": Fraction(100, 1),
    "leste": Fraction(420, 1),
    "oeste": Fraction(450, 1),
    "cobertura_horizontal": Fraction(650, 1),
}

# Fatores solares (FS) de vidros e proteções
FATOR_SOLAR_VIDROS: Final[dict[str, Fraction]] = {
    "vidro_incolor_sem_protecao": Fraction(87, 100),       # 0,87
    "vidro_incolor_com_persiana_interna": Fraction(55, 100),# 0,55
    "vidro_refletivo_controle_solar": Fraction(38, 100),   # 0,38
    "vidro_duplo_com_pelicula": Fraction(32, 100),         # 0,32
}

# Capacidades frigoríficas comerciais padronizadas em BTU/h
CAPACIDADES_COMERCIAIS_BTU: Final[tuple[int, ...]] = (
    9000, 12000, 18000, 24000, 30000, 36000, 48000, 60000,
    90000, 120000, 180000, 240000, 300000, 360000, 480000, 600000
)
