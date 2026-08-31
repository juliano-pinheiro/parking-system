"""
Modelo de dados da Reserva de Vaga.

Registra reservas de vagas para clientes/eventos, com periodo,
valor e status. Exclusao logica via 'status'.
"""

from dataclasses import dataclass, asdict, field
from datetime import datetime

FORMATO_DATA = "%d/%m/%Y %H:%M:%S"


@dataclass
class Reserva:
    """Representa uma reserva de vaga."""

    id: int
    cliente: str = ""
    telefone: str = ""
    placa: str = ""
    tipo_veiculo: str = "Carro"
    vaga: int | None = None
    data_inicio: str = ""
    data_fim: str = ""
    valor: float = 0.0
    status: str = "ativa"              # ativa / concluida / cancelada
    observacao: str = ""
    usuario: str = ""
    empresa_id: int | None = None
    criado_em: str = field(default_factory=lambda: datetime.now().strftime(FORMATO_DATA))
    alterado_em: str = field(default_factory=lambda: datetime.now().strftime(FORMATO_DATA))

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(dados: dict) -> "Reserva":
        return Reserva(
            id=int(dados["id"]),
            cliente=dados.get("cliente", ""),
            telefone=dados.get("telefone", ""),
            placa=dados.get("placa", ""),
            tipo_veiculo=dados.get("tipo_veiculo", "Carro"),
            vaga=int(dados["vaga"]) if dados.get("vaga") is not None else None,
            data_inicio=dados.get("data_inicio", ""),
            data_fim=dados.get("data_fim", ""),
            valor=float(dados.get("valor", 0) or 0),
            status=dados.get("status", "ativa"),
            observacao=dados.get("observacao", ""),
            usuario=dados.get("usuario", ""),
            empresa_id=dados.get("empresa_id"),
            criado_em=dados.get("criado_em"),
            alterado_em=dados.get("alterado_em"),
        )
