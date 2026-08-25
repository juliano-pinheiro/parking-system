"""
Modelo de dados do Usuario do sistema.

Representa um usuario do sistema de estacionamento, contendo as
informacoes de identificacao, perfil de acesso e status (ativo/inativo).
"""

from dataclasses import dataclass, asdict, field
from datetime import datetime
import hashlib

FORMATO_DATA_CADASTRO = "%d/%m/%Y %H:%M:%S"


def hash_senha(senha: str) -> str:
    """Gera o hash SHA-256 da senha (armazenamento seguro)."""
    return hashlib.sha256((senha or "").encode("utf-8")).hexdigest()


@dataclass
class Usuario:
    """Representa um usuario do sistema."""

    id: int                           # Identificador unico do usuario
    nome: str                         # Nome completo do usuario
    email: str                        # E-mail de contato/login
    perfil: str = "operador"          # Perfil de acesso (codigo do perfil)
    ativo: bool = True                # True = usuario ativo | False = desativado
    senha: str = ""                   # Hash da senha de acesso
    trocar_senha_no_proximo_acesso: bool = False  # True = forca troca de senha no proximo login
    empresa_id: int | None = None     # Empresa/CNPJ vinculado (None = master sem vinculo fixo)
    master: bool = False              # True = usuario master do sistema (gerencia todos os CNPJs)
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
            senha=dados.get("senha", ""),
            trocar_senha_no_proximo_acesso=dados.get("trocar_senha_no_proximo_acesso", False),
            empresa_id=dados.get("empresa_id"),
            master=bool(dados.get("master", False)),
            data_cadastro=dados.get("data_cadastro"),
        )
