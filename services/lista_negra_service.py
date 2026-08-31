"""
Servico de Lista Negra (bloqueio de veiculos).

Registra placas bloqueadas para entrada/saida sem autorizacao.
Exclusao logica via 'ativo'.
"""

from datetime import datetime
from typing import List, Optional

from models.lista_negra import ListaNegra, FORMATO_DATA
from services.base_supabase_service import BaseSupabaseService


class ListaNegraService(BaseSupabaseService):
    """Regras de negocio e persistencia da lista negra."""

    TABELA = "lista_negra"
    SCOPED_EMPRESA = True
    MODELO = ListaNegra
    CAMPOS_DATA = ("data", "criado_em")

    def __init__(self, empresa_id: Optional[int] = None):
        self._empresa_id = empresa_id
        self._registros: List[ListaNegra] = self._carregar()

    def criar(
        self,
        placa: str,
        motivo: str = "",
        usuario: str = "",
        ativo: bool = True,
    ) -> ListaNegra:
        placa = (placa or "").strip().upper()
        if not placa:
            raise ValueError("Informe a placa do veiculo.")

        registro = ListaNegra(
            id=self._proximo_id(self._registros),
            placa=placa,
            motivo=(motivo or "").strip(),
            ativo=bool(ativo),
            usuario=usuario,
            data=datetime.now().strftime(FORMATO_DATA),
            empresa_id=getattr(self, "_empresa_id", None),
        )
        self._registros.append(registro)
        self._persistir()
        return registro

    def atualizar(
        self,
        id_registro: int,
        placa: str | None = None,
        motivo: str | None = None,
        ativo: bool | None = None,
    ) -> Optional[ListaNegra]:
        registro = self.buscar_por_id(id_registro)
        if registro is None:
            return None
        if placa is not None:
            placa = placa.strip().upper()
            if not placa:
                raise ValueError("Informe a placa do veiculo.")
            registro.placa = placa
        if motivo is not None:
            registro.motivo = motivo
        if ativo is not None:
            registro.ativo = bool(ativo)
        self._persistir()
        return registro

    def verificar_placa(self, placa: str) -> Optional[ListaNegra]:
        """Retorna o registro ativo da placa, se bloqueado."""
        placa = (placa or "").strip().upper()
        for registro in self._registros:
            if registro.ativo and registro.placa == placa:
                return registro
        return None

    def _persistir(self) -> None:
        self._salvar(self._registros)
