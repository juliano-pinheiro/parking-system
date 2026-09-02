"""
Blueprint de funcionalidades avancadas: NFSe, lista negra, reservas,
ocorrencias, notificacoes de vencimento e backup.
"""

from datetime import datetime
import json

from flask import Blueprint, Response, jsonify, request

from services_registry import (
    servico,
    servico_auditoria,
    servico_backup,
    servico_lista_negra,
    servico_nfse,
    servico_notificacao,
    servico_ocorrencias,
    servico_reservas,
    usuario_logado,
    verificar_permissao,
)

bp = Blueprint("extras", __name__)


# ---------------------- API: NFSE ----------------------

@bp.route("/api/nfse", methods=["GET"])
def api_listar_nfse():
    """Retorna as notas fiscais emitidas."""
    ok, erro = verificar_permissao("nfse", "ver")
    if not ok:
        return erro
    notas = servico_nfse.listar()
    notas = sorted(notas, key=lambda n: n.numero, reverse=True)
    return jsonify({"notas": [n.to_dict() for n in notas]})


@bp.route("/api/nfse", methods=["POST"])
def api_emitir_nfse():
    """Emite uma NFSe simplificada."""
    ok, erro = verificar_permissao("nfse", "criar")
    if not ok:
        return erro
    dados = request.get_json(silent=True) or {}
    try:
        nota = servico_nfse.emitir(
            valor=dados.get("valor", 0),
            ticket_numero=dados.get("ticket_numero"),
            placa=dados.get("placa", ""),
            cpf_cnpj=dados.get("cpf_cnpj", ""),
            razao_social=dados.get("razao_social", ""),
            servico=dados.get("servico", "Estacionamento de veiculos"),
            usuario=usuario_logado().nome if usuario_logado() else "operador",
        )
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    servico_auditoria.registrar("nfse", nota.numero, "emitir", None, "nota emitida", usuario_logado().nome if usuario_logado() else "")
    return jsonify({"mensagem": "Nota emitida com sucesso!", "nota": nota.to_dict()}), 201


@bp.route("/api/nfse/<int:id_nota>/cancelar", methods=["POST"])
def api_cancelar_nfse(id_nota: int):
    """Cancela uma NFSe (logico)."""
    ok, erro = verificar_permissao("nfse", "cancelar")
    if not ok:
        return erro
    nota = servico_nfse.cancelar(id_nota, autorizador=usuario_logado().nome if usuario_logado() else "")
    if nota is None:
        return jsonify({"erro": "Nota nao encontrada."}), 404
    return jsonify({"mensagem": "Nota cancelada!", "nota": nota.to_dict()})


# ---------------------- API: LISTA NEGRA ----------------------

@bp.route("/api/lista-negra", methods=["GET"])
def api_listar_lista_negra():
    """Retorna os veiculos bloqueados."""
    ok, erro = verificar_permissao("lista_negra", "ver")
    if not ok:
        return erro
    registros = servico_lista_negra.listar()
    registros = sorted(registros, key=lambda r: r.data, reverse=True)
    return jsonify({"registros": [r.to_dict() for r in registros]})


@bp.route("/api/lista-negra", methods=["POST"])
def api_criar_lista_negra():
    """Bloqueia um veiculo."""
    ok, erro = verificar_permissao("lista_negra", "criar")
    if not ok:
        return erro
    dados = request.get_json(silent=True) or {}
    try:
        registro = servico_lista_negra.criar(
            placa=dados.get("placa", ""),
            motivo=dados.get("motivo", ""),
            usuario=usuario_logado().nome if usuario_logado() else "operador",
        )
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    return jsonify({"mensagem": "Veiculo bloqueado!", "registro": registro.to_dict()}), 201


