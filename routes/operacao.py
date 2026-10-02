"""
Blueprint de operacao: status, vagas, dashboard, historico, busca,
entrada/saida de veiculos e ticket perdido.
"""

from datetime import datetime

from flask import Blueprint, jsonify, request

from services_registry import (
    servico,
    servico_auditoria,
    servico_caixa,
    servico_lista_negra,
    servico_mensalistas,
    servico_pagamentos,
    servico_permissao,
    servico_tabela_precos,
    config_para_dict,
    tempo_estacionado,
    ticket_para_dict,
    usuario_logado,
    verificar_permissao,
)

bp = Blueprint("operacao", __name__)

FORMATO_DATA = "%d/%m/%Y %H:%M:%S"


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


@bp.route("/api/status", methods=["GET"])
def api_status():
    """Retorna o resumo de vagas (total, ocupadas, livres) e configuracao atual."""
    ok, erro = verificar_permissao("operacao", "ver")
    if not ok:
        return erro
    return jsonify(config_para_dict())


@bp.route("/api/vagas", methods=["GET"])
def api_vagas():
    """Retorna o controle de vagas: totais + lista de veiculos estacionados agora."""
    ok, erro = verificar_permissao("operacao", "ver")
    if not ok:
        return erro
    veiculos = sorted(servico.listar_tickets_abertos(), key=lambda t: t.vaga)
    return jsonify({
        "total_vagas": servico.config.total_vagas,
        "vagas_ocupadas": servico.vagas_ocupadas(),
        "vagas_livres": servico.vagas_livres(),
        "veiculos": [ticket_para_dict(t) for t in veiculos],
    })


@bp.route("/api/dashboard", methods=["GET"])
def api_dashboard():
    """Retorna os dados dos cards de resumo do topo do dashboard e status do caixa."""
    ok, erro = verificar_permissao("operacao", "ver")
    if not ok:
        return erro
    resumo = servico.resumo_dashboard()
    caixa_atual = servico_caixa.caixa_aberto()
    return jsonify({
        "no_patio_agora": resumo["no_patio_agora"],
        "total_vagas": resumo["total_vagas"],
        "vagas_disponiveis": resumo["vagas_disponiveis"],
        "faturamento_hoje": resumo["faturamento_hoje"],
        "saidas_hoje": resumo["saidas_hoje"],
        "permanencia_media_minutos": resumo["permanencia_media_minutos"],
        "permanencia_media_texto": formatar_permanencia_media(resumo["permanencia_media_minutos"]),
        "caixa_aberto": caixa_atual.to_dict() if caixa_atual else None,
        "caixa_status": "aberto" if caixa_atual else "fechado",
    })


@bp.route("/api/historico", methods=["GET"])
def api_historico():
    """Retorna o historico de veiculos que ja sairam do estacionamento."""
    ok, erro = verificar_permissao("operacao", "ver")
    if not ok:
        return erro
    fechados = servico.listar_tickets_fechados()
    return jsonify({"veiculos": [ticket_para_dict(t) for t in fechados]})


@bp.route("/api/buscar", methods=["GET"])
def api_buscar():
    """Busca tickets (abertos e fechados) por placa ou numero de ticket."""
    ok, erro = verificar_permissao("operacao", "ver")
    if not ok:
        return erro
    termo = request.args.get("q", "").strip()
    resultados = servico.buscar_tickets(termo)
    resultados = sorted(resultados, key=lambda t: t.numero, reverse=True)
    return jsonify({"veiculos": [ticket_para_dict(t) for t in resultados]})


