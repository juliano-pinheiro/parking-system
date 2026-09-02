"""
Blueprint financeiro: lancamentos financeiros, caixa, pagamentos,
estornos, formas de pagamento e dashboard financeiro.
"""

from flask import Blueprint, jsonify, request

from services_registry import (
    servico_caixa,
    servico_dashboard_financeiro,
    servico_estornos,
    servico_financeiro,
    servico_formas_pagamento,
    servico_pagamentos,
    usuario_logado,
    verificar_permissao,
)
from services.financeiro_service import FORMAS_PAGAMENTO_LABEL

bp = Blueprint("financeiro", __name__)


@bp.route("/api/financeiro", methods=["GET"])
def api_listar_financeiro():
    """Retorna a lista de lancamentos financeiros (com filtro opcional por periodo)."""
    ok, erro = verificar_permissao("financeiro", "ver")
    if not ok:
        return erro
    periodo = request.args.get("periodo", "").strip() or None

    lancamentos = servico_financeiro.listar()

    if periodo:
        try:
            inicio, fim = servico_financeiro.periodo_para_datas(periodo)
        except ValueError as erro:
            return jsonify({"erro": str(erro)}), 400
        lancamentos = servico_financeiro._filtrar_por_periodo(inicio, fim)

    return jsonify({
        "lancamentos": [l.to_dict() for l in lancamentos],
        "formas_pagamento": FORMAS_PAGAMENTO_LABEL,
    })


@bp.route("/api/financeiro", methods=["POST"])
def api_criar_financeiro():
    """Cria um novo lancamento financeiro (manual)."""
    ok, erro = verificar_permissao("financeiro", "criar")
    if not ok:
        return erro
    dados = request.get_json(silent=True) or {}

    tipo = (dados.get("tipo") or "").strip()
    descricao = (dados.get("descricao") or "").strip()
    forma_pagamento = (dados.get("forma_pagamento") or "dinheiro").strip()
    data = (dados.get("data") or "").strip() or None

    try:
        valor = float(dados.get("valor"))
    except (TypeError, ValueError):
        return jsonify({"erro": "Valor invalido."}), 400

    try:
        lancamento = servico_financeiro.criar(
            tipo=tipo,
            descricao=descricao,
            valor=valor,
            forma_pagamento=forma_pagamento,
            data=data,
        )
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400

    return jsonify({"mensagem": "Lancamento criado com sucesso!", "lancamento": lancamento.to_dict()}), 201


@bp.route("/api/financeiro/<int:id_lancamento>", methods=["GET"])
def api_obter_financeiro(id_lancamento: int):
    """Retorna um lancamento especifico pelo id."""
    ok, erro = verificar_permissao("financeiro", "ver")
    if not ok:
        return erro
    lancamento = servico_financeiro.buscar_por_id(id_lancamento)
    if lancamento is None:
        return jsonify({"erro": "Lancamento nao encontrado."}), 404
    return jsonify({"lancamento": lancamento.to_dict()})


@bp.route("/api/financeiro/<int:id_lancamento>", methods=["PUT"])
def api_atualizar_financeiro(id_lancamento: int):
    """Atualiza os dados de um lancamento financeiro."""
    ok, erro = verificar_permissao("financeiro", "editar")
    if not ok:
        return erro
    dados = request.get_json(silent=True) or {}

    tipo = dados.get("tipo")
    descricao = dados.get("descricao")
    forma_pagamento = dados.get("forma_pagamento")
    data = dados.get("data")

    valor = dados.get("valor")
    if valor is not None:
        try:
            valor = float(valor)
        except (TypeError, ValueError):
            return jsonify({"erro": "Valor invalido."}), 400

    try:
        lancamento = servico_financeiro.atualizar(
            id_lancamento=id_lancamento,
            tipo=tipo,
            descricao=descricao,
            valor=valor,
            forma_pagamento=forma_pagamento,
            data=data,
        )
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400

    if lancamento is None:
        return jsonify({"erro": "Lancamento nao encontrado."}), 404

    return jsonify({"mensagem": "Lancamento atualizado com sucesso!", "lancamento": lancamento.to_dict()})


@bp.route("/api/financeiro/<int:id_lancamento>", methods=["DELETE"])
def api_excluir_financeiro(id_lancamento: int):
    """Exclui um lancamento financeiro."""
    ok, erro = verificar_permissao("financeiro", "excluir")
    if not ok:
        return erro
    if not servico_financeiro.excluir(id_lancamento):
        return jsonify({"erro": "Lancamento nao encontrado."}), 404
    return jsonify({"mensagem": "Lancamento excluido com sucesso!"})


