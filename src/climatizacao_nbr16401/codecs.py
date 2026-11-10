"""Codificadores e decodificadores canônicos JSON para climatização NBR 16401:2008.

Garante conformidade RFC 8259:
- Rejeição estrita de BOM (\ufeff / \xef\xbb\xbf);
- Rejeição de chaves duplicadas no parsing;
- Rejeição de números de ponto flutuante IEEE-754 no parsing de entrada;
- Limite estrito de profundidade recursiva (máx 32);
- Serialização determinística com ordenação alfabética de chaves e indentação.
"""

from __future__ import annotations

from fractions import Fraction
import json
from typing import Any

from climatizacao_nbr16401.models import (
    CargaEquipamentos,
    CargaIluminacao,
    CargaOcupantes,
    ElementoEnvoltoria,
    EspacoClimatizado,
    ResultadoCargaTermica,
    ResultadoElementoEnvoltoria,
)

PROFUNDIDADE_MAXIMA_JSON = 32


def parse_fracao_ou_int(val: Any, campo: str) -> Fraction:
    """Converte int, str fracionária ('22/10') ou str decimal ('2.2') em Fraction exata.

    Rejeita terminantemente float nativo.
    """
    if isinstance(val, float):
        raise TypeError(
            f"Valor de ponto flutuante float proibido no campo '{campo}'. "
            f"Forneça inteiro ou string exata (ex: '22/10' ou '2.2')."
        )
    if isinstance(val, int):
        return Fraction(val, 1)
    if isinstance(val, str):
        val_limpo = val.strip()
        if not val_limpo:
            raise ValueError(f"Campo '{campo}' não pode ser string vazia.")
        try:
            return Fraction(val_limpo)
        except (ValueError, ZeroDivisionError) as exc:
            raise ValueError(f"Valor numérico inválido '{val}' no campo '{campo}': {exc}") from exc
    raise TypeError(
        f"Tipo inválido para '{campo}': {type(val).__name__}. Esperado int ou str."
    )


def _verificar_profundidade(obj: Any, nivel: int = 1) -> None:
    if nivel > PROFUNDIDADE_MAXIMA_JSON:
        raise ValueError(
            f"Profundidade de aninhamento JSON ({nivel}) excede o limite máximo permitido ({PROFUNDIDADE_MAXIMA_JSON})."
        )
    if isinstance(obj, dict):
        for v in obj.values():
            _verificar_profundidade(v, nivel + 1)
    elif isinstance(obj, list):
        for item in obj:
            _verificar_profundidade(item, nivel + 1)


def _pares_sem_duplicadas(pares: list[tuple[str, Any]]) -> dict[str, Any]:
    resultado: dict[str, Any] = {}
    for chave, valor in pares:
        if chave in resultado:
            raise ValueError(f"Chave duplicada detectada no JSON: '{chave}'.")
        resultado[chave] = valor
    return resultado


