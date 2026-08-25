"""
Modelo de dados do Mensalista e Mensalidade.

Cadastro completo de mensalistas (cliente, CPF/CNPJ, telefone, email,
veiculos, valor mensal, dia de vencimento, status) e suas mensalidades
(pagamento, historico, inadimplencia e bloqueio automatico).
"""

from dataclasses import dataclass, asdict, field
from datetime import datetime

FORMATO_DATA = "%d/%m/%Y %H:%M:%S"

STATUS_ATIVO = "ativo"
STATUS_BLOQUEADO = "bloqueado"
STATUS_INATIVO = "inativo"

MENSALIDADE_PENDENTE = "pendente"
MENSALIDADE_PAGO = "pago"
MENSALIDADE_ATRASADO = "atrasado"
MENSALIDADE_CANCELADO = "cancelado"


@dataclass
class Mensalista:
    """Representa um mensalista cadastrado."""

    id: int
    nome: str
    cliente_id: int | None = None
    cpf_cnpj: str = ""
    telefone: str = ""
    email: str = ""
    valor_mensal: float = 0.0
    dia_vencimento: int = 5
    status: str = STATUS_ATIVO
    empresa_id: int | None = None       # Empresa/CNPJ dono do mensalista
    criado_em: str = field(default_factory=lambda: datetime.now().strftime(FORMATO_DATA))
    alterado_em: str = field(default_factory=lambda: datetime.now().strftime(FORMATO_DATA))

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(dados: dict) -> "Mensalista":
        return Mensalista(
            id=dados["id"],
            nome=dados.get("nome", ""),
            cliente_id=dados.get("cliente_id"),
            cpf_cnpj=dados.get("cpf_cnpj", ""),
            telefone=dados.get("telefone", ""),
            email=dados.get("email", ""),
            valor_mensal=dados.get("valor_mensal", 0.0),
            dia_vencimento=dados.get("dia_vencimento", 5),
            status=dados.get("status", STATUS_ATIVO),
            empresa_id=dados.get("empresa_id"),
            criado_em=dados.get("criado_em"),
            alterado_em=dados.get("alterado_em"),
        )


@dataclass
class Mensalidade:
    """Representa uma mensalidade de um mensalista."""

    id: int
    mensalista_id: int
    competencia: str                 # 'MM/AAAA'
    valor: float = 0.0
    data_pagamento: str | None = None
    forma_pagamento: str | None = None
    status: str = MENSALIDADE_PENDENTE
    empresa_id: int | None = None       # Empresa/CNPJ dono da mensalidade
    criado_em: str = field(default_factory=lambda: datetime.now().strftime(FORMATO_DATA))

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(dados: dict) -> "Mensalidade":
        return Mensalidade(
            id=dados["id"],
            mensalista_id=dados.get("mensalista_id", 0),
            competencia=dados.get("competencia", ""),
            valor=dados.get("valor", 0.0),
            data_pagamento=dados.get("data_pagamento"),
            forma_pagamento=dados.get("forma_pagamento"),
            status=dados.get("status", MENSALIDADE_PENDENTE),
            empresa_id=dados.get("empresa_id"),
            criado_em=dados.get("criado_em"),
        )
