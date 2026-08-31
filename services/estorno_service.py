"""
Servico de Estornos.

Registra estornos de pagamentos. Nunca apaga registros: o pagamento
original recebe status 'estornado' e o estorno e registrado.
"""

from datetime import datetime
from typing import List, Optional

from models.estorno import Estorno, FORMATO_DATA
from services.base_supabase_service import BaseSupabaseService


class EstornoService(BaseSupabaseService):
    """Regras de negocio e persistencia dos estornos."""

    TABELA = "estornos"
    SCOPED_EMPRESA = True
    MODELO = Estorno
    CAMPOS_DATA = ("data", "criado_em")

    def __init__(self, empresa_id: Optional[int] = None):
        self._empresa_id = empresa_id
        self._registros: List[Estorno] = self._carregar()

    def criar(
        self,
        pagamento_id: int | None,
        valor: float,
        motivo: str,
        operador: str | None = None,
        forma_pagamento: str | None = None,
        autorizador: str | None = None,
    ) -> Estorno:
        if valor is None or valor <= 0:
            raise ValueError("Informe um valor valido para o estorno.")
        if not (motivo or "").strip():
            raise ValueError("Informe o motivo do estorno.")

        estorno = Estorno(
            id=self._proximo_id(self._registros),
            pagamento_id=pagamento_id,
            valor=round(float(valor), 2),
            motivo=motivo,
            operador=operador,
            forma_pagamento=forma_pagamento,
            data=datetime.now().strftime(FORMATO_DATA),
            autorizador=autorizador,
            empresa_id=getattr(self, "_empresa_id", None),
        )
        self._registros.append(estorno)
        self._persistir()
        return estorno

    def _persistir(self) -> None:
        self._salvar(self._registros)