def decodificar_espaco_json(texto: str | bytes) -> EspacoClimatizado:
    """Decodifica JSON para EspacoClimatizado com validações rigorosas."""
    if isinstance(texto, bytes):
        if texto.startswith(b"\xef\xbb\xbf"):
            raise ValueError("BOM UTF-8 proibido no payload JSON.")
        texto_str = texto.decode("utf-8")
    else:
        if texto.startswith("\ufeff"):
            raise ValueError("BOM UTF-8 proibido no payload JSON.")
        texto_str = texto

    dados = json.loads(
        texto_str,
        object_pairs_hook=_pares_sem_duplicadas,
        parse_float=lambda s: (_ for _ in ()).throw(
            TypeError(f"Float '{s}' proibido. Utilize string fracionária ou decimal exata.")
        ),
    )

    _verificar_profundidade(dados)

    if not isinstance(dados, dict):
        raise TypeError("Payload JSON de espaço climatizado deve ser um objeto dicionário.")

    projeto = str(dados.get("projeto", "")).strip()
    localidade = str(dados.get("localidade", "")).strip()
    tipo_renovacao = str(dados.get("tipo_renovacao", "")).strip()
    area_piso_m2 = parse_fracao_ou_int(dados.get("area_piso_m2"), "area_piso_m2")
    pe_direito_m = parse_fracao_ou_int(dados.get("pe_direito_m"), "pe_direito_m")

    tbs_interna = parse_fracao_ou_int(dados.get("tbs_interna_desejada_c", "24"), "tbs_interna_desejada_c")
    umidade_interna = parse_fracao_ou_int(dados.get("umidade_interna_g_kg", "10"), "umidade_interna_g_kg")
    fator_seguranca = parse_fracao_ou_int(dados.get("fator_seguranca_pct", "10"), "fator_seguranca_pct")

    # Ocupantes
    ocup_raw = dados.get("ocupantes")
    if not isinstance(ocup_raw, dict):
        raise ValueError("Configuração 'ocupantes' deve ser um objeto JSON.")
    ocupantes = CargaOcupantes(
        quantidade_pessoas=int(ocup_raw.get("quantidade_pessoas", 0)),
        atividade=str(ocup_raw.get("atividade", "")).strip(),
    )

    # Iluminação
    ilum_raw = dados.get("iluminacao")
    if not isinstance(ilum_raw, dict):
        raise ValueError("Configuração 'iluminacao' deve ser um objeto JSON.")
    iluminacao = CargaIluminacao(
        potencia_total_w=parse_fracao_ou_int(ilum_raw.get("potencia_total_w"), "iluminacao.potencia_total_w"),
        fator_uso=parse_fracao_ou_int(ilum_raw.get("fator_uso", "1"), "iluminacao.fator_uso"),
    )

    # Equipamentos
    equip_raw = dados.get("equipamentos")
    if not isinstance(equip_raw, dict):
        raise ValueError("Configuração 'equipamentos' deve ser um objeto JSON.")
    equipamentos = CargaEquipamentos(
        potencia_total_w=parse_fracao_ou_int(equip_raw.get("potencia_total_w"), "equipamentos.potencia_total_w"),
        fator_simultaneidade=parse_fracao_ou_int(equip_raw.get("fator_simultaneidade", "9/10"), "equipamentos.fator_simultaneidade"),
    )

    # Envoltória
    env_raw = dados.get("envoltoria")
    if not isinstance(env_raw, list):
        raise ValueError("Lista 'envoltoria' deve ser um array JSON.")

    lista_envoltoria: list[ElementoEnvoltoria] = []
    for idx, el in enumerate(env_raw):
        if not isinstance(el, dict):
            raise ValueError(f"Elemento da envoltória índice {idx} deve ser um objeto JSON.")

        nome = str(el.get("nome", "")).strip()
        tipo_material = str(el.get("tipo_material", "")).strip()
        area_m2 = parse_fracao_ou_int(el.get("area_m2"), f"envoltoria[{idx}].area_m2")

        orientacao = el.get("orientacao")
        orientacao_str = str(orientacao).strip() if orientacao is not None else None

        fator_solar = el.get("fator_solar_vidro")
        fator_solar_str = str(fator_solar).strip() if fator_solar is not None else None

        delta_t_esp = el.get("delta_t_especifico_c")
        delta_t_frac = parse_fracao_ou_int(delta_t_esp, f"envoltoria[{idx}].delta_t_especifico_c") if delta_t_esp is not None else None

        lista_envoltoria.append(
            ElementoEnvoltoria(
                nome=nome,
                tipo_material=tipo_material,
                area_m2=area_m2,
                orientacao=orientacao_str,
                fator_solar_vidro=fator_solar_str,
                delta_t_especifico_c=delta_t_frac,
            )
        )

    return EspacoClimatizado(
        projeto=projeto,
        localidade=localidade,
        tipo_renovacao=tipo_renovacao,
        area_piso_m2=area_piso_m2,
        pe_direito_m=pe_direito_m,
        ocupantes=ocupantes,
        iluminacao=iluminacao,
        equipamentos=equipamentos,
        envoltoria=tuple(lista_envoltoria),
        tbs_interna_desejada_c=tbs_interna,
        umidade_interna_g_kg=umidade_interna,
        fator_seguranca_pct=fator_seguranca,
    )


