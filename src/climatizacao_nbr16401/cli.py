"""Interface de linha de comando (CLI) em pt-BR para NBR 16401:2008.

Comandos:
- calcular: calcula balanço térmico, renovação de ar e dimensionamento do equipamento;
- catalogo: exibe tabelas normativas de cidades, atividades, renovação de ar e materiais;
- gerar-exemplo: cria modelo JSON representativo pronto para simulação.
"""

from __future__ import annotations

import argparse
from fractions import Fraction
import json
from pathlib import Path
import sys

from climatizacao_nbr16401 import __version__
from climatizacao_nbr16401.calculator import calcular_climatizacao_nbr16401
from climatizacao_nbr16401.codecs import (
    codificar_resultado_json,
    decodificar_espaco_json,
    espaco_para_dict,
)
from climatizacao_nbr16401.constants import (
    ATIVIDADES_METABOLICAS,
    CAPACIDADES_COMERCIAIS_BTU,
    CIDADES_CLIMATICAS_PROJETO,
    COEFICIENTES_TRANSMISSAO_U_W_M2_K,
    TAXAS_RENOVACAO_AR_EXTERIOR,
)
from climatizacao_nbr16401.exporters import (
    criar_pacote_zip_deterministico,
    formatar_fracao_decimal,
    gerar_csv_elementos,
    gerar_relatorio_texto,
)
from climatizacao_nbr16401.models import (
    CargaEquipamentos,
    CargaIluminacao,
    CargaOcupantes,
    ElementoEnvoltoria,
    EspacoClimatizado,
)
from climatizacao_nbr16401.svg_generator import gerar_painel_svg


def comando_catalogo(args: argparse.Namespace) -> int:
    """Exibe catálogo normativo de parâmetros da NBR 16401."""
    print("=" * 80)
    print("  CATÁLOGO NORMATIVO ABNT NBR 16401:2008 - CLIMATIZAÇÃO E AVAC")
    print("=" * 80)

    print("\n1. CIDADES E CONDIÇÕES CLIMÁTICAS EXTERNAS DE PROJETO (PARTE 1):")
    print(f"{'Código':<18} {'Nome':<25} {'TBS Ext (°C)':<15} {'Umidade (g/kg)':<15}")
    print("-" * 80)
    for chave, c in CIDADES_CLIMATICAS_PROJETO.items():
        print(
            f"{chave:<18} "
            f"{str(c['nome']):<25} "
            f"{formatar_fracao_decimal(Fraction(c['tbs_externa_c'])) + ' °C':<15} "
            f"{formatar_fracao_decimal(Fraction(c['umidade_externa_g_kg'])) + ' g/kg':<15}"
        )

    print("\n2. TAXAS MÍNIMAS DE RENOVAÇÃO DE AR EXTERIOR (PARTE 3 - QUALIDADE DO AR):")
    print(f"{'Código':<24} {'Nome':<36} {'Pessoa (m³/h)':<15} {'Área (m³/h/m²)'}")
    print("-" * 80)
    for chave, r in TAXAS_RENOVACAO_AR_EXTERIOR.items():
        print(
            f"{chave:<24} "
            f"{str(r['nome']):<36} "
            f"{formatar_fracao_decimal(Fraction(r['vazao_por_pessoa_m3_h'])) + ' m³/h':<15} "
            f"{formatar_fracao_decimal(Fraction(r['vazao_por_area_m3_h_m2'])) + ' m³/h/m²'}"
        )

    print("\n3. CARGA METABÓLICA HUMANA (PARTE 2 - CONFORTO TÉRMICO):")
    print(f"{'Atividade':<24} {'Nome':<36} {'Sensível (W)':<15} {'Latente (W)'}")
    print("-" * 80)
    for chave, a in ATIVIDADES_METABOLICAS.items():
        print(
            f"{chave:<24} "
            f"{str(a['nome']):<36} "
            f"{str(a['calor_sensivel_w']) + ' W':<15} "
            f"{str(a['calor_latente_w']) + ' W'}"
        )

    print("\n4. COEFICIENTES GLOBAIS DE TRANSMISSÃO TÉRMICA U (W/(m².K)):")
    print(f"{'Material':<38} {'U (W/(m².K))':<15} {'U (kcal/(h.m².°C))'}")
    print("-" * 80)
    for chave, u in COEFICIENTES_TRANSMISSAO_U_W_M2_K.items():
        from climatizacao_nbr16401.constants import FATOR_W_PARA_KCAL_H
        u_kcal = u * FATOR_W_PARA_KCAL_H
        print(
            f"{chave:<38} "
            f"{formatar_fracao_decimal(u) + ' W/m²K':<15} "
            f"{formatar_fracao_decimal(u_kcal) + ' kcal/h.m²°C'}"
        )

    print("\n5. CAPACIDADES COMERCIAIS PADRONIZADAS (BTU/h):")
    cap_str = ", ".join(f"{c:,} BTU/h".replace(",", ".") for c in CAPACIDADES_COMERCIAIS_BTU[:8])
    print(f"  {cap_str} ...")
    print("=" * 80)
    return 0


