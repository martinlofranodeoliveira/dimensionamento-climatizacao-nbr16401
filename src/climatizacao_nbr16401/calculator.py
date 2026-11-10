"""Motor de cálculo de carga térmica e renovação de ar conforme ABNT NBR 16401:2008.

Implementa balanço térmico de verão para regime de resfriamento permanente:
- Condução e radiação solar através da envoltória;
- Cargas internas de ocupação (sensível e latente);
- Cargas internas de iluminação e equipamentos;
- Renovação de ar exterior conforme NBR 16401-3 (taxa por pessoa e área);
- Vazão de ar insuflado e seleção de capacidade comercial de ar-condicionado.
Aritmética estritamente racional exata (Fraction e inteiros). Zero float.
"""

from __future__ import annotations

from fractions import Fraction

from climatizacao_nbr16401.constants import (
    ATIVIDADES_METABOLICAS,
    BTU_POR_TR,
    CALOR_LATENTE_AR_KCAL_M3_G_KG,
    CALOR_VOLUMETRICO_AR_KCAL_M3_C,
    CAPACIDADES_COMERCIAIS_BTU,
    CIDADES_CLIMATICAS_PROJETO,
    COEFICIENTES_TRANSMISSAO_U_W_M2_K,
    FATOR_KCAL_PARA_BTU,
    FATOR_SOLAR_VIDROS,
    FATOR_W_PARA_KCAL_H,
    KCAL_POR_TR,
    RADIACAO_SOLAR_FACHADA_W_M2,
    TAXAS_RENOVACAO_AR_EXTERIOR,
)
from climatizacao_nbr16401.models import (
    EspacoClimatizado,
    ResultadoCargaTermica,
    ResultadoElementoEnvoltoria,
)


