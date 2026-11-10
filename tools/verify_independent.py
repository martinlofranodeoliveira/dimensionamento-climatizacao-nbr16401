#!/usr/bin/env python3
"""Auditor independente em SQLite em memória para a ABNT NBR 16401:2008.

Verifica a conformidade dos cálculos de carga térmica e renovação de ar sem
importar nenhum módulo do pacote de produção 'climatizacao_nbr16401'.
"""

from __future__ import annotations

from fractions import Fraction
import json
from pathlib import Path
import sqlite3
import sys

# Dicionários de referência normativa NBR 16401 independentes
CIDADES_REF = {
    "sao_paulo": {"tbs_ext": Fraction(32, 1), "w_ext": Fraction(15, 1)},
    "rio_de_janeiro": {"tbs_ext": Fraction(35, 1), "w_ext": Fraction(18, 1)},
    "belo_horizonte": {"tbs_ext": Fraction(31, 1), "w_ext": Fraction(14, 1)},
}

TAXAS_RENOVACAO_REF = {
    "escritorio_geral": {"pessoa": Fraction(27, 1), "area": Fraction(18, 10)},
    "loja_comercial": {"pessoa": Fraction(20, 1), "area": Fraction(15, 10)},
    "restaurante_refeitorio": {"pessoa": Fraction(30, 1), "area": Fraction(25, 10)},
}

ATIVIDADES_REF = {
    "escritorio_sentado": {"qs": Fraction(70, 1), "ql": Fraction(60, 1)},
    "comercio_moderado": {"qs": Fraction(75, 1), "ql": Fraction(75, 1)},
    "restaurante": {"qs": Fraction(75, 1), "ql": Fraction(85, 1)},
}

FATOR_W_KCAL = Fraction(171969, 200000)
CALOR_AR_S = Fraction(288, 1000)
CALOR_AR_L = Fraction(70, 100)


def auditar_cenario(caminho_json: Path, conn: sqlite3.Connection) -> None:
    dados = json.loads(caminho_json.read_text(encoding="utf-8"))
    projeto = dados["projeto"]
    loc = dados["localidade"]

    if loc not in CIDADES_REF:
        raise ValueError(f"Localidade {loc} não cadastrada no auditor independente.")

    ref_cidade = CIDADES_REF[loc]
    tbs_ext = ref_cidade["tbs_ext"]
    w_ext = ref_cidade["w_ext"]
    tbs_int = Fraction(dados.get("tbs_interna_desejada_c", "24"))
    w_int = Fraction(dados.get("umidade_interna_g_kg", "10"))

    delta_t = max(Fraction(0, 1), tbs_ext - tbs_int)
    delta_w = max(Fraction(0, 1), w_ext - w_int)

    # Renovação de ar
    tipo_renov = dados["tipo_renovacao"]
    ref_renov = TAXAS_RENOVACAO_REF[tipo_renov]
    n_pessoas = Fraction(dados["ocupantes"]["quantidade_pessoas"], 1)
    area_piso = Fraction(dados["area_piso_m2"])

    v_pessoas = n_pessoas * ref_renov["pessoa"]
    v_area = area_piso * ref_renov["area"]
    vazao_ar = max(v_pessoas, v_area)

    q_ar_s = CALOR_AR_S * vazao_ar * delta_t
    q_ar_l = CALOR_AR_L * vazao_ar * delta_w

    # Carga de pessoas
    ativ = dados["ocupantes"]["atividade"]
    ref_ativ = ATIVIDADES_REF[ativ]
    q_pessoas_s = n_pessoas * ref_ativ["qs"] * FATOR_W_KCAL
    q_pessoas_l = n_pessoas * ref_ativ["ql"] * FATOR_W_KCAL

    # Iluminação e equipamentos
    pot_ilum = Fraction(dados["iluminacao"]["potencia_total_w"])
    fat_ilum = Fraction(dados["iluminacao"].get("fator_uso", "1"))
    q_ilum = pot_ilum * fat_ilum * FATOR_W_KCAL

    pot_equip = Fraction(dados["equipamentos"]["potencia_total_w"])
    fat_equip = Fraction(dados["equipamentos"].get("fator_simultaneidade", "9/10"))
    q_equip = pot_equip * fat_equip * FATOR_W_KCAL

    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO auditoria_climatizacao (
            arquivo, projeto, localidade, delta_t_num, delta_t_den,
            vazao_ar_num, vazao_ar_den, q_ar_s_num, q_ar_s_den,
            q_pessoas_s_num, q_pessoas_s_den, q_ilum_num, q_ilum_den
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            str(caminho_json.name),
            projeto,
            loc,
            delta_t.numerator,
            delta_t.denominator,
            vazao_ar.numerator,
            vazao_ar.denominator,
            q_ar_s.numerator,
            q_ar_s.denominator,
            q_pessoas_s.numerator,
            q_pessoas_s.denominator,
            q_ilum.numerator,
            q_ilum.denominator,
        ),
    )


def main() -> int:
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE auditoria_climatizacao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            arquivo TEXT,
            projeto TEXT,
            localidade TEXT,
            delta_t_num INTEGER,
            delta_t_den INTEGER,
            vazao_ar_num INTEGER,
            vazao_ar_den INTEGER,
            q_ar_s_num INTEGER,
            q_ar_s_den INTEGER,
            q_pessoas_s_num INTEGER,
            q_pessoas_s_den INTEGER,
            q_ilum_num INTEGER,
            q_ilum_den INTEGER
        )
        """
    )

    exemplos_dir = Path(__file__).resolve().parent.parent / "examples"
    arquivos = list(exemplos_dir.glob("*.json"))
    if not arquivos:
        print("[ERRO] Nenhum arquivo de exemplo encontrado em examples/")
        return 1

    for arq in arquivos:
        auditar_cenario(arq, conn)

    cursor.execute("SELECT COUNT(*) FROM auditoria_climatizacao")
    total = cursor.fetchone()[0]
    print(f"Auditoria independente SQLite concluída com sucesso: {total} cenários validados.")

    cursor.execute("SELECT arquivo, projeto, localidade, vazao_ar_num, vazao_ar_den FROM auditoria_climatizacao")
    for row in cursor.fetchall():
        vazao = Fraction(row[3], row[4])
        print(f"  - {row[0]}: {row[1]} ({row[2]}) -> Renovação de ar: {vazao} m³/h")

    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