@bp.route("/api/entrada", methods=["POST"])
def api_registrar_entrada():
    """Registra a entrada de um veiculo (emite ticket)."""
    ok, erro = verificar_permissao("operacao", "criar")
    if not ok:
        return erro

    dados = request.get_json(silent=True) or {}
    placa = (dados.get("placa") or "").strip()
    tipo_veiculo = (dados.get("tipo_veiculo") or "Carro").strip()
    observacoes = (dados.get("observacoes") or "").strip()

    # Regra Operacional Obrigatória: Não autorizar emissão de tickets sem caixa aberto
    caixa_atual = servico_caixa.caixa_aberto()
    if caixa_atual is None:
        return jsonify({
            "erro": "Não é permitido emitir tickets sem um caixa aberto. Por favor, realize a abertura do caixa antes de registrar entradas.",
            "caixa_fechado": True,
        }), 400

    if not placa:
        return jsonify({"erro": "Placa invalida."}), 400

    if servico.config.exigir_observacao and not observacoes:
        return jsonify({"erro": "Informe as observacoes do veiculo (cor, modelo, etc.)."}), 400

    # Lista negra: bloqueia a entrada de veiculos sem autorizacao
    bloqueio = servico_lista_negra.verificar_placa(placa)
    if bloqueio is not None:
        motivo = f"Veiculo na lista negra: {bloqueio.motivo or 'sem motivo informado'}"
        return jsonify({"erro": motivo, "lista_negra": True}), 403

    # Mensalista: valida status e bloqueio por inadimplencia
    mensalista = servico_mensalistas.buscar_por_placa(placa)
    if mensalista is not None:
        if mensalista.status == "bloqueado":
            return jsonify({
                "erro": f"Mensalista {mensalista.nome} esta BLOQUEADO por inadimplencia. Entrada nao autorizada.",
                "mensalista_bloqueado": True,
            }), 403
        if not observacoes:
            observacoes = f"Mensalista: {mensalista.nome}"
        tipo_veiculo = getattr(mensalista, "tipo_veiculo", tipo_veiculo) or tipo_veiculo

    try:
        ticket = servico.registrar_entrada(placa, tipo_veiculo=tipo_veiculo, observacoes=observacoes)
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400

    if ticket is None:
        return jsonify({"erro": "Nao ha vagas disponiveis no momento. Estacionamento cheio!"}), 409

    return jsonify({"mensagem": "Ticket emitido com sucesso!", "ticket": ticket_para_dict(ticket)}), 201


@bp.route("/api/saida/calcular", methods=["GET"])
def api_calcular_saida():
    """Calcula previamente o tempo de permanencia e o valor a pagar de um ticket aberto."""
    ok, erro = verificar_permissao("operacao", "ver")
    if not ok:
        return erro

    identificador = (request.args.get("identificador") or "").strip()
    if not identificador:
        return jsonify({"erro": "Informe a placa ou numero do ticket."}), 400

    ticket = servico._buscar_ticket_aberto(identificador)
    if ticket is None:
        return jsonify({"erro": "Nenhum veiculo aberto encontrado com esse ticket/placa."}), 404

    # Verifica se pertence a mensalista ativo
    mensalista = servico_mensalistas.buscar_por_placa(ticket.placa)
    eh_mensalista = (mensalista is not None and mensalista.status == "ativo")

    agora_str = datetime.now().strftime(FORMATO_DATA)
    tempo = tempo_estacionado(ticket)
    valor = 0.0 if eh_mensalista else servico.calcular_valor(ticket.entrada, agora_str, ticket.tipo_veiculo)

    return jsonify({
        "ticket": ticket_para_dict(ticket),
        "tempo_permanencia": tempo,
        "valor": valor,
        "eh_mensalista": eh_mensalista,
        "mensalista_nome": mensalista.nome if eh_mensalista else None,
    })


