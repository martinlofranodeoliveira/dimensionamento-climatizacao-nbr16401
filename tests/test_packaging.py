"""Testes unitários para empacotamento e integridade de arquivos do projeto."""

from __future__ import annotations

from pathlib import Path
import tomllib
import unittest


class TestPackaging(unittest.TestCase):
    def test_arquivos_raiz_obrigatorios(self) -> None:
        raiz = Path(__file__).resolve().parent.parent
        obrigatorios = [
            "pyproject.toml",
            "LICENSE",
            "README.md",
            ".gitignore",
            "src/climatizacao_nbr16401/__init__.py",
            "src/climatizacao_nbr16401/py.typed",
            "tools/verify_independent.py",
            "scripts/check_distribution.py",
            "scripts/generate_assets.py",
        ]
        for ob in obrigatorios:
            p = raiz / ob
            self.assertTrue(p.exists(), f"Arquivo obrigatório '{ob}' não encontrado.")

    def test_pyproject_toml_metadados(self) -> None:
        raiz = Path(__file__).resolve().parent.parent
        conteudo = (raiz / "pyproject.toml").read_text(encoding="utf-8")
        dados = tomllib.loads(conteudo)

        proj = dados["project"]
        self.assertEqual(proj["name"], "dimensionamento-climatizacao-nbr16401")
        self.assertEqual(proj["version"], "1.0.0")
        self.assertIn("Lofrano", proj["authors"][0]["name"])
        self.assertIn("climatizacao-nbr16401", proj["scripts"])

    def test_versao_init(self) -> None:
        from climatizacao_nbr16401 import __version__
        self.assertEqual(__version__, "1.0.0")

    def test_exports_completos(self) -> None:
        import climatizacao_nbr16401 as clm
        self.assertTrue(hasattr(clm, "calcular_climatizacao_nbr16401"))
        self.assertTrue(hasattr(clm, "EspacoClimatizado"))
        self.assertTrue(hasattr(clm, "gerar_painel_svg"))
        self.assertTrue(hasattr(clm, "gerar_relatorio_texto"))
