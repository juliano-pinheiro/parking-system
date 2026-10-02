"""
Blueprint de administracao: usuarios, empresas (multi-CNPJ), perfis,
permissoes e auditoria.
"""

from flask import Blueprint, jsonify, request, session

from services_registry import (
    servico_auditoria,
    servico_empresas,
    servico_perfil,
    servico_permissao,
    servico_usuarios,
    apenas_master,
    empresa_para_dict,
    usuario_logado,
    usuario_para_dict,
    verificar_permissao,
)

bp = Blueprint("administracao", __name__)


def perfil_para_dict(perfil):
    """Converte um Perfil em dicionario para a API."""
    return {
        "id": perfil.id,
        "codigo": perfil.codigo,
        "nome": perfil.nome,
        "descricao": perfil.descricao,
        "ativo": perfil.ativo,
    }


# ---------------------- API: USUARIOS ----------------------

@bp.route("/api/usuarios", methods=["GET"])
def api_listar_usuarios():
    """Retorna a lista de usuarios cadastrados."""
    ok, erro = verificar_permissao("usuarios", "ver")
    if not ok:
        return erro
    usuarios = servico_usuarios.listar()
    return jsonify({"usuarios": [usuario_para_dict(u) for u in usuarios]})


@bp.route("/api/usuarios", methods=["POST"])
def api_criar_usuario():
    """Cria um novo usuario."""
    ok, erro = verificar_permissao("usuarios", "criar")
    if not ok:
        return erro
    dados = request.get_json(silent=True) or {}

    nome = (dados.get("nome") or "").strip()
    email = (dados.get("email") or "").strip()
    perfil = (dados.get("perfil") or "operador").strip()
    ativo = dados.get("ativo", True)
    senha = dados.get("senha") or ""
    trocar_senha = dados.get("trocar_senha_no_proximo_acesso", False)
    empresa_id = dados.get("empresa_id")
    master = dados.get("master", False)

    try:
        ativo = bool(ativo)
        trocar_senha = bool(trocar_senha)
        master = bool(master)
    except (TypeError, ValueError):
        return jsonify({"erro": "Valor invalido para os campos booleanos."}), 400

    if not master and empresa_id in (None, ""):
        # Usuario nao-master sem empresa: tenta usar a empresa da sessao
        empresa_id = session.get("empresa_id")

    try:
        usuario = servico_usuarios.criar(
            nome=nome, email=email, perfil=perfil, ativo=ativo,
            senha=senha, trocar_senha_no_proximo_acesso=trocar_senha,
            empresa_id=empresa_id, master=master,
        )
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400

    return jsonify({"mensagem": "Usuario cadastrado com sucesso!", "usuario": usuario_para_dict(usuario)}), 201


@bp.route("/api/usuarios/<int:id_usuario>", methods=["GET"])
def api_obter_usuario(id_usuario: int):
    """Retorna um usuario especifico pelo id."""
    usuario = servico_usuarios.buscar_por_id(id_usuario)
    if usuario is None:
        return jsonify({"erro": "Usuario nao encontrado."}), 404
    return jsonify({"usuario": usuario_para_dict(usuario)})


@bp.route("/api/usuarios/<int:id_usuario>", methods=["PUT"])
def api_atualizar_usuario(id_usuario: int):
    """Atualiza os dados de um usuario existente."""
    ok, erro = verificar_permissao("usuarios", "editar")
    if not ok:
        return erro
    dados = request.get_json(silent=True) or {}

    nome = dados.get("nome")
    email = dados.get("email")
    perfil = dados.get("perfil")
    ativo = dados.get("ativo")
    senha = dados.get("senha")
    trocar_senha = dados.get("trocar_senha_no_proximo_acesso")
    empresa_id = dados.get("empresa_id")
    master = dados.get("master")

    if ativo is not None:
        try:
            ativo = bool(ativo)
        except (TypeError, ValueError):
            return jsonify({"erro": "Valor invalido para o campo 'ativo'."}), 400

    if trocar_senha is not None:
        try:
            trocar_senha = bool(trocar_senha)
        except (TypeError, ValueError):
            return jsonify({"erro": "Valor invalido para o campo 'trocar_senha_no_proximo_acesso'."}), 400

    if master is not None:
        try:
            master = bool(master)
        except (TypeError, ValueError):
            return jsonify({"erro": "Valor invalido para o campo 'master'."}), 400

    try:
        usuario = servico_usuarios.atualizar(
            id_usuario=id_usuario,
            nome=nome,
            email=email,
            perfil=perfil,
            ativo=ativo,
            senha=senha,
            trocar_senha_no_proximo_acesso=trocar_senha,
            empresa_id=empresa_id,
            master=master,
        )
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400

    if usuario is None:
        return jsonify({"erro": "Usuario nao encontrado."}), 404

    return jsonify({"mensagem": "Usuario atualizado com sucesso!", "usuario": usuario_para_dict(usuario)})


