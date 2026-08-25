"""
Modelo de dados da Forma de Pagamento.

Permite cadastrar formas de pagamento (Dinheiro, PIX, Cartao Credito,
Cartao Debito, Convenio, Mensalista, Cortesia) e novas formas.
"""

from dataclasses import dataclass, asdict, field
from datetime import datetime

FORMATO_DATA = "%d/%m/%Y %H:%M:%S"


@dataclass
class FormaPagamento:
    """Representa uma forma de pagamento cadastrada."""

    id: int
    nome: str
    codigo: str
    ativo: bool = True
    empresa_id: int | None = None       # Empresa/CNPJ dona da forma de pagamento
    criado_em: str = field(default_factory=lambda: datetime.now().strftime(FORMATO_DATA))

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(dados: dict) -> "FormaPagamento":
        return FormaPagamento(
            id=dados["id"],
            nome=dados.get("nome", ""),
            codigo=dados.get("codigo", ""),
            ativo=dados.get("ativo", True),
            empresa_id=dados.get("empresa_id"),
            criado_em=dados.get("criado_em"),
        )
