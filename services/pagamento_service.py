"""
Servico de Pagamentos.

Todo ticket pago gera automaticamente um pagamento, uma movimentacao
de caixa e um lancamento financeiro. Pagamentos nunca sao excluidos:
usam-se os status 'cancelado' e 'estornado'.
"""

from datetime import datetime
from typing import List, Optional

from models.pagamento import (
    Pagamento,
    FORMATO_DATA,
    STATUS_ATIVO,
    STATUS_CANCELADO,
    STATUS_ESTORNADO,
)
from services.base_supabase_service import BaseSupabaseService


class PagamentoService(BaseSupabaseService):
    """Regras de negocio e persistencia dos pagamentos."""

    TABELA = "pagamentos"
    SCOPED_EMPRESA = True
    MODELO = Pagamento
    CAMPOS_DATA = ("data", "criado_em", "alterado_em")

    def __init__(self, caixa_service=None, financeiro_service=None, empresa_id: Optional[int] = None):
        self._empresa_id = empresa_id
        self._registros: List[Pagamento] = self._carregar()
        self._caixa_service = caixa_service
        self._financeiro_service = financeiro_service

    def registrar_pagamento_ticket(
        self,
        ticket,
        forma_pagamento: str = "dinheiro",
        operador: str | None = None,
    ) -> Optional[Pagamento]:
        """
        Registra o pagamento de um ticket fechado.
        Gera o pagamento, a movimentacao de caixa e o lancamento financeiro.
        """
        if not ticket or not ticket.valor or ticket.valor <= 0:
            return None

        caixa = self._caixa_service.caixa_aberto() if self._caixa_service else None
        caixa_id = caixa.id if caixa else None

        pagamento = Pagamento(
            id=self._proximo_id(self._registros),
            ticket_numero=ticket.numero,
            valor=round(float(ticket.valor), 2),
            forma_pagamento=forma_pagamento,
            data=ticket.saida or datetime.now().strftime(FORMATO_DATA),
            operador=operador,
            caixa_id=caixa_id,
            status=STATUS_ATIVO,
        )
        self._registros.append(pagamento)
        self._persistir()

        # Movimentacao de caixa (se houver caixa aberto)
        if caixa and self._caixa_service:
            self._caixa_service.registrar_pagamento(
                caixa.id,
                pagamento.valor,
                forma_pagamento,
                f"Ticket #{ticket.numero} - {ticket.placa}",
                operador,
            )

        # Lancamento financeiro (receita)
        if self._financeiro_service:
            try:
                self._financeiro_service.registrar_receita_ticket(ticket)
            except Exception:
                pass

        return pagamento

    def cancelar(
        self,
        id_pagamento: int,
        motivo: str,
        operador: str | None = None,
        autorizador: str | None = None,
    ) -> Optional[Pagamento]:
        """Cancela (logicamente) um pagamento."""
        pagamento = self.buscar_por_id(id_pagamento)
        if pagamento is None:
            return None
        if pagamento.status != STATUS_ATIVO:
            raise ValueError("Somente pagamentos ativos podem ser cancelados.")
        if not (motivo or "").strip():
            raise ValueError("Informe o motivo do cancelamento.")

        pagamento.status = STATUS_CANCELADO
        pagamento.motivo_cancelamento = motivo
        pagamento.autorizador = autorizador
        pagamento.alterado_em = datetime.now().strftime(FORMATO_DATA)
        self._persistir()
        return pagamento

    def estornar(
        self,
        id_pagamento: int,
        motivo: str,
        operador: str | None = None,
        autorizador: str | None = None,
    ) -> Optional[Pagamento]:
        """Estorna (logicamente) um pagamento."""
        pagamento = self.buscar_por_id(id_pagamento)
        if pagamento is None:
            return None
        if pagamento.status != STATUS_ATIVO:
            raise ValueError("Somente pagamentos ativos podem ser estornados.")
        if not (motivo or "").strip():
            raise ValueError("Informe o motivo do estorno.")

        pagamento.status = STATUS_ESTORNADO
        pagamento.motivo_cancelamento = motivo
        pagamento.autorizador = autorizador
        pagamento.alterado_em = datetime.now().strftime(FORMATO_DATA)
        self._persistir()
        return pagamento

    def _persistir(self) -> None:
        self._salvar(self._registros)
