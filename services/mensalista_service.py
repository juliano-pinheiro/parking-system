"""
Servico de Mensalistas.

Cadastro completo de mensalistas, pagamento de mensalidades, historico,
inadimplencia e bloqueio automatico.
"""

from datetime import datetime
from typing import List, Optional

from models.mensalista import (
    Mensalista,
    Mensalidade,
    FORMATO_DATA,
    STATUS_ATIVO,
    STATUS_BLOQUEADO,
    STATUS_INATIVO,
    MENSALIDADE_PENDENTE,
    MENSALIDADE_PAGO,
    MENSALIDADE_ATRASADO,
    MENSALIDADE_CANCELADO,
)
from services.base_supabase_service import BaseSupabaseService
from supabase_client import supabase


class MensalistaService(BaseSupabaseService):
    """Regras de negocio e persistencia dos mensalistas."""

    TABELA = "mensalistas"
    MODELO = Mensalista
    CAMPOS_DATA = ("criado_em", "alterado_em")

    def __init__(self):
        self._registros: List[Mensalista] = self._carregar()
        self._mensalidades: List[Mensalidade] = self._carregar_mensalidades()

    def _carregar_mensalidades(self) -> List[Mensalidade]:
        try:
            resposta = supabase.table("mensalidades").select("*").order("id").execute()
        except Exception:
            return []
        mensalidades = []
        for item in resposta.data:
            item = dict(item)
            item["data_pagamento"] = self._converter_iso_para_interna(item.get("data_pagamento"))
            item["criado_em"] = self._converter_iso_para_interna(item.get("criado_em"))
            mensalidades.append(Mensalidade.from_dict(item))
        return mensalidades

    def _salvar_mensalidades(self) -> None:
        try:
            supabase.table("mensalidades").delete().neq("id", -1).execute()
        except Exception:
            return
        if not self._mensalidades:
            return
        dados = []
        for m in self._mensalidades:
            item = m.to_dict()
            item["data_pagamento"] = self._converter_interna_para_iso(item.get("data_pagamento"))
            item["criado_em"] = self._converter_interna_para_iso(item.get("criado_em"))
            dados.append(item)
        try:
            supabase.table("mensalidades").insert(dados).execute()
        except Exception:
            pass

    # =====================================================
    # CRUD MENSALISTA
    # =====================================================

    def criar(
        self,
        nome: str,
        cpf_cnpj: str = "",
        telefone: str = "",
        email: str = "",
        valor_mensal: float = 0.0,
        dia_vencimento: int = 5,
        cliente_id: int | None = None,
    ) -> Mensalista:
        nome = (nome or "").strip()
        if not nome:
            raise ValueError("Informe o nome do mensalista.")
        if valor_mensal is None or valor_mensal < 0:
            raise ValueError("Informe um valor mensal valido.")
        if not (1 <= int(dia_vencimento or 5) <= 31):
            raise ValueError("Dia de vencimento invalido (1 a 31).")

        mensalista = Mensalista(
            id=self._proximo_id(self._registros),
            nome=nome,
            cliente_id=cliente_id,
            cpf_cnpj=cpf_cnpj,
            telefone=telefone,
            email=email,
            valor_mensal=round(float(valor_mensal), 2),
            dia_vencimento=int(dia_vencimento),
            status=STATUS_ATIVO,
        )
        self._registros.append(mensalista)
        self._persistir()
        return mensalista

    def atualizar(
        self,
        id_mensalista: int,
        nome: str | None = None,
        cpf_cnpj: str | None = None,
        telefone: str | None = None,
        email: str | None = None,
        valor_mensal: float | None = None,
        dia_vencimento: int | None = None,
        status: str | None = None,
    ) -> Optional[Mensalista]:
        mensalista = self.buscar_por_id(id_mensalista)
        if mensalista is None:
            return None
        if nome is not None:
            nome = nome.strip()
            if not nome:
                raise ValueError("Informe o nome do mensalista.")
            mensalista.nome = nome
        if cpf_cnpj is not None:
            mensalista.cpf_cnpj = cpf_cnpj
        if telefone is not None:
            mensalista.telefone = telefone
        if email is not None:
            mensalista.email = email
        if valor_mensal is not None:
            if valor_mensal < 0:
                raise ValueError("Valor mensal invalido.")
            mensalista.valor_mensal = round(float(valor_mensal), 2)
        if dia_vencimento is not None:
            if not (1 <= int(dia_vencimento) <= 31):
                raise ValueError("Dia de vencimento invalido.")
            mensalista.dia_vencimento = int(dia_vencimento)
        if status is not None:
            if status not in (STATUS_ATIVO, STATUS_BLOQUEADO, STATUS_INATIVO):
                raise ValueError("Status invalido.")
            mensalista.status = status
        mensalista.alterado_em = datetime.now().strftime(FORMATO_DATA)
        self._persistir()
        return mensalista

    def bloquear(self, id_mensalista: int) -> Optional[Mensalista]:
        """Bloqueia um mensalista (bloqueio automatico por inadimplencia)."""
        mensalista = self.buscar_por_id(id_mensalista)
        if mensalista is None:
            return None
        mensalista.status = STATUS_BLOQUEADO
        mensalista.alterado_em = datetime.now().strftime(FORMATO_DATA)
        self._persistir()
        return mensalista

    def desbloquear(self, id_mensalista: int) -> Optional[Mensalista]:
        mensalista = self.buscar_por_id(id_mensalista)
        if mensalista is None:
            return None
        mensalista.status = STATUS_ATIVO
        mensalista.alterado_em = datetime.now().strftime(FORMATO_DATA)
        self._persistir()
        return mensalista

    # =====================================================
    # MENSALIDADES
    # =====================================================

    def gerar_mensalidade(self, id_mensalista: int, competencia: str) -> Mensalidade:
        """Gera uma mensalidade para o mensalista."""
        mensalista = self.buscar_por_id(id_mensalista)
        if mensalista is None:
            raise ValueError("Mensalista nao encontrado.")
        if not competencia:
            raise ValueError("Informe a competencia (MM/AAAA).")
        if any(m.mensalista_id == id_mensalista and m.competencia == competencia for m in self._mensalidades):
            raise ValueError("Ja existe mensalidade para essa competencia.")

        mensalidade = Mensalidade(
            id=self._proximo_id(self._mensalidades),
            mensalista_id=id_mensalista,
            competencia=competencia,
            valor=round(float(mensalista.valor_mensal), 2),
            status=MENSALIDADE_PENDENTE,
        )
        self._mensalidades.append(mensalidade)
        self._salvar_mensalidades()
        return mensalidade

    def pagar_mensalidade(
        self,
        id_mensalidade: int,
        forma_pagamento: str = "dinheiro",
        data_pagamento: str | None = None,
    ) -> Optional[Mensalidade]:
        """Registra o pagamento de uma mensalidade."""
        mensalidade = self.buscar_mensalidade_por_id(id_mensalidade)
        if mensalidade is None:
            return None
        if mensalidade.status == MENSALIDADE_PAGO:
            raise ValueError("Esta mensalidade ja foi paga.")

        mensalidade.status = MENSALIDADE_PAGO
        mensalidade.forma_pagamento = forma_pagamento
        mensalidade.data_pagamento = data_pagamento or datetime.now().strftime(FORMATO_DATA)
        self._salvar_mensalidades()
        return mensalidade

    def buscar_mensalidade_por_id(self, id_mensalidade: int) -> Optional[Mensalidade]:
        for m in self._mensalidades:
            if m.id == id_mensalidade:
                return m
        return None

    def mensalidades_do_mensalista(self, id_mensalista: int) -> List[Mensalidade]:
        return [m for m in self._mensalidades if m.mensalista_id == id_mensalista]

    def listar_mensalidades(self) -> List[Mensalidade]:
        return list(self._mensalidades)

    # =====================================================
    # INADIMPLENCIA / BLOQUEIO AUTOMATICO
    # =====================================================

    def verificar_inadimplencia(self) -> List[Mensalista]:
        """
        Marca mensalidades vencidas como 'atrasado' e bloqueia
        automaticamente mensalistas com mensalidade em atraso.
        """
        hoje = datetime.now()
        competencia_atual = hoje.strftime("%m/%Y")
        bloqueados = []

        for mensalidade in self._mensalidades:
            if mensalidade.status != MENSALIDADE_PENDENTE:
                continue
            if mensalidade.competencia < competencia_atual:
                mensalidade.status = MENSALIDADE_ATRASADO
                mensalista = self.buscar_por_id(mensalidade.mensalista_id)
                if mensalista and mensalista.status == STATUS_ATIVO:
                    mensalista.status = STATUS_BLOQUEADO
                    mensalista.alterado_em = datetime.now().strftime(FORMATO_DATA)
                    bloqueados.append(mensalista)

        if bloqueados:
            self._persistir()
        self._salvar_mensalidades()
        return bloqueados

    def _persistir(self) -> None:
        self._salvar(self._registros)
