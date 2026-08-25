"""
Modelo de dados da Cortesia.

Representa uma cortesia concedida (nao contabilizada como receita).
Registra motivo, usuario, autorizacao, data e hora.
"""

from dataclasses import dataclass, asdict, field
from datetime import datetime

FORMATO_DATA = "%d/%m/%Y %H:%M:%S"

STATUS_ATIVO = "ativo"
STATUS_CANCELADO = "cancelado"


@dataclass
class Cortesia:
    """Representa uma cortesia concedida."""

    id: int
    motivo: str
    usuario: str | None = None
    autorizador: str | None = None
    data: str = field(default_factory=lambda: datetime.now().strftime(FORMATO_DATA))
    ticket_numero: int | None = None
    status: str = STATUS_ATIVO
    empresa_id: int | None = None       # Empresa/CNPJ dono da cortesia
    criado_em: str = field(default_factory=lambda: datetime.now().strftime(FORMATO_DATA))

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(dados: dict) -> "Cortesia":
        return Cortesia(
            id=dados["id"],
            motivo=dados.get("motivo", ""),
            usuario=dados.get("usuario"),
            autorizador=dados.get("autorizador"),
            data=dados.get("data"),
            ticket_numero=dados.get("ticket_numero"),
            status=dados.get("status", STATUS_ATIVO),
            empresa_id=dados.get("empresa_id"),
            criado_em=dados.get("criado_em"),
        )
