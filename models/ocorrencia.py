"""
Modelo de dados de Ocorrencia / Termo de Avarias.

Registra ocorrencias com veiculos (avaria, perda, etc.) para
formalizar o termo. Exclusao logica via 'status'.
"""

from dataclasses import dataclass, asdict, field
from datetime import datetime

FORMATO_DATA = "%d/%m/%Y %H:%M:%S"


@dataclass
class Ocorrencia:
    """Representa uma ocorrencia registrada no estacionamento."""

    id: int
    tipo: str = "avaria"               # avaria / perda / outro
    placa: str = ""
    ticket_numero: int | None = None
    descricao: str = ""
    status: str = "aberta"             # aberta / resolvida
    usuario: str = ""
    autorizador: str = ""
    data: str = field(default_factory=lambda: datetime.now().strftime(FORMATO_DATA))
    empresa_id: int | None = None
    criado_em: str = field(default_factory=lambda: datetime.now().strftime(FORMATO_DATA))
    alterado_em: str = field(default_factory=lambda: datetime.now().strftime(FORMATO_DATA))

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(dados: dict) -> "Ocorrencia":
        return Ocorrencia(
            id=int(dados["id"]),
            tipo=dados.get("tipo", "avaria"),
            placa=dados.get("placa", ""),
            ticket_numero=int(dados["ticket_numero"]) if dados.get("ticket_numero") is not None else None,
            descricao=dados.get("descricao", ""),
            status=dados.get("status", "aberta"),
            usuario=dados.get("usuario", ""),
            autorizador=dados.get("autorizador", ""),
            data=dados.get("data"),
            empresa_id=dados.get("empresa_id"),
            criado_em=dados.get("criado_em"),
            alterado_em=dados.get("alterado_em"),
        )