@bp.route("/api/saida", methods=["POST"])
def api_registrar_saida():
    """Registra a saida de um veiculo (busca por ticket ou placa e calcula o valor)."""
    ok, erro = verificar_permissao("operacao", "criar")
    if not ok:
        return erro

    dados = request.get_json(silent=True) or {}
    identificador = str(dados.get("identificador") or "").strip()
    forma_pagamento = (dados.get("forma_pagamento") or "").strip() or None

    if not identificador:
        return jsonify({"erro": "Informe o numero do ticket ou a placa do veiculo."}), 400

    # Verifica antecipadamente se pertence a mensalista ativo
    ticket_aberto = servico._buscar_ticket_aberto(identificador)
    eh_mensalista = False
    if ticket_aberto is not None:
        mensalista = servico_mensalistas.buscar_por_placa(ticket_aberto.placa)
        if mensalista is not None and mensalista.status == "ativo":
            eh_mensalista = True
            forma_pagamento = "mensalista"

    ticket = servico.registrar_saida(identificador, forma_pagamento)

    if ticket is None:
        return jsonify({"erro": "Nenhum veiculo encontrado com esse ticket/placa (ou ja saiu)."}), 404

    # Mensalista ativo nao e cobrado por saida avulsa (valor zerado)
    if eh_mensalista:
        ticket.valor = 0.0
        ticket.forma_pagamento = "mensalista"
        servico.persistencia.salvar_ticket_individual(ticket, servico.empresa_id)
        return jsonify({
            "mensagem": f"Saida de mensalista registrada com sucesso! (Isento de cobranca avulsa)",
            "ticket": ticket_para_dict(ticket),
        })

    # Gera o pagamento + movimentacao de caixa + lancamento financeiro.
    # A saida do veiculo nao e bloqueada se o financeiro falhar, mas o erro
    # e registrado na auditoria e retornado como aviso (nunca ignorado).
    usuario = usuario_logado()
    operador = usuario.nome if usuario else "operador"
    aviso = None
    try:
        servico_pagamentos.registrar_pagamento_ticket(
            ticket,
            forma_pagamento=forma_pagamento or "dinheiro",
            operador=operador,
        )
    except Exception as erro_pagamento:
        aviso = ("Saida registrada, mas houve falha ao registrar o pagamento "
                 "no financeiro. Verifique o caixa/financeiro.")
        try:
            servico_auditoria.registrar(
                "pagamentos", ticket.numero, "registrar_pagamento_ticket",
                None, str(erro_pagamento), operador, request.remote_addr,
            )
        except Exception:
            pass

    resposta = {"mensagem": "Saida registrada com sucesso!", "ticket": ticket_para_dict(ticket)}
    if aviso:
        resposta["aviso"] = aviso
    return jsonify(resposta)