@bp.route("/api/lista-negra/<int:id_registro>", methods=["PUT"])
def api_atualizar_lista_negra(id_registro: int):
    """Atualiza um registro da lista negra."""
    ok, erro = verificar_permissao("lista_negra", "editar")
    if not ok:
        return erro
    dados = request.get_json(silent=True) or {}
    try:
        registro = servico_lista_negra.atualizar(
            id_registro,
            placa=dados.get("placa"),
            motivo=dados.get("motivo"),
            ativo=dados.get("ativo"),
        )
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    if registro is None:
        return jsonify({"erro": "Registro nao encontrado."}), 404
    return jsonify({"mensagem": "Registro atualizado!", "registro": registro.to_dict()})


@bp.route("/api/lista-negra/<int:id_registro>/alternar-ativo", methods=["POST"])
def api_alternar_lista_negra(id_registro: int):
    """Ativa/inativa o bloqueio de um veiculo."""
    ok, erro = verificar_permissao("lista_negra", "editar")
    if not ok:
        return erro
    registro = servico_lista_negra.buscar_por_id(id_registro)
    if registro is None:
        return jsonify({"erro": "Registro nao encontrado."}), 404
    registro = servico_lista_negra.atualizar(id_registro, ativo=not registro.ativo)
    return jsonify({"mensagem": "Status atualizado!", "registro": registro.to_dict()})


@bp.route("/api/lista-negra/<int:id_registro>", methods=["DELETE"])
def api_excluir_lista_negra(id_registro: int):
    """Remove o bloqueio (exclusao logica)."""
    ok, erro = verificar_permissao("lista_negra", "excluir")
    if not ok:
        return erro
    if not servico_lista_negra.excluir(id_registro):
        return jsonify({"erro": "Registro nao encontrado."}), 404
    return jsonify({"mensagem": "Bloqueio removido!"})


# ---------------------- API: RESERVAS ----------------------

@bp.route("/api/reservas", methods=["GET"])
def api_listar_reservas():
    """Retorna as reservas de vaga."""
    ok, erro = verificar_permissao("reservas", "ver")
    if not ok:
        return erro
    reservas = servico_reservas.listar()
    reservas = sorted(reservas, key=lambda r: r.data_inicio, reverse=True)
    return jsonify({"reservas": [r.to_dict() for r in reservas]})


@bp.route("/api/reservas", methods=["POST"])
def api_criar_reserva():
    """Cria uma reserva de vaga."""
    ok, erro = verificar_permissao("reservas", "criar")
    if not ok:
        return erro
    dados = request.get_json(silent=True) or {}
    try:
        reserva = servico_reservas.criar(
            cliente=dados.get("cliente", ""),
            data_inicio=dados.get("data_inicio", ""),
            data_fim=dados.get("data_fim", ""),
            telefone=dados.get("telefone", ""),
            placa=dados.get("placa", ""),
            tipo_veiculo=dados.get("tipo_veiculo", "Carro"),
            vaga=dados.get("vaga"),
            valor=dados.get("valor", 0),
            observacao=dados.get("observacao", ""),
            usuario=usuario_logado().nome if usuario_logado() else "operador",
        )
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    return jsonify({"mensagem": "Reserva criada!", "reserva": reserva.to_dict()}), 201


@bp.route("/api/reservas/<int:id_reserva>", methods=["PUT"])
def api_atualizar_reserva(id_reserva: int):
    """Atualiza uma reserva."""
    ok, erro = verificar_permissao("reservas", "editar")
    if not ok:
        return erro
    dados = request.get_json(silent=True) or {}
    try:
        reserva = servico_reservas.atualizar(
            id_reserva,
            cliente=dados.get("cliente"),
            data_inicio=dados.get("data_inicio"),
            data_fim=dados.get("data_fim"),
            telefone=dados.get("telefone"),
            placa=dados.get("placa"),
            tipo_veiculo=dados.get("tipo_veiculo"),
            vaga=dados.get("vaga"),
            valor=dados.get("valor"),
            observacao=dados.get("observacao"),
            status=dados.get("status"),
        )
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    if reserva is None:
        return jsonify({"erro": "Reserva nao encontrada."}), 404
    return jsonify({"mensagem": "Reserva atualizada!", "reserva": reserva.to_dict()})


