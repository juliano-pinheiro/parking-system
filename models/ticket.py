"""
Modelo de dados do Ticket de estacionamento.

Representa cada ticket emitido para um veiculo, contendo as informacoes
de entrada, saida e valor cobrado.
"""

from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class Ticket:
    """Representa um ticket de estacionamento."""

    numero: int                     # Numero sequencial do ticket
    placa: str                      # Placa do veiculo
    entrada: str                    # Data/hora de entrada (formato ISO string)
    saida: Optional[str] = None     # Data/hora de saida (None enquanto o veiculo estiver no estacionamento)
    valor: Optional[float] = None   # Valor cobrado (None enquanto nao houver saida)
    vaga: Optional[int] = None      # Numero da vaga ocupada
    status: str = "ABERTO"          # ABERTO -> veiculo ainda esta no estacionamento | FECHADO -> ja saiu
    tipo_veiculo: str = "Carro"     # Tipo do veiculo: Carro, Moto ou Caminhonete
    observacoes: str = ""           # Observacoes opcionais (cor, modelo, etc.)

    def to_dict(self) -> dict:
        """Converte o ticket em um dicionario (para salvar em JSON)."""
        return asdict(self)

    @staticmethod
    def from_dict(dados: dict) -> "Ticket":
        """Cria um objeto Ticket a partir de um dicionario (lido do JSON)."""
        return Ticket(
            numero=dados["numero"],
            placa=dados["placa"],
            entrada=dados["entrada"],
            saida=dados.get("saida"),
            valor=dados.get("valor"),
            vaga=dados.get("vaga"),
            status=dados.get("status", "ABERTO"),
            tipo_veiculo=dados.get("tipo_veiculo", "Carro"),
            observacoes=dados.get("observacoes", ""),
        )
