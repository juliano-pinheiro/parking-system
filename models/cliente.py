"""
Modelo de dados do Cliente (mensalista) do sistema.

Representa um cliente mensalista do estacionamento, contendo os dados
basicos de contato, do veiculo e a vigencia do plano mensal adquirido.
"""

from dataclasses import dataclass, asdict, field
from datetime import datetime

# Categorias de veiculo permitidas
CATEGORIAS_VALIDAS = ("carro_pequeno", "carro_grande", "moto", "caminhonete")

FORMATO_DATA = "%d/%m/%Y"
FORMATO_DATA_CADASTRO = "%d/%m/%Y %H:%M:%S"


@dataclass
class Cliente:
    """Representa um cliente mensalista do estacionamento."""

    id: int                             # Identificador unico do cliente
    nome: str                           # Nome do cliente
    telefone: str = ""                  # Telefone de contato
    placa: str = ""                     # Placa do veiculo
    categoria: str = "carro_pequeno"    # Categoria do veiculo: carro_pequeno, carro_grande, moto ou caminhonete
    data_inicio: str = ""               # Inicio da vigencia do plano mensal (dd/mm/aaaa)
    data_fim: str = ""                  # Fim da vigencia do plano mensal (dd/mm/aaaa)
    ativo: bool = True                  # True = plano/cliente ativo | False = desativado
    empresa_id: int | None = None       # Empresa/CNPJ dono do cliente
    data_cadastro: str = field(default_factory=lambda: datetime.now().strftime(FORMATO_DATA_CADASTRO))

    def to_dict(self) -> dict:
        """Converte o cliente em um dicionario (para salvar em JSON)."""
        return asdict(self)

    @staticmethod
    def from_dict(dados: dict) -> "Cliente":
        """Cria um objeto Cliente a partir de um dicionario (lido do JSON)."""
        return Cliente(
            id=dados["id"],
            nome=dados["nome"],
            telefone=dados.get("telefone", ""),
            placa=dados.get("placa", ""),
            categoria=dados.get("categoria", "carro_pequeno"),
            data_inicio=dados.get("data_inicio", ""),
            data_fim=dados.get("data_fim", ""),
            ativo=dados.get("ativo", True),
            empresa_id=dados.get("empresa_id"),
            data_cadastro=dados.get("data_cadastro"),
        )