@bp.route("/api/reservas/<int:id_reserva>/cancelar", methods=["POST"])
def api_cancelar_reserva(id_reserva: int):
    """Cancela uma reserva."""
    ok, erro = verificar_permissao("reservas", "editar")
    if not ok:
        return erro
    reserva = servico_reservas.buscar_por_id(id_reserva)
    if reserva is None:
        return jsonify({"erro": "Reserva nao encontrada."}), 404
    reserva = servico_reservas.atualizar(id_reserva, status="cancelada")
    return jsonify({"mensagem": "Reserva cancelada!", "reserva": reserva.to_dict()})


# ---------------------- API: OCORRENCIAS ----------------------

@bp.route("/api/ocorrencias", methods=["GET"])
def api_listar_ocorrencias():
    """Retorna as ocorrencias registradas."""
    ok, erro = verificar_permissao("ocorrencias", "ver")
    if not ok:
        return erro
    ocorrencias = servico_ocorrencias.listar()
    ocorrencias = sorted(ocorrencias, key=lambda o: o.data, reverse=True)
    return jsonify({"ocorrencias": [o.to_dict() for o in ocorrencias]})


@bp.route("/api/ocorrencias", methods=["POST"])
def api_criar_ocorrencia():
    """Registra uma ocorrencia."""
    ok, erro = verificar_permissao("ocorrencias", "criar")
    if not ok:
        return erro
    dados = request.get_json(silent=True) or {}
    try:
        ocorrencia = servico_ocorrencias.criar(
            tipo=dados.get("tipo", "avaria"),
            placa=dados.get("placa", ""),
            descricao=dados.get("descricao", ""),
            ticket_numero=dados.get("ticket_numero"),
            usuario=usuario_logado().nome if usuario_logado() else "operador",
            autorizador=dados.get("autorizador", ""),
        )
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    return jsonify({"mensagem": "Ocorrencia registrada!", "ocorrencia": ocorrencia.to_dict()}), 201


@bp.route("/api/ocorrencias/<int:id_ocorrencia>", methods=["PUT"])
def api_atualizar_ocorrencia(id_ocorrencia: int):
    """Atualiza uma ocorrencia."""
    ok, erro = verificar_permissao("ocorrencias", "editar")
    if not ok:
        return erro
    dados = request.get_json(silent=True) or {}
    try:
        ocorrencia = servico_ocorrencias.atualizar(
            id_ocorrencia,
            tipo=dados.get("tipo"),
            placa=dados.get("placa"),
            descricao=dados.get("descricao"),
            ticket_numero=dados.get("ticket_numero"),
            status=dados.get("status"),
            autorizador=dados.get("autorizador"),
        )
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    if ocorrencia is None:
        return jsonify({"erro": "Ocorrencia nao encontrada."}), 404
    return jsonify({"mensagem": "Ocorrencia atualizada!", "ocorrencia": ocorrencia.to_dict()})


# ---------------------- API: NOTIFICACOES DE VENCIMENTO ----------------------

@bp.route("/api/notificacoes-vencimento", methods=["GET"])
def api_notificacoes_vencimento():
    """Retorna a central de avisos de vencimento de mensalistas."""
    ok, erro = verificar_permissao("notificacoes", "ver")
    if not ok:
        return erro
    return jsonify(servico_notificacao.gerar_avisos())


# ---------------------- API: BACKUP / EXPORTACAO ----------------------

@bp.route("/api/backup", methods=["GET"])
def api_backup():
    """Exporta o backup completo (JSON) da empresa ativa.
    Restrito a quem pode editar usuarios (na pratica, admin)."""
    ok, erro = verificar_permissao("usuarios", "editar")
    if not ok:
        return erro
    backup = servico_backup.gerar(nome_estacionamento=servico.config.nome_estacionamento)
    return Response(
        json.dumps(backup, ensure_ascii=False, indent=2, default=str),
        mimetype="application/json",
        headers={
            "Content-Disposition": (
                f"attachment; filename=backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
        },
    )
