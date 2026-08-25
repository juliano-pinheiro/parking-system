"""
Modelo de dados de Perfil.

Representa um perfil de acesso do sistema (admin, supervisor, operador
ou perfis personalizados como gerencia, supervisao, manobrista).
"""

from dataclasses import dataclass, asdict
from datetime import datetime

FORMATO_DATA = "%d/%m/%Y %H:%M:%S"


@dataclass
class Perfil:
    """Representa um perfil de acesso do sistema."""

    id: int
    codigo: str                    # slug unico (ex: gerencia, manobrista)
    nome: str                      # nome exibido (ex: Gerencia)
    descricao: str = ""            # descricao do perfil
    ativo: bool = True             # perfil ativo/inativo
    criado_em: str = ""
    alterado_em: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(dados: dict) -> "Perfil":
        return Perfil(
            id=dados["id"],
            codigo=dados.get("codigo", ""),
            nome=dados.get("nome", ""),
            descricao=dados.get("descricao", ""),
            ativo=dados.get("ativo", True),
            criado_em=dados.get("criado_em", ""),
            alterado_em=dados.get("alterado_em", ""),
        )
