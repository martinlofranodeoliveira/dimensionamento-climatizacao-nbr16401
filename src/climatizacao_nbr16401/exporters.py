"""Módulo de exportação de relatórios, planilhas CSV e pacotes ZIP determinísticos.

Implementa:
- Relatório técnico em texto plano (pt-BR);
- Planilha CSV sanitizada contra injeção de fórmulas (=, +, -, @, \\t, \\r);
- Pacote ZIP determinístico com carimbo temporal fixo (2026-01-01 00:00:00) e O_EXCL.
"""

from __future__ import annotations

import csv
from datetime import datetime
from fractions import Fraction
import io
import os
from pathlib import Path
import zipfile

from climatizacao_nbr16401.codecs import codificar_resultado_json
from climatizacao_nbr16401.models import ResultadoCargaTermica

DATA_FIXA_ZIP = (2026, 1, 1, 0, 0, 0)


def formatar_fracao_decimal(f: Fraction, casas: int = 2) -> str:
    """Converte fração para string decimal pt-BR com vírgula sem usar float."""
    if f < 0:
        sinal = "-"
        f_pos = -f
    else:
        sinal = ""
        f_pos = f

    fator = 10**casas
    num_arredondado = (f_pos.numerator * fator * 2 + f_pos.denominator) // (f_pos.denominator * 2)
    parte_inteira = num_arredondado // fator
    resto = num_arredondado % fator
    resto_str = str(resto).zfill(casas)
    return f"{sinal}{parte_inteira},{resto_str}"


def sanitizar_campo_csv(val: str) -> str:
    """Sanitiza strings para CSV prevenindo ataques de CSV Formula Injection."""
    if val and val[0] in ("=", "+", "-", "@", "\t", "\r"):
        return f"'{val}"
    return val


def gerar_relatorio_texto(res: ResultadoCargaTermica) -> str:
    """Gera relatório técnico executivo em texto puro formatado (pt-BR)."""
    linhas: list[str] = [
        "=" * 80,
        "    LOFRANO TECNOLOGIA - ENGENHARIA TÉRMICA E CLIMATIZAÇÃO",
        "    CÁLCULO DE CARGA TÉRMICA E RENOVAÇÃO DE AR - ABNT NBR 16401:2008",
        "=" * 80,
        f"Projeto: {res.projeto}",
        f"Localidade: {res.localidade_nome} ({res.localidade_codigo})",
        f"Condições de Projeto: Externa TBS = {formatar_fracao_decimal(res.tbs_externa_c)} °C | Interna TBS = {formatar_fracao_decimal(res.tbs_interna_c)} °C (ΔT = {formatar_fracao_decimal(res.delta_t_c)} °C)",
        "-" * 80,
        "1. CARGAS TÉRMICAS DA ENVOLTÓRIA (CONDUÇÃO E RADIAÇÃO SOLAR)",
        f"{'Elemento':<24} {'Área(m²)':<10} {'U(W/m²K)':<10} {'ΔT(°C)':<8} {'Cond(kcal/h)':<14} {'Sol(kcal/h)':<14}",
        "-" * 80,
    ]

    for el in res.elementos:
        linhas.append(
            f"{el.nome:<24} "
            f"{formatar_fracao_decimal(el.area_m2):<10} "
            f"{formatar_fracao_decimal(el.u_w_m2_k):<10} "
            f"{formatar_fracao_decimal(el.delta_t_c):<8} "
            f"{formatar_fracao_decimal(el.calor_conducao_kcal_h):<14} "
            f"{formatar_fracao_decimal(el.calor_solar_kcal_h):<14}"
        )

    linhas.extend([
        "-" * 80,
        f"  * Total Condução Envoltória:        {formatar_fracao_decimal(res.calor_conducao_total_kcal_h)} kcal/h",
        f"  * Total Radiação Solar (Vidros):    {formatar_fracao_decimal(res.calor_solar_total_kcal_h)} kcal/h",
        "-" * 80,
        "2. CARGAS INTERNAS (OCUPANTES, ILUMINAÇÃO E EQUIPAMENTOS)",
        f"  - Ocupantes (Calor Sensível):       {formatar_fracao_decimal(res.calor_pessoas_sensivel_kcal_h)} kcal/h",
        f"  - Ocupantes (Calor Latente):        {formatar_fracao_decimal(res.calor_pessoas_latente_kcal_h)} kcal/h",
        f"  - Iluminação Artificial:            {formatar_fracao_decimal(res.calor_iluminacao_kcal_h)} kcal/h",
        f"  - Equipamentos Eletroeletrônicos:   {formatar_fracao_decimal(res.calor_equipamentos_kcal_h)} kcal/h",
        "-" * 80,
        "3. RENOVAÇÃO DE AR EXTERIOR (NBR 16401-3 - QUALIDADE DO AR)",
        f"  - Vazão de Renovação Requerida:     {formatar_fracao_decimal(res.vazao_ar_renovacao_m3_h)} m³/h",
        f"  - Carga Térmica Sensível do Ar:     {formatar_fracao_decimal(res.calor_ar_externo_sensivel_kcal_h)} kcal/h",
        f"  - Carga Térmica Latente do Ar:      {formatar_fracao_decimal(res.calor_ar_externo_latente_kcal_h)} kcal/h",
        "-" * 80,
        "4. BALANÇO TÉRMICO CONSOLIDADO E DIMENSIONAMENTO DO SISTEMA",
        f"  - Subtotal Calor Sensível:          {formatar_fracao_decimal(res.calor_sensivel_subtotal_kcal_h)} kcal/h",
        f"  - Subtotal Calor Latente:           {formatar_fracao_decimal(res.calor_latente_subtotal_kcal_h)} kcal/h",
        f"  - Margem de Segurança Aplicada:     {formatar_fracao_decimal(res.fator_seguranca_pct)} %",
        f"  - Carga Sensível Efetiva:           {formatar_fracao_decimal(res.calor_sensivel_total_kcal_h)} kcal/h",
        f"  - Carga Latente Efetiva:            {formatar_fracao_decimal(res.calor_latente_total_kcal_h)} kcal/h",
        f"  - CARGA TÉRMICA TOTAL:              {formatar_fracao_decimal(res.carga_termica_total_kcal_h)} kcal/h",
        f"  - CARGA TÉRMICA EM BTU/h:           {formatar_fracao_decimal(res.carga_termica_total_btu_h, 0)} BTU/h",
        f"  - CARGA TÉRMICA EM TR:              {formatar_fracao_decimal(res.carga_termica_total_tr, 2)} TR",
        f"  - Fator de Calor Sensível (FCS):    {formatar_fracao_decimal(res.fator_calor_sensivel, 3)}",
        f"  - Vazão de Ar Insuflado estimada:   {formatar_fracao_decimal(res.vazao_ar_insuflado_m3_h)} m³/h (ΔT=10°C)",
        "-" * 80,
        "5. SELEÇÃO DE EQUIPAMENTO COMERCIAL RECOMENDADO",
        f"  - Capacidade Frigorífica Padronizada: {res.capacidade_comercial_btu_h:,} BTU/h ({formatar_fracao_decimal(res.capacidade_comercial_tr, 2)} TR)".replace(",", "."),
        "-" * 80,
        "6. OBSERVAÇÕES E NOTAS NORMATIVAS",
    ])
    for obs in res.observacoes:
        linhas.append(f"  * {obs}")
    linhas.extend([
        "=" * 80,
        "Emitido via Lofrano Tecnologia - Conforme ABNT NBR 16401:2008",
        "=" * 80,
        "",
    ])
    return "\n".join(linhas)


