"""
Modelo de dados do Usuario do sistema.

Representa um usuario do sistema de estacionamento, contendo as
informacoes de identificacao, perfil de acesso e status (ativo/inativo).
"""

from dataclasses import dataclass, asdict, field
from datetime import datetime

# Perfis de acesso possiveis
PERFIS_VALIDOS = ("admin", "operador")

FORMATO_DATA_CADASTRO = "%d/%m/%Y %H:%M:%S"


@dataclass
class Usuario:
    """Representa um usuario do sistema."""

    id: int                           # Identificador unico do usuario
    nome: str                         # Nome completo do usuario
    email: str                        # E-mail de contato/login
    perfil: str = "operador"          # Perfil de acesso: admin ou operador
    ativo: bool = True                # True = usuario ativo | False = desativado
    data_cadastro: str = field(default_factory=lambda: datetime.now().strftime(FORMATO_DATA_CADASTRO))

    def to_dict(self) -> dict:
        """Converte o usuario em um dicionario (para salvar em JSON)."""
        return asdict(self)

    @staticmethod
    def from_dict(dados: dict) -> "Usuario":
        """Cria um objeto Usuario a partir de um dicionario (lido do JSON)."""
        return Usuario(
            id=dados["id"],
            nome=dados["nome"],
            email=dados["email"],
            perfil=dados.get("perfil", "operador"),
            ativo=dados.get("ativo", True),
            data_cadastro=dados.get("data_cadastro"),
        )
