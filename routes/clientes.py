"""
Blueprint de clientes: clientes mensalistas, mensalistas, convenios e
contas a receber.
"""

from flask import Blueprint, jsonify, request

from services_registry import (
    servico_clientes,
    servico_contas_receber,
    servico_convenios,
    servico_mensalistas,
    verificar_permissao,
)

bp = Blueprint("clientes", __name__)


# ---------------------- CLIENTES ----------------------

@bp.route("/api/clientes", methods=["GET"])
def api_listar_clientes():
    """Retorna a lista de clientes (mensalistas) cadastrados."""
    ok, erro = verificar_permissao("clientes", "ver")
    if not ok:
        return erro
    clientes = servico_clientes.listar()
    return jsonify({"clientes": [c.to_dict() for c in clientes]})


@bp.route("/api/clientes", methods=["POST"])
def api_criar_cliente():
    """Cria um novo cliente mensalista."""
    ok, erro = verificar_permissao("clientes", "criar")
    if not ok:
        return erro
    dados = request.get_json(silent=True) or {}

    nome = (dados.get("nome") or "").strip()
    telefone = (dados.get("telefone") or "").strip()
    placa = (dados.get("placa") or "").strip()
    categoria = (dados.get("categoria") or "carro_pequeno").strip()
    data_inicio = (dados.get("data_inicio") or "").strip()
    data_fim = (dados.get("data_fim") or "").strip()

    try:
        cliente = servico_clientes.criar(
            nome=nome,
            telefone=telefone,
            placa=placa,
            categoria=categoria,
            data_inicio=data_inicio,
            data_fim=data_fim,
        )
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400

    return jsonify({"mensagem": "Cliente cadastrado com sucesso!", "cliente": cliente.to_dict()}), 201


@bp.route("/api/clientes/<int:id_cliente>", methods=["GET"])
def api_obter_cliente(id_cliente: int):
    """Retorna um cliente especifico pelo id."""
    ok, erro = verificar_permissao("clientes", "ver")
    if not ok:
        return erro
    cliente = servico_clientes.buscar_por_id(id_cliente)
    if cliente is None:
        return jsonify({"erro": "Cliente nao encontrado."}), 404
    return jsonify({"cliente": cliente.to_dict()})


@bp.route("/api/clientes/<int:id_cliente>", methods=["PUT"])
def api_atualizar_cliente(id_cliente: int):
    """Atualiza os dados de um cliente existente."""
    ok, erro = verificar_permissao("clientes", "editar")
    if not ok:
        return erro
    dados = request.get_json(silent=True) or {}

    nome = dados.get("nome")
    telefone = dados.get("telefone")
    placa = dados.get("placa")
    categoria = dados.get("categoria")
    data_inicio = dados.get("data_inicio")
    data_fim = dados.get("data_fim")
    ativo = dados.get("ativo")

    if ativo is not None:
        try:
            ativo = bool(ativo)
        except (TypeError, ValueError):
            return jsonify({"erro": "Valor invalido para o campo 'ativo'."}), 400

    try:
        cliente = servico_clientes.atualizar(
            id_cliente=id_cliente,
            nome=nome,
            telefone=telefone,
            placa=placa,
            categoria=categoria,
            data_inicio=data_inicio,
            data_fim=data_fim,
            ativo=ativo,
        )
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400

    if cliente is None:
        return jsonify({"erro": "Cliente nao encontrado."}), 404

    return jsonify({"mensagem": "Cliente atualizado com sucesso!", "cliente": cliente.to_dict()})


@bp.route("/api/clientes/<int:id_cliente>", methods=["DELETE"])
def api_excluir_cliente(id_cliente: int):
    """Desativa/exclui um cliente."""
    ok, erro = verificar_permissao("clientes", "excluir")
    if not ok:
        return erro
    if not servico_clientes.excluir(id_cliente):
        return jsonify({"erro": "Cliente nao encontrado."}), 404
    return jsonify({"mensagem": "Cliente desativado com sucesso!"})


# ---------------------- MENSALISTAS ----------------------

@bp.route("/api/mensalistas", methods=["GET"])
def api_listar_mensalistas():
    """Retorna a lista de mensalistas."""
    ok, erro = verificar_permissao("mensalistas", "ver")
    if not ok:
        return erro
    servico_mensalistas.verificar_inadimplencia()
    mensalistas = servico_mensalistas.listar()
    return jsonify({"mensalistas": [m.to_dict() for m in mensalistas]})


