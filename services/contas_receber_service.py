"""
Servico de Contas a Receber.

Contas a receber geradas a partir de convenios (faturamento posterior).
Permite baixa (pagamento), historico e cancelamento.
"""

from datetime import datetime
from typing import List, Optional

from models.convenio import ContaReceber, FORMATO_DATA, CONTA_ABERTA, CONTA_PAGA, CONTA_CANCELADA
from services.base_supabase_service import BaseSupabaseService


class ContasReceberService(BaseSupabaseService):
    """Regras de negocio e persistencia das contas a receber."""

    TABELA = "contas_receber"
    MODELO = ContaReceber
    CAMPOS_DATA = ("vencimento", "data_pagamento", "criado_em")

    def __init__(self):
        self._registros: List[ContaReceber] = self._carregar()

    def criar(
        self,
        convenio_id: int | None,
        valor: float,
        descricao: str = "",
        vencimento: str | None = None,
    ) -> ContaReceber:
        if valor is None or valor <= 0:
            raise ValueError("Informe um valor valido para a conta a receber.")

        conta = ContaReceber(
            id=self._proximo_id(self._registros),
            convenio_id=convenio_id,
            descricao=descricao,
            valor=round(float(valor), 2),
            vencimento=vencimento,
            status=CONTA_ABERTA,
        )
        self._registros.append(conta)
        self._persistir()
        return conta

    def baixar(
        self,
        id_conta: int,
        forma_pagamento: str = "dinheiro",
        data_pagamento: str | None = None,
    ) -> Optional[ContaReceber]:
        """Registra o pagamento (baixa) de uma conta a receber."""
        conta = self.buscar_por_id(id_conta)
        if conta is None:
            return None
        if conta.status == CONTA_PAGA:
            raise ValueError("Esta conta ja foi paga.")

        conta.status = CONTA_PAGA
        conta.forma_pagamento = forma_pagamento
        conta.data_pagamento = data_pagamento or datetime.now().strftime(FORMATO_DATA)
        self._persistir()
        return conta

    def cancelar(self, id_conta: int) -> Optional[ContaReceber]:
        conta = self.buscar_por_id(id_conta)
        if conta is None:
            return None
        conta.status = CONTA_CANCELADA
        self._persistir()
        return conta

    def _persistir(self) -> None:
        self._salvar(self._registros)
