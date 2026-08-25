"""
Modelo de dados do Convenio e Conta a Receber.

Cadastro de empresas conveniadas (faturamento posterior) e as contas
a receber geradas a partir dos lancamentos.
"""

from dataclasses import dataclass, asdict, field
from datetime import datetime

FORMATO_DATA = "%d/%m/%Y %H:%M:%S"

CONTA_ABERTA = "aberta"
CONTA_PAGA = "paga"
CONTA_CANCELADA = "cancelada"


@dataclass
class Convenio:
    """Representa uma empresa conveniada."""

    id: int
    nome: str
    cnpj: str = ""
    contato: str = ""
    ativo: bool = True
    empresa_id: int | None = None       # Empresa/CNPJ dono do convenio
    criado_em: str = field(default_factory=lambda: datetime.now().strftime(FORMATO_DATA))

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(dados: dict) -> "Convenio":
        return Convenio(
            id=dados["id"],
            nome=dados.get("nome", ""),
            cnpj=dados.get("cnpj", ""),
            contato=dados.get("contato", ""),
            ativo=dados.get("ativo", True),
            empresa_id=dados.get("empresa_id"),
            criado_em=dados.get("criado_em"),
        )


@dataclass
class ContaReceber:
    """Representa uma conta a receber de um convenio."""

    id: int
    convenio_id: int | None = None
    descricao: str = ""
    valor: float = 0.0
    vencimento: str | None = None
    status: str = CONTA_ABERTA
    data_pagamento: str | None = None
    forma_pagamento: str | None = None
    empresa_id: int | None = None       # Empresa/CNPJ dono da conta
    criado_em: str = field(default_factory=lambda: datetime.now().strftime(FORMATO_DATA))

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(dados: dict) -> "ContaReceber":
        return ContaReceber(
            id=dados["id"],
            convenio_id=dados.get("convenio_id"),
            descricao=dados.get("descricao", ""),
            valor=dados.get("valor", 0.0),
            vencimento=dados.get("vencimento"),
            status=dados.get("status", CONTA_ABERTA),
            data_pagamento=dados.get("data_pagamento"),
            forma_pagamento=dados.get("forma_pagamento"),
            empresa_id=dados.get("empresa_id"),
            criado_em=dados.get("criado_em"),
        )
