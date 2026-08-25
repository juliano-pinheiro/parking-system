"""
Servico de Relatorios Financeiros.

Gera relatorios filtráveis por periodo com agrupamento por
Dia (ultimos 30), Semana (ultimas 12) ou Mes (ultimos 12),
com series para grafico de barras e totais (faturamento, saidas,
ticket medio). Suporta exportacao CSV.
"""

import csv
import io
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List

from models.lancamento import FORMATO_DATA

AGRUPAMENTO_DIA = "dia"
AGRUPAMENTO_SEMANA = "semana"
AGRUPAMENTO_MES = "mes"

AGRUPAMENTOS_VALIDOS = (AGRUPAMENTO_DIA, AGRUPAMENTO_SEMANA, AGRUPAMENTO_MES)


class RelatorioService:
    """Gera relatorios financeiros com agrupamento e exportacao."""

    def __init__(self, financeiro_service=None, nome_estacionamento="Estacionamento"):
        self._financeiro = financeiro_service
        self._nome_estacionamento = nome_estacionamento or "Estacionamento"

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
        # Remove sufixo de timezone (+00:00, -03:00) que vem depois da data/hora
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
        resultado = []
        for lancamento in self._lancamentos():
            if lancamento.tipo != "entrada":
                continue
            data = self._parse(lancamento.data)
            if data and inicio <= data <= fim:
                resultado.append(lancamento)
        return resultado

    def _periodo_agrupamento(self, agrupamento: str) -> tuple:
        """Retorna (inicio, fim) do periodo conforme o agrupamento."""
        agora = datetime.now()
        if agrupamento == AGRUPAMENTO_DIA:
            inicio = agora - timedelta(days=29)
            inicio = inicio.replace(hour=0, minute=0, second=0, microsecond=0)
            fim = agora.replace(hour=23, minute=59, second=59, microsecond=0)
        elif agrupamento == AGRUPAMENTO_SEMANA:
            # Ultimas 12 semanas (segunda a domingo)
            inicio = agora - timedelta(weeks=11)
            inicio = inicio - timedelta(days=inicio.weekday())
            inicio = inicio.replace(hour=0, minute=0, second=0, microsecond=0)
            fim = agora.replace(hour=23, minute=59, second=59, microsecond=0)
        elif agrupamento == AGRUPAMENTO_MES:
            # Ultimos 12 meses
            inicio = agora.replace(day=1) - timedelta(days=30 * 11)
            inicio = inicio.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            fim = agora.replace(hour=23, minute=59, second=59, microsecond=0)
        else:
            raise ValueError("Agrupamento invalido. Use 'dia', 'semana' ou 'mes'.")
        return inicio, fim

    def _chave_agrupamento(self, data: datetime, agrupamento: str) -> str:
        if agrupamento == AGRUPAMENTO_DIA:
            return data.strftime("%d/%m")
        if agrupamento == AGRUPAMENTO_SEMANA:
            # Semana iniciando na segunda-feira
            inicio_semana = data - timedelta(days=data.weekday())
            return inicio_semana.strftime("%d/%m")
        return data.strftime("%m/%Y")

    def gerar(self, agrupamento: str = AGRUPAMENTO_DIA) -> dict:
        """Gera o relatorio com series e totais conforme o agrupamento."""
        if agrupamento not in AGRUPAMENTOS_VALIDOS:
            raise ValueError("Agrupamento invalido. Use 'dia', 'semana' ou 'mes'.")

        inicio, fim = self._periodo_agrupamento(agrupamento)
        receitas = self._receitas(inicio, fim)

        # Agrupa por chave
        por_chave = defaultdict(float)
        for r in receitas:
            data = self._parse(r.data)
            if data:
                por_chave[self._chave_agrupamento(data, agrupamento)] += r.valor

        # Ordena as chaves cronologicamente
        chaves_ordenadas = sorted(por_chave.keys(), key=lambda c: self._chave_sort(c, agrupamento))

        labels = []
        valores = []
        for chave in chaves_ordenadas:
            labels.append(chave)
            valores.append(round(por_chave[chave], 2))

        # Totais
        faturamento_total = round(sum(r.valor for r in receitas), 2)
        total_saidas = len(receitas)
        ticket_medio = round(faturamento_total / total_saidas, 2) if total_saidas else 0.0

        # Faturamento por forma de pagamento
        por_forma = defaultdict(float)
        for r in receitas:
            por_forma[r.forma_pagamento] += r.valor

        return {
            "agrupamento": agrupamento,
            "inicio": inicio.strftime("%d/%m/%Y"),
            "fim": fim.strftime("%d/%m/%Y"),
            "labels": labels,
            "valores": valores,
            "faturamento_total": faturamento_total,
            "total_saidas": total_saidas,
            "ticket_medio": ticket_medio,
            "formas_pagamento": {k: round(v, 2) for k, v in por_forma.items()},
            "lancamentos": [l.to_dict() for l in receitas],
        }

    def _chave_sort(self, chave: str, agrupamento: str) -> str:
        """Converte a chave para um valor ordenavel cronologicamente."""
        try:
            if agrupamento == AGRUPAMENTO_DIA:
                return datetime.strptime(chave, "%d/%m").strftime("%m-%d")
            if agrupamento == AGRUPAMENTO_SEMANA:
                return datetime.strptime(chave, "%d/%m").strftime("%m-%d")
            return datetime.strptime(chave, "%m/%Y").strftime("%Y-%m")
        except ValueError:
            return chave

    def exportar_csv(self, agrupamento: str = AGRUPAMENTO_DIA) -> str:
        """Gera o relatorio em CSV (string)."""
        dados = self.gerar(agrupamento)

        saida = io.StringIO()
        escritor = csv.writer(saida)
        escritor.writerow([self._nome_estacionamento])
        escritor.writerow(["Relatorio de Faturamento"])
        escritor.writerow([f"Periodo: {dados['inicio']} a {dados['fim']}"])
        escritor.writerow([f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}"])
        escritor.writerow([])
        escritor.writerow(["Periodo", "Faturamento", "Saidas", "Ticket medio"])
        escritor.writerow([
            f"{dados['inicio']} a {dados['fim']}",
            dados["faturamento_total"],
            dados["total_saidas"],
            dados["ticket_medio"],
        ])
        escritor.writerow([])
        escritor.writerow(["Agrupamento", "Valor"])
        for label, valor in zip(dados["labels"], dados["valores"]):
            escritor.writerow([label, valor])
        escritor.writerow([])
        escritor.writerow(["Forma de pagamento", "Valor"])
        for forma, valor in dados["formas_pagamento"].items():
            escritor.writerow([forma, valor])
        return saida.getvalue()

    def exportar_pdf(self, agrupamento: str = AGRUPAMENTO_DIA) -> bytes:
        """
        Gera o relatorio em PDF (bytes) com layout baseado no nome do
        estacionamento, usando a biblioteca reportlab.
        """
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import (
            Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
        )

        dados = self.gerar(agrupamento)

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=A4,
            rightMargin=15 * mm, leftMargin=15 * mm,
            topMargin=15 * mm, bottomMargin=15 * mm,
        )

        estilos = getSampleStyleSheet()
        estilo_titulo = ParagraphStyle(
            "Titulo", parent=estilos["Title"],
            fontSize=18, textColor=colors.HexColor("#1d4ed8"),
            spaceAfter=2,
        )
        estilo_sub = ParagraphStyle(
            "Sub", parent=estilos["Normal"],
            fontSize=11, textColor=colors.HexColor("#4b5563"),
            alignment=1, spaceAfter=2,
        )
        estilo_cab = ParagraphStyle(
            "Cab", parent=estilos["Normal"],
            fontSize=9, textColor=colors.HexColor("#6b7280"),
            alignment=1,
        )
        estilo_celula = ParagraphStyle(
            "Celula", parent=estilos["Normal"], fontSize=9,
        )
        estilo_celula_bold = ParagraphStyle(
            "CelulaBold", parent=estilos["Normal"], fontSize=9,
            fontName="Helvetica-Bold",
        )

        elementos = []

        # Cabecalho com o nome do estacionamento
        elementos.append(Paragraph(self._nome_estacionamento, estilo_titulo))
        elementos.append(Paragraph("Relatório de Faturamento", estilo_sub))
        elementos.append(Paragraph(
            f"Período: {dados['inicio']} a {dados['fim']}  •  "
            f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            estilo_cab,
        ))
        elementos.append(Spacer(1, 6 * mm))

        # Totais
        totais = [
            ["Faturamento", "Saídas", "Ticket médio"],
            [
                f"R$ {dados['faturamento_total']:.2f}",
                str(dados["total_saidas"]),
                f"R$ {dados['ticket_medio']:.2f}",
            ],
        ]
        tabela_totais = Table(totais, colWidths=[60 * mm, 40 * mm, 50 * mm])
        tabela_totais.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1d4ed8")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#eff6ff")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        elementos.append(tabela_totais)
        elementos.append(Spacer(1, 6 * mm))

        # Tabela de faturamento por periodo
        elementos.append(Paragraph("Faturamento por período", estilo_cab))
        elementos.append(Spacer(1, 2 * mm))
        dados_tabela = [["Período", "Valor"]]
        for label, valor in zip(dados["labels"], dados["valores"]):
            dados_tabela.append([label, f"R$ {valor:.2f}"])
        tabela_periodo = Table(dados_tabela, colWidths=[80 * mm, 80 * mm])
        tabela_periodo.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1d4ed8")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        elementos.append(tabela_periodo)
        elementos.append(Spacer(1, 6 * mm))

        # Faturamento por forma de pagamento
        elementos.append(Paragraph("Faturamento por forma de pagamento", estilo_cab))
        elementos.append(Spacer(1, 2 * mm))
        dados_formas = [["Forma de pagamento", "Valor"]]
        for forma, valor in dados["formas_pagamento"].items():
            dados_formas.append([forma, f"R$ {valor:.2f}"])
        tabela_formas = Table(dados_formas, colWidths=[80 * mm, 80 * mm])
        tabela_formas.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1d4ed8")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        elementos.append(tabela_formas)

        doc.build(elementos)
        return buffer.getvalue()
