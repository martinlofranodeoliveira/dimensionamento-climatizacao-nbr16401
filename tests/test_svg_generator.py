"""Testes unitários para o gerador de painel SVG 1440x900 da NBR 16401:2008."""

from __future__ import annotations

from pathlib import Path
import unittest

from climatizacao_nbr16401.calculator import calcular_climatizacao_nbr16401
from climatizacao_nbr16401.codecs import decodificar_espaco_json
from climatizacao_nbr16401.svg_generator import gerar_painel_svg


class TestSvgGenerator(unittest.TestCase):
    def setUp(self) -> None:
        ex_path = Path(__file__).resolve().parent.parent / "examples" / "escritorio_corporativo_paulista.json"
        espaco = decodificar_espaco_json(ex_path.read_text(encoding="utf-8"))
        self.resultado = calcular_climatizacao_nbr16401(espaco)

    def test_gerar_painel_svg_estrutura(self) -> None:
        svg = gerar_painel_svg(self.resultado)
        self.assertIn('<svg xmlns="http://www.w3.org/2000/svg"', svg)
        self.assertIn('viewBox="0 0 1440 900"', svg)
        self.assertIn('width="1440"', svg)
        self.assertIn('height="900"', svg)
        self.assertIn("</svg>", svg)

    def test_gerar_painel_svg_elementos_tecnicos(self) -> None:
        svg = gerar_painel_svg(self.resultado)
        self.assertIn("LOFRANO TECNOLOGIA", svg)
        self.assertIn("ABNT NBR 16401:2008", svg)
        self.assertIn("CARGA TÉRMICA TOTAL", svg)
        self.assertIn("CAPACIDADE EM TR", svg)
        self.assertIn("VAZÃO DE AR INSUFLADO", svg)
        self.assertIn("AR EXTERIOR", svg)
        self.assertIn("EQUIPAMENTO RECOMENDADO", svg)
        self.assertIn("UNIDADE CLIMATIZADORA", svg)
        self.assertIn("RECINTO CONDICIONADO", svg)
