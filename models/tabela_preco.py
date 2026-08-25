"""
Modelo de dados da Tabela de Precos.

Contem os valores cobrados pelo estacionamento e as regras de calculo
(primeira hora, hora adicional, diaria, mensal, valor por minuto,
valor maximo diario, tolerancia, valor noturno, fim de semana e feriados).

Suporta precos diferenciados por tipo de veiculo (carro, moto, carro
grande, caminhonete) e fracionamento de cobranca (15/30/60 minutos).
"""

from dataclasses import dataclass, asdict, field
from datetime import datetime

FORMATO_DATA = "%d/%m/%Y %H:%M:%S"

# Tipos de veiculo suportados
TIPOS_VEICULO = ("carro", "moto", "carro_grande", "caminhonete")

# Campos de preco por tipo de veiculo
CAMPOS_PRECO_TIPO = (
    "primeira_hora", "hora_adicional", "diaria", "valor_minuto",
    "valor_maximo_diario", "mensal",
)


@dataclass
class TabelaPreco:
    """Representa a tabela de precos vigente."""

    id: int
    # Valores padrao (aplicados ao tipo "carro")
    primeira_hora: float = 0.0
    hora_adicional: float = 0.0
    diaria: float = 0.0
    mensal: float = 0.0
    valor_minuto: float = 0.0
    valor_maximo_diario: float = 0.0
    tolerancia_minutos: int = 0
    valor_noturno: float = 0.0
    fim_semana: float = 0.0
    feriados: float = 0.0
    # Fracionamento e tarifas especiais
    fracionamento_minutos: int = 60          # 15, 30 ou 60
    tarifa_minima: float = 0.0               # valor minimo cobrado
    meia_estadia_minutos: int = 0            # ate quantos minutos vale a meia estadia
    meia_estadia_valor: float = 0.0          # valor da meia estadia
    # Precos por tipo de veiculo (carro_grande, moto, caminhonete)
    carro_grande_primeira_hora: float = 0.0
    carro_grande_hora_adicional: float = 0.0
    carro_grande_diaria: float = 0.0
    carro_grande_valor_minuto: float = 0.0
    carro_grande_valor_maximo_diario: float = 0.0
    carro_grande_mensal: float = 0.0
    moto_primeira_hora: float = 0.0
    moto_hora_adicional: float = 0.0
    moto_diaria: float = 0.0
    moto_valor_minuto: float = 0.0
    moto_valor_maximo_diario: float = 0.0
    moto_mensal: float = 0.0
    caminhonete_primeira_hora: float = 0.0
    caminhonete_hora_adicional: float = 0.0
    caminhonete_diaria: float = 0.0
    caminhonete_valor_minuto: float = 0.0
    caminhonete_valor_maximo_diario: float = 0.0
    caminhonete_mensal: float = 0.0
    ativo: bool = True
    empresa_id: int | None = None       # Empresa/CNPJ dona da tabela de precos
    criado_em: str = field(default_factory=lambda: datetime.now().strftime(FORMATO_DATA))
    alterado_em: str = field(default_factory=lambda: datetime.now().strftime(FORMATO_DATA))

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(dados: dict) -> "TabelaPreco":
        def _f(chave, padrao=0.0):
            valor = dados.get(chave, padrao)
            try:
                return float(valor) if valor is not None else padrao
            except (TypeError, ValueError):
                return padrao

        def _i(chave, padrao=0):
            valor = dados.get(chave, padrao)
            try:
                return int(valor) if valor is not None else padrao
            except (TypeError, ValueError):
                return padrao

        return TabelaPreco(
            id=dados["id"],
            primeira_hora=_f("primeira_hora"),
            hora_adicional=_f("hora_adicional"),
            diaria=_f("diaria"),
            mensal=_f("mensal"),
            valor_minuto=_f("valor_minuto"),
            valor_maximo_diario=_f("valor_maximo_diario"),
            tolerancia_minutos=_i("tolerancia_minutos"),
            valor_noturno=_f("valor_noturno"),
            fim_semana=_f("fim_semana"),
            feriados=_f("feriados"),
            fracionamento_minutos=_i("fracionamento_minutos", 60),
            tarifa_minima=_f("tarifa_minima"),
            meia_estadia_minutos=_i("meia_estadia_minutos"),
            meia_estadia_valor=_f("meia_estadia_valor"),
            carro_grande_primeira_hora=_f("carro_grande_primeira_hora"),
            carro_grande_hora_adicional=_f("carro_grande_hora_adicional"),
            carro_grande_diaria=_f("carro_grande_diaria"),
            carro_grande_valor_minuto=_f("carro_grande_valor_minuto"),
            carro_grande_valor_maximo_diario=_f("carro_grande_valor_maximo_diario"),
            carro_grande_mensal=_f("carro_grande_mensal"),
            moto_primeira_hora=_f("moto_primeira_hora"),
            moto_hora_adicional=_f("moto_hora_adicional"),
            moto_diaria=_f("moto_diaria"),
            moto_valor_minuto=_f("moto_valor_minuto"),
            moto_valor_maximo_diario=_f("moto_valor_maximo_diario"),
            moto_mensal=_f("moto_mensal"),
            caminhonete_primeira_hora=_f("caminhonete_primeira_hora"),
            caminhonete_hora_adicional=_f("caminhonete_hora_adicional"),
            caminhonete_diaria=_f("caminhonete_diaria"),
            caminhonete_valor_minuto=_f("caminhonete_valor_minuto"),
            caminhonete_valor_maximo_diario=_f("caminhonete_valor_maximo_diario"),
            caminhonete_mensal=_f("caminhonete_mensal"),
            ativo=dados.get("ativo", True),
            empresa_id=dados.get("empresa_id"),
            criado_em=dados.get("criado_em"),
            alterado_em=dados.get("alterado_em"),
        )
