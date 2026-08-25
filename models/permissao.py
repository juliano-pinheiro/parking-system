"""
Modelo de dados de Permissao.

Representa uma permissao concedida a um perfil em um modulo do sistema.
Cada linha indica que o perfil pode executar determinada acao no modulo.
"""

from dataclasses import dataclass, asdict
from datetime import datetime

FORMATO_DATA = "%d/%m/%Y %H:%M:%S"


@dataclass
class Permissao:
    """Representa uma permissao de um perfil em um modulo."""

    id: int
    perfil: str                 # admin | supervisor | operador
    modulo: str                 # ex.: caixa, pagamentos, usuarios...
    acao: str                   # ex.: ver, criar, editar, excluir...
    criado_em: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(dados: dict) -> "Permissao":
        return Permissao(
            id=dados["id"],
            perfil=dados.get("perfil", ""),
            modulo=dados.get("modulo", ""),
            acao=dados.get("acao", ""),
            criado_em=dados.get("criado_em", ""),
        )