@bp.route("/api/ticket-perdido", methods=["POST"])
def api_ticket_perdido():
    """Registra um ticket perdido: cobra a tarifa de ticket perdido e
    gera pagamento + movimentacao + lancamento financeiro.
    Requer autorizacao (admin/supervisor) ou parametro 'autorizado'.
    """
    ok, erro = verificar_permissao("operacao", "criar")
    if not ok:
        return erro

    dados = request.get_json(silent=True) or {}
    placa = (dados.get("placa") or "").strip().upper()
    observacoes = (dados.get("observacoes") or "").strip()
    forma_pagamento = (dados.get("forma_pagamento") or "dinheiro").strip() or "dinheiro"
    autorizador = (dados.get("autorizador") or "").strip()

    # Validação Operacional Obrigatória: Não autorizar cobrança de ticket sem caixa aberto
    if servico_caixa.caixa_aberto() is None:
        return jsonify({
            "erro": "Não é permitido registrar ticket perdido com o caixa fechado. Por favor, realize a abertura do caixa antes.",
            "caixa_fechado": True,
        }), 400

    usuario = usuario_logado()
    perfil = usuario.perfil if usuario else ""
    if perfil != "admin" and not servico_permissao.pode(perfil, "operacao", "autorizar") and not autorizador:
        return jsonify({"erro": "Ticket perdido requer autorizacao de admin/supervisor."}), 403

    tabela = servico_tabela_precos.obter_vigente()
    valor = dados.get("valor")
    if valor is None or float(valor) <= 0:
        valor = getattr(tabela, "valor_ticket_perdido", 0) or 0
    if not valor or float(valor) <= 0:
        return jsonify({"erro": "Configure a tarifa de ticket perdido na tabela de precos."}), 400
    valor = round(float(valor), 2)

    if not observacoes:
        return jsonify({"erro": "Informe as observacoes do ticket perdido."}), 400

    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    # Integridade Operacional: se o veiculo ja esta estacionado no patio, encerra o ticket original
    # liberando a vaga e evitando 'veiculo fantasma' no patio.
    ticket_aberto = servico._buscar_ticket_aberto(placa) if placa else None
    if ticket_aberto is not None:
        ticket_aberto.saida = agora
        ticket_aberto.valor = valor
        ticket_aberto.status = "FECHADO"
        ticket_aberto.forma_pagamento = forma_pagamento
        obs_antiga = ticket_aberto.observacoes or ""
        ticket_aberto.observacoes = f"{obs_antiga} | TICKET PERDIDO - {observacoes}".strip(" |")
        servico.persistencia.salvar_ticket_individual(ticket_aberto, servico.empresa_id)
        ticket = ticket_aberto
    else:
        # Gera um ticket fechado (perdido) avulso caso nao houvesse registro de entrada
        numero = max(servico.config.proximo_numero_ticket, servico.persistencia.proximo_numero_global())
        from models.ticket import Ticket
        ticket = Ticket(
            numero=numero,
            placa=placa or f"PERDIDO-{numero}",
            entrada=agora,
            saida=agora,
            valor=valor,
            vaga=None,
            status="FECHADO",
            tipo_veiculo=(dados.get("tipo_veiculo") or "Carro").strip() or "Carro",
            observacoes=f"TICKET PERDIDO - {observacoes}",
            forma_pagamento=forma_pagamento,
            empresa_id=servico.empresa_id,
        )
        servico.tickets.append(ticket)
        servico.config.proximo_numero_ticket = numero + 1
        servico._salvar_tudo()

    operador = usuario.nome if usuario else "operador"
    aviso = None
    try:
        servico_pagamentos.registrar_pagamento_ticket(
            ticket, forma_pagamento=forma_pagamento, operador=operador,
        )
    except Exception as erro_pagamento:
        aviso = "Ticket perdido registrado, mas houve falha ao registrar o pagamento no financeiro."
        try:
            servico_auditoria.registrar(
                "pagamentos", ticket.numero, "ticket_perdido", None, str(erro_pagamento),
                operador, request.remote_addr,
            )
        except Exception:
            pass

    try:
        servico_auditoria.registrar(
            "operacao", ticket.numero, "ticket_perdido", None,
            f"Ticket perdido cobrado ({valor:.2f}) autorizado por {autorizador or perfil or 'admin'}",
            operador, request.remote_addr,
        )
    except Exception:
        pass

    resposta = {"mensagem": "Ticket perdido registrado!", "ticket": ticket_para_dict(ticket)}
    if aviso:
        resposta["aviso"] = aviso
    return jsonify(resposta), 201


@bp.route("/api/acesso-mobile", methods=["GET"])
def api_acesso_mobile():
    """Retorna dados de conexão para acesso via smartphone (IP local, porta, URL e QR Code)."""
    ok, erro = verificar_permissao("operacao", "ver")
    if not ok:
        return erro

    import socket
    ip_local = "127.0.0.1"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        s.connect(("8.8.8.8", 80))
        ip_local = s.getsockname()[0]
        s.close()
    except Exception:
        try:
            ip_local = socket.gethostbyname(socket.gethostname())
        except Exception:
            ip_local = "127.0.0.1"

    host_req = request.host.split(":")[0]
    porta = request.host.split(":")[1] if ":" in request.host else "5000"

    # Se a requisição veio de um IP na rede ou host real, prioriza esse host
    ip_final = host_req if host_req not in ("localhost", "127.0.0.1") else ip_local
    url_acesso = f"http://{ip_final}:{porta}"

    return jsonify({
        "ip_local": ip_final,
        "porta": porta,
        "url_acesso": url_acesso,
        "hostname": socket.gethostname(),
    })
