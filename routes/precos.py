"""
Blueprint de precos e configuracoes: configuracoes gerais, tabela de
precos, tipos de veiculo, descontos e cortesias.
"""

from flask import Blueprint, jsonify, request, session

from services_registry import (
    servico,
    servico_auditoria,
    servico_cortesias,
    servico_descontos,
    servico_tabela_precos,
    servico_tipos_veiculo,
    config_para_dict,
    verificar_permissao,
)
from services.tabela_preco_service import TIPO_VEICULO_CHAVE

bp = Blueprint("precos", __name__)


# ---------------------- CONFIGURACOES ----------------------

@bp.route("/api/configuracoes", methods=["GET"])
def api_obter_configuracoes():
    """Retorna as configuracoes atuais (precos e total de vagas)."""
    ok_cfg, erro_cfg = verificar_permissao("configuracoes", "ver")
    if ok_cfg:
        return jsonify(config_para_dict())
    ok_op, erro_op = verificar_permissao("operacao", "ver")
    if ok_op:
        return jsonify(config_para_dict())
    return erro_cfg or erro_op


def _normalizar_valor_config(campo: str, valor) -> any:
    """Converte o valor recebido da API para o tipo adequado do campo."""
    if valor is None:
        return None
    campos_int = {
        "total_vagas", "vagas_carro", "vagas_moto",
        "vagas_carro_grande", "vagas_caminhonete",
    }
    campos_float = {"valor_primeira_hora", "valor_hora_adicional", "valor_mensal"}
    campos_bool = {
        "bloquear_sem_vaga", "exigir_observacao",
        "ticket_exibir_cnpj", "ticket_exibir_contato", "ticket_exibir_codigo_barras",
    }
    try:
        if campo in campos_int:
            return int(valor)
        if campo in campos_float:
            return float(valor)
        if campo in campos_bool:
            return bool(valor)
        return str(valor).strip()
    except (TypeError, ValueError):
        raise ValueError(f"Valor invalido para o campo '{campo}'.")


@bp.route("/api/configuracoes", methods=["POST"])
def api_atualizar_configuracoes():
    """Atualiza as configuracoes do estacionamento."""
    ok, erro = verificar_permissao("configuracoes", "editar")
    if not ok:
        return erro
    dados = request.get_json(silent=True) or {}

    campos_permitidos = {
        "nome_estacionamento", "cnpj", "telefone", "endereco",
        "cidade", "estado", "cep", "total_vagas", "vagas_carro",
        "vagas_moto", "vagas_carro_grande", "vagas_caminhonete",
        "valor_primeira_hora", "valor_hora_adicional", "valor_mensal",
        "horario_abertura", "horario_fechamento", "cabecalho_ticket",
        "rodape_ticket", "bloquear_sem_vaga", "exigir_observacao",
        "pix_tipo", "pix_chave", "ticket_formato_papel",
        "ticket_exibir_cnpj", "ticket_exibir_contato", "ticket_exibir_codigo_barras",
    }

    try:
        atualizacoes = {}
        for campo in campos_permitidos:
            if campo in dados:
                atualizacoes[campo] = _normalizar_valor_config(campo, dados[campo])
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400

    novo_total_vagas = atualizacoes.get("total_vagas")
    if novo_total_vagas is not None and novo_total_vagas < servico.vagas_ocupadas():
        return jsonify({
            "erro": f"Nao e possivel definir {novo_total_vagas} vagas: "
                    f"ja existem {servico.vagas_ocupadas()} veiculos estacionados."
        }), 400

    servico.atualizar_configuracao(**atualizacoes)

    return jsonify({"mensagem": "Configuracoes atualizadas com sucesso!", "configuracao": config_para_dict()})


# ---------------------- TABELA DE PRECOS ----------------------

@bp.route("/api/tabela-precos", methods=["GET"])
def api_obter_tabela_precos():
    """Retorna a tabela de precos vigente."""
    tabela = servico_tabela_precos.obter_vigente()
    return jsonify({"tabela_precos": tabela.to_dict()})


