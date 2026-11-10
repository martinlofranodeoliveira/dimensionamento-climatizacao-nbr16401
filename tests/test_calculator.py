"""Testes unitários para o motor de cálculo da NBR 16401:2008."""

from __future__ import annotations

from fractions import Fraction
import unittest

from climatizacao_nbr16401.calculator import calcular_climatizacao_nbr16401
from climatizacao_nbr16401.models import (
    CargaEquipamentos,
    CargaIluminacao,
    CargaOcupantes,
    ElementoEnvoltoria,
    EspacoClimatizado,
)


class TestCalculadora(unittest.TestCase):
    def test_calculo_escritorio_padrao(self) -> None:
        espaco = EspacoClimatizado(
            projeto="Escritório Teste",
            localidade="sao_paulo",
            tipo_renovacao="escritorio_geral",
            area_piso_m2=Fraction(100, 1),
            pe_direito_m=Fraction(3, 1),
            ocupantes=CargaOcupantes(10, "escritorio_sentado"),
            iluminacao=CargaIluminacao(Fraction(1000, 1)),
            equipamentos=CargaEquipamentos(Fraction(2000, 1)),
            envoltoria=(
                ElementoEnvoltoria(
                    nome="Janela Leste",
                    tipo_material="vidro_simples_incolor_4mm",
                    area_m2=Fraction(20, 1),
                    orientacao="leste",
                    fator_solar_vidro="vidro_incolor_com_persiana_interna",
                ),
                ElementoEnvoltoria(
                    nome="Parede Alvenaria",
                    tipo_material="alvenaria_tijolo_furado_reboco",
                    area_m2=Fraction(60, 1),
                ),
            ),
        )
        res = calcular_climatizacao_nbr16401(espaco)
        self.assertEqual(res.localidade_codigo, "sao_paulo")
        self.assertEqual(res.tbs_externa_c, Fraction(32, 1))
        self.assertEqual(res.tbs_interna_c, Fraction(24, 1))
        self.assertEqual(res.delta_t_c, Fraction(8, 1))

        self.assertGreater(res.calor_conducao_total_kcal_h, 0)
        self.assertGreater(res.calor_solar_total_kcal_h, 0)
        self.assertGreater(res.calor_pessoas_sensivel_kcal_h, 0)
        self.assertGreater(res.calor_pessoas_latente_kcal_h, 0)
        self.assertGreater(res.calor_iluminacao_kcal_h, 0)
        self.assertGreater(res.calor_equipamentos_kcal_h, 0)
        self.assertGreater(res.vazao_ar_renovacao_m3_h, 0)
        self.assertGreater(res.vazao_ar_insuflado_m3_h, 0)
        self.assertGreater(res.carga_termica_total_btu_h, 0)
        self.assertGreater(res.carga_termica_total_tr, 0)
        self.assertTrue(0 < res.fator_calor_sensivel <= 1)
        self.assertGreater(res.capacidade_comercial_btu_h, 0)

    def test_renovacao_ar_governado_por_pessoas_vs_area(self) -> None:
        # 10 pessoas * 27 m³/h = 270 m³/h; 50 m² * 1,8 m³/h/m² = 90 m³/h => governa pessoas (270)
        espaco_pessoas = EspacoClimatizado(
            projeto="Sala Reunião",
            localidade="sao_paulo",
            tipo_renovacao="escritorio_geral",
            area_piso_m2=Fraction(50, 1),
            pe_direito_m=Fraction(3, 1),
            ocupantes=CargaOcupantes(10, "escritorio_sentado"),
            iluminacao=CargaIluminacao(Fraction(300, 1)),
            equipamentos=CargaEquipamentos(Fraction(500, 1)),
            envoltoria=(ElementoEnvoltoria("Parede", "alvenaria_tijolo_furado_reboco", Fraction(30, 1)),),
        )
        res_p = calcular_climatizacao_nbr16401(espaco_pessoas)
        self.assertEqual(res_p.vazao_ar_renovacao_m3_h, Fraction(270, 1))

        # 2 pessoas * 27 = 54; 200 m² * 1,8 = 360 m³/h => governa área (360)
        espaco_area = EspacoClimatizado(
            projeto="Arquivo Morto / Salao Amplo",
            localidade="sao_paulo",
            tipo_renovacao="escritorio_geral",
            area_piso_m2=Fraction(200, 1),
            pe_direito_m=Fraction(3, 1),
            ocupantes=CargaOcupantes(2, "escritorio_sentado"),
            iluminacao=CargaIluminacao(Fraction(300, 1)),
            equipamentos=CargaEquipamentos(Fraction(500, 1)),
            envoltoria=(ElementoEnvoltoria("Parede", "alvenaria_tijolo_furado_reboco", Fraction(30, 1)),),
        )
        res_a = calcular_climatizacao_nbr16401(espaco_area)
        self.assertEqual(res_a.vazao_ar_renovacao_m3_h, Fraction(360, 1))

    def test_alta_carga_latente_academia(self) -> None:
        espaco_academia = EspacoClimatizado(
            projeto="Academia Musculação",
            localidade="curitiba",
            tipo_renovacao="academia",
            area_piso_m2=Fraction(200, 1),
            pe_direito_m=Fraction(4, 1),
            ocupantes=CargaOcupantes(30, "academia_musculacao"),
            iluminacao=CargaIluminacao(Fraction(1500, 1)),
            equipamentos=CargaEquipamentos(Fraction(2000, 1)),
            envoltoria=(ElementoEnvoltoria("Parede", "alvenaria_bloco_concreto", Fraction(100, 1)),),
        )
        res = calcular_climatizacao_nbr16401(espaco_academia)
        # Latente emitido por ocupantes em academia é muito alto (180 W/pessoa vs 90 W sensível)
        self.assertGreater(res.calor_pessoas_latente_kcal_h, res.calor_pessoas_sensivel_kcal_h)

    def test_excecao_localidade_invalida(self) -> None:
        espaco = EspacoClimatizado(
            projeto="A",
            localidade="cidade_inexistente",
            tipo_renovacao="escritorio_geral",
            area_piso_m2=Fraction(50, 1),
            pe_direito_m=Fraction(3, 1),
            ocupantes=CargaOcupantes(2, "escritorio_sentado"),
            iluminacao=CargaIluminacao(Fraction(100, 1)),
            equipamentos=CargaEquipamentos(Fraction(100, 1)),
            envoltoria=(ElementoEnvoltoria("Parede", "alvenaria_tijolo_furado_reboco", Fraction(20, 1)),),
        )
        with self.assertRaises(ValueError):
            calcular_climatizacao_nbr16401(espaco)

    def test_excecao_material_invalido(self) -> None:
        espaco = EspacoClimatizado(
            projeto="A",
            localidade="sao_paulo",
            tipo_renovacao="escritorio_geral",
            area_piso_m2=Fraction(50, 1),
            pe_direito_m=Fraction(3, 1),
            ocupantes=CargaOcupantes(2, "escritorio_sentado"),
            iluminacao=CargaIluminacao(Fraction(100, 1)),
            equipamentos=CargaEquipamentos(Fraction(100, 1)),
            envoltoria=(ElementoEnvoltoria("Parede", "material_desconhecido_123", Fraction(20, 1)),),
        )
        with self.assertRaises(ValueError):
            calcular_climatizacao_nbr16401(espaco)

    def test_excecao_orientacao_invalida(self) -> None:
        espaco = EspacoClimatizado(
            projeto="A",
            localidade="sao_paulo",
            tipo_renovacao="escritorio_geral",
            area_piso_m2=Fraction(50, 1),
            pe_direito_m=Fraction(3, 1),
            ocupantes=CargaOcupantes(2, "escritorio_sentado"),
            iluminacao=CargaIluminacao(Fraction(100, 1)),
            equipamentos=CargaEquipamentos(Fraction(100, 1)),
            envoltoria=(ElementoEnvoltoria("Vidro", "vidro_simples_incolor_4mm", Fraction(10, 1), orientacao="noroeste_invalido"),),
        )
        with self.assertRaises(ValueError):
            calcular_climatizacao_nbr16401(espaco)

    def test_calculo_restaurante_completo(self) -> None:
        espaco = EspacoClimatizado(
            projeto="Restaurante Teste",
            localidade="belo_horizonte",
            tipo_renovacao="restaurante_refeitorio",
            area_piso_m2=Fraction(150, 1),
            pe_direito_m=Fraction(32, 10),
            ocupantes=CargaOcupantes(50, "restaurante"),
            iluminacao=CargaIluminacao(Fraction(1500, 1)),
            equipamentos=CargaEquipamentos(Fraction(3000, 1)),
            envoltoria=(ElementoEnvoltoria("Parede", "alvenaria_tijolo_furado_reboco", Fraction(80, 1)),),
        )
        res = calcular_climatizacao_nbr16401(espaco)
        self.assertEqual(res.localidade_codigo, "belo_horizonte")
        self.assertGreater(res.carga_termica_total_btu_h, 50000)
        self.assertGreater(res.capacidade_comercial_btu_h, 60000)

    def test_calculo_comercio_loja(self) -> None:
        espaco = EspacoClimatizado(
            projeto="Loja Teste",
            localidade="rio_de_janeiro",
            tipo_renovacao="loja_comercial",
            area_piso_m2=Fraction(120, 1),
            pe_direito_m=Fraction(35, 10),
            ocupantes=CargaOcupantes(20, "comercio_moderado"),
            iluminacao=CargaIluminacao(Fraction(2000, 1)),
            equipamentos=CargaEquipamentos(Fraction(1500, 1)),
            envoltoria=(ElementoEnvoltoria("Vitrine", "vidro_simples_incolor_4mm", Fraction(30, 1), orientacao="sul"),),
        )
        res = calcular_climatizacao_nbr16401(espaco)
        self.assertEqual(res.localidade_codigo, "rio_de_janeiro")
        self.assertEqual(res.tbs_externa_c, Fraction(35, 1))

    def test_calculo_margem_seguranca_zero(self) -> None:
        espaco = EspacoClimatizado(
            projeto="Sem Margem",
            localidade="sao_paulo",
            tipo_renovacao="escritorio_geral",
            area_piso_m2=Fraction(60, 1),
            pe_direito_m=Fraction(3, 1),
            ocupantes=CargaOcupantes(4, "escritorio_sentado"),
            iluminacao=CargaIluminacao(Fraction(500, 1)),
            equipamentos=CargaEquipamentos(Fraction(800, 1)),
            envoltoria=(ElementoEnvoltoria("Parede", "alvenaria_tijolo_furado_reboco", Fraction(40, 1)),),
            fator_seguranca_pct=Fraction(0, 1),
        )
        res = calcular_climatizacao_nbr16401(espaco)
        self.assertEqual(res.calor_sensivel_total_kcal_h, res.calor_sensivel_subtotal_kcal_h)
        self.assertEqual(res.calor_latente_total_kcal_h, res.calor_latente_subtotal_kcal_h)

