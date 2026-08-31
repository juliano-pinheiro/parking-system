"""
Modelo de dados da Lista Negra (bloqueio de veiculos).

Registra placas que nao podem entrar/sair sem autorizacao.
Exclusao logica via 'ativo'.
"""

from dataclasses import dataclass, asdict, field
from datetime import datetime

FORMATO_DATA = "%d/%m/%Y %H:%M:%S"


@dataclass
class ListaNegra:
    """Representa um registro de veiculo bloqueado."""

    id: int
    placa: str = ""
    motivo: str = ""
    ativo: bool = True
    usuario: str = ""
    data: str = field(default_factory=lambda: datetime.now().strftime(FORMATO_DATA))
    empresa_id: int | None = None
    criado_em: str = field(default_factory=lambda: datetime.now().strftime(FORMATO_DATA))

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(dados: dict) -> "ListaNegra":
        return ListaNegra(
            id=int(dados["id"]),
            placa=dados.get("placa", ""),
            motivo=dados.get("motivo", ""),
            ativo=bool(dados.get("ativo", True)),
            usuario=dados.get("usuario", ""),
            data=dados.get("data"),
            empresa_id=dados.get("empresa_id"),
            criado_em=dados.get("criado_em"),
        )