@bp.route("/api/financeiro/resumo", methods=["GET"])
def api_resumo_financeiro():
    """Retorna o resumo financeiro por periodo (diario|semanal|mensal)."""
    ok, erro = verificar_permissao("financeiro", "ver")
    if not ok:
        return erro
    periodo = request.args.get("periodo", "diario").strip() or "diario"

    try:
        inicio, fim = servico_financeiro.periodo_para_datas(periodo)
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400

    resumo = servico_financeiro.resumo_periodo(inicio, fim)
    formas = servico_financeiro.resumo_por_forma_pagamento(inicio, fim)

    return jsonify({
        "periodo": periodo,
        "inicio": inicio,
        "fim": fim,
        "resumo": resumo,
        "formas_pagamento": formas,
    })


# ---------------------- CAIXA ----------------------

@bp.route("/api/caixa", methods=["GET"])
def api_listar_caixas():
    """Retorna a lista de caixas e o caixa aberto atual."""
    ok, erro = verificar_permissao("caixa", "ver")
    if not ok:
        return erro
    caixas = servico_caixa.listar()
    caixa_aberto = servico_caixa.caixa_aberto()
    return jsonify({
        "caixas": [c.to_dict() for c in caixas],
        "caixa_aberto": caixa_aberto.to_dict() if caixa_aberto else None,
    })


@bp.route("/api/caixa", methods=["POST"])
def api_abrir_caixa():
    """Abre um novo caixa."""
    ok, erro = verificar_permissao("caixa", "criar")
    if not ok:
        return erro
    dados = request.get_json(silent=True) or {}
    operador = (dados.get("operador") or "").strip()
    valor_inicial = dados.get("valor_inicial", 0)
    observacoes = (dados.get("observacoes") or "").strip()
    try:
        valor_inicial = float(valor_inicial or 0)
    except (TypeError, ValueError):
        return jsonify({"erro": "Valor inicial invalido."}), 400

    try:
        caixa = servico_caixa.abrir(operador, valor_inicial, observacoes)
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400

    from services_registry import servico_auditoria
    servico_auditoria.registrar("caixas", caixa.id, "status", None, "aberto", operador)
    return jsonify({"mensagem": "Caixa aberto com sucesso!", "caixa": caixa.to_dict()}), 201


@bp.route("/api/caixa/<int:id_caixa>/fechar", methods=["POST"])
def api_fechar_caixa(id_caixa: int):
    """Fecha um caixa, calculando totais, diferenca e status."""
    ok, erro = verificar_permissao("caixa", "fechar_caixa")
    if not ok:
        return erro
    dados = request.get_json(silent=True) or {}
    valor_contado = dados.get("valor_contado", 0)
    observacoes = (dados.get("observacoes") or "").strip()
    try:
        valor_contado = float(valor_contado or 0)
    except (TypeError, ValueError):
        return jsonify({"erro": "Valor contado invalido."}), 400

    try:
        caixa = servico_caixa.fechar(id_caixa, valor_contado, observacoes)
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400

    totais = servico_caixa.totais_por_forma(id_caixa)
    from services_registry import servico_auditoria
    servico_auditoria.registrar("caixas", caixa.id, "status", "aberto", "fechado", caixa.operador)
    return jsonify({
        "mensagem": "Caixa fechado com sucesso!",
        "caixa": caixa.to_dict(),
        "totais_por_forma": totais,
    })


@bp.route("/api/caixa/<int:id_caixa>/sangria", methods=["POST"])
def api_sangria(id_caixa: int):
    """Registra uma sangria no caixa."""
    ok, erro = verificar_permissao("caixa", "editar")
    if not ok:
        return erro
    dados = request.get_json(silent=True) or {}
    valor = dados.get("valor", 0)
    motivo = (dados.get("motivo") or "").strip()
    try:
        valor = float(valor or 0)
    except (TypeError, ValueError):
        return jsonify({"erro": "Valor invalido."}), 400
    try:
        mov = servico_caixa.sangria(id_caixa, valor, motivo)
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    return jsonify({"mensagem": "Sangria registrada!", "movimentacao": mov.to_dict()}), 201


@bp.route("/api/caixa/<int:id_caixa>/suprimento", methods=["POST"])
def api_suprimento(id_caixa: int):
    """Registra um suprimento no caixa."""
    ok, erro = verificar_permissao("caixa", "editar")
    if not ok:
        return erro
    dados = request.get_json(silent=True) or {}
    valor = dados.get("valor", 0)
    motivo = (dados.get("motivo") or "").strip()
    try:
        valor = float(valor or 0)
    except (TypeError, ValueError):
        return jsonify({"erro": "Valor invalido."}), 400
    try:
        mov = servico_caixa.suprimento(id_caixa, valor, motivo)
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    return jsonify({"mensagem": "Suprimento registrado!", "movimentacao": mov.to_dict()}), 201


@bp.route("/api/caixa/<int:id_caixa>/movimentacoes", methods=["GET"])
def api_movimentacoes_caixa(id_caixa: int):
    """Retorna as movimentacoes de um caixa."""
    movs = servico_caixa.movimentacoes_do_caixa(id_caixa)
    return jsonify({"movimentacoes": [m.to_dict() for m in movs]})


# ---------------------- PAGAMENTOS ----------------------

