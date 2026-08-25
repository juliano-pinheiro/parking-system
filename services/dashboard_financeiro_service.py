"""
Servico de Dashboard Financeiro.

Calcula os indicadores financeiros: receita do dia/mes/ano, quantidade
de tickets, ticket medio, receita por operador, por forma de pagamento,
por horario, top operadores, graficos diario/mensal/anual e comparativo
mensal.
"""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import List

from models.lancamento import FORMATO_DATA


class DashboardFinanceiroService:
    """Calcula os indicadores do dashboard financeiro."""

    def __init__(self, financeiro_service=None, pagamento_service=None):
        self._financeiro = financeiro_service
        self._pagamentos = pagamento_service

    def _lancamentos(self) -> List:
        if self._financeiro is None:
            return []
        return self._financeiro.listar()

    def _parse(self, data: str) -> datetime | None:
        if not data:
            return None
        texto = str(data).replace("T", " ").strip()
        if "." in texto:
            texto = texto.split(".")[0]
        texto = texto.rstrip("Z")
        # Remove sufixo de timezone (+00:00, -03:00)
        for sufixo in ("+", "-"):
            idx = texto.rfind(sufixo)
            if idx > 10:
                texto = texto[:idx].strip()
                break
        for formato in (FORMATO_DATA, "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(texto, formato)
            except (ValueError, TypeError):
                continue
        return None

    def _receitas(self, inicio: datetime, fim: datetime) -> List:
        """Retorna os lancamentos de entrada (receitas) no intervalo."""
        resultado = []
        for lancamento in self._lancamentos():
            if lancamento.tipo != "entrada":
                continue
            data = self._parse(lancamento.data)
            if data and inicio <= data <= fim:
                resultado.append(lancamento)
        return resultado

    def gerar(self) -> dict:
        """Gera todos os indicadores do dashboard financeiro."""
        agora = datetime.now()

        # Periodos
        inicio_dia = agora.replace(hour=0, minute=0, second=0, microsecond=0)
        fim_dia = agora.replace(hour=23, minute=59, second=59, microsecond=0)
        inicio_mes = agora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        fim_mes = agora.replace(hour=23, minute=59, second=59, microsecond=0)
        inicio_ano = agora.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        fim_ano = agora.replace(hour=23, minute=59, second=59, microsecond=0)

        receitas_dia = self._receitas(inicio_dia, fim_dia)
        receitas_mes = self._receitas(inicio_mes, fim_mes)
        receitas_ano = self._receitas(inicio_ano, fim_ano)

        receita_dia = round(sum(r.valor for r in receitas_dia), 2)
        receita_mes = round(sum(r.valor for r in receitas_mes), 2)
        receita_ano = round(sum(r.valor for r in receitas_ano), 2)

        quantidade_tickets = len(receitas_mes)
        ticket_medio = round(receita_mes / quantidade_tickets, 2) if quantidade_tickets else 0.0

        # Receita por forma de pagamento (mes)
        por_forma = defaultdict(float)
        for r in receitas_mes:
            por_forma[r.forma_pagamento] += r.valor

        # Receita por operador (mes) - usa ticket_numero para agrupar por ticket
        por_operador = defaultdict(float)
        for r in receitas_mes:
            por_operador[r.origem] += r.valor

        # Receita por horario (dia) - agrupa por hora
        por_horario = defaultdict(float)
        for r in receitas_dia:
            data = self._parse(r.data)
            if data:
                por_horario[data.strftime("%H:00")] += r.valor

        # Grafico diario (ultimos 30 dias)
        grafico_diario = self._grafico_diario(agora)
        # Grafico mensal (ultimos 12 meses)
        grafico_mensal = self._grafico_mensal(agora)
        # Grafico anual (ultimos 5 anos)
        grafico_anual = self._grafico_anual(agora)
        # Comparativo mensal (mes atual vs anterior)
        comparativo_mensal = self._comparativo_mensal(agora)

        # Top operadores (por origem/ticket)
        top_operadores = sorted(por_operador.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "receita_dia": receita_dia,
            "receita_mes": receita_mes,
            "receita_ano": receita_ano,
            "quantidade_tickets": quantidade_tickets,
            "ticket_medio": ticket_medio,
            "receita_por_forma": {k: round(v, 2) for k, v in por_forma.items()},
            "receita_por_operador": {k: round(v, 2) for k, v in por_operador.items()},
            "receita_por_horario": {k: round(v, 2) for k, v in sorted(por_horario.items())},
            "top_operadores": [{"nome": k, "valor": round(v, 2)} for k, v in top_operadores],
            "grafico_diario": grafico_diario,
            "grafico_mensal": grafico_mensal,
            "grafico_anual": grafico_anual,
            "comparativo_mensal": comparativo_mensal,
        }

    def _grafico_diario(self, agora: datetime) -> dict:
        """Receita dos ultimos 30 dias."""
        labels = []
        valores = []
        for i in range(29, -1, -1):
            dia = agora - timedelta(days=i)
            labels.append(dia.strftime("%d/%m"))
            inicio = dia.replace(hour=0, minute=0, second=0, microsecond=0)
            fim = dia.replace(hour=23, minute=59, second=59, microsecond=0)
            total = sum(r.valor for r in self._receitas(inicio, fim))
            valores.append(round(total, 2))
        return {"labels": labels, "valores": valores}

    def _grafico_mensal(self, agora: datetime) -> dict:
        """Receita dos ultimos 12 meses."""
        labels = []
        valores = []
        for i in range(11, -1, -1):
            mes = agora.replace(day=1) - timedelta(days=30 * i)
            mes = mes.replace(day=1)
            labels.append(mes.strftime("%m/%Y"))
            if mes.month == 12:
                fim = mes.replace(year=mes.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                fim = mes.replace(month=mes.month + 1, day=1) - timedelta(days=1)
            inicio = mes.replace(hour=0, minute=0, second=0, microsecond=0)
            fim = fim.replace(hour=23, minute=59, second=59, microsecond=0)
            total = sum(r.valor for r in self._receitas(inicio, fim))
            valores.append(round(total, 2))
        return {"labels": labels, "valores": valores}

    def _grafico_anual(self, agora: datetime) -> dict:
        """Receita dos ultimos 5 anos."""
        labels = []
        valores = []
        for i in range(4, -1, -1):
            ano = agora.year - i
            labels.append(str(ano))
            inicio = datetime(ano, 1, 1)
            fim = datetime(ano, 12, 31, 23, 59, 59)
            total = sum(r.valor for r in self._receitas(inicio, fim))
            valores.append(round(total, 2))
        return {"labels": labels, "valores": valores}

    def _comparativo_mensal(self, agora: datetime) -> dict:
        """Comparativo entre o mes atual e o mes anterior."""
        mes_atual = agora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if mes_atual.month == 1:
            mes_anterior = mes_atual.replace(year=mes_atual.year - 1, month=12)
        else:
            mes_anterior = mes_atual.replace(month=mes_atual.month - 1)

        def total_mes(mes: datetime) -> float:
            if mes.month == 12:
                fim = mes.replace(year=mes.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                fim = mes.replace(month=mes.month + 1, day=1) - timedelta(days=1)
            fim = fim.replace(hour=23, minute=59, second=59, microsecond=0)
            return round(sum(r.valor for r in self._receitas(mes, fim)), 2)

        atual = total_mes(mes_atual)
        anterior = total_mes(mes_anterior)
        variacao = 0.0
        if anterior > 0:
            variacao = round(((atual - anterior) / anterior) * 100, 2)

        return {
            "mes_atual": atual,
            "mes_anterior": anterior,
            "variacao_percentual": variacao,
        }