def comando_gerar_exemplo(args: argparse.Namespace) -> int:
    """Gera arquivo JSON de exemplo representativo."""
    tipo_raw = getattr(args, "tipo", "escritorio")
    tipo = str(tipo_raw).replace("-", "_")

    if tipo in ("comercio", "loja", "loja_comercial"):
        espaco = EspacoClimatizado(
            projeto="Loja Shopping Iguatemi - Pavimento Térreo",
            localidade="rio_de_janeiro",
            tipo_renovacao="loja_comercial",
            area_piso_m2=Fraction(120, 1),
            pe_direito_m=Fraction(35, 10),
            tbs_interna_desejada_c=Fraction(24, 1),
            umidade_interna_g_kg=Fraction(10, 1),
            ocupantes=CargaOcupantes(
                quantidade_pessoas=25,
                atividade="comercio_moderado",
            ),
            iluminacao=CargaIluminacao(
                potencia_total_w=Fraction(2400, 1),
                fator_uso=Fraction(1, 1),
            ),
            equipamentos=CargaEquipamentos(
                potencia_total_w=Fraction(1500, 1),
                fator_simultaneidade=Fraction(9, 10),
            ),
            envoltoria=(
                ElementoEnvoltoria(
                    nome="Fachada Vitrine Corredor",
                    tipo_material="vidro_simples_incolor_4mm",
                    area_m2=Fraction(35, 1),
                    orientacao="sul",
                    fator_solar_vidro="vidro_incolor_sem_protecao",
                ),
                ElementoEnvoltoria(
                    nome="Paredes Divisórias Laterais",
                    tipo_material="drywall_isolamento_la",
                    area_m2=Fraction(80, 1),
                    delta_t_especifico_c=Fraction(3, 1),
                ),
                ElementoEnvoltoria(
                    nome="Parede de Fundo (Depósito)",
                    tipo_material="alvenaria_bloco_concreto",
                    area_m2=Fraction(30, 1),
                    delta_t_especifico_c=Fraction(4, 1),
                ),
            ),
            fator_seguranca_pct=Fraction(10, 1),
        )
    elif tipo in ("restaurante", "restaurante_refeitorio"):
        espaco = EspacoClimatizado(
            projeto="Restaurante Jardins - Salão Principal",
            localidade="belo_horizonte",
            tipo_renovacao="restaurante_refeitorio",
            area_piso_m2=Fraction(150, 1),
            pe_direito_m=Fraction(32, 10),
            tbs_interna_desejada_c=Fraction(23, 1),
            umidade_interna_g_kg=Fraction(10, 1),
            ocupantes=CargaOcupantes(
                quantidade_pessoas=60,
                atividade="restaurante",
            ),
            iluminacao=CargaIluminacao(
                potencia_total_w=Fraction(1800, 1),
                fator_uso=Fraction(1, 1),
            ),
            equipamentos=CargaEquipamentos(
                potencia_total_w=Fraction(3000, 1),
                fator_simultaneidade=Fraction(85, 100),
            ),
            envoltoria=(
                ElementoEnvoltoria(
                    nome="Fachada Principal Envidraçada",
                    tipo_material="vidro_duplo_insulado_6mm",
                    area_m2=Fraction(40, 1),
                    orientacao="norte",
                    fator_solar_vidro="vidro_incolor_com_persiana_interna",
                ),
                ElementoEnvoltoria(
                    nome="Parede Externa Alvenaria",
                    tipo_material="alvenaria_tijolo_furado_reboco",
                    area_m2=Fraction(70, 1),
                    orientacao="leste",
                ),
                ElementoEnvoltoria(
                    nome="Divisória Cozinha Quente",
                    tipo_material="alvenaria_bloco_concreto",
                    area_m2=Fraction(45, 1),
                    delta_t_especifico_c=Fraction(8, 1),
                ),
            ),
            fator_seguranca_pct=Fraction(10, 1),
        )
    else:
        espaco = EspacoClimatizado(
            projeto="Edifício Corporativo Paulista - Escritório Open Space",
            localidade="sao_paulo",
            tipo_renovacao="escritorio_geral",
            area_piso_m2=Fraction(180, 1),
            pe_direito_m=Fraction(3, 1),
            tbs_interna_desejada_c=Fraction(24, 1),
            umidade_interna_g_kg=Fraction(10, 1),
            ocupantes=CargaOcupantes(
                quantidade_pessoas=20,
                atividade="escritorio_sentado",
            ),
            iluminacao=CargaIluminacao(
                potencia_total_w=Fraction(1600, 1),
                fator_uso=Fraction(1, 1),
            ),
            equipamentos=CargaEquipamentos(
                potencia_total_w=Fraction(3500, 1),
                fator_simultaneidade=Fraction(9, 10),
            ),
            envoltoria=(
                ElementoEnvoltoria(
                    nome="Fachada Envidraçada Leste",
                    tipo_material="vidro_simples_incolor_4mm",
                    area_m2=Fraction(45, 1),
                    orientacao="leste",
                    fator_solar_vidro="vidro_incolor_com_persiana_interna",
                ),
                ElementoEnvoltoria(
                    nome="Fachada Envidraçada Norte",
                    tipo_material="vidro_simples_incolor_4mm",
                    area_m2=Fraction(30, 1),
                    orientacao="norte",
                    fator_solar_vidro="vidro_incolor_com_persiana_interna",
                ),
                ElementoEnvoltoria(
                    nome="Paredes Externas Alvenaria",
                    tipo_material="alvenaria_tijolo_furado_reboco",
                    area_m2=Fraction(65, 1),
                    orientacao="leste",
                ),
                ElementoEnvoltoria(
                    nome="Divisórias Internas Hall",
                    tipo_material="drywall_isolamento_la",
                    area_m2=Fraction(50, 1),
                    delta_t_especifico_c=Fraction(2, 1),
                ),
            ),
            fator_seguranca_pct=Fraction(10, 1),
        )

    saida = json.dumps(espaco_para_dict(espaco), indent=2, sort_keys=True, ensure_ascii=False) + "\n"

    caminho_saida = getattr(args, "saida", None)
    if caminho_saida:
        p = Path(caminho_saida).resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(saida, encoding="utf-8")
        print(f"Exemplo gravado com sucesso em '{p}'.")
    else:
        sys.stdout.write(saida)
    return 0


