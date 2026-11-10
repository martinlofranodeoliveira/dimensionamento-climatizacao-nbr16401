"""Testes unitários para a CLI da NBR 16401:2008."""

from __future__ import annotations

import io
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

from climatizacao_nbr16401.cli import main


class TestCli(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cli_versao(self) -> None:
        buffer = io.StringIO()
        old_stdout = sys.stdout
        try:
            sys.stdout = buffer
            with self.assertRaises(SystemExit) as cm:
                main(["--versao"])
            self.assertEqual(cm.exception.code, 0)
            self.assertIn("climatizacao-nbr16401", buffer.getvalue())
        finally:
            sys.stdout = old_stdout

    def test_cli_catalogo(self) -> None:
        buffer = io.StringIO()
        old_stdout = sys.stdout
        try:
            sys.stdout = buffer
            codigo = main(["catalogo"])
            self.assertEqual(codigo, 0)
            saida = buffer.getvalue()
            self.assertIn("CATÁLOGO NORMATIVO ABNT NBR 16401:2008", saida)
            self.assertIn("sao_paulo", saida)
            self.assertIn("escritorio_geral", saida)
            self.assertIn("vidro_simples_incolor_4mm", saida)
        finally:
            sys.stdout = old_stdout

    def test_cli_gerar_exemplo_stdout(self) -> None:
        buffer = io.StringIO()
        old_stdout = sys.stdout
        try:
            sys.stdout = buffer
            codigo = main(["gerar-exemplo", "--tipo", "escritorio"])
            self.assertEqual(codigo, 0)
            saida = buffer.getvalue()
            self.assertIn('"localidade": "sao_paulo"', saida)
        finally:
            sys.stdout = old_stdout

    def test_cli_gerar_exemplo_arquivo(self) -> None:
        saida_json = self.temp_dir / "exemplo_loja.json"
        codigo = main(["gerar-exemplo", "--tipo", "comercio", "--saida", str(saida_json)])
        self.assertEqual(codigo, 0)
        self.assertTrue(saida_json.exists())
        conteudo = saida_json.read_text(encoding="utf-8")
        self.assertIn('"tipo_renovacao": "loja_comercial"', conteudo)

    def test_cli_calcular_completo(self) -> None:
        ex_path = Path(__file__).resolve().parent.parent / "examples" / "escritorio_corporativo_paulista.json"
        out_txt = self.temp_dir / "relatorio.txt"
        out_json = self.temp_dir / "resultado.json"
        out_csv = self.temp_dir / "elementos.csv"
        out_svg = self.temp_dir / "painel.svg"
        out_zip = self.temp_dir / "pacote.zip"

        codigo = main([
            "calcular",
            str(ex_path),
            "--saida-txt", str(out_txt),
            "--saida-json", str(out_json),
            "--saida-csv", str(out_csv),
            "--saida-svg", str(out_svg),
            "--pacote-zip", str(out_zip),
        ])
        self.assertEqual(codigo, 0)
        self.assertTrue(out_txt.exists())
        self.assertTrue(out_json.exists())
        self.assertTrue(out_csv.exists())
        self.assertTrue(out_svg.exists())
        self.assertTrue(out_zip.exists())

    def test_cli_calcular_formato_texto(self) -> None:
        ex_path = Path(__file__).resolve().parent.parent / "examples" / "escritorio_corporativo_paulista.json"
        buffer = io.StringIO()
        old_stdout = sys.stdout
        try:
            sys.stdout = buffer
            codigo = main(["calcular", str(ex_path), "--formato", "texto"])
            self.assertEqual(codigo, 0)
            self.assertIn("LOFRANO TECNOLOGIA", buffer.getvalue())
        finally:
            sys.stdout = old_stdout

    def test_cli_calcular_arquivo_inexistente(self) -> None:
        buffer_err = io.StringIO()
        old_stderr = sys.stderr
        try:
            sys.stderr = buffer_err
            codigo = main(["calcular", "arquivo_inexistente_clima.json"])
            self.assertEqual(codigo, 1)
            self.assertIn("não encontrado", buffer_err.getvalue())
        finally:
            sys.stderr = old_stderr
