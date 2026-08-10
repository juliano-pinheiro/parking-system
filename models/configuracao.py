"""
Modelo de configuracao do estacionamento.

Guarda a tabela de precos e o numero total de vagas disponiveis.
"""

from dataclasses import dataclass, asdict


@dataclass
class Configuracao:
    """Representa as configuracoes gerais do estacionamento."""

    total_vagas: int = 20          # Quantidade total de vagas do estacionamento
    valor_primeira_hora: float = 5.0   # Valor cobrado na primeira hora (ou fracao)
    valor_hora_adicional: float = 3.0  # Valor cobrado por cada hora adicional (ou fracao)
    valor_mensal: float = 150.0    # Valor pago por clientes mensalistas
    proximo_numero_ticket: int = 1     # Controle do proximo numero de ticket a ser emitido

    def to_dict(self) -> dict:
        """Converte a configuracao em um dicionario (para salvar em JSON)."""
        return asdict(self)

    @staticmethod
    def from_dict(dados: dict) -> "Configuracao":
        """Cria um objeto Configuracao a partir de um dicionario (lido do JSON)."""
        return Configuracao(
            total_vagas=dados.get("total_vagas", 20),
            valor_primeira_hora=dados.get("valor_primeira_hora", 5.0),
            valor_hora_adicional=dados.get("valor_hora_adicional", 3.0),
            valor_mensal=dados.get("valor_mensal", 150.0),
            proximo_numero_ticket=dados.get("proximo_numero_ticket", 1),
        )