@bp.route("/api/tabela-precos/<int:id_tabela>", methods=["PUT"])
def api_atualizar_tabela_precos(id_tabela: int):
    """Atualiza a tabela de precos."""
    ok, erro = verificar_permissao("tabela_precos", "editar")
    if not ok:
        return erro
    dados = request.get_json(silent=True) or {}
    try:
        tabela = servico_tabela_precos.atualizar(id_tabela, dados)
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    if tabela is None:
        return jsonify({"erro": "Tabela de precos nao encontrada."}), 404
    return jsonify({"mensagem": "Tabela de precos atualizada!", "tabela_precos": tabela.to_dict()})


@bp.route("/api/tabela-precos/calcular", methods=["POST"])
def api_calcular_valor():
    """Calcula o valor de um ticket com base na tabela de precos."""
    dados = request.get_json(silent=True) or {}
    entrada = (dados.get("entrada") or "").strip()
    saida = (dados.get("saida") or "").strip()
    tipo_veiculo = (dados.get("tipo_veiculo") or "Carro").strip()
    noturno = bool(dados.get("noturno", False))
    fim_semana = bool(dados.get("fim_semana", False))
    feriado = bool(dados.get("feriado", False))
    if not entrada or not saida:
        return jsonify({"erro": "Informe entrada e saida."}), 400
    valor = servico_tabela_precos.calcular_valor(entrada, saida, tipo_veiculo, noturno, fim_semana, feriado)
    return jsonify({"valor": valor})


# ---------------------- TIPOS DE VEICULO ----------------------

@bp.route("/api/tipos-veiculo", methods=["GET"])
def api_listar_tipos_veiculo():
    """Retorna os tipos de veiculo (sistema + personalizados).

    Tipos do sistema exibem os precos reais da tabela de precos (onde
    ficam gravados); personalizados mostram os precos proprios.
    """
    ok, erro = verificar_permissao("configuracoes", "ver")
    if not ok:
        return erro
    tipos = servico_tipos_veiculo.listar()
    tabela = servico_tabela_precos.obter_vigente()
    resultado = []
    for t in tipos:
        dados = t.to_dict()
        if t.sistema:
            chave = TIPO_VEICULO_CHAVE.get(t.nome, "carro")
            for campo in ("primeira_hora", "hora_adicional", "diaria", "valor_minuto", "valor_maximo_diario", "mensal"):
                dados[campo] = (
                    getattr(tabela, campo) if chave == "carro"
                    else getattr(tabela, f"{chave}_{campo}")
                )
        resultado.append(dados)
    return jsonify({"tipos_veiculo": resultado})


@bp.route("/api/tipos-veiculo", methods=["POST"])
def api_criar_tipo_veiculo():
    """Cria um tipo de veiculo personalizado (com precos opcionais)."""
    ok, erro = verificar_permissao("configuracoes", "editar")
    if not ok:
        return erro
    dados = request.get_json(silent=True) or {}
    try:
        tipo = servico_tipos_veiculo.criar(
            nome=dados.get("nome", ""),
            precos={
                "primeira_hora": dados.get("primeira_hora"),
                "hora_adicional": dados.get("hora_adicional"),
                "diaria": dados.get("diaria"),
                "valor_minuto": dados.get("valor_minuto"),
                "valor_maximo_diario": dados.get("valor_maximo_diario"),
                "mensal": dados.get("mensal"),
            },
        )
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400

    servico_tabela_precos.definir_tipos_personalizados(
        servico_tipos_veiculo.listar(somente_ativos=True)
    )
    servico_auditoria.registrar(
        "tipos_veiculo", tipo.id, "criar", None, tipo.nome,
        session.get("usuario", {}).get("nome"), request.remote_addr,
    )
    return jsonify({"mensagem": "Tipo de veiculo criado!", "tipo_veiculo": tipo.to_dict()}), 201