def espaco_para_dict(espaco: EspacoClimatizado) -> dict[str, Any]:
    """Serializa EspacoClimatizado em dicionário canônico."""
    return {
        "projeto": espaco.projeto,
        "localidade": espaco.localidade,
        "tipo_renovacao": espaco.tipo_renovacao,
        "area_piso_m2": str(espaco.area_piso_m2),
        "pe_direito_m": str(espaco.pe_direito_m),
        "tbs_interna_desejada_c": str(espaco.tbs_interna_desejada_c),
        "umidade_interna_g_kg": str(espaco.umidade_interna_g_kg),
        "fator_seguranca_pct": str(espaco.fator_seguranca_pct),
        "ocupantes": {
            "quantidade_pessoas": espaco.ocupantes.quantidade_pessoas,
            "atividade": espaco.ocupantes.atividade,
        },
        "iluminacao": {
            "potencia_total_w": str(espaco.iluminacao.potencia_total_w),
            "fator_uso": str(espaco.iluminacao.fator_uso),
        },
        "equipamentos": {
            "potencia_total_w": str(espaco.equipamentos.potencia_total_w),
            "fator_simultaneidade": str(espaco.equipamentos.fator_simultaneidade),
        },
        "envoltoria": [
            {
                "nome": el.nome,
                "tipo_material": el.tipo_material,
                "area_m2": str(el.area_m2),
                "orientacao": el.orientacao,
                "fator_solar_vidro": el.fator_solar_vidro,
                "delta_t_especifico_c": str(el.delta_t_especifico_c) if el.delta_t_especifico_c is not None else None,
            }
            for el in espaco.envoltoria
        ],
    }


def resultado_para_dict(res: ResultadoCargaTermica) -> dict[str, Any]:
    """Serializa ResultadoCargaTermica em dicionário canônico."""
    return {
        "projeto": res.projeto,
        "localidade_codigo": res.localidade_codigo,
        "localidade_nome": res.localidade_nome,
        "tbs_externa_c": str(res.tbs_externa_c),
        "tbs_interna_c": str(res.tbs_interna_c),
        "delta_t_c": str(res.delta_t_c),
        "calor_conducao_total_kcal_h": str(res.calor_conducao_total_kcal_h),
        "calor_solar_total_kcal_h": str(res.calor_solar_total_kcal_h),
        "calor_pessoas_sensivel_kcal_h": str(res.calor_pessoas_sensivel_kcal_h),
        "calor_pessoas_latente_kcal_h": str(res.calor_pessoas_latente_kcal_h),
        "calor_iluminacao_kcal_h": str(res.calor_iluminacao_kcal_h),
        "calor_equipamentos_kcal_h": str(res.calor_equipamentos_kcal_h),
        "vazao_ar_renovacao_m3_h": str(res.vazao_ar_renovacao_m3_h),
        "calor_ar_externo_sensivel_kcal_h": str(res.calor_ar_externo_sensivel_kcal_h),
        "calor_ar_externo_latente_kcal_h": str(res.calor_ar_externo_latente_kcal_h),
        "calor_sensivel_subtotal_kcal_h": str(res.calor_sensivel_subtotal_kcal_h),
        "calor_latente_subtotal_kcal_h": str(res.calor_latente_subtotal_kcal_h),
        "fator_seguranca_pct": str(res.fator_seguranca_pct),
        "calor_sensivel_total_kcal_h": str(res.calor_sensivel_total_kcal_h),
        "calor_latente_total_kcal_h": str(res.calor_latente_total_kcal_h),
        "carga_termica_total_kcal_h": str(res.carga_termica_total_kcal_h),
        "carga_termica_total_btu_h": str(res.carga_termica_total_btu_h),
        "carga_termica_total_tr": str(res.carga_termica_total_tr),
        "fator_calor_sensivel": str(res.fator_calor_sensivel),
        "vazao_ar_insuflado_m3_h": str(res.vazao_ar_insuflado_m3_h),
        "capacidade_comercial_btu_h": res.capacidade_comercial_btu_h,
        "capacidade_comercial_tr": str(res.capacidade_comercial_tr),
        "observacoes": list(res.observacoes),
        "elementos": [
            {
                "nome": el.nome,
                "tipo_material": el.tipo_material,
                "area_m2": str(el.area_m2),
                "u_w_m2_k": str(el.u_w_m2_k),
                "u_kcal_h_m2_c": str(el.u_kcal_h_m2_c),
                "delta_t_c": str(el.delta_t_c),
                "calor_conducao_kcal_h": str(el.calor_conducao_kcal_h),
                "calor_solar_kcal_h": str(el.calor_solar_kcal_h),
                "calor_total_kcal_h": str(el.calor_total_kcal_h),
            }
            for el in res.elementos
        ],
    }


def codificar_resultado_json(res: ResultadoCargaTermica) -> str:
    """Serializa ResultadoCargaTermica em JSON RFC 8259 formatado."""
    dados = resultado_para_dict(res)
    return json.dumps(dados, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