@bp.route("/api/mensalistas", methods=["POST"])
def api_criar_mensalista():
    """Cria um novo mensalista."""
    ok, erro = verificar_permissao("mensalistas", "criar")
    if not ok:
        return erro
    dados = request.get_json(silent=True) or {}
    try:
        mensalista = servico_mensalistas.criar(
            nome=dados.get("nome"),
            cpf_cnpj=dados.get("cpf_cnpj", ""),
            telefone=dados.get("telefone", ""),
            email=dados.get("email", ""),
            valor_mensal=dados.get("valor_mensal", 0),
            dia_vencimento=dados.get("dia_vencimento", 5),
            cliente_id=dados.get("cliente_id"),
            placa=dados.get("placa", ""),
            tipo_veiculo=dados.get("tipo_veiculo", "Carro"),
        )
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    return jsonify({"mensagem": "Mensalista cadastrado!", "mensalista": mensalista.to_dict()}), 201


@bp.route("/api/mensalistas/<int:id_mensalista>", methods=["PUT"])
def api_atualizar_mensalista(id_mensalista: int):
    """Atualiza um mensalista."""
    ok, erro = verificar_permissao("mensalistas", "editar")
    if not ok:
        return erro
    dados = request.get_json(silent=True) or {}
    try:
        mensalista = servico_mensalistas.atualizar(
            id_mensalista,
            nome=dados.get("nome"),
            cpf_cnpj=dados.get("cpf_cnpj"),
            telefone=dados.get("telefone"),
            email=dados.get("email"),
            valor_mensal=dados.get("valor_mensal"),
            dia_vencimento=dados.get("dia_vencimento"),
            status=dados.get("status"),
            placa=dados.get("placa"),
            tipo_veiculo=dados.get("tipo_veiculo"),
        )
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    if mensalista is None:
        return jsonify({"erro": "Mensalista nao encontrado."}), 404
    return jsonify({"mensagem": "Mensalista atualizado!", "mensalista": mensalista.to_dict()})


@bp.route("/api/mensalistas/<int:id_mensalista>/bloquear", methods=["POST"])
def api_bloquear_mensalista(id_mensalista: int):
    """Bloqueia um mensalista."""
    ok, erro = verificar_permissao("mensalistas", "editar")
    if not ok:
        return erro
    mensalista = servico_mensalistas.bloquear(id_mensalista)
    if mensalista is None:
        return jsonify({"erro": "Mensalista nao encontrado."}), 404
    return jsonify({"mensagem": "Mensalista bloqueado!", "mensalista": mensalista.to_dict()})


@bp.route("/api/mensalistas/<int:id_mensalista>/desbloquear", methods=["POST"])
def api_desbloquear_mensalista(id_mensalista: int):
    """Desbloqueia um mensalista."""
    ok, erro = verificar_permissao("mensalistas", "editar")
    if not ok:
        return erro
    mensalista = servico_mensalistas.desbloquear(id_mensalista)
    if mensalista is None:
        return jsonify({"erro": "Mensalista nao encontrado."}), 404
    return jsonify({"mensagem": "Mensalista desbloqueado!", "mensalista": mensalista.to_dict()})


@bp.route("/api/mensalistas/<int:id_mensalista>/mensalidades", methods=["GET"])
def api_mensalidades_mensalista(id_mensalista: int):
    """Retorna as mensalidades de um mensalista."""
    mensalidades = servico_mensalistas.mensalidades_do_mensalista(id_mensalista)
    return jsonify({"mensalidades": [m.to_dict() for m in mensalidades]})


@bp.route("/api/mensalistas/<int:id_mensalista>/mensalidades", methods=["POST"])
def api_gerar_mensalidade(id_mensalista: int):
    """Gera uma mensalidade para o mensalista."""
    ok, erro = verificar_permissao("mensalistas", "criar")
    if not ok:
        return erro
    dados = request.get_json(silent=True) or {}
    competencia = (dados.get("competencia") or "").strip()
    try:
        mensalidade = servico_mensalistas.gerar_mensalidade(id_mensalista, competencia)
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    return jsonify({"mensagem": "Mensalidade gerada!", "mensalidade": mensalidade.to_dict()}), 201


