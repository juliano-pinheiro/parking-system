"""
Modelo de dados da Auditoria e Log de Acesso.

Registra toda alteracao feita no sistema (tabela, registro, campo,
valor antigo, valor novo, usuario, data/hora, IP) e os logs de acesso.
Nenhuma alteracao pode ser perdida.
"""

from dataclasses import dataclass, asdict, field
from datetime import datetime

FORMATO_DATA = "%d/%m/%Y %H:%M:%S"


@dataclass
class Auditoria:
    """Representa um registro de auditoria de alteracao."""

    id: int
    tabela: str
    registro_id: int | None = None
    campo: str | None = None
    valor_antigo: str | None = None
    valor_novo: str | None = None
    usuario: str | None = None
    data: str = field(default_factory=lambda: datetime.now().strftime(FORMATO_DATA))
    ip: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(dados: dict) -> "Auditoria":
        return Auditoria(
            id=dados["id"],
            tabela=dados.get("tabela", ""),
            registro_id=dados.get("registro_id"),
            campo=dados.get("campo"),
            valor_antigo=dados.get("valor_antigo"),
            valor_novo=dados.get("valor_novo"),
            usuario=dados.get("usuario"),
            data=dados.get("data"),
            ip=dados.get("ip"),
        )


@dataclass
class LogAcesso:
    """Representa um log de acesso ao sistema."""

    id: int
    usuario: str | None = None
    acao: str = ""
    modulo: str = ""
    data: str = field(default_factory=lambda: datetime.now().strftime(FORMATO_DATA))
    ip: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(dados: dict) -> "LogAcesso":
        return LogAcesso(
            id=dados["id"],
            usuario=dados.get("usuario"),
            acao=dados.get("acao", ""),
            modulo=dados.get("modulo", ""),
            data=dados.get("data"),
            ip=dados.get("ip"),
        )
