"""
Modelo de dados do Estorno.

Representa o estorno de um pagamento. Nunca apaga registros:
o pagamento original recebe status 'estornado' e o estorno e registrado.
"""

from dataclasses import dataclass, asdict, field
from datetime import datetime

FORMATO_DATA = "%d/%m/%Y %H:%M:%S"


@dataclass
class Estorno:
    """Representa um estorno de pagamento."""

    id: int
    pagamento_id: int | None = None
    valor: float = 0.0
    motivo: str = ""
    operador: str | None = None
    forma_pagamento: str | None = None
    data: str = field(default_factory=lambda: datetime.now().strftime(FORMATO_DATA))
    autorizador: str | None = None
    empresa_id: int | None = None       # Empresa/CNPJ dono do estorno
    criado_em: str = field(default_factory=lambda: datetime.now().strftime(FORMATO_DATA))

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(dados: dict) -> "Estorno":
        return Estorno(
            id=dados["id"],
            pagamento_id=dados.get("pagamento_id"),
            valor=dados.get("valor", 0.0),
            motivo=dados.get("motivo", ""),
            operador=dados.get("operador"),
            forma_pagamento=dados.get("forma_pagamento"),
            data=dados.get("data"),
            autorizador=dados.get("autorizador"),
            empresa_id=dados.get("empresa_id"),
            criado_em=dados.get("criado_em"),
        )
