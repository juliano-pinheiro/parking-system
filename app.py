"""
Sistema de Estacionamento - Interface Web
==========================================

Ponto de entrada da aplicacao web. Expoe uma API REST (Flask) que
reaproveita as mesmas regras de negocio do terminal (EstacionamentoService)
e serve o frontend HTML/CSS/JS localizado em templates/ e static/.

Para executar:
    python app.py

Depois, acesse http://127.0.0.1:5000 no navegador.
"""

from datetime import datetime

from flask import Flask, jsonify, render_template, request

from services.estacionamento_service import EstacionamentoService, FORMATO_DATA
from services.usuario_service import UsuarioService
from services.cliente_service import ClienteService

app = Flask(__name__)

# Instancia unica do servico, compartilhada entre todas as requisicoes.
# Usa os mesmos arquivos JSON (data/tickets.json e data/configuracao.json)
# que a versao de terminal (main.py) utiliza.
servico = EstacionamentoService()
servico_usuarios = UsuarioService()
servico_clientes = ClienteService()


# ---------------------- FUNCOES AUXILIARES ----------------------

def tempo_estacionado(ticket) -> str:
    """Calcula ha quanto tempo o veiculo esta estacionado (para tickets abertos)."""
    entrada = datetime.strptime(ticket.entrada, FORMATO_DATA)
    referencia = datetime.strptime(ticket.saida, FORMATO_DATA) if ticket.saida else datetime.now()
    minutos_totais = int((referencia - entrada).total_seconds() // 60)

    if minutos_totais < 60:
        return f"{max(minutos_totais, 0)}min"

    horas = minutos_totais // 60
    minutos = minutos_totais % 60
    if minutos == 0:
        return f"{horas}h"
    return f"{horas}h{minutos:02d}min"


def ticket_para_dict(ticket) -> dict:
    """Serializa um Ticket para um dicionario simples (JSON-friendly)."""
    return {
        "numero": ticket.numero,
        "placa": ticket.placa,
        "vaga": ticket.vaga,
        "entrada": ticket.entrada,
        "saida": ticket.saida,
        "valor": ticket.valor,
        "status": ticket.status,
        "tipo_veiculo": ticket.tipo_veiculo,
        "observacoes": ticket.observacoes,
        "tempo_estacionado": tempo_estacionado(ticket),
    }


def config_para_dict() -> dict:
    """Serializa a configuracao atual (mais os contadores de vagas) em dict."""
    return {
        "total_vagas": servico.config.total_vagas,
        "valor_primeira_hora": servico.config.valor_primeira_hora,
        "valor_hora_adicional": servico.config.valor_hora_adicional,
        "valor_mensal": servico.config.valor_mensal,
        "vagas_ocupadas": servico.vagas_ocupadas(),
        "vagas_livres": servico.vagas_livres(),
    }


def usuario_para_dict(usuario) -> dict:
    """Serializa um Usuario para um dicionario simples (JSON-friendly)."""
    return usuario.to_dict()


def cliente_para_dict(cliente) -> dict:
    """Serializa um Cliente para um dicionario simples (JSON-friendly)."""
    return cliente.to_dict()


# ---------------------- ROTA PRINCIPAL (FRONTEND) ----------------------

@app.route("/")
def index():
    """Serve a pagina principal (SPA) do sistema."""
    return render_template("index.html")


# ---------------------- API: VAGAS / STATUS ----------------------

@app.route("/api/status", methods=["GET"])
def api_status():
    """Retorna o resumo de vagas (total, ocupadas, livres) e configuracao atual."""
    return jsonify(config_para_dict())


@app.route("/api/vagas", methods=["GET"])
def api_vagas():
    """Retorna o controle de vagas: totais + lista de veiculos estacionados agora."""
    veiculos = sorted(servico.listar_tickets_abertos(), key=lambda t: t.vaga)
    return jsonify({
        "total_vagas": servico.config.total_vagas,
        "vagas_ocupadas": servico.vagas_ocupadas(),
        "vagas_livres": servico.vagas_livres(),
        "veiculos": [ticket_para_dict(t) for t in veiculos],
    })


# ---------------------- API: DASHBOARD ----------------------

def formatar_permanencia_media(minutos):
    """Formata a permanencia media (em minutos) como texto legivel, ou '-' se nao houver dados."""
    if minutos is None:
        return "-"
    if minutos < 60:
        return f"{minutos}min"
    horas = minutos // 60
    resto = minutos % 60
    if resto == 0:
        return f"{horas}h"
    return f"{horas}h{resto:02d}min"


@app.route("/api/dashboard", methods=["GET"])
def api_dashboard():
    """Retorna os dados dos cards de resumo do topo do dashboard."""
    resumo = servico.resumo_dashboard()
    return jsonify({
        "no_patio_agora": resumo["no_patio_agora"],
        "faturamento_hoje": resumo["faturamento_hoje"],
        "saidas_hoje": resumo["saidas_hoje"],
        "permanencia_media_minutos": resumo["permanencia_media_minutos"],
        "permanencia_media_texto": formatar_permanencia_media(resumo["permanencia_media_minutos"]),
    })


# ---------------------- API: HISTORICO ----------------------

@app.route("/api/historico", methods=["GET"])
def api_historico():
    """Retorna o historico de veiculos que ja sairam do estacionamento."""
    fechados = servico.listar_tickets_fechados()
    return jsonify({"veiculos": [ticket_para_dict(t) for t in fechados]})


# ---------------------- API: BUSCA ----------------------

@app.route("/api/buscar", methods=["GET"])
def api_buscar():
    """Busca tickets (abertos e fechados) por placa ou numero de ticket."""
    termo = request.args.get("q", "").strip()
    resultados = servico.buscar_tickets(termo)
    resultados = sorted(resultados, key=lambda t: t.numero, reverse=True)
    return jsonify({"veiculos": [ticket_para_dict(t) for t in resultados]})


# ---------------------- API: ENTRADA ----------------------

@app.route("/api/entrada", methods=["POST"])
def api_registrar_entrada():
    """Registra a entrada de um veiculo (emite ticket)."""
    dados = request.get_json(silent=True) or {}
    placa = (dados.get("placa") or "").strip()
    tipo_veiculo = (dados.get("tipo_veiculo") or "Carro").strip()
    observacoes = (dados.get("observacoes") or "").strip()

    if not placa:
        return jsonify({"erro": "Placa invalida."}), 400

    try:
        ticket = servico.registrar_entrada(placa, tipo_veiculo=tipo_veiculo, observacoes=observacoes)
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400

    if ticket is None:
        return jsonify({"erro": "Nao ha vagas disponiveis no momento. Estacionamento cheio!"}), 409

    return jsonify({"mensagem": "Ticket emitido com sucesso!", "ticket": ticket_para_dict(ticket)}), 201


# ---------------------- API: SAIDA ----------------------

@app.route("/api/saida", methods=["POST"])
def api_registrar_saida():
    """Registra a saida de um veiculo (busca por ticket ou placa e calcula o valor)."""
    dados = request.get_json(silent=True) or {}
    identificador = (dados.get("identificador") or "").strip()

    if not identificador:
        return jsonify({"erro": "Informe o numero do ticket ou a placa do veiculo."}), 400

    ticket = servico.registrar_saida(identificador)

    if ticket is None:
        return jsonify({"erro": "Nenhum veiculo encontrado com esse ticket/placa (ou ja saiu)."}), 404

    return jsonify({"mensagem": "Saida registrada com sucesso!", "ticket": ticket_para_dict(ticket)})


# ---------------------- API: RELATORIO ----------------------

@app.route("/api/relatorio", methods=["GET"])
def api_relatorio():
    """Gera o relatorio de movimentacao, com filtro opcional por data (dd/mm/aaaa)."""
    data = request.args.get("data", "").strip() or None

    relatorio = servico.relatorio_movimentacao(data)

    return jsonify({
        "total_entradas": relatorio["total_entradas"],
        "total_saidas": relatorio["total_saidas"],
        "faturamento_total": relatorio["faturamento_total"],
        "veiculos_entrada": [ticket_para_dict(t) for t in relatorio["veiculos_entrada"]],
        "veiculos_saida": [ticket_para_dict(t) for t in relatorio["veiculos_saida"]],
    })


# ---------------------- API: CONFIGURACOES ----------------------

@app.route("/api/configuracoes", methods=["GET"])
def api_obter_configuracoes():
    """Retorna as configuracoes atuais (precos e total de vagas)."""
    return jsonify(config_para_dict())


@app.route("/api/configuracoes", methods=["POST"])
def api_atualizar_configuracoes():
    """Atualiza as configuracoes (precos, valor mensal e/ou total de vagas)."""
    dados = request.get_json(silent=True) or {}

    novo_total_vagas = dados.get("total_vagas")
    novo_valor_primeira_hora = dados.get("valor_primeira_hora")
    novo_valor_hora_adicional = dados.get("valor_hora_adicional")
    novo_valor_mensal = dados.get("valor_mensal")

    try:
        if novo_total_vagas is not None:
            novo_total_vagas = int(novo_total_vagas)
        if novo_valor_primeira_hora is not None:
            novo_valor_primeira_hora = float(novo_valor_primeira_hora)
        if novo_valor_hora_adicional is not None:
            novo_valor_hora_adicional = float(novo_valor_hora_adicional)
        if novo_valor_mensal is not None:
            novo_valor_mensal = float(novo_valor_mensal)
    except (TypeError, ValueError):
        return jsonify({"erro": "Valor invalido informado."}), 400

    if novo_total_vagas is not None and novo_total_vagas < servico.vagas_ocupadas():
        return jsonify({
            "erro": f"Nao e possivel definir {novo_total_vagas} vagas: "
                    f"ja existem {servico.vagas_ocupadas()} veiculos estacionados."
        }), 400

    servico.atualizar_configuracao(
        total_vagas=novo_total_vagas,
        valor_primeira_hora=novo_valor_primeira_hora,
        valor_hora_adicional=novo_valor_hora_adicional,
        valor_mensal=novo_valor_mensal,
    )

    return jsonify({"mensagem": "Configuracoes atualizadas com sucesso!", "configuracao": config_para_dict()})


# ---------------------- API: USUARIOS ----------------------

@app.route("/api/usuarios", methods=["GET"])
def api_listar_usuarios():
    """Retorna a lista de usuarios cadastrados."""
    usuarios = servico_usuarios.listar()
    return jsonify({"usuarios": [usuario_para_dict(u) for u in usuarios]})


@app.route("/api/usuarios", methods=["POST"])
def api_criar_usuario():
    """Cria um novo usuario."""
    dados = request.get_json(silent=True) or {}

    nome = (dados.get("nome") or "").strip()
    email = (dados.get("email") or "").strip()
    perfil = (dados.get("perfil") or "operador").strip()
    ativo = dados.get("ativo", True)

    try:
        ativo = bool(ativo)
    except (TypeError, ValueError):
        return jsonify({"erro": "Valor invalido para o campo 'ativo'."}), 400

    try:
        usuario = servico_usuarios.criar(nome=nome, email=email, perfil=perfil, ativo=ativo)
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400

    return jsonify({"mensagem": "Usuario cadastrado com sucesso!", "usuario": usuario_para_dict(usuario)}), 201


@app.route("/api/usuarios/<int:id_usuario>", methods=["GET"])
def api_obter_usuario(id_usuario: int):
    """Retorna um usuario especifico pelo id."""
    usuario = servico_usuarios.buscar_por_id(id_usuario)
    if usuario is None:
        return jsonify({"erro": "Usuario nao encontrado."}), 404
    return jsonify({"usuario": usuario_para_dict(usuario)})


@app.route("/api/usuarios/<int:id_usuario>", methods=["PUT"])
def api_atualizar_usuario(id_usuario: int):
    """Atualiza os dados de um usuario existente."""
    dados = request.get_json(silent=True) or {}

    nome = dados.get("nome")
    email = dados.get("email")
    perfil = dados.get("perfil")
    ativo = dados.get("ativo")

    if ativo is not None:
        try:
            ativo = bool(ativo)
        except (TypeError, ValueError):
            return jsonify({"erro": "Valor invalido para o campo 'ativo'."}), 400

    try:
        usuario = servico_usuarios.atualizar(
            id_usuario=id_usuario,
            nome=nome,
            email=email,
            perfil=perfil,
            ativo=ativo,
        )
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400

    if usuario is None:
        return jsonify({"erro": "Usuario nao encontrado."}), 404

    return jsonify({"mensagem": "Usuario atualizado com sucesso!", "usuario": usuario_para_dict(usuario)})


@app.route("/api/usuarios/<int:id_usuario>", methods=["DELETE"])
def api_excluir_usuario(id_usuario: int):
    """Desativa/exclui um usuario."""
    if not servico_usuarios.excluir(id_usuario):
        return jsonify({"erro": "Usuario nao encontrado."}), 404
    return jsonify({"mensagem": "Usuario desativado com sucesso!"})


# ---------------------- API: CLIENTES ----------------------

@app.route("/api/clientes", methods=["GET"])
def api_listar_clientes():
    """Retorna a lista de clientes (mensalistas) cadastrados."""
    clientes = servico_clientes.listar()
    return jsonify({"clientes": [cliente_para_dict(c) for c in clientes]})


@app.route("/api/clientes", methods=["POST"])
def api_criar_cliente():
    """Cria um novo cliente mensalista."""
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

    return jsonify({"mensagem": "Cliente cadastrado com sucesso!", "cliente": cliente_para_dict(cliente)}), 201


@app.route("/api/clientes/<int:id_cliente>", methods=["GET"])
def api_obter_cliente(id_cliente: int):
    """Retorna um cliente especifico pelo id."""
    cliente = servico_clientes.buscar_por_id(id_cliente)
    if cliente is None:
        return jsonify({"erro": "Cliente nao encontrado."}), 404
    return jsonify({"cliente": cliente_para_dict(cliente)})


@app.route("/api/clientes/<int:id_cliente>", methods=["PUT"])
def api_atualizar_cliente(id_cliente: int):
    """Atualiza os dados de um cliente existente."""
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

    return jsonify({"mensagem": "Cliente atualizado com sucesso!", "cliente": cliente_para_dict(cliente)})


@app.route("/api/clientes/<int:id_cliente>", methods=["DELETE"])
def api_excluir_cliente(id_cliente: int):
    """Desativa/exclui um cliente."""
    if not servico_clientes.excluir(id_cliente):
        return jsonify({"erro": "Cliente nao encontrado."}), 404
    return jsonify({"mensagem": "Cliente desativado com sucesso!"})


if __name__ == "__main__":
    app.run(debug=True)
