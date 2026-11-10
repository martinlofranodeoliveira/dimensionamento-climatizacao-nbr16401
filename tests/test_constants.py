"""Testes unitários para as constantes e tabelas normativas da NBR 16401:2008."""

from __future__ import annotations

from fractions import Fraction
import unittest

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


class TestConstantes(unittest.TestCase):
    def test_conversoes_termodinamicas(self) -> None:
        self.assertEqual(BTU_POR_TR, 12000)
        self.assertEqual(KCAL_POR_TR, 3024)
        self.assertEqual(FATOR_KCAL_PARA_BTU, Fraction(15873, 4000))
        self.assertEqual(FATOR_W_PARA_KCAL_H, Fraction(171969, 200000))
        self.assertEqual(CALOR_VOLUMETRICO_AR_KCAL_M3_C, Fraction(288, 1000))
        self.assertEqual(CALOR_LATENTE_AR_KCAL_M3_G_KG, Fraction(70, 100))

    def test_condicoes_internas_padrao(self) -> None:
        self.assertEqual(TBS_INTERNA_CONFORTO_PADRAO_C, Fraction(24, 1))
        self.assertEqual(UMIDADE_INTERNA_CONFORTO_PADRAO_G_KG, Fraction(10, 1))

    def test_cidades_climaticas_presenca_e_campos(self) -> None:
        cidades_minimas = {"sao_paulo", "rio_de_janeiro", "belo_horizonte", "brasilia", "curitiba"}
        self.assertTrue(cidades_minimas.issubset(set(CIDADES_CLIMATICAS_PROJETO.keys())))
        for cid, info in CIDADES_CLIMATICAS_PROJETO.items():
            with self.subTest(cidade=cid):
                self.assertIn("codigo", info)
                self.assertIn("nome", info)
                self.assertIsInstance(info["tbs_externa_c"], Fraction)
                self.assertGreater(info["tbs_externa_c"], 0)
                self.assertIsInstance(info["umidade_externa_g_kg"], Fraction)
                self.assertGreater(info["umidade_externa_g_kg"], 0)

    def test_atividades_metabolicas(self) -> None:
        self.assertIn("escritorio_sentado", ATIVIDADES_METABOLICAS)
        self.assertIn("comercio_moderado", ATIVIDADES_METABOLICAS)
        self.assertIn("restaurante", ATIVIDADES_METABOLICAS)
        for ativ, info in ATIVIDADES_METABOLICAS.items():
            with self.subTest(atividade=ativ):
                self.assertIn("nome", info)
                self.assertIsInstance(info["calor_sensivel_w"], Fraction)
                self.assertGreater(info["calor_sensivel_w"], 0)
                self.assertIsInstance(info["calor_latente_w"], Fraction)
                self.assertGreater(info["calor_latente_w"], 0)

    def test_taxas_renovacao_ar(self) -> None:
        self.assertIn("escritorio_geral", TAXAS_RENOVACAO_AR_EXTERIOR)
        self.assertIn("loja_comercial", TAXAS_RENOVACAO_AR_EXTERIOR)
        for renov, info in TAXAS_RENOVACAO_AR_EXTERIOR.items():
            with self.subTest(renovacao=renov):
                self.assertIsInstance(info["vazao_por_pessoa_m3_h"], Fraction)
                self.assertGreater(info["vazao_por_pessoa_m3_h"], 0)
                self.assertIsInstance(info["vazao_por_area_m3_h_m2"], Fraction)
                self.assertGreater(info["vazao_por_area_m3_h_m2"], 0)

    def test_coeficientes_transmissao_u(self) -> None:
        self.assertIn("alvenaria_tijolo_furado_reboco", COEFICIENTES_TRANSMISSAO_U_W_M2_K)
        self.assertIn("vidro_simples_incolor_4mm", COEFICIENTES_TRANSMISSAO_U_W_M2_K)
        for mat, u in COEFICIENTES_TRANSMISSAO_U_W_M2_K.items():
            with self.subTest(material=mat):
                self.assertIsInstance(u, Fraction)
                self.assertGreater(u, 0)

    def test_radiacao_solar_fachada(self) -> None:
        orientacoes = {"norte", "sul", "leste", "oeste", "cobertura_horizontal"}
        self.assertEqual(set(RADIACAO_SOLAR_FACHADA_W_M2.keys()), orientacoes)
        for ori, rad in RADIACAO_SOLAR_FACHADA_W_M2.items():
            with self.subTest(orientacao=ori):
                self.assertIsInstance(rad, Fraction)
                self.assertGreater(rad, 0)

    def test_fatores_solares_vidro(self) -> None:
        self.assertIn("vidro_incolor_sem_protecao", FATOR_SOLAR_VIDROS)
        for fs_nome, fs_val in FATOR_SOLAR_VIDROS.items():
            with self.subTest(fs=fs_nome):
                self.assertIsInstance(fs_val, Fraction)
                self.assertTrue(0 < fs_val <= 1)

    def test_capacidades_comerciais(self) -> None:
        self.assertIn(9000, CAPACIDADES_COMERCIAIS_BTU)
        self.assertIn(12000, CAPACIDADES_COMERCIAIS_BTU)
        self.assertIn(60000, CAPACIDADES_COMERCIAIS_BTU)
        self.assertEqual(CAPACIDADES_COMERCIAIS_BTU, tuple(sorted(CAPACIDADES_COMERCIAIS_BTU)))