@bp.route("/api/usuarios/<int:id_usuario>", methods=["DELETE"])
def api_excluir_usuario(id_usuario: int):
    """Desativa/exclui um usuario."""
    ok, erro = verificar_permissao("usuarios", "excluir")
    if not ok:
        return erro
    try:
        if not servico_usuarios.excluir(id_usuario):
            return jsonify({"erro": "Usuario nao encontrado."}), 404
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    return jsonify({"mensagem": "Usuario desativado com sucesso!"})


# ---------------------- API: EMPRESAS (MULTI-CNPJ) ----------------------

@bp.route("/api/empresas", methods=["GET"])
def api_listar_empresas():
    """Lista todas as empresas. Usuarios nao-master veem apenas a sua."""
    usuario = usuario_logado()
    if usuario is None:
        return jsonify({"erro": "Nao autenticado."}), 401

    if usuario.master or usuario.perfil == "admin":
        empresas = servico_empresas.listar()
    else:
        if usuario.empresa_id:
            empresa = servico_empresas.buscar_por_id(usuario.empresa_id)
            empresas = [empresa] if empresa else []
        else:
            empresas = []

    return jsonify({"empresas": [empresa_para_dict(e) for e in empresas]})


@bp.route("/api/empresas", methods=["POST"])
def api_criar_empresa():
    """Cria uma nova empresa/CNPJ (somente master)."""
    ok, erro = apenas_master()
    if not ok:
        return erro
    dados = request.get_json(silent=True) or {}

    try:
        empresa = servico_empresas.criar(
            cnpj=(dados.get("cnpj") or "").strip(),
            razao_social=(dados.get("razao_social") or "").strip(),
            nome_fantasia=(dados.get("nome_fantasia") or "").strip(),
            telefone=(dados.get("telefone") or "").strip(),
            email=(dados.get("email") or "").strip(),
            endereco=(dados.get("endereco") or "").strip(),
            cidade=(dados.get("cidade") or "").strip(),
            estado=(dados.get("estado") or "").strip(),
            cep=(dados.get("cep") or "").strip(),
            ativo=dados.get("ativo", True),
        )
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400

    # Garante a configuracao inicial com o nome e CNPJ da nova empresa
    try:
        from services_registry import servico
        servico.persistencia.garantir_configuracao(
            empresa_id=empresa.id,
            nome_estacionamento=empresa.nome_fantasia,
            cnpj=empresa.cnpj,
        )
    except Exception:
        pass

    servico_auditoria.registrar("empresas", empresa.id, "criar", None, empresa.cnpj, usuario_logado().nome)
    return jsonify({"mensagem": "Empresa cadastrada com sucesso!", "empresa": empresa_para_dict(empresa)}), 201


@bp.route("/api/empresas/<int:id_empresa>", methods=["GET"])
def api_obter_empresa(id_empresa: int):
    """Retorna uma empresa especifica."""
    usuario = usuario_logado()
    if usuario is None:
        return jsonify({"erro": "Nao autenticado."}), 401
    if not (usuario.master or usuario.perfil == "admin") and usuario.empresa_id != id_empresa:
        return jsonify({"erro": "Voce nao tem acesso a esta empresa."}), 403
    empresa = servico_empresas.buscar_por_id(id_empresa)
    if empresa is None:
        return jsonify({"erro": "Empresa nao encontrada."}), 404
    return jsonify({"empresa": empresa_para_dict(empresa)})


