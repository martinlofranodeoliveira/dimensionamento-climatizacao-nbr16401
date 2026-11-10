"""Testes unitários para codecs e conformidade RFC 8259 da NBR 16401:2008."""

from __future__ import annotations

from fractions import Fraction
import json
from pathlib import Path
import unittest

from climatizacao_nbr16401.calculator import calcular_climatizacao_nbr16401
from climatizacao_nbr16401.codecs import (
    codificar_resultado_json,
    decodificar_espaco_json,
    espaco_para_dict,
    parse_fracao_ou_int,
    resultado_para_dict,
)


class TestCodecs(unittest.TestCase):
    def test_parse_fracao_ou_int_validos(self) -> None:
        self.assertEqual(parse_fracao_ou_int(25, "campo"), Fraction(25, 1))
        self.assertEqual(parse_fracao_ou_int("22/10", "campo"), Fraction(22, 10))
        self.assertEqual(parse_fracao_ou_int("2.2", "campo"), Fraction(22, 10))

    def test_parse_fracao_ou_int_rejeita_float(self) -> None:
        with self.assertRaises(TypeError):
            parse_fracao_ou_int(2.2, "campo")

    def test_parse_fracao_ou_int_rejeita_vazio_e_invalido(self) -> None:
        with self.assertRaises(ValueError):
            parse_fracao_ou_int("   ", "campo")

        with self.assertRaises(ValueError):
            parse_fracao_ou_int("abc", "campo")

        with self.assertRaises(TypeError):
            parse_fracao_ou_int([], "campo")

    def test_decodificacao_exemplos_reais(self) -> None:
        ex_dir = Path(__file__).resolve().parent.parent / "examples"
        for ex_file in ex_dir.glob("*.json"):
            with self.subTest(arquivo=ex_file.name):
                conteudo = ex_file.read_text(encoding="utf-8")
                espaco = decodificar_espaco_json(conteudo)
                self.assertTrue(len(espaco.projeto) > 0)
                self.assertTrue(len(espaco.envoltoria) > 0)

    def test_decodificacao_bytes_utf8(self) -> None:
        ex_path = Path(__file__).resolve().parent.parent / "examples" / "escritorio_corporativo_paulista.json"
        espaco = decodificar_espaco_json(ex_path.read_bytes())
        self.assertEqual(espaco.localidade, "sao_paulo")

    def test_rejeicao_bom_utf8(self) -> None:
        with self.assertRaises(ValueError):
            decodificar_espaco_json("\ufeff{}")

        with self.assertRaises(ValueError):
            decodificar_espaco_json(b"\xef\xbb\xbf{}")

    def test_rejeicao_chave_duplicada(self) -> None:
        json_dup = '{"projeto": "A", "projeto": "B", "localidade": "sao_paulo"}'
        with self.assertRaises(ValueError):
            decodificar_espaco_json(json_dup)

    def test_rejeicao_float_nativo_no_json(self) -> None:
        json_float = '{"projeto": "A", "area_piso_m2": 150.5}'
        with self.assertRaises(TypeError):
            decodificar_espaco_json(json_float)

    def test_rejeicao_profundidade_excessiva(self) -> None:
        profundo: dict = {"nivel": 0}
        atual = profundo
        for i in range(1, 35):
            atual["prox"] = {"nivel": i}
            atual = atual["prox"]

        texto_profundo = json.dumps(profundo)
        with self.assertRaises(ValueError):
            decodificar_espaco_json(texto_profundo)

    def test_serializacao_e_roundtrip(self) -> None:
        ex_path = Path(__file__).resolve().parent.parent / "examples" / "escritorio_corporativo_paulista.json"
        espaco = decodificar_espaco_json(ex_path.read_text(encoding="utf-8"))
        res = calcular_climatizacao_nbr16401(espaco)

        d_espaco = espaco_para_dict(espaco)
        self.assertEqual(d_espaco["localidade"], "sao_paulo")

        d_res = resultado_para_dict(res)
        self.assertIn("carga_termica_total_btu_h", d_res)

        json_str = codificar_resultado_json(res)
        self.assertIn('"localidade_codigo": "sao_paulo"', json_str)
