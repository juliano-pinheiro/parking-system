"""
Servico financeiro.

Contem as regras de negocio e a persistencia dos lancamentos financeiros
(entradas/receitas e saidas/despesas) no Supabase (tabela 'financeiro').
"""

from datetime import datetime, timedelta
from typing import List, Optional

from models.lancamento import (
    Lancamento,
    TIPOS_VALIDOS,
    FORMAS_PAGAMENTO_VALIDAS,
    ORIGEM_TICKET,
    ORIGEM_MANUAL,
    FORMATO_DATA,
)
from supabase_client import supabase

# Formas de pagamento exibiveis (rotulo)
FORMAS_PAGAMENTO_LABEL = {
    "dinheiro": "Dinheiro",
    "pix": "Pix",
    "cartao_credito": "Cartão de crédito",
    "cartao_debito": "Cartão de débito",
}


class FinanceiroService:
    """Regras de negocio e persistencia dos lancamentos financeiros."""

    def __init__(self, empresa_id: Optional[int] = None):
        self._empresa_id = empresa_id
        self.lancamentos: List[Lancamento] = self._carregar(empresa_id)

    # =====================================================
    # PERSISTENCIA (SUPABASE)
    # =====================================================

    def recarregar(self, empresa_id: Optional[int] = None) -> None:
        """Recarrega os lancamentos, filtrando pela empresa quando aplicavel."""
        self._empresa_id = empresa_id
        self.lancamentos = self._carregar(empresa_id)

    def _carregar(self, empresa_id: Optional[int] = None) -> List[Lancamento]:
        """Carrega os lancamentos do Supabase (filtrados por empresa se informado)."""
        try:
            query = supabase.table("financeiro").select("*").order("data")
            eid = empresa_id if empresa_id is not None else getattr(self, "_empresa_id", None)
            if eid is not None:
                query = query.eq("empresa_id", eid)
            resposta = query.execute()
        except Exception:
            # Tabela ainda nao existe no Supabase: inicia vazio
            return []

        lancamentos = []
        for item in resposta.data:
            item = dict(item)
            item["data"] = self._converter_iso_para_interna(item.get("data"))
            lancamentos.append(Lancamento.from_dict(item))

        return lancamentos

    def _salvar(self) -> None:
        """Sincroniza os lancamentos em memoria com o Supabase (upsert por id).

        Usa upsert (on_conflict=id) para nao apagar lancamentos de outras
        empresas quando o servico esta isolado por empresa_id.
        """
        if not self.lancamentos:
            return

        dados = []
        for lancamento in self.lancamentos:
            item = lancamento.to_dict()
            item["data"] = self._converter_interna_para_iso(item.get("data"))
            eid = getattr(self, "_empresa_id", None)
            if eid is not None:
                item["empresa_id"] = eid
            dados.append(item)

        try:
            supabase.table("financeiro").upsert(dados, on_conflict="id").execute()
        except Exception as erro:
            raise ValueError(
                "Nao foi possivel salvar no Supabase. Verifique se a tabela 'financeiro' foi criada "
                "(execute o script sql/criar_tabela_financeiro.sql no SQL Editor)."
            ) from erro

    # =====================================================
    # CONVERSAO DE DATAS
    # =====================================================

    @staticmethod
    def _converter_interna_para_iso(data: str | None) -> str | None:
        """DD/MM/YYYY HH:MM:SS -> YYYY-MM-DD HH:MM:SS (ou None)."""
        if not data:
            return None
        try:
            return datetime.strptime(data, FORMATO_DATA).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            return data

    @staticmethod
    def _converter_iso_para_interna(data: str | None) -> str | None:
        """YYYY-MM-DDTHH:MM:SS (ou com espaco) -> DD/MM/YYYY HH:MM:SS (ou None)."""
        if not data:
            return None
        texto = str(data).replace("T", " ").strip()
        if "." in texto:
            texto = texto.split(".")[0]
        try:
            return datetime.strptime(texto, "%Y-%m-%d %H:%M:%S").strftime(FORMATO_DATA)
        except ValueError:
            return str(data)

    # =====================================================
    # CRUD
    # =====================================================

    def _proximo_id(self) -> int:
        """Retorna o proximo id disponivel (maior id existente + 1)."""
        if not self.lancamentos:
            return 1
        return max(l.id for l in self.lancamentos) + 1

    def criar(
        self,
        tipo: str,
        descricao: str,
        valor: float,
        forma_pagamento: str = "dinheiro",
        data: Optional[str] = None,
        origem: str = ORIGEM_MANUAL,
        ticket_numero: Optional[int] = None,
    ) -> Lancamento:
        """Cria e salva um novo lancamento financeiro."""
        tipo = (tipo or "").strip()
        descricao = (descricao or "").strip()
        forma_pagamento = (forma_pagamento or "dinheiro").strip()

        if tipo not in TIPOS_VALIDOS:
            raise ValueError(f"Tipo invalido. Use 'entrada' ou 'saida'.")
        if not descricao:
            raise ValueError("Informe a descricao do lancamento.")
        if valor is None or valor < 0:
            raise ValueError("Informe um valor valido (maior ou igual a zero).")
        if forma_pagamento not in FORMAS_PAGAMENTO_VALIDAS:
            raise ValueError(f"Forma de pagamento invalida. Use uma destas: {', '.join(FORMAS_PAGAMENTO_VALIDAS)}.")

        lancamento = Lancamento(
            id=self._proximo_id(),
            tipo=tipo,
            descricao=descricao,
            valor=round(float(valor), 2),
            forma_pagamento=forma_pagamento,
            data=data or datetime.now().strftime(FORMATO_DATA),
            origem=origem,
            ticket_numero=ticket_numero,
            empresa_id=getattr(self, "_empresa_id", None),
        )
        self.lancamentos.append(lancamento)
        self._salvar()
        return lancamento

    def listar(self) -> List[Lancamento]:
        """Retorna a lista de todos os lancamentos."""
        return list(self.lancamentos)

    def buscar_por_id(self, id_lancamento: int) -> Optional[Lancamento]:
        """Busca um lancamento pelo id. Retorna None se nao existir."""
        for lancamento in self.lancamentos:
            if lancamento.id == id_lancamento:
                return lancamento
        return None

    def atualizar(
        self,
        id_lancamento: int,
        tipo: Optional[str] = None,
        descricao: Optional[str] = None,
        valor: Optional[float] = None,
        forma_pagamento: Optional[str] = None,
        data: Optional[str] = None,
    ) -> Optional[Lancamento]:
        """Atualiza os dados de um lancamento. Retorna o lancamento ou None se nao existir."""
        lancamento = self.buscar_por_id(id_lancamento)
        if lancamento is None:
            return None

        if tipo is not None:
            if tipo not in TIPOS_VALIDOS:
                raise ValueError("Tipo invalido. Use 'entrada' ou 'saida'.")
            lancamento.tipo = tipo

        if descricao is not None:
            descricao = descricao.strip()
            if not descricao:
                raise ValueError("Informe a descricao do lancamento.")
            lancamento.descricao = descricao

        if valor is not None:
            if valor < 0:
                raise ValueError("Informe um valor valido (maior ou igual a zero).")
            lancamento.valor = round(float(valor), 2)

        if forma_pagamento is not None:
            if forma_pagamento not in FORMAS_PAGAMENTO_VALIDAS:
                raise ValueError(f"Forma de pagamento invalida. Use uma destas: {', '.join(FORMAS_PAGAMENTO_VALIDAS)}.")
            lancamento.forma_pagamento = forma_pagamento

        if data is not None:
            lancamento.data = data

        self._salvar()
        return lancamento

    def excluir(self, id_lancamento: int) -> bool:
        """Exclui um lancamento. Retorna True se encontrado."""
        lancamento = self.buscar_por_id(id_lancamento)
        if lancamento is None:
            return False

        self.lancamentos = [l for l in self.lancamentos if l.id != id_lancamento]
        self._salvar()
        return True

    # =====================================================
    # RECEITAS DE TICKETS
    # =====================================================

    def registrar_receita_ticket(self, ticket) -> Optional[Lancamento]:
        """
        Gera um lancamento de receita (entrada) a partir de um ticket fechado.
        Retorna o lancamento criado, ou None se o ticket nao tiver valor.
        """
        if not ticket or not ticket.valor or ticket.valor <= 0:
            return None

        forma = ticket.forma_pagamento or "dinheiro"
        if forma not in FORMAS_PAGAMENTO_VALIDAS:
            forma = "dinheiro"

        return self.criar(
            tipo="entrada",
            descricao=f"Ticket #{ticket.numero} - {ticket.placa}",
            valor=ticket.valor,
            forma_pagamento=forma,
            data=ticket.saida,
            origem=ORIGEM_TICKET,
            ticket_numero=ticket.numero,
        )

    # =====================================================
    # RESUMOS
    # =====================================================

    def _filtrar_por_periodo(self, inicio: str, fim: str) -> List[Lancamento]:
        """Filtra lancamentos cuja data esteja entre inicio e fim (dd/mm/aaaa)."""
        resultado = []
        try:
            dt_inicio = datetime.strptime(inicio, "%d/%m/%Y").date()
            dt_fim = datetime.strptime(fim, "%d/%m/%Y").date()
        except (ValueError, TypeError):
            return list(self.lancamentos)

        for lancamento in self.lancamentos:
            if not lancamento.data:
                continue
            data_lanc_str = lancamento.data.split(" ")[0].strip()
            try:
                dt_lanc = datetime.strptime(data_lanc_str, "%d/%m/%Y").date()
                if dt_inicio <= dt_lanc <= dt_fim:
                    resultado.append(lancamento)
            except (ValueError, TypeError):
                continue
        return resultado

    def resumo_periodo(self, inicio: str, fim: str) -> dict:
        """
        Retorna o resumo financeiro do periodo (inicio/fim em dd/mm/aaaa):
        total de entradas, saidas e saldo.
        """
        lancamentos = self._filtrar_por_periodo(inicio, fim)

        total_entradas = sum(l.valor for l in lancamentos if l.tipo == "entrada")
        total_saidas = sum(l.valor for l in lancamentos if l.tipo == "saida")

        return {
            "total_entradas": round(total_entradas, 2),
            "total_saidas": round(total_saidas, 2),
            "saldo": round(total_entradas - total_saidas, 2),
            "quantidade": len(lancamentos),
        }

    def resumo_por_forma_pagamento(self, inicio: str, fim: str) -> dict:
        """
        Retorna o faturamento (entradas) agrupado por forma de pagamento
        no periodo (inicio/fim em dd/mm/aaaa).
        """
        lancamentos = self._filtrar_por_periodo(inicio, fim)

        resumo = {forma: 0.0 for forma in FORMAS_PAGAMENTO_VALIDAS}
        for lancamento in lancamentos:
            if lancamento.tipo == "entrada":
                forma = lancamento.forma_pagamento
                if forma in resumo:
                    resumo[forma] += lancamento.valor

        return {forma: round(valor, 2) for forma, valor in resumo.items()}

    def periodo_para_datas(self, periodo: str) -> tuple:
        """
        Converte um periodo ('diario', 'semanal', 'mensal') em um par
        (inicio, fim) de datas no formato dd/mm/aaaa.
        """
        hoje = datetime.now()

        if periodo == "diario":
            inicio = hoje
            fim = hoje
        elif periodo == "semanal":
            # Semana de segunda a domingo
            inicio = hoje - timedelta(days=hoje.weekday())
            fim = inicio + timedelta(days=6)
        elif periodo == "mensal":
            inicio = hoje.replace(day=1)
            if inicio.month == 12:
                fim = inicio.replace(year=inicio.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                fim = inicio.replace(month=inicio.month + 1, day=1) - timedelta(days=1)
        else:
            raise ValueError("Periodo invalido. Use 'diario', 'semanal' ou 'mensal'.")

        return inicio.strftime("%d/%m/%Y"), fim.strftime("%d/%m/%Y")
