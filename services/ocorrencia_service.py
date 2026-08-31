"""
Servico de Ocorrencias / Termo de Avarias.

Registro de ocorrencias com veiculos (avaria, perda, etc.).
Exclusao logica via 'status'.
"""

from datetime import datetime
from typing import List, Optional

from models.ocorrencia import Ocorrencia, FORMATO_DATA
from services.base_supabase_service import BaseSupabaseService

TIPOS_VALIDOS = ("avaria", "perda", "outro")
STATUS_VALIDOS = ("aberta", "resolvida")


class OcorrenciaService(BaseSupabaseService):
    """Regras de negocio e persistencia das ocorrencias."""

    TABELA = "ocorrencias"
    SCOPED_EMPRESA = True
    MODELO = Ocorrencia
    CAMPOS_DATA = ("data", "criado_em", "alterado_em")

    def __init__(self, empresa_id: Optional[int] = None):
        self._empresa_id = empresa_id
        self._registros: List[Ocorrencia] = self._carregar()

    def criar(
        self,
        tipo: str = "avaria",
        placa: str = "",
        descricao: str = "",
        ticket_numero: int | None = None,
        usuario: str = "",
        autorizador: str = "",
    ) -> Ocorrencia:
        if tipo not in TIPOS_VALIDOS:
            raise ValueError("Tipo de ocorrencia invalido.")
        descricao = (descricao or "").strip()
        if not descricao:
            raise ValueError("Informe a descricao da ocorrencia.")

        ocorrencia = Ocorrencia(
            id=self._proximo_id(self._registros),
            tipo=tipo,
            placa=(placa or "").strip().upper(),
            ticket_numero=int(ticket_numero) if ticket_numero else None,
            descricao=descricao,
            status="aberta",
            usuario=usuario,
            autorizador=(autorizador or "").strip(),
            data=datetime.now().strftime(FORMATO_DATA),
            empresa_id=getattr(self, "_empresa_id", None),
        )
        self._registros.append(ocorrencia)
        self._persistir()
        return ocorrencia

    def atualizar(
        self,
        id_ocorrencia: int,
        tipo: str | None = None,
        placa: str | None = None,
        descricao: str | None = None,
        ticket_numero: int | None = None,
        status: str | None = None,
        autorizador: str | None = None,
    ) -> Optional[Ocorrencia]:
        ocorrencia = self.buscar_por_id(id_ocorrencia)
        if ocorrencia is None:
            return None
        if tipo is not None:
            if tipo not in TIPOS_VALIDOS:
                raise ValueError("Tipo de ocorrencia invalido.")
            ocorrencia.tipo = tipo
        if placa is not None:
            ocorrencia.placa = placa.strip().upper()
        if descricao is not None:
            descricao = descricao.strip()
            if not descricao:
                raise ValueError("Informe a descricao da ocorrencia.")
            ocorrencia.descricao = descricao
        if ticket_numero is not None:
            ocorrencia.ticket_numero = int(ticket_numero) if ticket_numero else None
        if status is not None:
            if status not in STATUS_VALIDOS:
                raise ValueError("Status de ocorrencia invalido.")
            ocorrencia.status = status
        if autorizador is not None:
            ocorrencia.autorizador = autorizador
        ocorrencia.alterado_em = datetime.now().strftime(FORMATO_DATA)
        self._persistir()
        return ocorrencia

    def _persistir(self) -> None:
        self._salvar(self._registros)
