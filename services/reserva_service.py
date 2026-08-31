"""
Servico de Reservas de Vaga.

CRUD de reservas com cliente, periodo, vaga e valor.
Exclusao logica via 'status'.
"""

from datetime import datetime
from typing import List, Optional

from models.reserva import Reserva, FORMATO_DATA
from services.base_supabase_service import BaseSupabaseService

STATUS_VALIDOS = ("ativa", "concluida", "cancelada")


class ReservaService(BaseSupabaseService):
    """Regras de negocio e persistencia das reservas de vaga."""

    TABELA = "reservas"
    SCOPED_EMPRESA = True
    MODELO = Reserva
    CAMPOS_DATA = ("data_inicio", "data_fim", "criado_em", "alterado_em")

    def __init__(self, empresa_id: Optional[int] = None):
        self._empresa_id = empresa_id
        self._registros: List[Reserva] = self._carregar()

    def criar(
        self,
        cliente: str,
        data_inicio: str,
        data_fim: str,
        telefone: str = "",
        placa: str = "",
        tipo_veiculo: str = "Carro",
        vaga: int | None = None,
        valor: float = 0.0,
        observacao: str = "",
        usuario: str = "",
    ) -> Reserva:
        cliente = (cliente or "").strip()
        if not cliente:
            raise ValueError("Informe o nome do cliente.")
        if not data_inicio or not data_fim:
            raise ValueError("Informe o periodo da reserva.")
        if self._periodo_invalido(data_inicio, data_fim):
            raise ValueError("A data de fim da reserva nao pode ser anterior a data de inicio.")

        reserva = Reserva(
            id=self._proximo_id(self._registros),
            cliente=cliente,
            telefone=(telefone or "").strip(),
            placa=(placa or "").strip().upper(),
            tipo_veiculo=(tipo_veiculo or "Carro").strip() or "Carro",
            vaga=int(vaga) if vaga else None,
            data_inicio=data_inicio,
            data_fim=data_fim,
            valor=round(float(valor or 0), 2),
            status="ativa",
            observacao=(observacao or "").strip(),
            usuario=usuario,
            empresa_id=getattr(self, "_empresa_id", None),
        )
        self._registros.append(reserva)
        self._persistir()
        return reserva

    def atualizar(
        self,
        id_reserva: int,
        cliente: str | None = None,
        data_inicio: str | None = None,
        data_fim: str | None = None,
        telefone: str | None = None,
        placa: str | None = None,
        tipo_veiculo: str | None = None,
        vaga: int | None = None,
        valor: float | None = None,
        observacao: str | None = None,
        status: str | None = None,
    ) -> Optional[Reserva]:
        reserva = self.buscar_por_id(id_reserva)
        if reserva is None:
            return None
        if cliente is not None:
            cliente = cliente.strip()
            if not cliente:
                raise ValueError("Informe o nome do cliente.")
            reserva.cliente = cliente
        if data_inicio is not None:
            reserva.data_inicio = data_inicio
        if data_fim is not None:
            reserva.data_fim = data_fim
        if reserva.data_inicio and reserva.data_fim and self._periodo_invalido(reserva.data_inicio, reserva.data_fim):
            raise ValueError("A data de fim da reserva nao pode ser anterior a data de inicio.")
        if telefone is not None:
            reserva.telefone = telefone
        if placa is not None:
            reserva.placa = placa.strip().upper()
        if tipo_veiculo is not None:
            reserva.tipo_veiculo = tipo_veiculo.strip() or "Carro"
        if vaga is not None:
            reserva.vaga = int(vaga) if vaga else None
        if valor is not None:
            reserva.valor = round(float(valor), 2)
        if observacao is not None:
            reserva.observacao = observacao
        if status is not None:
            if status not in STATUS_VALIDOS:
                raise ValueError("Status de reserva invalido.")
            reserva.status = status
        reserva.alterado_em = datetime.now().strftime(FORMATO_DATA)
        self._persistir()
        return reserva

    def listar_ativas(self) -> List[Reserva]:
        return [r for r in self._registros if r.status == "ativa"]

    def _periodo_invalido(self, inicio: str, fim: str) -> bool:
        try:
            return datetime.strptime(fim, "%d/%m/%Y %H:%M") < datetime.strptime(inicio, "%d/%m/%Y %H:%M")
        except (ValueError, TypeError):
            try:
                return datetime.strptime(fim, FORMATO_DATA) < datetime.strptime(inicio, FORMATO_DATA)
            except (ValueError, TypeError):
                return False

    def _persistir(self) -> None:
        self._salvar(self._registros)
