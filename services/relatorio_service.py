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

    def __init__(
        self,
        financeiro_service=None,
        nome_estacionamento="Estacionamento",
        estacionamento_service=None,
        desconto_service=None,
        cortesia_service=None,
        estorno_service=None,
        mensalista_service=None,
        conta_receber_service=None,
        pagamento_service=None,
        forma_pagamento_service=None,
    ):
        self._financeiro = financeiro_service
        self._nome_estacionamento = nome_estacionamento or "Estacionamento"
        self._estacionamento = estacionamento_service
        self._descontos = desconto_service
        self._cortesias = cortesia_service
        self._estornos = estorno_service
        self._mensalistas = mensalista_service
        self._contas_receber = conta_receber_service
        self._pagamentos = pagamento_service
        self._formas_pagamento = forma_pagamento_service

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

    # ------------------------------------------------------------
    # RELATORIO DE OCUPACAO
    # ------------------------------------------------------------
    def relatorio_ocupacao(self) -> dict:
        """Retorna a ocupacao atual e por tipo de veiculo."""
        total_vagas = 0
        vagas_ocupadas = 0
        tickets_abertos = []
        tickets_por_tipo = {}

        if self._estacionamento is not None:
            try:
                config = self._estacionamento.config
                total_vagas = getattr(config, "vagas", 0) or 0
                tickets_abertos = self._estacionamento.listar_tickets_abertos()
                vagas_ocupadas = len(tickets_abertos)
            except Exception:
                pass

        # Vagas por tipo de veiculo (se configurado)
        vagas_por_tipo = {}
        if self._estacionamento is not None:
            try:
                config = self._estacionamento.config
                for tipo in ("Carro", "Moto", "Carro Grande", "Caminhonete"):
                    v = getattr(config, f"vagas_{tipo.lower().replace(' ', '_')}", None)
                    if v is None:
                        v = getattr(config, tipo.lower().replace(" ", "_"), None)
                    if v is not None:
                        vagas_por_tipo[tipo] = int(v)
            except Exception:
                pass

        # Contagem de ocupados por tipo
        for ticket in tickets_abertos:
            tipo = getattr(ticket, "tipo_veiculo", None) or "Carro"
            tickets_por_tipo[tipo] = tickets_por_tipo.get(tipo, 0) + 1

        disponiveis = max(total_vagas - vagas_ocupadas, 0)
        taxa = round((vagas_ocupadas / total_vagas) * 100, 1) if total_vagas else 0

        return {
            "total_vagas": total_vagas,
            "ocupadas": vagas_ocupadas,
            "disponiveis": disponiveis,
            "taxa_ocupacao": taxa,
            "por_tipo": {
                tipo: {
                    "ocupadas": tickets_por_tipo.get(tipo, 0),
                    "vagas": vagas_por_tipo.get(tipo, 0),
                }
                for tipo in sorted(set(list(vagas_por_tipo.keys()) + list(tickets_por_tipo.keys())))
            },
        }

    # ------------------------------------------------------------
    # DRE (Demonstracao do Resultado do Exercicio)
    # ------------------------------------------------------------
    def relatorio_dre(self) -> dict:
        """Retorna um DRE simples: receita bruta, descontos, cortesias,
        estornos e resultado liquido, no periodo do agrupamento 'dia'."""
        inicio, fim = self._periodo_agrupamento(AGRUPAMENTO_DIA)

        receita_bruta = 0.0
        for lancamento in self._receitas(inicio, fim):
            receita_bruta += float(getattr(lancamento, "valor", 0) or 0)

        total_descontos = 0.0
        if self._descontos is not None:
            try:
                for desconto in self._descontos.listar():
                    data = self._parse(getattr(desconto, "criado_em", None))
                    if data and inicio <= data <= fim:
                        if hasattr(desconto, "valor") and desconto.valor:
                            total_descontos += float(desconto.valor or 0)
            except Exception:
                pass

        total_cortesias = 0.0
        if self._cortesias is not None:
            try:
                for cortesia in self._cortesias.listar():
                    data = self._parse(getattr(cortesia, "data", None))
                    if data and inicio <= data <= fim:
                        # Cortesias nao contabilizam como receita; registra contagem
                        total_cortesias += 1
            except Exception:
                pass

        total_estornos = 0.0
        if self._estornos is not None:
            try:
                for estorno in self._estornos.listar():
                    data = self._parse(getattr(estorno, "data", None))
                    if data and inicio <= data <= fim:
                        total_estornos += float(getattr(estorno, "valor", 0) or 0)
            except Exception:
                pass

        resultado = round(receita_bruta - total_estornos, 2)

        return {
            "periodo": {"inicio": inicio.strftime("%d/%m/%Y"), "fim": fim.strftime("%d/%m/%Y")},
            "receita_bruta": round(receita_bruta, 2),
            "total_descontos": round(total_descontos, 2),
            "total_cortesias": int(total_cortesias),
            "total_estornos": round(total_estornos, 2),
            "resultado_liquido": resultado,
        }

    # ==================================================================
    # RELATORIO: PAGAMENTOS POR FORMA DE PAGAMENTO
    # ==================================================================

    def _parse_data_filtro(self, data_str: str, eh_fim: bool = False) -> datetime | None:
        """Converte strings de filtro (YYYY-MM-DD ou DD/MM/YYYY) para datetime."""
        if not data_str:
            return None
        s = str(data_str).strip()
        formatos = [
            "%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M",
            "%d/%m/%Y", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M",
        ]
        for f in formatos:
            try:
                dt = datetime.strptime(s, f)
                if len(s) == 10:
                    if eh_fim:
                        return dt.replace(hour=23, minute=59, second=59)
                    else:
                        return dt.replace(hour=0, minute=0, second=0)
                return dt
            except (ValueError, TypeError):
                continue
        return self._parse(data_str)

    def relatorio_pagamentos_por_forma(
        self,
        inicio: str | None = None,
        fim: str | None = None,
        forma_pagamento: str | None = None,
        status: str = "ativo",
    ) -> dict:
        """
        Extrai e totaliza pagamentos por forma de pagamento no periodo filtrado.
        Retorna receita total, quantidade, ticket medio, resumo agrupado e lista de transacoes.
        """
        dt_inicio = self._parse_data_filtro(inicio, eh_fim=False) if inicio else None
        dt_fim = self._parse_data_filtro(fim, eh_fim=True) if fim else None
        forma_filtro = (forma_pagamento or "").strip().lower()

        # Obtem o mapa de formas cadastradas (codigo -> nome legivel)
        mapa_nomes = {}
        if self._formas_pagamento:
            try:
                for f in self._formas_pagamento.listar():
                    mapa_nomes[f.codigo.lower()] = f.nome
            except Exception:
                pass

        pagamentos = self._pagamentos.listar() if self._pagamentos else []

        transacoes_filtradas = []
        resumo_dict = defaultdict(lambda: {"quantidade": 0, "receita": 0.0})

        receita_total = 0.0
        quantidade_total = 0

        for p in pagamentos:
            # Filtro de status ('ativo', 'estornado', 'cancelado', ou 'todos')
            p_status = (getattr(p, "status", "") or "").lower()
            if status and status.lower() != "todos" and p_status != status.lower():
                continue

            # Filtro de forma de pagamento
            p_forma = (getattr(p, "forma_pagamento", "") or "").strip().lower()
            if forma_filtro and forma_filtro != "todas" and p_forma != forma_filtro:
                continue

            # Filtro de data
            data_val = getattr(p, "data", None)
            dt_pag = self._parse(data_val)
            if dt_pag:
                if dt_inicio and dt_pag < dt_inicio:
                    continue
                if dt_fim and dt_pag > dt_fim:
                    continue
            elif dt_inicio or dt_fim:
                continue

            valor = round(float(getattr(p, "valor", 0.0) or 0.0), 2)
            receita_total += valor
            quantidade_total += 1

            resumo_dict[p_forma]["quantidade"] += 1
            resumo_dict[p_forma]["receita"] += valor

            nome_forma = mapa_nomes.get(p_forma, p_forma.replace("_", " ").title())

            transacoes_filtradas.append({
                "id": p.id,
                "ticket_numero": getattr(p, "ticket_numero", None),
                "valor": valor,
                "forma_pagamento": p_forma,
                "forma_pagamento_nome": nome_forma,
                "data": str(data_val or ""),
                "operador": getattr(p, "operador", None) or "—",
                "status": getattr(p, "status", "ativo"),
                "caixa_id": getattr(p, "caixa_id", None),
            })

        # Ordena transacoes da mais recente para a mais antiga
        def _chave_ordenacao(item):
            d = self._parse(item["data"])
            return d if d else datetime.min

        transacoes_filtradas.sort(key=_chave_ordenacao, reverse=True)

        # Monta o resumo agrupado por forma
        resumo_formas = []
        for codigo, dados in resumo_dict.items():
            nome = mapa_nomes.get(codigo, codigo.replace("_", " ").title())
            rec = round(dados["receita"], 2)
            pct = round((rec / receita_total * 100), 1) if receita_total > 0 else 0.0
            ticket_medio_forma = round(rec / dados["quantidade"], 2) if dados["quantidade"] > 0 else 0.0
            resumo_formas.append({
                "codigo": codigo,
                "nome": nome,
                "quantidade": dados["quantidade"],
                "receita": rec,
                "percentual": pct,
                "ticket_medio": ticket_medio_forma,
            })

        # Ordena formas por maior receita decrescente
        resumo_formas.sort(key=lambda x: x["receita"], reverse=True)

        ticket_medio_geral = round(receita_total / quantidade_total, 2) if quantidade_total > 0 else 0.0

        return {
            "receita_total": round(receita_total, 2),
            "quantidade_total": quantidade_total,
            "ticket_medio": ticket_medio_geral,
            "filtros": {
                "inicio": inicio or "",
                "fim": fim or "",
                "forma_pagamento": forma_filtro or "todas",
                "status": status or "ativo",
            },
            "resumo_formas": resumo_formas,
            "transacoes": transacoes_filtradas,
        }

    def exportar_pagamentos_csv(
        self,
        inicio: str | None = None,
        fim: str | None = None,
        forma_pagamento: str | None = None,
        status: str = "ativo",
    ) -> str:
        """Gera o arquivo CSV com cabecalho, resumo consolidado e linhas analiticas."""
        dados = self.relatorio_pagamentos_por_forma(inicio, fim, forma_pagamento, status)
        output = io.StringIO()
        writer = csv.writer(output, delimiter=";", lineterminator="\r\n")

        writer.writerow(["RELATORIO DE PAGAMENTOS POR FORMA DE PAGAMENTO"])
        writer.writerow(["Estacionamento", self._nome_estacionamento])
        writer.writerow(["Periodo", f"{inicio or 'Inicio'} ate {fim or 'Hoje'}"])
        writer.writerow(["Forma de Pagamento", forma_pagamento or "Todas"])
        writer.writerow(["Status", (status or "Ativo").capitalize()])
        writer.writerow(["Gerado em", datetime.now().strftime("%d/%m/%Y %H:%M:%S")])
        writer.writerow([])

        # Bloco de Totais
        writer.writerow(["RESUMO GERAL"])
        writer.writerow(["Receita Total (R$)", f"{dados['receita_total']:.2f}".replace(".", ",")])
        writer.writerow(["Total de Pagamentos", dados["quantidade_total"]])
        writer.writerow(["Ticket Medio (R$)", f"{dados['ticket_medio']:.2f}".replace(".", ",")])
        writer.writerow([])

        # Bloco de Formas
        writer.writerow(["DISTRIBUICAO POR FORMA DE PAGAMENTO"])
        writer.writerow(["Forma de Pagamento", "Quantidade", "Receita (R$)", "Participacao (%)", "Ticket Medio (R$)"])
        for rf in dados["resumo_formas"]:
            writer.writerow([
                rf["nome"],
                rf["quantidade"],
                f"{rf['receita']:.2f}".replace(".", ","),
                f"{rf['percentual']:.1f}%".replace(".", ","),
                f"{rf['ticket_medio']:.2f}".replace(".", ","),
            ])
        writer.writerow([])

        # Bloco Analitico
        writer.writerow(["DETALHAMENTO DE TRANSACOES"])
        writer.writerow(["Ticket / Ref", "Data / Hora", "Operador", "Forma de Pagamento", "Valor (R$)", "Status"])
        for t in dados["transacoes"]:
            data_formatada = t["data"]
            dt = self._parse(t["data"])
            if dt:
                data_formatada = dt.strftime("%d/%m/%Y %H:%M:%S")
            writer.writerow([
                f"#{t['ticket_numero']}" if t.get("ticket_numero") else "—",
                data_formatada,
                t.get("operador") or "—",
                t.get("forma_pagamento_nome", ""),
                f"{t['valor']:.2f}".replace(".", ","),
                (t.get("status") or "").capitalize(),
            ])

        return output.getvalue()