@bp.route("/api/empresas/<int:id_empresa>", methods=["PUT"])
def api_atualizar_empresa(id_empresa: int):
    """Atualiza os dados de uma empresa existente (somente master)."""
    ok, erro = apenas_master()
    if not ok:
        return erro
    dados = request.get_json(silent=True) or {}

    campos = {
        "cnpj", "razao_social", "nome_fantasia", "telefone",
        "email", "endereco", "cidade", "estado", "cep", "ativo",
    }
    atualizacoes = {k: v for k, v in dados.items() if k in campos}

    try:
        empresa = servico_empresas.atualizar(id_empresa, **atualizacoes)
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400

    if empresa is None:
        return jsonify({"erro": "Empresa nao encontrada."}), 404

    # Sincroniza o nome do estacionamento na sessao ativa se for a mesma empresa
    if session.get("empresa_id") == empresa.id and "nome_fantasia" in atualizacoes:
        try:
            from services_registry import servico
            from supabase_client import supabase
            servico.config.nome_estacionamento = empresa.nome_fantasia
            supabase.table("configuracao").update({"nome_estacionamento": empresa.nome_fantasia}).eq("empresa_id", empresa.id).execute()
        except Exception:
            pass

    servico_auditoria.registrar("empresas", empresa.id, "atualizar", None, empresa.cnpj, usuario_logado().nome)
    return jsonify({"mensagem": "Empresa atualizada com sucesso!", "empresa": empresa_para_dict(empresa)})


@bp.route("/api/empresas/<int:id_empresa>/inativar", methods=["POST"])
def api_inativar_empresa(id_empresa: int):
    """Inativa uma empresa (somente master)."""
    ok, erro = apenas_master()
    if not ok:
        return erro
    if not servico_empresas.inativar(id_empresa):
        return jsonify({"erro": "Empresa nao encontrada."}), 404
    servico_auditoria.registrar("empresas", id_empresa, "inativar", None, None, usuario_logado().nome)
    return jsonify({"mensagem": "Empresa inativada com sucesso!"})


# ---------------------- API: PERMISSOES ----------------------

@bp.route("/api/permissoes", methods=["GET"])
def api_obter_permissoes():
    """Retorna a matriz de permissoes (modulo -> perfil -> acoes) e metadados.

    Acessivel a qualquer usuario autenticado: o frontend precisa desta matriz
    para montar o menu e ocultar telas/acoes sem permissao. As operacoes de
    edicao (PUT, perfis) continuam protegidas por 'usuarios/editar'.
    """
    if usuario_logado() is None:
        return jsonify({"erro": "Nao autenticado."}), 401
    catalogo = servico_permissao.catalogo_modulos()
    return jsonify({
        "matriz": servico_permissao.matriz(),
        "perfis": list(servico_permissao.perfis_validos()),
        "modulos": list(servico_permissao.modulos()),
        "acoes": list(servico_permissao.acoes_validas()),
        "categorias": catalogo.get("categorias", []),
        "acoes_por_modulo": catalogo.get("acoes_por_modulo", {}),
        "perfis_detalhes": [
            {
                "id": p.id,
                "codigo": p.codigo,
                "nome": p.nome,
                "descricao": p.descricao,
                "ativo": p.ativo,
            }
            for p in servico_perfil.listar_ativos()
        ],
    })


@bp.route("/api/permissoes", methods=["PUT"])
def api_salvar_permissoes():
    """Salva a matriz de permissoes personalizada."""
    ok, erro = verificar_permissao("usuarios", "editar")
    if not ok:
        return erro
    dados = request.get_json(silent=True) or {}
    nova_matriz = dados.get("matriz")
    if nova_matriz is None:
        return jsonify({"erro": "Matriz de permissoes nao informada."}), 400
    try:
        servico_permissao.salvar_matriz(nova_matriz)
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    servico_auditoria.registrar("permissoes", None, "matriz", None, "atualizada", usuario_logado().nome)
    return jsonify({"mensagem": "Permissoes atualizadas com sucesso!", "matriz": servico_permissao.matriz()})


@bp.route("/api/permissoes/restaurar", methods=["POST"])
def api_restaurar_permissoes():
    """Restaura as permissoes padrao de todos os perfis."""
    ok, erro = verificar_permissao("usuarios", "editar")
    if not ok:
        return erro
    servico_permissao.restaurar_padrao()
    servico_auditoria.registrar("permissoes", None, "matriz", None, "restaurada_padrao", usuario_logado().nome)
    return jsonify({"mensagem": "Permissoes restauradas para o padrao!", "matriz": servico_permissao.matriz()})


# ---------------------- API: PERFIS ----------------------

@bp.route("/api/perfis", methods=["GET"])
def api_listar_perfis():
    """Retorna todos os perfis cadastrados."""
    ok, erro = verificar_permissao("usuarios", "ver")
    if not ok:
        return erro
    return jsonify({
        "perfis": [perfil_para_dict(p) for p in servico_perfil.listar()],
        "ativos": [p.codigo for p in servico_perfil.listar_ativos()],
    })