@bp.route("/api/pagamentos", methods=["GET"])
def api_listar_pagamentos():
    """Retorna a lista de pagamentos."""
    ok, erro = verificar_permissao("pagamentos", "ver")
    if not ok:
        return erro
    pagamentos = servico_pagamentos.listar()
    return jsonify({"pagamentos": [p.to_dict() for p in pagamentos]})


@bp.route("/api/pagamentos/<int:id_pagamento>/cancelar", methods=["POST"])
def api_cancelar_pagamento(id_pagamento: int):
    """Cancela (logicamente) um pagamento."""
    ok, erro = verificar_permissao("pagamentos", "cancelar")
    if not ok:
        return erro
    dados = request.get_json(silent=True) or {}
    motivo = (dados.get("motivo") or "").strip()
    autorizador = (dados.get("autorizador") or "").strip() or None
    try:
        pagamento = servico_pagamentos.cancelar(id_pagamento, motivo, autorizador=autorizador)
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    if pagamento is None:
        return jsonify({"erro": "Pagamento nao encontrado."}), 404
    from services_registry import servico_auditoria
    servico_auditoria.registrar("pagamentos", pagamento.id, "status", "ativo", "cancelado", autorizador)
    return jsonify({"mensagem": "Pagamento cancelado!", "pagamento": pagamento.to_dict()})


@bp.route("/api/pagamentos/<int:id_pagamento>/estornar", methods=["POST"])
def api_estornar_pagamento(id_pagamento: int):
    """Estorna (logicamente) um pagamento e registra o estorno."""
    ok, erro = verificar_permissao("pagamentos", "estornar")
    if not ok:
        return erro
    dados = request.get_json(silent=True) or {}
    motivo = (dados.get("motivo") or "").strip()
    autorizador = (dados.get("autorizador") or "").strip() or None
    try:
        pagamento = servico_pagamentos.estornar(id_pagamento, motivo, autorizador=autorizador)
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    if pagamento is None:
        return jsonify({"erro": "Pagamento nao encontrado."}), 404
    servico_estornos.criar(
        pagamento_id=pagamento.id,
        valor=pagamento.valor,
        motivo=motivo,
        forma_pagamento=pagamento.forma_pagamento,
        autorizador=autorizador,
    )
    from services_registry import servico_auditoria
    servico_auditoria.registrar("pagamentos", pagamento.id, "status", "ativo", "estornado", autorizador)
    return jsonify({"mensagem": "Pagamento estornado!", "pagamento": pagamento.to_dict()})


# ---------------------- FORMAS DE PAGAMENTO ----------------------

@bp.route("/api/formas-pagamento", methods=["GET"])
def api_listar_formas_pagamento():
    """Retorna a lista de formas de pagamento."""
    formas = servico_formas_pagamento.listar()
    return jsonify({"formas_pagamento": [f.to_dict() for f in formas]})


@bp.route("/api/formas-pagamento", methods=["POST"])
def api_criar_forma_pagamento():
    """Cria uma nova forma de pagamento."""
    ok, erro = verificar_permissao("formas_pagamento", "criar")
    if not ok:
        return erro
    dados = request.get_json(silent=True) or {}
    nome = (dados.get("nome") or "").strip()
    codigo = (dados.get("codigo") or "").strip()
    ativo = dados.get("ativo", True)
    try:
        forma = servico_formas_pagamento.criar(nome, codigo, ativo)
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    return jsonify({"mensagem": "Forma de pagamento criada!", "forma_pagamento": forma.to_dict()}), 201


@bp.route("/api/formas-pagamento/<int:id_forma>", methods=["PUT"])
def api_atualizar_forma_pagamento(id_forma: int):
    """Atualiza uma forma de pagamento."""
    ok, erro = verificar_permissao("formas_pagamento", "editar")
    if not ok:
        return erro
    dados = request.get_json(silent=True) or {}
    try:
        forma = servico_formas_pagamento.atualizar(
            id_forma,
            nome=dados.get("nome"),
            ativo=dados.get("ativo"),
        )
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    if forma is None:
        return jsonify({"erro": "Forma de pagamento nao encontrada."}), 404
    return jsonify({"mensagem": "Forma de pagamento atualizada!", "forma_pagamento": forma.to_dict()})


# ---------------------- ESTORNOS ----------------------

@bp.route("/api/estornos", methods=["GET"])
def api_listar_estornos():
    """Retorna a lista de estornos."""
    estornos = servico_estornos.listar()
    return jsonify({"estornos": [e.to_dict() for e in estornos]})


# ---------------------- DASHBOARD FINANCEIRO ----------------------

@bp.route("/api/dashboard-financeiro", methods=["GET"])
def api_dashboard_financeiro():
    """Retorna os indicadores do dashboard financeiro."""
    ok, erro = verificar_permissao("dashboard_financeiro", "ver")
    if not ok:
        return erro
    return jsonify(servico_dashboard_financeiro.gerar())
