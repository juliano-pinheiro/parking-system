"""Modelo de Tipo de Veiculo.

Tipos fixos do sistema (Carro, Moto, Carro Grande, Caminhonete) alimentam
vagas e tabela de precos padrao e nao podem ser excluidos. Tipos
personalizados podem ter precos proprios; campos zerados herdam os
precos de carro.
"""

from dataclasses import dataclass, field, fields, asdict
from typing import Optional

TIPOS_SISTEMA = ("Carro", "Moto", "Carro Grande", "Caminhonete")

CAMPOS_PRECO = (
    "primeira_hora",
    "hora_adicional",
    "diaria",
    "valor_minuto",
    "valor_maximo_diario",
    "mensal",
)


@dataclass
class TipoVeiculo:
    id: int = 0
    nome: str = ""
    ativo: bool = True
    criado_em: Optional[str] = None
    # Precos proprios (0 = herda o preco de carro)
    primeira_hora: float = 0.0
    hora_adicional: float = 0.0
    diaria: float = 0.0
    valor_minuto: float = 0.0
    valor_maximo_diario: float = 0.0
    mensal: float = 0.0

    @property
    def sistema(self) -> bool:
        return self.nome in TIPOS_SISTEMA

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, dados: dict) -> "TipoVeiculo":
        nomes = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in dict(dados).items() if k in nomes})