def gerar_csv_elementos(res: ResultadoCargaTermica) -> str:
    """Gera planilha CSV com os elementos da envoltória e sanitização de fórmulas."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";", lineterminator="\n")

    writer.writerow([
        sanitizar_campo_csv("nome"),
        sanitizar_campo_csv("tipo_material"),
        sanitizar_campo_csv("area_m2"),
        sanitizar_campo_csv("u_w_m2_k"),
        sanitizar_campo_csv("u_kcal_h_m2_c"),
        sanitizar_campo_csv("delta_t_c"),
        sanitizar_campo_csv("calor_conducao_kcal_h"),
        sanitizar_campo_csv("calor_solar_kcal_h"),
        sanitizar_campo_csv("calor_total_kcal_h"),
    ])

    for el in res.elementos:
        writer.writerow([
            sanitizar_campo_csv(el.nome),
            sanitizar_campo_csv(el.tipo_material),
            sanitizar_campo_csv(formatar_fracao_decimal(el.area_m2)),
            sanitizar_campo_csv(formatar_fracao_decimal(el.u_w_m2_k)),
            sanitizar_campo_csv(formatar_fracao_decimal(el.u_kcal_h_m2_c)),
            sanitizar_campo_csv(formatar_fracao_decimal(el.delta_t_c)),
            sanitizar_campo_csv(formatar_fracao_decimal(el.calor_conducao_kcal_h)),
            sanitizar_campo_csv(formatar_fracao_decimal(el.calor_solar_kcal_h)),
            sanitizar_campo_csv(formatar_fracao_decimal(el.calor_total_kcal_h)),
        ])

    return buffer.getvalue()


def criar_pacote_zip_deterministico(
    caminho_saida: str | Path,
    res: ResultadoCargaTermica,
    conteudo_svg: str | None = None,
    sobrescrever: bool = True,
) -> Path:
    """Gera pacote ZIP com timestamp determinístico e modo seguro de criação."""
    caminho = Path(caminho_saida).resolve()
    caminho.parent.mkdir(parents=True, exist_ok=True)

    if caminho.exists():
        if sobrescrever:
            caminho.unlink()
        else:
            raise FileExistsError(f"Arquivo de destino '{caminho}' já existe.")

    flags = os.O_CREAT | os.O_EXCL | os.O_RDWR
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY

    fd = os.open(str(caminho), flags, 0o644)
    with os.fdopen(fd, "wb") as f_out:
        with zipfile.ZipFile(f_out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            relatorio_txt = gerar_relatorio_texto(res).encode("utf-8")
            zinfo_txt = zipfile.ZipInfo(filename="relatorio_climatizacao.txt", date_time=DATA_FIXA_ZIP)
            zinfo_txt.external_attr = 0o644 << 16
            zf.writestr(zinfo_txt, relatorio_txt)

            resultado_json = codificar_resultado_json(res).encode("utf-8")
            zinfo_json = zipfile.ZipInfo(filename="resultado_climatizacao.json", date_time=DATA_FIXA_ZIP)
            zinfo_json.external_attr = 0o644 << 16
            zf.writestr(zinfo_json, resultado_json)

            csv_elementos = gerar_csv_elementos(res).encode("utf-8")
            zinfo_csv = zipfile.ZipInfo(filename="elementos_envoltoria.csv", date_time=DATA_FIXA_ZIP)
            zinfo_csv.external_attr = 0o644 << 16
            zf.writestr(zinfo_csv, csv_elementos)

            if conteudo_svg:
                zinfo_svg = zipfile.ZipInfo(filename="painel_climatizacao.svg", date_time=DATA_FIXA_ZIP)
                zinfo_svg.external_attr = 0o644 << 16
                zf.writestr(zinfo_svg, conteudo_svg.encode("utf-8"))

    return caminho