@bp.route("/api/tipos-veiculo/<int:id_tipo>", methods=["PUT"])
def api_atualizar_tipo_veiculo(id_tipo: int):
    """Atualiza um tipo de veiculo.

    Personalizado: nome + precos proprios (tabela tipos_veiculo).
    Sistema: apenas precos, gravados na tabela de precos (nome fixo).
    """
    ok, erro = verificar_permissao("configuracoes", "editar")
    if not ok:
        return erro
    dados = request.get_json(silent=True) or {}
    tipo = servico_tipos_veiculo.buscar_por_id(id_tipo)
    if tipo is None:
        return jsonify({"erro": "Tipo de veiculo nao encontrado."}), 404

    precos = {
        "primeira_hora": dados.get("primeira_hora"),
        "hora_adicional": dados.get("hora_adicional"),
        "diaria": dados.get("diaria"),
        "valor_minuto": dados.get("valor_minuto"),
        "valor_maximo_diario": dados.get("valor_maximo_diario"),
        "mensal": dados.get("mensal"),
    }

    if tipo.sistema:
        tabela = servico_tabela_precos.atualizar_precos_por_nome_tipo(tipo.nome, precos)
        if tabela is None:
            return jsonify({"erro": "Nao foi possivel atualizar os precos."}), 400
        descricao = f"{tipo.nome} (precos)"
    else:
        try:
            tipo = servico_tipos_veiculo.atualizar(
                id_tipo,
                nome=dados.get("nome", ""),
                precos=precos,
            )
        except ValueError as erro:
            return jsonify({"erro": str(erro)}), 400
        if tipo is None:
            return jsonify({"erro": "Tipo de veiculo nao encontrado."}), 404
        descricao = tipo.nome

    servico_tabela_precos.definir_tipos_personalizados(
        servico_tipos_veiculo.listar(somente_ativos=True)
    )
    servico_auditoria.registrar(
        "tipos_veiculo", id_tipo, "editar", None, descricao,
        session.get("usuario", {}).get("nome"), request.remote_addr,
    )
    return jsonify({"mensagem": "Tipo de veiculo atualizado!", "tipo_veiculo": tipo.to_dict()})


@bp.route("/api/tipos-veiculo/<int:id_tipo>/alternar-ativo", methods=["POST"])
def api_alternar_ativo_tipo_veiculo(id_tipo: int):
    """Ativa ou inativa um tipo personalizado."""
    ok, erro = verificar_permissao("configuracoes", "editar")
    if not ok:
        return erro
    try:
        tipo = servico_tipos_veiculo.alternar_ativo(id_tipo)
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    if tipo is None:
        return jsonify({"erro": "Tipo de veiculo nao encontrado."}), 404

    servico_tabela_precos.definir_tipos_personalizados(
        servico_tipos_veiculo.listar(somente_ativos=True)
    )
    acao = "ativar" if tipo.ativo else "inativar"
    servico_auditoria.registrar(
        "tipos_veiculo", id_tipo, acao, None, tipo.nome,
        session.get("usuario", {}).get("nome"), request.remote_addr,
    )
    return jsonify({"mensagem": f"Tipo '{tipo.nome}' {'ativado' if tipo.ativo else 'inativado'}!", "tipo_veiculo": tipo.to_dict()})


@bp.route("/api/tipos-veiculo/<int:id_tipo>", methods=["DELETE"])
def api_excluir_tipo_veiculo(id_tipo: int):
    """Exclui um tipo de veiculo personalizado (tipos do sistema nao podem)."""
    ok, erro = verificar_permissao("configuracoes", "editar")
    if not ok:
        return erro
    tipo = servico_tipos_veiculo.buscar_por_id(id_tipo)
    try:
        if not servico_tipos_veiculo.excluir(id_tipo):
            return jsonify({"erro": "Tipo de veiculo nao encontrado."}), 404
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400

    servico_tabela_precos.definir_tipos_personalizados(
        servico_tipos_veiculo.listar(somente_ativos=True)
    )
    servico_auditoria.registrar(
        "tipos_veiculo", id_tipo, "excluir",
        tipo.nome if tipo else None, None,
        session.get("usuario", {}).get("nome"), request.remote_addr,
    )
    return jsonify({"mensagem": "Tipo de veiculo excluido!"})


