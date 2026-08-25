"""
Modelo de dados do Pagamento.

Representa o pagamento de um ticket. Nunca e excluido do banco:
usa-se o campo 'status' (ativo | cancelado | estornado).
"""

from dataclasses import dataclass, asdict, field
from datetime import datetime

FORMATO_DATA = "%d/%m/%Y %H:%M:%S"

STATUS_ATIVO = "ativo"
STATUS_CANCELADO = "cancelado"
STATUS_ESTORNADO = "estornado"


@dataclass
class Pagamento:
    """Representa um pagamento de ticket."""

    id: int
    ticket_numero: int | None = None
    valor: float = 0.0
    forma_pagamento: str = "dinheiro"
    data: str = field(default_factory=lambda: datetime.now().strftime(FORMATO_DATA))
    operador: str | None = None
    caixa_id: int | None = None
    status: str = STATUS_ATIVO
    motivo_cancelamento: str | None = None
    autorizador: str | None = None
    empresa_id: int | None = None       # Empresa/CNPJ dono do pagamento
    criado_em: str = field(default_factory=lambda: datetime.now().strftime(FORMATO_DATA))
    alterado_em: str = field(default_factory=lambda: datetime.now().strftime(FORMATO_DATA))

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(dados: dict) -> "Pagamento":
        return Pagamento(
            id=dados["id"],
            ticket_numero=dados.get("ticket_numero"),
            valor=dados.get("valor", 0.0),
            forma_pagamento=dados.get("forma_pagamento", "dinheiro"),
            data=dados.get("data"),
            operador=dados.get("operador"),
            caixa_id=dados.get("caixa_id"),
            status=dados.get("status", STATUS_ATIVO),
            motivo_cancelamento=dados.get("motivo_cancelamento"),
            autorizador=dados.get("autorizador"),
            empresa_id=dados.get("empresa_id"),
            criado_em=dados.get("criado_em"),
            alterado_em=dados.get("alterado_em"),
        )
