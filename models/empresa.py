"""
Modelo de dados da Empresa (estacionamento).

Representa um estacionamento vinculado a um CNPJ. O usuario master
pode gerenciar varias empresas; usuarios comuns estao vinculados a
apenas uma empresa e so enxergam seus dados.
"""

from dataclasses import dataclass, asdict


@dataclass
class Empresa:
    """Representa uma empresa/estacionamento do sistema."""

    id: int
    cnpj: str
    razao_social: str
    nome_fantasia: str
    telefone: str = ""
    email: str = ""
    endereco: str = ""
    cidade: str = ""
    estado: str = ""
    cep: str = ""
    ativo: bool = True
    criado_em: str = ""
    alterado_em: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(dados: dict) -> "Empresa":
        return Empresa(
            id=dados["id"],
            cnpj=dados.get("cnpj", ""),
            razao_social=dados.get("razao_social", ""),
            nome_fantasia=dados.get("nome_fantasia", ""),
            telefone=dados.get("telefone", ""),
            email=dados.get("email", ""),
            endereco=dados.get("endereco", ""),
            cidade=dados.get("cidade", ""),
            estado=dados.get("estado", ""),
            cep=dados.get("cep", ""),
            ativo=dados.get("ativo", True),
            criado_em=dados.get("criado_em", ""),
            alterado_em=dados.get("alterado_em", ""),
        )
