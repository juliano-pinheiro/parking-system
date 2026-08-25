"""
Servico de Cortesias.

CRUD de cortesias. Registra motivo, usuario, autorizacao, data e hora.
Cortesias nao sao contabilizadas como receita.
"""

from datetime import datetime
from typing import List, Optional

from models.cortesia import Cortesia, FORMATO_DATA, STATUS_ATIVO, STATUS_CANCELADO
from services.base_supabase_service import BaseSupabaseService


class CortesiaService(BaseSupabaseService):
    """Regras de negocio e persistencia das cortesias."""

    TABELA = "cortesias"
    SCOPED_EMPRESA = True
    MODELO = Cortesia
    CAMPOS_DATA = ("data", "criado_em")

    def __init__(self, empresa_id: Optional[int] = None):
        self._empresa_id = empresa_id
        self._registros: List[Cortesia] = self._carregar()

    def criar(
        self,
        motivo: str,
        usuario: str | None = None,
        autorizador: str | None = None,
        ticket_numero: int | None = None,
    ) -> Cortesia:
        motivo = (motivo or "").strip()
        if not motivo:
            raise ValueError("Informe o motivo da cortesia.")

        cortesia = Cortesia(
            id=self._proximo_id(self._registros),
            motivo=motivo,
            usuario=usuario,
            autorizador=autorizador,
            data=datetime.now().strftime(FORMATO_DATA),
            ticket_numero=ticket_numero,
            status=STATUS_ATIVO,
            empresa_id=getattr(self, "_empresa_id", None),
        )
        self._registros.append(cortesia)
        self._persistir()
        return cortesia

    def cancelar(self, id_cortesia: int, autorizador: str | None = None) -> Optional[Cortesia]:
        cortesia = self.buscar_por_id(id_cortesia)
        if cortesia is None:
            return None
        cortesia.status = STATUS_CANCELADO
        cortesia.autorizador = autorizador or cortesia.autorizador
        self._persistir()
        return cortesia

    def _persistir(self) -> None:
        self._salvar(self._registros)
