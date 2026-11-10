"""Testes unitários para exportadores TXT, CSV e ZIP da NBR 16401:2008."""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path
import shutil
import tempfile
import unittest
import zipfile

from climatizacao_nbr16401.calculator import calcular_climatizacao_nbr16401
from climatizacao_nbr16401.codecs import decodificar_espaco_json
from climatizacao_nbr16401.exporters import (
    DATA_FIXA_ZIP,
    criar_pacote_zip_deterministico,
    formatar_fracao_decimal,
    gerar_csv_elementos,
    gerar_relatorio_texto,
    sanitizar_campo_csv,
)


class TestExportadores(unittest.TestCase):
    def setUp(self) -> None:
        ex_path = Path(__file__).resolve().parent.parent / "examples" / "escritorio_corporativo_paulista.json"
        espaco = decodificar_espaco_json(ex_path.read_text(encoding="utf-8"))
        self.resultado = calcular_climatizacao_nbr16401(espaco)
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_formatar_fracao_decimal(self) -> None:
        self.assertEqual(formatar_fracao_decimal(Fraction(0, 1)), "0,00")
        self.assertEqual(formatar_fracao_decimal(Fraction(24, 1)), "24,00")
        self.assertEqual(formatar_fracao_decimal(Fraction(22, 10)), "2,20")
        self.assertEqual(formatar_fracao_decimal(Fraction(1, 3), casas=3), "0,333")
        self.assertEqual(formatar_fracao_decimal(Fraction(-15, 2)), "-7,50")

    def test_sanitizar_campo_csv(self) -> None:
        self.assertEqual(sanitizar_campo_csv("parede"), "parede")
        self.assertEqual(sanitizar_campo_csv("=1+1"), "'=1+1")
        self.assertEqual(sanitizar_campo_csv("+SOMA()"), "'+SOMA()")
        self.assertEqual(sanitizar_campo_csv("-10"), "'-10")
        self.assertEqual(sanitizar_campo_csv("@CMD"), "'@CMD")
        self.assertEqual(sanitizar_campo_csv("\ttab"), "'\ttab")
        self.assertEqual(sanitizar_campo_csv("\rret"), "'\rret")

    def test_gerar_relatorio_texto(self) -> None:
        texto = gerar_relatorio_texto(self.resultado)
        self.assertIn("LOFRANO TECNOLOGIA", texto)
        self.assertIn("ABNT NBR 16401:2008", texto)
        self.assertIn("CARGA TÉRMICA TOTAL", texto)
        self.assertIn("RENOVAÇÃO DE AR EXTERIOR", texto)
        self.assertIn("BTU/h", texto)

    def test_gerar_csv_elementos(self) -> None:
        csv_str = gerar_csv_elementos(self.resultado)
        linhas = csv_str.strip().split("\n")
        self.assertGreaterEqual(len(linhas), 2)
        self.assertIn("nome;tipo_material;area_m2", linhas[0])
        self.assertIn("Fachada Envidraçada Leste", csv_str)

    def test_criar_pacote_zip_deterministico(self) -> None:
        zip_path = self.temp_dir / "teste_climatizacao.zip"
        caminho_gerado = criar_pacote_zip_deterministico(
            zip_path,
            self.resultado,
            conteudo_svg="<svg></svg>",
            sobrescrever=True,
        )
        self.assertTrue(caminho_gerado.exists())
        self.assertGreater(zip_path.stat().st_size, 0)

        with zipfile.ZipFile(zip_path, "r") as zf:
            nomes = zf.namelist()
            self.assertIn("relatorio_climatizacao.txt", nomes)
            self.assertIn("resultado_climatizacao.json", nomes)
            self.assertIn("elementos_envoltoria.csv", nomes)
            self.assertIn("painel_climatizacao.svg", nomes)

            for info in zf.infolist():
                self.assertEqual(info.date_time, DATA_FIXA_ZIP)

        with self.assertRaises(FileExistsError):
            criar_pacote_zip_deterministico(zip_path, self.resultado, sobrescrever=False)
