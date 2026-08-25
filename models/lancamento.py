"""
Modelo de dados do Lancamento financeiro.

Representa uma movimentacao financeira do estacionamento: uma entrada
(receita) ou saida (despesa), com a forma de pagamento utilizada.
"""

from dataclasses import dataclass, asdict, field
from datetime import datetime

# Tipos de lancamento
TIPOS_VALIDOS = ("entrada", "saida")

# Formas de pagamento permitidas
FORMAS_PAGAMENTO_VALIDAS = ("dinheiro", "pix", "cartao_credito", "cartao_debito")

# Origem do lancamento
ORIGEM_TICKET = "ticket"
ORIGEM_MANUAL = "manual"

FORMATO_DATA = "%d/%m/%Y %H:%M:%S"


@dataclass
class Lancamento:
    """Representa um lancamento financeiro (entrada ou saida)."""

    id: int                             # Identificador unico do lancamento
    tipo: str                           # 'entrada' (receita) ou 'saida' (despesa)
    descricao: str                      # Descricao do lancamento
    valor: float                        # Valor (positivo)
    forma_pagamento: str = "dinheiro"   # dinheiro, pix, cartao_credito, cartao_debito
    data: str = field(default_factory=lambda: datetime.now().strftime(FORMATO_DATA))
    origem: str = ORIGEM_MANUAL         # 'ticket' (automatico) ou 'manual'
    ticket_numero: int | None = None    # Numero do ticket vinculado (quando origem=ticket)
    empresa_id: int | None = None       # Empresa/CNPJ dono do lancamento

    def to_dict(self) -> dict:
        """Converte o lancamento em um dicionario (para salvar em JSON)."""
        return asdict(self)

    @staticmethod
    def from_dict(dados: dict) -> "Lancamento":
        """Cria um objeto Lancamento a partir de um dicionario (lido do JSON)."""
        return Lancamento(
            id=dados["id"],
            tipo=dados["tipo"],
            descricao=dados["descricao"],
            valor=dados["valor"],
            forma_pagamento=dados.get("forma_pagamento", "dinheiro"),
            data=dados.get("data"),
            origem=dados.get("origem", ORIGEM_MANUAL),
            ticket_numero=dados.get("ticket_numero"),
            empresa_id=dados.get("empresa_id"),
        )