@bp.route("/api/perfis", methods=["POST"])
def api_criar_perfil():
    """Cria um novo perfil personalizado."""
    ok, erro = verificar_permissao("usuarios", "editar")
    if not ok:
        return erro
    dados = request.get_json(silent=True) or {}
    nome = (dados.get("nome") or "").strip()
    codigo = (dados.get("codigo") or "").strip()
    descricao = (dados.get("descricao") or "").strip()
    try:
        perfil = servico_perfil.criar(nome=nome, codigo=codigo, descricao=descricao, ativo=True)
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    servico_auditoria.registrar("perfis", perfil.id, "criar", None, perfil.codigo, usuario_logado().nome)
    return jsonify({"mensagem": "Perfil criado com sucesso!", "perfil": perfil_para_dict(perfil)}), 201


@bp.route("/api/perfis/<int:id_perfil>", methods=["PUT"])
def api_atualizar_perfil(id_perfil):
    """Atualiza nome/descricao de um perfil."""
    ok, erro = verificar_permissao("usuarios", "editar")
    if not ok:
        return erro
    dados = request.get_json(silent=True) or {}
    nome = dados.get("nome")
    descricao = dados.get("descricao")
    try:
        perfil = servico_perfil.atualizar(id_perfil, nome=nome, descricao=descricao)
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    if perfil is None:
        return jsonify({"erro": "Perfil nao encontrado."}), 404
    servico_auditoria.registrar("perfis", perfil.id, "atualizar", None, perfil.codigo, usuario_logado().nome)
    return jsonify({"mensagem": "Perfil atualizado com sucesso!", "perfil": perfil_para_dict(perfil)})


@bp.route("/api/perfis/<int:id_perfil>/ativar", methods=["POST"])
def api_ativar_perfil(id_perfil):
    """Ativa um perfil."""
    ok, erro = verificar_permissao("usuarios", "editar")
    if not ok:
        return erro
    try:
        perfil = servico_perfil.atualizar(id_perfil, ativo=True)
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    if perfil is None:
        return jsonify({"erro": "Perfil nao encontrado."}), 404
    return jsonify({"mensagem": "Perfil ativado com sucesso!", "perfil": perfil_para_dict(perfil)})


@bp.route("/api/perfis/<int:id_perfil>/inativar", methods=["POST"])
def api_inativar_perfil(id_perfil):
    """Inativa um perfil."""
    ok, erro = verificar_permissao("usuarios", "editar")
    if not ok:
        return erro
    try:
        perfil = servico_perfil.atualizar(id_perfil, ativo=False)
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    if perfil is None:
        return jsonify({"erro": "Perfil nao encontrado."}), 404
    return jsonify({"mensagem": "Perfil inativado com sucesso!", "perfil": perfil_para_dict(perfil)})


@bp.route("/api/perfis/<int:id_perfil>/clonar", methods=["POST"])
def api_clonar_perfil(id_perfil):
    """Copia as permissoes de um perfil de origem para o perfil informado."""
    ok, erro = verificar_permissao("usuarios", "editar")
    if not ok:
        return erro
    dados = request.get_json(silent=True) or {}
    origem = (dados.get("origem") or "").strip()
    if not origem:
        return jsonify({"erro": "Informe o perfil de origem."}), 400
    perfil = servico_perfil.buscar_por_id(id_perfil)
    if perfil is None:
        return jsonify({"erro": "Perfil nao encontrado."}), 404
    try:
        servico_permissao.clonar_perfil(origem, perfil.codigo)
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    servico_auditoria.registrar("permissoes", None, "clonar", origem, perfil.codigo, usuario_logado().nome)
    return jsonify({"mensagem": "Permissoes clonadas com sucesso!", "matriz": servico_permissao.matriz()})


# ---------------------- API: AUDITORIA ----------------------

@bp.route("/api/auditoria", methods=["GET"])
def api_listar_auditoria():
    """Retorna os registros de auditoria."""
    ok, erro = verificar_permissao("auditoria", "ver")
    if not ok:
        return erro
    registros = servico_auditoria.listar()
    return jsonify({"auditoria": [a.to_dict() for a in registros]})


@bp.route("/api/logs-acesso", methods=["GET"])
def api_listar_logs_acesso():
    """Retorna os logs de acesso."""
    ok, erro = verificar_permissao("auditoria", "ver")
    if not ok:
        return erro
    logs = servico_auditoria.listar_logs()
    return jsonify({"logs_acesso": [l.to_dict() for l in logs]})
