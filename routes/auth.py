"""
Blueprint de autenticacao: login, logout, troca de senha, sessao e
troca de empresa ativa.
"""

from flask import Blueprint, jsonify, request, session

from services_registry import (
    servico_auditoria,
    servico_empresas,
    servico_usuarios,
    empresa_para_dict,
    recarregar_services_por_empresa,
    usuario_logado,
    usuario_para_dict,
)

bp = Blueprint("auth", __name__)


@bp.route("/api/login", methods=["POST"])
def api_login():
    """Autentica um usuario (email + senha) e inicia a sessao."""
    dados = request.get_json(silent=True) or {}
    email = (dados.get("email") or "").strip()
    senha = dados.get("senha") or ""

    if not email or not senha:
        return jsonify({"erro": "Informe e-mail e senha."}), 400

    usuario = servico_usuarios.autenticar(email, senha)
    if usuario is None:
        return jsonify({"erro": "E-mail ou senha invalidos, ou usuario inativo."}), 401

    session["usuario_id"] = usuario.id
    session["usuario_nome"] = usuario.nome
    session["usuario_perfil"] = usuario.perfil
    session["usuario_master"] = usuario.master or usuario.perfil == "admin"

    # Redireciona automaticamente para a empresa vinculada ao usuario
    empresa_redirect = None
    eh_master = session["usuario_master"]
    if eh_master:
        # Master: fica na primeira empresa ativa (ou None se nao houver)
        empresas_ativas = servico_empresas.listar(ativos=True)
        if empresas_ativas:
            session["empresa_id"] = empresas_ativas[0].id
            empresa_redirect = empresas_ativas[0].id
        else:
            session.pop("empresa_id", None)
    elif usuario.empresa_id:
        session["empresa_id"] = usuario.empresa_id
        empresa_redirect = usuario.empresa_id
    else:
        session.pop("empresa_id", None)

    # Recarrega os services com a empresa ativa (isolamento por CNPJ)
    recarregar_services_por_empresa(session.get("empresa_id"))

    # Registra log de acesso
    try:
        servico_auditoria.registrar_log_acesso(
            usuario=usuario.nome,
            acao="login",
            modulo="autenticacao",
            ip=request.remote_addr,
        )
    except Exception:
        pass

    dados_retorno = usuario_para_dict(usuario)
    empresa = servico_empresas.buscar_por_id(session.get("empresa_id")) if session.get("empresa_id") else None
    dados_retorno["empresa"] = empresa_para_dict(empresa) if empresa else None
    dados_retorno["empresa_redirect"] = empresa_redirect

    return jsonify({"mensagem": "Login realizado com sucesso!", "usuario": dados_retorno})


@bp.route("/api/logout", methods=["POST"])
def api_logout():
    """Encerra a sessao do usuario."""
    usuario = usuario_logado()
    if usuario:
        try:
            servico_auditoria.registrar_log_acesso(
                usuario=usuario.nome,
                acao="logout",
                modulo="autenticacao",
                ip=request.remote_addr,
            )
        except Exception:
            pass
    session.clear()
    return jsonify({"mensagem": "Logout realizado com sucesso."})


@bp.route("/api/trocar-senha", methods=["POST"])
def api_trocar_senha():
    """Permite ao usuario logado trocar a propria senha."""
    usuario = usuario_logado()
    if usuario is None:
        return jsonify({"erro": "Nao autenticado."}), 401

    dados = request.get_json(silent=True) or {}
    senha_atual = dados.get("senha_atual") or ""
    nova_senha = dados.get("nova_senha") or ""

    try:
        servico_usuarios.trocar_senha(usuario.id, senha_atual, nova_senha)
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400

    return jsonify({"mensagem": "Senha alterada com sucesso!"})


@bp.route("/api/sessao", methods=["GET"])
def api_sessao():
    """Retorna o usuario autenticado na sessao atual (ou null)."""
    usuario = usuario_logado()
    if usuario is None:
        return jsonify({"usuario": None})
    dados = usuario_para_dict(usuario)
    empresa = servico_empresas.buscar_por_id(session.get("empresa_id")) if session.get("empresa_id") else None
    dados["empresa"] = empresa_para_dict(empresa) if empresa else None
    dados["empresa_id"] = session.get("empresa_id")
    return jsonify({"usuario": dados})


@bp.route("/api/empresa/atual", methods=["GET"])
def api_empresa_atual():
    """Retorna a empresa ativa na sessao."""
    usuario = usuario_logado()
    if usuario is None:
        return jsonify({"erro": "Nao autenticado."}), 401
    empresa = servico_empresas.buscar_por_id(session.get("empresa_id")) if session.get("empresa_id") else None
    if empresa is None:
        return jsonify({"empresa": None})
    return jsonify({"empresa": empresa_para_dict(empresa)})


@bp.route("/api/empresa/trocar", methods=["POST"])
def api_trocar_empresa():
    """Permite ao usuario master trocar a empresa ativa da sessao."""
    usuario = usuario_logado()
    if usuario is None:
        return jsonify({"erro": "Nao autenticado."}), 401
    if not (usuario.master or usuario.perfil == "admin"):
        return jsonify({"erro": "Somente o usuario master pode trocar de empresa."}), 403

    dados = request.get_json(silent=True) or {}
    id_empresa = dados.get("empresa_id")
    try:
        id_empresa = int(id_empresa)
    except (TypeError, ValueError):
        return jsonify({"erro": "Empresa invalida."}), 400

    empresa = servico_empresas.buscar_por_id(id_empresa)
    if empresa is None or not empresa.ativo:
        return jsonify({"erro": "Empresa nao encontrada ou inativa."}), 404

    session["empresa_id"] = id_empresa
    recarregar_services_por_empresa(id_empresa)
    servico_auditoria.registrar("empresas", id_empresa, "trocar_empresa", None, empresa.nome_fantasia, usuario.nome)
    return jsonify({"mensagem": f"Empresa alterada para {empresa.nome_fantasia}!", "empresa": empresa_para_dict(empresa)})
