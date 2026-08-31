"""
Servico de NFSe (Nota Fiscal de Servico simplificada).

Emissao, listagem e cancelamento de notas vinculadas a tickets.
As notas nunca sao excluidas (cancelamento logico via status).
"""

from datetime import datetime
from typing import List, Optional

from models.nfse import Nfse, FORMATO_DATA
from services.base_supabase_service import BaseSupabaseService


class NfseService(BaseSupabaseService):
    """Regras de negocio e persistencia das notas fiscais de servico."""

    TABELA = "nfse"
    SCOPED_EMPRESA = True
    MODELO = Nfse
    CAMPOS_DATA = ("data", "criado_em")

    def __init__(self, empresa_id: Optional[int] = None):
        self._empresa_id = empresa_id
        self._registros: List[Nfse] = self._carregar()

    def proximo_numero(self) -> int:
        """Proximo numero sequencial da nota para a empresa atual."""
        ativas = [n for n in self._registros if n.status != "cancelada"]
        return max([n.numero for n in ativas], default=0) + 1

    def emitir(
        self,
        valor: float,
        ticket_numero: int | None = None,
        placa: str = "",
        cpf_cnpj: str = "",
        razao_social: str = "",
        servico: str = "Estacionamento de veiculos",
        usuario: str = "",
    ) -> Nfse:
        if valor is None or valor <= 0:
            raise ValueError("Informe um valor valido para a nota.")
        if not cpf_cnpj and not razao_social:
            raise ValueError("Informe o CPF/CNPJ ou a razao social do tomador do servico.")

        nota = Nfse(
            id=self._proximo_id(self._registros),
            numero=self.proximo_numero(),
            ticket_numero=int(ticket_numero) if ticket_numero else None,
            placa=(placa or "").strip().upper(),
            valor=round(float(valor), 2),
            cpf_cnpj=(cpf_cnpj or "").strip(),
            razao_social=(razao_social or "").strip(),
            servico=(servico or "Estacionamento de veiculos").strip(),
            data=datetime.now().strftime(FORMATO_DATA),
            usuario=usuario,
            status="emitida",
            empresa_id=getattr(self, "_empresa_id", None),
        )
        self._registros.append(nota)
        self._persistir()
        return nota

    def cancelar(self, id_nota: int, autorizador: str = "") -> Optional[Nfse]:
        nota = self.buscar_por_id(id_nota)
        if nota is None:
            return None
        nota.status = "cancelada"
        nota.usuario = autorizador or nota.usuario
        self._persistir()
        return nota

    def _persistir(self) -> None:
        self._salvar(self._registros)