@bp.route("/api/mensalidades/<int:id_mensalidade>/pagar", methods=["POST"])
def api_pagar_mensalidade(id_mensalidade: int):
    """Registra o pagamento de uma mensalidade."""
    ok, erro = verificar_permissao("mensalistas", "editar")
    if not ok:
        return erro
    dados = request.get_json(silent=True) or {}
    try:
        mensalidade = servico_mensalistas.pagar_mensalidade(
            id_mensalidade,
            forma_pagamento=dados.get("forma_pagamento", "dinheiro"),
            data_pagamento=dados.get("data_pagamento"),
        )
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    if mensalidade is None:
        return jsonify({"erro": "Mensalidade nao encontrada."}), 404
    return jsonify({"mensagem": "Mensalidade paga!", "mensalidade": mensalidade.to_dict()})


# ---------------------- CONVENIOS ----------------------

@bp.route("/api/convenios", methods=["GET"])
def api_listar_convenios():
    """Retorna a lista de convenios."""
    ok, erro = verificar_permissao("convenios", "ver")
    if not ok:
        return erro
    convenios = servico_convenios.listar()
    return jsonify({"convenios": [c.to_dict() for c in convenios]})


@bp.route("/api/convenios", methods=["POST"])
def api_criar_convenio():
    """Cria um novo convenio."""
    ok, erro = verificar_permissao("convenios", "criar")
    if not ok:
        return erro
    dados = request.get_json(silent=True) or {}
    try:
        convenio = servico_convenios.criar(
            nome=dados.get("nome", ""),
            cnpj=dados.get("cnpj", ""),
            contato=dados.get("contato", ""),
            ativo=dados.get("ativo", True),
        )
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    return jsonify({"mensagem": "Convenio cadastrado!", "convenio": convenio.to_dict()}), 201


@bp.route("/api/convenios/<int:id_convenio>", methods=["PUT"])
def api_atualizar_convenio(id_convenio: int):
    """Atualiza um convenio."""
    ok, erro = verificar_permissao("convenios", "editar")
    if not ok:
        return erro
    dados = request.get_json(silent=True) or {}
    try:
        convenio = servico_convenios.atualizar(
            id_convenio,
            nome=dados.get("nome"),
            cnpj=dados.get("cnpj"),
            contato=dados.get("contato"),
            ativo=dados.get("ativo"),
        )
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    if convenio is None:
        return jsonify({"erro": "Convenio nao encontrado."}), 404
    return jsonify({"mensagem": "Convenio atualizado!", "convenio": convenio.to_dict()})


# ---------------------- CONTAS A RECEBER ----------------------

@bp.route("/api/contas-receber", methods=["GET"])
def api_listar_contas_receber():
    """Retorna a lista de contas a receber."""
    ok, erro = verificar_permissao("contas_receber", "ver")
    if not ok:
        return erro
    contas = servico_contas_receber.listar()
    return jsonify({"contas_receber": [c.to_dict() for c in contas]})


@bp.route("/api/contas-receber", methods=["POST"])
def api_criar_conta_receber():
    """Cria uma nova conta a receber."""
    ok, erro = verificar_permissao("contas_receber", "criar")
    if not ok:
        return erro
    dados = request.get_json(silent=True) or {}
    try:
        conta = servico_contas_receber.criar(
            convenio_id=dados.get("convenio_id"),
            valor=dados.get("valor", 0),
            descricao=dados.get("descricao", ""),
            vencimento=dados.get("vencimento"),
        )
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    return jsonify({"mensagem": "Conta a receber criada!", "conta_receber": conta.to_dict()}), 201


@bp.route("/api/contas-receber/<int:id_conta>/baixar", methods=["POST"])
def api_baixar_conta_receber(id_conta: int):
    """Registra a baixa (pagamento) de uma conta a receber."""
    ok, erro = verificar_permissao("contas_receber", "editar")
    if not ok:
        return erro
    dados = request.get_json(silent=True) or {}
    try:
        conta = servico_contas_receber.baixar(
            id_conta,
            forma_pagamento=dados.get("forma_pagamento", "dinheiro"),
            data_pagamento=dados.get("data_pagamento"),
        )
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    if conta is None:
        return jsonify({"erro": "Conta a receber nao encontrada."}), 404
    return jsonify({"mensagem": "Conta a receber baixada!", "conta_receber": conta.to_dict()})
