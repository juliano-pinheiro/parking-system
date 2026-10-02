"""
Blueprint de relatorios: movimentacao, financeiro (CSV/PDF), ocupacao e DRE.
"""

from datetime import datetime

from flask import Blueprint, Response, jsonify, request

from services_registry import (
    servico,
    servico_financeiro,
    servico_relatorio,
    ticket_para_dict,
    verificar_permissao,
)

bp = Blueprint("relatorios", __name__)


@bp.route("/api/relatorio", methods=["GET"])
def api_relatorio():
    """
    Gera o relatorio de movimentacao.
    Filtros: 'data' (dd/mm/aaaa) ou 'periodo' (diario|semanal|mensal).
    Retorna tambem o faturamento por forma de pagamento.
    """
    ok, erro = verificar_permissao("relatorios", "ver")
    if not ok:
        return erro

    data = request.args.get("data", "").strip() or None
    periodo = request.args.get("periodo", "").strip() or None

    # Define o intervalo de datas (inicio/fim) para o resumo financeiro
    if periodo:
        try:
            inicio, fim = servico_financeiro.periodo_para_datas(periodo)
        except ValueError as erro:
            return jsonify({"erro": str(erro)}), 400
    elif data:
        inicio, fim = data, data
    else:
        inicio, fim = None, None

    relatorio = servico.relatorio_movimentacao(data)

    # Resumo financeiro do periodo (entradas, saidas, saldo e por forma de pagamento)
    resumo_financeiro = None
    formas_pagamento = None
    if inicio and fim:
        resumo_financeiro = servico_financeiro.resumo_periodo(inicio, fim)
        formas_pagamento = servico_financeiro.resumo_por_forma_pagamento(inicio, fim)

    return jsonify({
        "total_entradas": relatorio["total_entradas"],
        "total_saidas": relatorio["total_saidas"],
        "faturamento_total": relatorio["faturamento_total"],
        "veiculos_entrada": [ticket_para_dict(t) for t in relatorio["veiculos_entrada"]],
        "veiculos_saida": [ticket_para_dict(t) for t in relatorio["veiculos_saida"]],
        "resumo_financeiro": resumo_financeiro,
        "formas_pagamento": formas_pagamento,
    })


@bp.route("/api/relatorio-financeiro", methods=["GET"])
def api_relatorio_financeiro():
    """Gera o relatorio financeiro com agrupamento (dia|semana|mes)."""
    ok, erro = verificar_permissao("relatorios", "ver")
    if not ok:
        return erro
    agrupamento = request.args.get("agrupamento", "dia").strip() or "dia"
    try:
        relatorio = servico_relatorio.gerar(agrupamento)
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    return jsonify(relatorio)


@bp.route("/api/relatorio-financeiro/exportar", methods=["GET"])
def api_relatorio_financeiro_exportar():
    """Exporta o relatorio financeiro em CSV ou PDF."""
    ok, erro = verificar_permissao("relatorios", "ver")
    if not ok:
        return erro
    agrupamento = request.args.get("agrupamento", "dia").strip() or "dia"
    formato = request.args.get("formato", "csv").strip().lower() or "csv"
    try:
        if formato == "pdf":
            pdf_bytes = servico_relatorio.exportar_pdf(agrupamento)
            return Response(
                pdf_bytes,
                mimetype="application/pdf",
                headers={"Content-Disposition": f"attachment; filename=relatorio_financeiro_{agrupamento}.pdf"},
            )
        csv_texto = servico_relatorio.exportar_csv(agrupamento)
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    return Response(
        csv_texto,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=relatorio_financeiro_{agrupamento}.csv"},
    )


@bp.route("/api/relatorio-ocupacao", methods=["GET"])
def api_relatorio_ocupacao():
    """Retorna a ocupacao atual e por tipo de veiculo."""
    ok, erro = verificar_permissao("relatorios", "ver")
    if not ok:
        return erro
    return jsonify(servico_relatorio.relatorio_ocupacao())


@bp.route("/api/relatorio-dre", methods=["GET"])
def api_relatorio_dre():
    """Retorna o DRE simples (receita, descontos, cortesias, estornos)."""
    ok, erro = verificar_permissao("relatorios", "ver")
    if not ok:
        return erro
    return jsonify(servico_relatorio.relatorio_dre())


@bp.route("/api/relatorio-pagamentos", methods=["GET"])
def api_relatorio_pagamentos():
    """Retorna o relatorio de pagamentos filtrado por periodo, forma de pagamento e status."""
    ok, erro = verificar_permissao("relatorios", "ver")
    if not ok:
        return erro

    inicio = request.args.get("data_inicio", "").strip() or None
    fim = request.args.get("data_fim", "").strip() or None
    forma = request.args.get("forma_pagamento", "").strip() or None
    status = request.args.get("status", "ativo").strip() or "ativo"

    dados = servico_relatorio.relatorio_pagamentos_por_forma(
        inicio=inicio,
        fim=fim,
        forma_pagamento=forma,
        status=status,
    )
    return jsonify(dados)


@bp.route("/api/relatorio-pagamentos/exportar", methods=["GET"])
def api_relatorio_pagamentos_exportar():
    """Exporta o relatorio de pagamentos em CSV conforme os filtros aplicados."""
    ok, erro = verificar_permissao("relatorios", "ver")
    if not ok:
        return erro

    inicio = request.args.get("data_inicio", "").strip() or None
    fim = request.args.get("data_fim", "").strip() or None
    forma = request.args.get("forma_pagamento", "").strip() or None
    status = request.args.get("status", "ativo").strip() or "ativo"

    csv_texto = servico_relatorio.exportar_pagamentos_csv(
        inicio=inicio,
        fim=fim,
        forma_pagamento=forma,
        status=status,
    )
    nome_arquivo = f"relatorio_pagamentos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        csv_texto,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={nome_arquivo}"},
    )
