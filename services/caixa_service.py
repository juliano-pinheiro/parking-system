"""
Servico de Caixa.

Implementa abertura e fechamento de caixa, sangria e suprimento.
O fechamento calcula automaticamente os totais por forma de pagamento,
o valor esperado, o valor contado, a diferenca e o status.
Nao permite fechar o caixa duas vezes.
"""

from datetime import datetime
from typing import List, Optional

from models.caixa import Caixa, MovimentacaoCaixa, FORMATO_DATA, STATUS_ABERTO, STATUS_FECHADO
from services.base_supabase_service import BaseSupabaseService
from supabase_client import supabase

# Formas de pagamento consideradas no fechamento
FORMAS_FECHAMENTO = (
    "dinheiro", "pix", "cartao_credito", "cartao_debito",
    "convenio", "mensalista", "cortesia",
)


class CaixaService(BaseSupabaseService):
    """Regras de negocio e persistencia dos caixas."""

    TABELA = "caixas"
    SCOPED_EMPRESA = True
    MODELO = Caixa
    CAMPOS_DATA = ("data_abertura", "data_fechamento", "criado_em", "alterado_em")

    def __init__(self, empresa_id: Optional[int] = None):
        self._empresa_id = empresa_id
        self._registros: List[Caixa] = self._carregar()
        self._movimentacoes: List[MovimentacaoCaixa] = self._carregar_movimentacoes()

    def recarregar(self, empresa_id: Optional[int] = None) -> None:
        """Recarrega caixas e movimentacoes, filtrando pela empresa."""
        self._empresa_id = empresa_id
        self._registros = self._carregar()
        self._movimentacoes = self._carregar_movimentacoes()

    # =====================================================
    # MOVIMENTACOES
    # =====================================================

    def _carregar_movimentacoes(self) -> List[MovimentacaoCaixa]:
        try:
            query = supabase.table("movimentacoes_caixa").select("*").order("id")
            eid = getattr(self, "_empresa_id", None)
            if eid is not None:
                query = query.eq("empresa_id", eid)
            resposta = query.execute()
        except Exception:
            return []
        movs = []
        for item in resposta.data:
            item = dict(item)
            item["data"] = self._converter_iso_para_interna(item.get("data"))
            item["criado_em"] = self._converter_iso_para_interna(item.get("criado_em"))
            movs.append(MovimentacaoCaixa.from_dict(item))
        return movs

    def _salvar_movimentacoes(self) -> None:
        try:
            supabase.table("movimentacoes_caixa").delete().neq("id", -1).execute()
        except Exception:
            return
        if not self._movimentacoes:
            return
        dados = []
        for mov in self._movimentacoes:
            item = mov.to_dict()
            item["data"] = self._converter_interna_para_iso(item.get("data"))
            item["criado_em"] = self._converter_interna_para_iso(item.get("criado_em"))
            eid = getattr(self, "_empresa_id", None)
            if eid is not None:
                item["empresa_id"] = eid
            dados.append(item)
        try:
            supabase.table("movimentacoes_caixa").insert(dados).execute()
        except Exception:
            pass

    def _adicionar_movimentacao(
        self,
        caixa_id: int,
        tipo: str,
        valor: float,
        descricao: str = "",
        forma_pagamento: str | None = None,
        usuario: str | None = None,
    ) -> MovimentacaoCaixa:
        mov = MovimentacaoCaixa(
            id=self._proximo_id(self._movimentacoes),
            caixa_id=caixa_id,
            tipo=tipo,
            descricao=descricao,
            valor=round(float(valor), 2),
            forma_pagamento=forma_pagamento,
            data=datetime.now().strftime(FORMATO_DATA),
            usuario=usuario,
            empresa_id=getattr(self, "_empresa_id", None),
        )
        self._movimentacoes.append(mov)
        self._salvar_movimentacoes()
        return mov

    # =====================================================
    # CAIXA
    # =====================================================

    def caixa_aberto(self) -> Optional[Caixa]:
        """Retorna o caixa aberto atual, se houver."""
        for caixa in self._registros:
            if caixa.status == STATUS_ABERTO:
                return caixa
        return None

    def abrir(
        self,
        operador: str,
        valor_inicial: float = 0.0,
        observacoes: str = "",
        usuario: str | None = None,
        ip: str | None = None,
    ) -> Caixa:
        """Abre um novo caixa. Nao permite abrir se ja houver um aberto."""
        if self.caixa_aberto() is not None:
            raise ValueError("Ja existe um caixa aberto. Feche-o antes de abrir outro.")

        operador = (operador or "").strip()
        if not operador:
            raise ValueError("Informe o operador do caixa.")

        caixa = Caixa(
            id=self._proximo_id(self._registros),
            operador=operador,
            data_abertura=datetime.now().strftime(FORMATO_DATA),
            valor_inicial=round(float(valor_inicial or 0), 2),
            status=STATUS_ABERTO,
            observacoes=observacoes,
            empresa_id=getattr(self, "_empresa_id", None),
            usuario=usuario,
            ip=ip,
        )
        self._registros.append(caixa)
        self._persistir()

        # Registra o valor inicial como suprimento inicial
        if caixa.valor_inicial > 0:
            self._adicionar_movimentacao(
                caixa.id, "suprimento", caixa.valor_inicial,
                "Valor inicial de abertura", "dinheiro", usuario,
            )
        return caixa

    def fechar(
        self,
        id_caixa: int,
        valor_contado: float = 0.0,
        observacoes: str = "",
        usuario: str | None = None,
    ) -> Caixa:
        """Fecha um caixa, calculando totais, diferenca e status."""
        caixa = self.buscar_por_id(id_caixa)
        if caixa is None:
            raise ValueError("Caixa nao encontrado.")
        if caixa.status == STATUS_FECHADO:
            raise ValueError("Este caixa ja foi fechado. Nao e possivel fechar duas vezes.")

        # Calcula os totais por forma de pagamento a partir das movimentacoes
        totais = self.totais_por_forma(id_caixa)
        valor_esperado = round(sum(totais.values()), 2)

        caixa.valor_esperado = valor_esperado
        caixa.valor_contado = round(float(valor_contado or 0), 2)
        caixa.diferenca = round(caixa.valor_contado - valor_esperado, 2)
        caixa.data_fechamento = datetime.now().strftime(FORMATO_DATA)
        caixa.status = STATUS_FECHADO
        caixa.observacoes = observacoes or caixa.observacoes
        caixa.alterado_em = datetime.now().strftime(FORMATO_DATA)
        caixa.usuario = usuario or caixa.usuario
        self._persistir()
        return caixa

    def sangria(
        self,
        id_caixa: int,
        valor: float,
        motivo: str = "",
        usuario: str | None = None,
    ) -> MovimentacaoCaixa:
        """Registra uma sangria (retirada de dinheiro) no caixa."""
        caixa = self.buscar_por_id(id_caixa)
        if caixa is None or caixa.status != STATUS_ABERTO:
            raise ValueError("Caixa nao encontrado ou ja fechado.")
        if valor is None or valor <= 0:
            raise ValueError("Informe um valor valido para a sangria.")
        return self._adicionar_movimentacao(
            id_caixa, "sangria", valor, motivo or "Sangria", "dinheiro", usuario,
        )

    def suprimento(
        self,
        id_caixa: int,
        valor: float,
        motivo: str = "",
        usuario: str | None = None,
    ) -> MovimentacaoCaixa:
        """Registra um suprimento (entrada de dinheiro) no caixa."""
        caixa = self.buscar_por_id(id_caixa)
        if caixa is None or caixa.status != STATUS_ABERTO:
            raise ValueError("Caixa nao encontrado ou ja fechado.")
        if valor is None or valor <= 0:
            raise ValueError("Informe um valor valido para o suprimento.")
        return self._adicionar_movimentacao(
            id_caixa, "suprimento", valor, motivo or "Suprimento", "dinheiro", usuario,
        )

    def registrar_pagamento(
        self,
        id_caixa: int,
        valor: float,
        forma_pagamento: str,
        descricao: str = "",
        usuario: str | None = None,
    ) -> Optional[MovimentacaoCaixa]:
        """Registra um pagamento (entrada) no caixa aberto."""
        caixa = self.buscar_por_id(id_caixa)
        if caixa is None or caixa.status != STATUS_ABERTO:
            return None
        return self._adicionar_movimentacao(
            id_caixa, "entrada", valor, descricao, forma_pagamento, usuario,
        )

    # =====================================================
    # TOTAIS
    # =====================================================

    def totais_por_forma(self, id_caixa: int) -> dict:
        """Retorna os totais recebidos por forma de pagamento no caixa."""
        totais = {forma: 0.0 for forma in FORMAS_FECHAMENTO}
        for mov in self._movimentacoes:
            if mov.caixa_id != id_caixa:
                continue
            if mov.tipo == "entrada":
                forma = mov.forma_pagamento or "dinheiro"
                if forma in totais:
                    totais[forma] += mov.valor
        return {forma: round(valor, 2) for forma, valor in totais.items()}

    def movimentacoes_do_caixa(self, id_caixa: int) -> List[MovimentacaoCaixa]:
        """Retorna as movimentacoes de um caixa."""
        return [m for m in self._movimentacoes if m.caixa_id == id_caixa]

    def _persistir(self) -> None:
        self._salvar(self._registros)
