"""
Modelo de dados da NFSe (Nota Fiscal de Servico simplificada).

Registra cada nota emitida, vinculada a um ticket de estacionamento.
As notas nunca sao excluidas (status: emitida / cancelada).
"""

from dataclasses import dataclass, asdict, field
from datetime import datetime

FORMATO_DATA = "%d/%m/%Y %H:%M:%S"


@dataclass
class Nfse:
    """Representa uma nota fiscal de servico emitida."""

    id: int
    numero: int                        # Numero sequencial da nota (por empresa)
    ticket_numero: int | None = None   # Ticket vinculado (opcional)
    placa: str = ""
    valor: float = 0.0
    cpf_cnpj: str = ""
    razao_social: str = ""
    servico: str = "Estacionamento de veiculos"
    data: str = field(default_factory=lambda: datetime.now().strftime(FORMATO_DATA))
    usuario: str = ""
    status: str = "emitida"            # emitida / cancelada
    empresa_id: int | None = None
    criado_em: str = field(default_factory=lambda: datetime.now().strftime(FORMATO_DATA))

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(dados: dict) -> "Nfse":
        return Nfse(
            id=int(dados["id"]),
            numero=int(dados.get("numero", dados.get("id", 0))),
            ticket_numero=int(dados["ticket_numero"]) if dados.get("ticket_numero") is not None else None,
            placa=dados.get("placa", ""),
            valor=float(dados.get("valor", 0) or 0),
            cpf_cnpj=dados.get("cpf_cnpj", ""),
            razao_social=dados.get("razao_social", ""),
            servico=dados.get("servico", "Estacionamento de veiculos"),
            data=dados.get("data"),
            usuario=dados.get("usuario", ""),
            status=dados.get("status", "emitida"),
            empresa_id=dados.get("empresa_id"),
            criado_em=dados.get("criado_em"),
        )
