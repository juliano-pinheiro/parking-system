"""
Modelo de dados do Caixa.

Representa a abertura e fechamento de um caixa do estacionamento,
com controle de valor inicial, totais por forma de pagamento e
diferenca entre o valor esperado e o valor contado.
"""

from dataclasses import dataclass, asdict, field
from datetime import datetime

FORMATO_DATA = "%d/%m/%Y %H:%M:%S"

STATUS_ABERTO = "aberto"
STATUS_FECHADO = "fechado"


@dataclass
class Caixa:
    """Representa um caixa (aberto ou fechado)."""

    id: int
    operador: str
    data_abertura: str = field(default_factory=lambda: datetime.now().strftime(FORMATO_DATA))
    valor_inicial: float = 0.0
    data_fechamento: str | None = None
    valor_esperado: float = 0.0
    valor_contado: float = 0.0
    diferenca: float = 0.0
    status: str = STATUS_ABERTO
    observacoes: str = ""
    empresa_id: int | None = None       # Empresa/CNPJ dono do caixa
    criado_em: str = field(default_factory=lambda: datetime.now().strftime(FORMATO_DATA))
    alterado_em: str = field(default_factory=lambda: datetime.now().strftime(FORMATO_DATA))
    usuario: str | None = None
    ip: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(dados: dict) -> "Caixa":
        return Caixa(
            id=dados["id"],
            operador=dados.get("operador", ""),
            data_abertura=dados.get("data_abertura"),
            valor_inicial=dados.get("valor_inicial", 0.0),
            data_fechamento=dados.get("data_fechamento"),
            valor_esperado=dados.get("valor_esperado", 0.0),
            valor_contado=dados.get("valor_contado", 0.0),
            diferenca=dados.get("diferenca", 0.0),
            status=dados.get("status", STATUS_ABERTO),
            observacoes=dados.get("observacoes", ""),
            empresa_id=dados.get("empresa_id"),
            criado_em=dados.get("criado_em"),
            alterado_em=dados.get("alterado_em"),
            usuario=dados.get("usuario"),
            ip=dados.get("ip"),
        )


@dataclass
class MovimentacaoCaixa:
    """Representa uma movimentacao dentro de um caixa."""

    id: int
    caixa_id: int
    tipo: str                       # entrada | saida | sangria | suprimento
    descricao: str = ""
    valor: float = 0.0
    forma_pagamento: str | None = None
    data: str = field(default_factory=lambda: datetime.now().strftime(FORMATO_DATA))
    usuario: str | None = None
    empresa_id: int | None = None       # Empresa/CNPJ dono da movimentacao
    criado_em: str = field(default_factory=lambda: datetime.now().strftime(FORMATO_DATA))

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(dados: dict) -> "MovimentacaoCaixa":
        return MovimentacaoCaixa(
            id=dados["id"],
            caixa_id=dados.get("caixa_id", 0),
            tipo=dados.get("tipo", "entrada"),
            descricao=dados.get("descricao", ""),
            valor=dados.get("valor", 0.0),
            forma_pagamento=dados.get("forma_pagamento"),
            data=dados.get("data"),
            usuario=dados.get("usuario"),
            empresa_id=dados.get("empresa_id"),
            criado_em=dados.get("criado_em"),
        )
