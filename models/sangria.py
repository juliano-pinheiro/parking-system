"""
Modelo de dados da Sangria.

Representa uma retirada de dinheiro do caixa durante o expediente.
"""

from dataclasses import dataclass, asdict, field
from datetime import datetime

FORMATO_DATA = "%d/%m/%Y %H:%M:%S"


@dataclass
class Sangria:
    """Representa uma sangria de caixa."""

    id: int
    caixa_id: int | None = None
    valor: float = 0.0
    motivo: str = ""
    operador: str | None = None
    data: str = field(default_factory=lambda: datetime.now().strftime(FORMATO_DATA))
    criado_em: str = field(default_factory=lambda: datetime.now().strftime(FORMATO_DATA))

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(dados: dict) -> "Sangria":
        return Sangria(
            id=dados["id"],
            caixa_id=dados.get("caixa_id"),
            valor=dados.get("valor", 0.0),
            motivo=dados.get("motivo", ""),
            operador=dados.get("operador"),
            data=dados.get("data"),
            criado_em=dados.get("criado_em"),
        )