def comando_calcular(args: argparse.Namespace) -> int:
    """Executa o cálculo e dimensionamento de climatização."""
    caminho_entrada = Path(args.arquivo).resolve()
    if not caminho_entrada.exists():
        sys.stderr.write(f"Erro: arquivo de entrada '{caminho_entrada}' não encontrado.\n")
        return 1

    try:
        conteudo = caminho_entrada.read_text(encoding="utf-8")
        espaco = decodificar_espaco_json(conteudo)
        resultado = calcular_climatizacao_nbr16401(espaco)
    except Exception as exc:
        sys.stderr.write(f"Erro no processamento térmico: {exc}\n")
        return 2

    relatorio_txt = gerar_relatorio_texto(resultado)

    if getattr(args, "saida_txt", None):
        p_txt = Path(args.saida_txt).resolve()
        p_txt.parent.mkdir(parents=True, exist_ok=True)
        p_txt.write_text(relatorio_txt, encoding="utf-8")
        print(f"[TXT] Relatório gravado em '{p_txt}'")

    if getattr(args, "saida_json", None):
        p_json = Path(args.saida_json).resolve()
        p_json.parent.mkdir(parents=True, exist_ok=True)
        p_json.write_text(codificar_resultado_json(resultado), encoding="utf-8")
        print(f"[JSON] Resultado gravado em '{p_json}'")

    if getattr(args, "saida_csv", None):
        p_csv = Path(args.saida_csv).resolve()
        p_csv.parent.mkdir(parents=True, exist_ok=True)
        p_csv.write_text(gerar_csv_elementos(resultado), encoding="utf-8")
        print(f"[CSV] Planilha de elementos gravada em '{p_csv}'")

    svg_conteudo: str | None = None
    if getattr(args, "saida_svg", None) or getattr(args, "pacote_zip", None) or getattr(args, "formato", None) in ("svg", "zip"):
        svg_conteudo = gerar_painel_svg(resultado)

    if getattr(args, "saida_svg", None) and svg_conteudo:
        p_svg = Path(args.saida_svg).resolve()
        p_svg.parent.mkdir(parents=True, exist_ok=True)
        p_svg.write_text(svg_conteudo, encoding="utf-8")
        print(f"[SVG] Painel executivo gravado em '{p_svg}'")

    if getattr(args, "pacote_zip", None):
        p_zip = Path(args.pacote_zip).resolve()
        criar_pacote_zip_deterministico(
            p_zip,
            resultado,
            conteudo_svg=svg_conteudo,
            sobrescrever=True,
        )
        print(f"[ZIP] Pacote determinístico gerado em '{p_zip}'")

    formato = getattr(args, "formato", "texto")
    saida_especifica = getattr(args, "saida", None)

    if formato == "json":
        json_out = codificar_resultado_json(resultado)
        if saida_especifica:
            Path(saida_especifica).write_text(json_out, encoding="utf-8")
        else:
            print(json_out)
    elif formato == "csv":
        csv_out = gerar_csv_elementos(resultado)
        if saida_especifica:
            Path(saida_especifica).write_text(csv_out, encoding="utf-8")
        else:
            print(csv_out)
    elif formato == "svg":
        if not svg_conteudo:
            svg_conteudo = gerar_painel_svg(resultado)
        if saida_especifica:
            Path(saida_especifica).write_text(svg_conteudo, encoding="utf-8")
        else:
            print(svg_conteudo)
    elif formato == "zip":
        if saida_especifica:
            criar_pacote_zip_deterministico(saida_especifica, resultado, conteudo_svg=svg_conteudo, sobrescrever=True)
        else:
            sys.stderr.write("Aviso: formato 'zip' requer especificar --saida <caminho.zip>\n")
    else:
        if saida_especifica:
            Path(saida_especifica).write_text(relatorio_txt, encoding="utf-8")
        else:
            print(relatorio_txt)

    return 0


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada principal da CLI."""
    parser = argparse.ArgumentParser(
        prog="climatizacao-nbr16401",
        description="Dimensionamento de Climatização e Ar-Condicionado - ABNT NBR 16401:2008",
    )
    parser.add_argument(
        "--versao",
        "-v",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Exibe a versão instalada do programa.",
    )
    subparsers = parser.add_subparsers(dest="comando", required=True)

    # Subcomando 'calcular'
    parser_calc = subparsers.add_parser("calcular", help="Calcula balanço térmico a partir de arquivo JSON")
    parser_calc.add_argument("arquivo", help="Caminho do arquivo JSON de espaço climatizado")
    parser_calc.add_argument(
        "--formato",
        "-f",
        choices=["texto", "json", "csv", "svg", "zip"],
        default="texto",
        help="Formato do resultado de saída (padrão: texto).",
    )
    parser_calc.add_argument(
        "--saida",
        "-o",
        help="Arquivo de destino (se omitido, imprime no terminal).",
    )
    parser_calc.add_argument("--saida-json", help="Exporta resultado em formato JSON RFC 8259")
    parser_calc.add_argument("--saida-txt", help="Exporta relatório técnico executivo em texto puro")
    parser_calc.add_argument("--saida-csv", help="Exporta tabela de elementos térmicos em CSV")
    parser_calc.add_argument("--saida-svg", help="Exporta painel vetorial executivo 1440x900 em SVG")
    parser_calc.add_argument("--pacote-zip", help="Gera pacote determinístico completo em arquivo ZIP")
    parser_calc.set_defaults(funcao=comando_calcular)

    # Subcomando 'catalogo'
    parser_cat = subparsers.add_parser("catalogo", help="Exibe parâmetros normativos da NBR 16401")
    parser_cat.set_defaults(funcao=comando_catalogo)

    # Subcomando 'gerar-exemplo'
    parser_ex = subparsers.add_parser("gerar-exemplo", help="Gera arquivo de entrada JSON de exemplo")
    parser_ex.add_argument(
        "--tipo",
        default="escritorio",
        help="Tipo de ambiente de exemplo (ex: escritorio, comercio, restaurante)",
    )
    parser_ex.add_argument("--saida", help="Caminho de saída para o arquivo JSON gerado")
    parser_ex.set_defaults(funcao=comando_gerar_exemplo)

    args = parser.parse_args(argv)
    return int(args.funcao(args))


if __name__ == "__main__":
    sys.exit(main())
