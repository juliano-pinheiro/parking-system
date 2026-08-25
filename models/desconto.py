"""
Modelo de dados do Desconto.

Representa um desconto aplicavel a um pagamento. Pode ser percentual
ou valor fixo, e pode exigir autorizacao.
"""

from dataclasses import dataclass, asdict, field
from datetime import datetime

FORMATO_DATA = "%d/%m/%Y %H:%M:%S"

TIPO_PERCENTUAL = "percentual"
TIPO_FIXO = "fixo"


@dataclass
class Desconto:
    """Representa um desconto cadastrado."""

    id: int
    nome: str
    tipo: str = TIPO_PERCENTUAL
    valor: float = 0.0
    motivo: str = ""
    necessita_autorizacao: bool = False
    ativo: bool = True
    empresa_id: int | None = None       # Empresa/CNPJ dono do desconto
    criado_em: str = field(default_factory=lambda: datetime.now().strftime(FORMATO_DATA))

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(dados: dict) -> "Desconto":
        return Desconto(
            id=dados["id"],
            nome=dados.get("nome", ""),
            tipo=dados.get("tipo", TIPO_PERCENTUAL),
            valor=dados.get("valor", 0.0),
            motivo=dados.get("motivo", ""),
            necessita_autorizacao=dados.get("necessita_autorizacao", False),
            ativo=dados.get("ativo", True),
            empresa_id=dados.get("empresa_id"),
            criado_em=dados.get("criado_em"),
        )
