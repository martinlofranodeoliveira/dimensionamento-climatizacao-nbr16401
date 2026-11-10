"""Modelos de dados imutáveis para cálculo de climatização NBR 16401:2008.

Garante imutabilidade (frozen=True) e tipagem rigorosa com Fraction e inteiros.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction


@dataclass(frozen=True)
class ElementoEnvoltoria:
    """Superfície da envoltória (parede, cobertura, divisória ou vidro)."""

    nome: str
    tipo_material: str
    area_m2: Fraction
    orientacao: str | None = None
    fator_solar_vidro: str | None = None
    delta_t_especifico_c: Fraction | None = None

    def __post_init__(self) -> None:
        if not self.nome.strip():
            raise ValueError("O nome do elemento da envoltória não pode ser vazio.")
        if self.area_m2 <= 0:
            raise ValueError(f"Área do elemento '{self.nome}' deve ser estritamente positiva.")


@dataclass(frozen=True)
class CargaOcupantes:
    """Carga interna gerada pela ocupação humana."""

    quantidade_pessoas: int
    atividade: str

    def __post_init__(self) -> None:
        if self.quantidade_pessoas < 0:
            raise ValueError("Quantidade de pessoas não pode ser negativa.")


@dataclass(frozen=True)
class CargaIluminacao:
    """Carga térmica gerada pelo sistema de iluminação artificial."""

    potencia_total_w: Fraction
    fator_uso: Fraction = Fraction(1, 1)

    def __post_init__(self) -> None:
        if self.potencia_total_w < 0:
            raise ValueError("Potência de iluminação não pode ser negativa.")
        if self.fator_uso <= 0 or self.fator_uso > 2:
            raise ValueError("Fator de uso de iluminação deve estar no intervalo (0, 2].")


@dataclass(frozen=True)
class CargaEquipamentos:
    """Carga térmica gerada por computadores, eletrodomésticos e servidores."""

    potencia_total_w: Fraction
    fator_simultaneidade: Fraction = Fraction(9, 10)

    def __post_init__(self) -> None:
        if self.potencia_total_w < 0:
            raise ValueError("Potência de equipamentos não pode ser negativa.")
        if self.fator_simultaneidade <= 0 or self.fator_simultaneidade > 1:
            raise ValueError("Fator de simultaneidade deve estar no intervalo (0, 1].")


@dataclass(frozen=True)
class EspacoClimatizado:
    """Definição do recinto a ser condicionado termicamente."""

    projeto: str
    localidade: str
    tipo_renovacao: str
    area_piso_m2: Fraction
    pe_direito_m: Fraction
    ocupantes: CargaOcupantes
    iluminacao: CargaIluminacao
    equipamentos: CargaEquipamentos
    envoltoria: tuple[ElementoEnvoltoria, ...]
    tbs_interna_desejada_c: Fraction = Fraction(24, 1)
    umidade_interna_g_kg: Fraction = Fraction(10, 1)
    fator_seguranca_pct: Fraction = Fraction(10, 1)

    def __post_init__(self) -> None:
        if not self.projeto.strip():
            raise ValueError("O nome do projeto não pode ser vazio.")
        if self.area_piso_m2 <= 0:
            raise ValueError("A área do piso deve ser estritamente positiva.")
        if self.pe_direito_m <= 0:
            raise ValueError("O pé-direito deve ser estritamente positivo.")
        if len(self.envoltoria) == 0:
            raise ValueError("A envoltória do espaço deve conter pelo menos um elemento construtivo.")
        if self.fator_seguranca_pct < 0:
            raise ValueError("O fator de segurança não pode ser negativo.")


@dataclass(frozen=True)
class ResultadoElementoEnvoltoria:
    """Parcelas térmicas de um elemento específico da envoltória."""

    nome: str
    tipo_material: str
    area_m2: Fraction
    u_w_m2_k: Fraction
    u_kcal_h_m2_c: Fraction
    delta_t_c: Fraction
    calor_conducao_kcal_h: Fraction
    calor_solar_kcal_h: Fraction
    calor_total_kcal_h: Fraction


@dataclass(frozen=True)
class ResultadoCargaTermica:
    """Balanço térmico consolidado do espaço condicionado."""

    projeto: str
    localidade_codigo: str
    localidade_nome: str
    tbs_externa_c: Fraction
    tbs_interna_c: Fraction
    delta_t_c: Fraction
    elementos: tuple[ResultadoElementoEnvoltoria, ...]
    calor_conducao_total_kcal_h: Fraction
    calor_solar_total_kcal_h: Fraction
    calor_pessoas_sensivel_kcal_h: Fraction
    calor_pessoas_latente_kcal_h: Fraction
    calor_iluminacao_kcal_h: Fraction
    calor_equipamentos_kcal_h: Fraction
    vazao_ar_renovacao_m3_h: Fraction
    calor_ar_externo_sensivel_kcal_h: Fraction
    calor_ar_externo_latente_kcal_h: Fraction
    calor_sensivel_subtotal_kcal_h: Fraction
    calor_latente_subtotal_kcal_h: Fraction
    fator_seguranca_pct: Fraction
    calor_sensivel_total_kcal_h: Fraction
    calor_latente_total_kcal_h: Fraction
    carga_termica_total_kcal_h: Fraction
    carga_termica_total_btu_h: Fraction
    carga_termica_total_tr: Fraction
    fator_calor_sensivel: Fraction
    vazao_ar_insuflado_m3_h: Fraction
    capacidade_comercial_btu_h: int
    capacidade_comercial_tr: Fraction
    observacoes: tuple[str, ...]