# ---------------------- DESCONTOS ----------------------

@bp.route("/api/descontos", methods=["GET"])
def api_listar_descontos():
    """Retorna a lista de descontos."""
    ok, erro = verificar_permissao("descontos", "ver")
    if not ok:
        return erro
    descontos = servico_descontos.listar()
    return jsonify({"descontos": [d.to_dict() for d in descontos]})


@bp.route("/api/descontos", methods=["POST"])
def api_criar_desconto():
    """Cria um novo desconto."""
    ok, erro = verificar_permissao("descontos", "criar")
    if not ok:
        return erro
    dados = request.get_json(silent=True) or {}
    try:
        desconto = servico_descontos.criar(
            nome=dados.get("nome", ""),
            tipo=dados.get("tipo", "percentual"),
            valor=dados.get("valor", 0),
            motivo=dados.get("motivo", ""),
            necessita_autorizacao=dados.get("necessita_autorizacao", False),
            ativo=dados.get("ativo", True),
        )
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    return jsonify({"mensagem": "Desconto criado!", "desconto": desconto.to_dict()}), 201


@bp.route("/api/descontos/<int:id_desconto>", methods=["PUT"])
def api_atualizar_desconto(id_desconto: int):
    """Atualiza um desconto."""
    ok, erro = verificar_permissao("descontos", "editar")
    if not ok:
        return erro
    dados = request.get_json(silent=True) or {}
    try:
        desconto = servico_descontos.atualizar(
            id_desconto,
            nome=dados.get("nome"),
            tipo=dados.get("tipo"),
            valor=dados.get("valor"),
            motivo=dados.get("motivo"),
            necessita_autorizacao=dados.get("necessita_autorizacao"),
            ativo=dados.get("ativo"),
        )
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    if desconto is None:
        return jsonify({"erro": "Desconto nao encontrado."}), 404
    return jsonify({"mensagem": "Desconto atualizado!", "desconto": desconto.to_dict()})


# ---------------------- CORTESIAS ----------------------

@bp.route("/api/cortesias", methods=["GET"])
def api_listar_cortesias():
    """Retorna a lista de cortesias."""
    ok, erro = verificar_permissao("cortesias", "ver")
    if not ok:
        return erro
    cortesias = servico_cortesias.listar()
    return jsonify({"cortesias": [c.to_dict() for c in cortesias]})


@bp.route("/api/cortesias", methods=["POST"])
def api_criar_cortesia():
    """Cria uma nova cortesia."""
    ok, erro = verificar_permissao("cortesias", "criar")
    if not ok:
        return erro
    dados = request.get_json(silent=True) or {}
    try:
        cortesia = servico_cortesias.criar(
            motivo=dados.get("motivo", ""),
            usuario=dados.get("usuario"),
            autorizador=dados.get("autorizador"),
            ticket_numero=dados.get("ticket_numero"),
        )
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    return jsonify({"mensagem": "Cortesia registrada!", "cortesia": cortesia.to_dict()}), 201


@bp.route("/api/cortesias/<int:id_cortesia>/cancelar", methods=["POST"])
def api_cancelar_cortesia(id_cortesia: int):
    """Cancela uma cortesia."""
    ok, erro = verificar_permissao("cortesias", "editar")
    if not ok:
        return erro
    dados = request.get_json(silent=True) or {}
    cortesia = servico_cortesias.cancelar(id_cortesia, dados.get("autorizador"))
    if cortesia is None:
        return jsonify({"erro": "Cortesia nao encontrada."}), 404
    return jsonify({"mensagem": "Cortesia cancelada!", "cortesia": cortesia.to_dict()})
