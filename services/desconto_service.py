"""
Servico de Descontos.

CRUD de descontos (percentual ou valor fixo) com motivo e necessidade
de autorizacao.
"""

from typing import List, Optional

from models.desconto import Desconto, TIPO_PERCENTUAL, TIPO_FIXO
from services.base_supabase_service import BaseSupabaseService


class DescontoService(BaseSupabaseService):
    """Regras de negocio e persistencia dos descontos."""

    TABELA = "descontos"
    SCOPED_EMPRESA = True
    MODELO = Desconto
    CAMPOS_DATA = ("criado_em",)

    def __init__(self, empresa_id: Optional[int] = None):
        self._empresa_id = empresa_id
        self._registros: List[Desconto] = self._carregar()

    def criar(
        self,
        nome: str,
        tipo: str = TIPO_PERCENTUAL,
        valor: float = 0.0,
        motivo: str = "",
        necessita_autorizacao: bool = False,
        ativo: bool = True,
    ) -> Desconto:
        nome = (nome or "").strip()
        if not nome:
            raise ValueError("Informe o nome do desconto.")
        if tipo not in (TIPO_PERCENTUAL, TIPO_FIXO):
            raise ValueError("Tipo de desconto invalido. Use 'percentual' ou 'fixo'.")
        if valor is None or valor < 0:
            raise ValueError("Informe um valor valido para o desconto.")
        if tipo == TIPO_PERCENTUAL and valor > 100:
            raise ValueError("Desconto percentual nao pode ser maior que 100%.")

        desconto = Desconto(
            id=self._proximo_id(self._registros),
            nome=nome,
            tipo=tipo,
            valor=round(float(valor), 2),
            motivo=motivo,
            necessita_autorizacao=bool(necessita_autorizacao),
            ativo=bool(ativo),
            empresa_id=getattr(self, "_empresa_id", None),
        )
        self._registros.append(desconto)
        self._persistir()
        return desconto

    def atualizar(
        self,
        id_desconto: int,
        nome: str | None = None,
        tipo: str | None = None,
        valor: float | None = None,
        motivo: str | None = None,
        necessita_autorizacao: bool | None = None,
        ativo: bool | None = None,
    ) -> Optional[Desconto]:
        desconto = self.buscar_por_id(id_desconto)
        if desconto is None:
            return None
        if nome is not None:
            nome = nome.strip()
            if not nome:
                raise ValueError("Informe o nome do desconto.")
            desconto.nome = nome
        if tipo is not None:
            if tipo not in (TIPO_PERCENTUAL, TIPO_FIXO):
                raise ValueError("Tipo de desconto invalido.")
            desconto.tipo = tipo
        if valor is not None:
            if valor < 0:
                raise ValueError("Valor invalido para o desconto.")
            desconto.valor = round(float(valor), 2)
        if motivo is not None:
            desconto.motivo = motivo
        if necessita_autorizacao is not None:
            desconto.necessita_autorizacao = bool(necessita_autorizacao)
        if ativo is not None:
            desconto.ativo = bool(ativo)
        self._persistir()
        return desconto

    def _persistir(self) -> None:
        self._salvar(self._registros)