def calcular_climatizacao_nbr16401(espaco: EspacoClimatizado) -> ResultadoCargaTermica:
    """Calcula o balanço térmico completo e vazões de renovação e insuflamento."""
    # 1. Validações de parâmetros normativos
    if espaco.localidade not in CIDADES_CLIMATICAS_PROJETO:
        cidades_validas = ", ".join(CIDADES_CLIMATICAS_PROJETO.keys())
        raise ValueError(f"Localidade '{espaco.localidade}' inválida. Opções: {cidades_validas}.")

    if espaco.tipo_renovacao not in TAXAS_RENOVACAO_AR_EXTERIOR:
        taxas_validas = ", ".join(TAXAS_RENOVACAO_AR_EXTERIOR.keys())
        raise ValueError(f"Tipo de renovação '{espaco.tipo_renovacao}' inválido. Opções: {taxas_validas}.")

    if espaco.ocupantes.atividade not in ATIVIDADES_METABOLICAS:
        ativ_validas = ", ".join(ATIVIDADES_METABOLICAS.keys())
        raise ValueError(f"Atividade '{espaco.ocupantes.atividade}' inválida. Opções: {ativ_validas}.")

    info_cidade = CIDADES_CLIMATICAS_PROJETO[espaco.localidade]
    nome_cidade = str(info_cidade["nome"])
    tbs_ext = Fraction(info_cidade["tbs_externa_c"])
    umidade_ext = Fraction(info_cidade["umidade_externa_g_kg"])

    tbs_int = espaco.tbs_interna_desejada_c
    delta_t_padrao = max(Fraction(0, 1), tbs_ext - tbs_int)
    delta_w = max(Fraction(0, 1), umidade_ext - espaco.umidade_interna_g_kg)

    # 2. Cargas da Envoltória (Paredes, Coberturas, Vidros)
    resultados_elementos: list[ResultadoElementoEnvoltoria] = []
    calor_conducao_total = Fraction(0, 1)
    calor_solar_total = Fraction(0, 1)

    for el in espaco.envoltoria:
        if el.tipo_material not in COEFICIENTES_TRANSMISSAO_U_W_M2_K:
            materiais_validos = ", ".join(COEFICIENTES_TRANSMISSAO_U_W_M2_K.keys())
            raise ValueError(
                f"Material '{el.tipo_material}' do elemento '{el.nome}' inválido. Opções: {materiais_validos}."
            )

        u_w = COEFICIENTES_TRANSMISSAO_U_W_M2_K[el.tipo_material]
        u_kcal = u_w * FATOR_W_PARA_KCAL_H

        delta_t_el = el.delta_t_especifico_c if el.delta_t_especifico_c is not None else delta_t_padrao
        delta_t_el = max(Fraction(0, 1), delta_t_el)

        q_cond = u_kcal * el.area_m2 * delta_t_el

        # Radiação solar em vidros ou elementos expostos
        q_solar = Fraction(0, 1)
        if el.orientacao is not None:
            if el.orientacao not in RADIACAO_SOLAR_FACHADA_W_M2:
                orientacoes_validas = ", ".join(RADIACAO_SOLAR_FACHADA_W_M2.keys())
                raise ValueError(
                    f"Orientação '{el.orientacao}' no elemento '{el.nome}' inválida. Opções: {orientacoes_validas}."
                )
            rad_w_m2 = RADIACAO_SOLAR_FACHADA_W_M2[el.orientacao]

            fator_solar = Fraction(1, 1)
            if el.fator_solar_vidro is not None:
                if el.fator_solar_vidro not in FATOR_SOLAR_VIDROS:
                    fs_validos = ", ".join(FATOR_SOLAR_VIDROS.keys())
                    raise ValueError(
                        f"Fator solar '{el.fator_solar_vidro}' inválido. Opções: {fs_validos}."
                    )
                fator_solar = FATOR_SOLAR_VIDROS[el.fator_solar_vidro]
                q_solar = el.area_m2 * rad_w_m2 * fator_solar * FATOR_W_PARA_KCAL_H

        q_total_el = q_cond + q_solar
        calor_conducao_total += q_cond
        calor_solar_total += q_solar

        resultados_elementos.append(
            ResultadoElementoEnvoltoria(
                nome=el.nome,
                tipo_material=el.tipo_material,
                area_m2=el.area_m2,
                u_w_m2_k=u_w,
                u_kcal_h_m2_c=u_kcal,
                delta_t_c=delta_t_el,
                calor_conducao_kcal_h=q_cond,
                calor_solar_kcal_h=q_solar,
                calor_total_kcal_h=q_total_el,
            )
        )

    # 3. Carga Interna de Ocupantes (sensível e latente)
    info_ativ = ATIVIDADES_METABOLICAS[espaco.ocupantes.atividade]
    qs_pessoa_w = Fraction(info_ativ["calor_sensivel_w"])
    ql_pessoa_w = Fraction(info_ativ["calor_latente_w"])
    n_pessoas = Fraction(espaco.ocupantes.quantidade_pessoas, 1)

    calor_pessoas_sensivel = n_pessoas * qs_pessoa_w * FATOR_W_PARA_KCAL_H
    calor_pessoas_latente = n_pessoas * ql_pessoa_w * FATOR_W_PARA_KCAL_H

    # 4. Carga de Iluminação (100% sensível)
    calor_iluminacao = espaco.iluminacao.potencia_total_w * espaco.iluminacao.fator_uso * FATOR_W_PARA_KCAL_H

    # 5. Carga de Equipamentos (100% sensível)
    calor_equipamentos = espaco.equipamentos.potencia_total_w * espaco.equipamentos.fator_simultaneidade * FATOR_W_PARA_KCAL_H

    # 6. Renovação de Ar Exterior (NBR 16401-3)
    info_renov = TAXAS_RENOVACAO_AR_EXTERIOR[espaco.tipo_renovacao]
    taxa_pessoa = Fraction(info_renov["vazao_por_pessoa_m3_h"])
    taxa_area = Fraction(info_renov["vazao_por_area_m3_h_m2"])

    vazao_ar_pessoas = n_pessoas * taxa_pessoa
    vazao_ar_area = espaco.area_piso_m2 * taxa_area
    vazao_ar_renovacao = max(vazao_ar_pessoas, vazao_ar_area)

    calor_ar_ext_sensivel = CALOR_VOLUMETRICO_AR_KCAL_M3_C * vazao_ar_renovacao * delta_t_padrao
    calor_ar_ext_latente = CALOR_LATENTE_AR_KCAL_M3_G_KG * vazao_ar_renovacao * delta_w

    # 7. Subtotais e Aplicação do Fator de Segurança
    calor_sensivel_subtotal = (
        calor_conducao_total
        + calor_solar_total
        + calor_pessoas_sensivel
        + calor_iluminacao
        + calor_equipamentos
        + calor_ar_ext_sensivel
    )
    calor_latente_subtotal = calor_pessoas_latente + calor_ar_ext_latente

    fator_seguranca = Fraction(1, 1) + (espaco.fator_seguranca_pct / Fraction(100, 1))
    calor_sensivel_total = calor_sensivel_subtotal * fator_seguranca
    calor_latente_total = calor_latente_subtotal * fator_seguranca

    carga_termica_total_kcal_h = calor_sensivel_total + calor_latente_total
    carga_termica_total_btu_h = carga_termica_total_kcal_h * FATOR_KCAL_PARA_BTU
    carga_termica_total_tr = carga_termica_total_kcal_h / Fraction(KCAL_POR_TR, 1)

    fator_calor_sensivel = (
        calor_sensivel_total / carga_termica_total_kcal_h
        if carga_termica_total_kcal_h > 0
        else Fraction(1, 1)
    )

    # 8. Vazão de Ar Insuflado (Delta T de insuflamento padrão de 10 °C)
    delta_t_insuflamento = Fraction(10, 1)
    vazao_ar_insuflado_m3_h = (
        calor_sensivel_total / (CALOR_VOLUMETRICO_AR_KCAL_M3_C * delta_t_insuflamento)
        if calor_sensivel_total > 0
        else Fraction(0, 1)
    )

    # 9. Seleção de Capacidade Comercial de Ar-Condicionado em BTU/h
    capacidade_comercial_btu = CAPACIDADES_COMERCIAIS_BTU[-1]
    for cap in CAPACIDADES_COMERCIAIS_BTU:
        if Fraction(cap, 1) >= carga_termica_total_btu_h:
            capacidade_comercial_btu = cap
            break

    capacidade_comercial_tr = Fraction(capacidade_comercial_btu, BTU_POR_TR)

    observacoes: list[str] = [
        f"Projeto dimensionado rigorosamente conforme ABNT NBR 16401:2008 (Partes 1, 2 e 3).",
        f"Condições externas de projeto para {nome_cidade}: TBS = {tbs_ext} °C, w = {umidade_ext} g/kg.",
        f"Renovação de ar exterior: {vazao_ar_renovacao} m³/h adotada (maior entre taxa por pessoas e por área).",
    ]

    return ResultadoCargaTermica(
        projeto=espaco.projeto,
        localidade_codigo=espaco.localidade,
        localidade_nome=nome_cidade,
        tbs_externa_c=tbs_ext,
        tbs_interna_c=tbs_int,
        delta_t_c=delta_t_padrao,
        elementos=tuple(resultados_elementos),
        calor_conducao_total_kcal_h=calor_conducao_total,
        calor_solar_total_kcal_h=calor_solar_total,
        calor_pessoas_sensivel_kcal_h=calor_pessoas_sensivel,
        calor_pessoas_latente_kcal_h=calor_pessoas_latente,
        calor_iluminacao_kcal_h=calor_iluminacao,
        calor_equipamentos_kcal_h=calor_equipamentos,
        vazao_ar_renovacao_m3_h=vazao_ar_renovacao,
        calor_ar_externo_sensivel_kcal_h=calor_ar_ext_sensivel,
        calor_ar_externo_latente_kcal_h=calor_ar_ext_latente,
        calor_sensivel_subtotal_kcal_h=calor_sensivel_subtotal,
        calor_latente_subtotal_kcal_h=calor_latente_subtotal,
        fator_seguranca_pct=espaco.fator_seguranca_pct,
        calor_sensivel_total_kcal_h=calor_sensivel_total,
        calor_latente_total_kcal_h=calor_latente_total,
        carga_termica_total_kcal_h=carga_termica_total_kcal_h,
        carga_termica_total_btu_h=carga_termica_total_btu_h,
        carga_termica_total_tr=carga_termica_total_tr,
        fator_calor_sensivel=fator_calor_sensivel,
        vazao_ar_insuflado_m3_h=vazao_ar_insuflado_m3_h,
        capacidade_comercial_btu_h=capacidade_comercial_btu,
        capacidade_comercial_tr=capacidade_comercial_tr,
        observacoes=tuple(observacoes),
    )
