"""Testes unitários para modelos de dados da NBR 16401:2008."""

from __future__ import annotations

from fractions import Fraction
import unittest

from climatizacao_nbr16401.models import (
    CargaEquipamentos,
    CargaIluminacao,
    CargaOcupantes,
    ElementoEnvoltoria,
    EspacoClimatizado,
)


class TestModelos(unittest.TestCase):
    def test_elemento_envoltoria_valido(self) -> None:
        el = ElementoEnvoltoria(
            nome="Parede Leste",
            tipo_material="alvenaria_tijolo_furado_reboco",
            area_m2=Fraction(50, 1),
            orientacao="leste",
        )
        self.assertEqual(el.nome, "Parede Leste")
        self.assertEqual(el.area_m2, Fraction(50, 1))
        self.assertEqual(el.orientacao, "leste")

    def test_elemento_envoltoria_validacoes(self) -> None:
        with self.assertRaises(ValueError):
            ElementoEnvoltoria("", "alvenaria_tijolo_furado_reboco", Fraction(20, 1))

        with self.assertRaises(ValueError):
            ElementoEnvoltoria("Parede", "alvenaria_tijolo_furado_reboco", Fraction(0, 1))

        with self.assertRaises(ValueError):
            ElementoEnvoltoria("Parede", "alvenaria_tijolo_furado_reboco", Fraction(-10, 1))

    def test_carga_ocupantes_validacoes(self) -> None:
        ocup = CargaOcupantes(10, "escritorio_sentado")
        self.assertEqual(ocup.quantidade_pessoas, 10)
        with self.assertRaises(ValueError):
            CargaOcupantes(-2, "escritorio_sentado")

    def test_carga_iluminacao_validacoes(self) -> None:
        ilum = CargaIluminacao(Fraction(1000, 1), Fraction(1, 1))
        self.assertEqual(ilum.potencia_total_w, Fraction(1000, 1))
        with self.assertRaises(ValueError):
            CargaIluminacao(Fraction(-100, 1))
        with self.assertRaises(ValueError):
            CargaIluminacao(Fraction(1000, 1), Fraction(0, 1))
        with self.assertRaises(ValueError):
            CargaIluminacao(Fraction(1000, 1), Fraction(3, 1))

    def test_carga_equipamentos_validacoes(self) -> None:
        equip = CargaEquipamentos(Fraction(2000, 1), Fraction(9, 10))
        self.assertEqual(equip.potencia_total_w, Fraction(2000, 1))
        with self.assertRaises(ValueError):
            CargaEquipamentos(Fraction(-50, 1))
        with self.assertRaises(ValueError):
            CargaEquipamentos(Fraction(2000, 1), Fraction(0, 1))
        with self.assertRaises(ValueError):
            CargaEquipamentos(Fraction(2000, 1), Fraction(15, 10))

    def test_espaco_climatizado_validacoes(self) -> None:
        el = ElementoEnvoltoria("Parede", "alvenaria_tijolo_furado_reboco", Fraction(20, 1))
        ocup = CargaOcupantes(5, "escritorio_sentado")
        ilum = CargaIluminacao(Fraction(500, 1))
        equip = CargaEquipamentos(Fraction(1000, 1))

        with self.assertRaises(ValueError):
            EspacoClimatizado(" ", "sao_paulo", "escritorio_geral", Fraction(50, 1), Fraction(3, 1), ocup, ilum, equip, (el,))

        with self.assertRaises(ValueError):
            EspacoClimatizado("Proj", "sao_paulo", "escritorio_geral", Fraction(0, 1), Fraction(3, 1), ocup, ilum, equip, (el,))

        with self.assertRaises(ValueError):
            EspacoClimatizado("Proj", "sao_paulo", "escritorio_geral", Fraction(50, 1), Fraction(0, 1), ocup, ilum, equip, (el,))

        with self.assertRaises(ValueError):
            EspacoClimatizado("Proj", "sao_paulo", "escritorio_geral", Fraction(50, 1), Fraction(3, 1), ocup, ilum, equip, ())

        with self.assertRaises(ValueError):
            EspacoClimatizado("Proj", "sao_paulo", "escritorio_geral", Fraction(50, 1), Fraction(3, 1), ocup, ilum, equip, (el,), fator_seguranca_pct=Fraction(-5, 1))
