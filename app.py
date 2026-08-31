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

from flask import Flask, jsonify, render_template, request, session, redirect, url_for

from services.estacionamento_service import EstacionamentoService, FORMATO_DATA
from services.usuario_service import UsuarioService
from services.cliente_service import ClienteService
from services.financeiro_service import FinanceiroService, FORMAS_PAGAMENTO_LABEL
from services.caixa_service import CaixaService
from services.pagamento_service import PagamentoService
from services.forma_pagamento_service import FormaPagamentoService
from services.tabela_preco_service import TabelaPrecoService
from services.tipo_veiculo_service import TipoVeiculoService
from services.desconto_service import DescontoService
from services.cortesia_service import CortesiaService
from services.mensalista_service import MensalistaService
from services.convenio_service import ConvenioService
from services.contas_receber_service import ContasReceberService
from services.estorno_service import EstornoService
from services.auditoria_service import AuditoriaService
from services.permissao_service import PermissaoService
from services.perfil_service import PerfilService
from services.empresa_service import EmpresaService
from services.dashboard_financeiro_service import DashboardFinanceiroService
from services.relatorio_service import RelatorioService
from services.nfse_service import NfseService
from services.lista_negra_service import ListaNegraService
from services.reserva_service import ReservaService
from services.ocorrencia_service import OcorrenciaService
from services.backup_service import BackupService
from services.notificacao_service import NotificacaoService

app = Flask(__name__)
app.secret_key = "estaciona-parking-secret-key-2026"

# Instancia unica do servico, compartilhada entre todas as requisicoes.
# Os dados sao persistidos no Supabase (mesmas regras de negocio da
# versao de terminal main.py).
servico = EstacionamentoService()
servico_empresas = EmpresaService()
servico_usuarios = UsuarioService()
servico_clientes = ClienteService()
servico_financeiro = FinanceiroService()
servico_caixa = CaixaService()
servico_pagamentos = PagamentoService(
    caixa_service=servico_caixa,
    financeiro_service=servico_financeiro,
)
servico_formas_pagamento = FormaPagamentoService()
servico_tabela_precos = TabelaPrecoService()
servico_tipos_veiculo = TipoVeiculoService()
servico_tabela_precos.definir_tipos_personalizados(servico_tipos_veiculo.listar(somente_ativos=True))
servico_descontos = DescontoService()
servico_cortesias = CortesiaService()
servico_mensalistas = MensalistaService()
servico_convenios = ConvenioService()
servico_contas_receber = ContasReceberService()
servico_estornos = EstornoService()
servico_auditoria = AuditoriaService()
servico_perfil = PerfilService()
servico_permissao = PermissaoService(perfil_service=servico_perfil)
servico_dashboard_financeiro = DashboardFinanceiroService(
    financeiro_service=servico_financeiro,
    pagamento_service=servico_pagamentos,
)
servico_relatorio = RelatorioService(
    financeiro_service=servico_financeiro,
    nome_estacionamento=servico.config.nome_estacionamento,
    estacionamento_service=servico,
    desconto_service=servico_descontos,
    cortesia_service=servico_cortesias,
    estorno_service=servico_estornos,
    mensalista_service=servico_mensalistas,
    conta_receber_service=servico_contas_receber,
)
servico_nfse = NfseService()
servico_lista_negra = ListaNegraService()
servico_reservas = ReservaService()
servico_ocorrencias = OcorrenciaService()
servico_notificacao = NotificacaoService(
    mensalista_service=servico_mensalistas,
    nome_estacionamento=servico.config.nome_estacionamento,
)
servico_backup = BackupService(services={
    "servico": servico,
    "financeiro": servico_financeiro,
    "caixa": servico_caixa,
    "pagamentos": servico_pagamentos,
    "formas_pagamento": servico_formas_pagamento,
    "tabela_precos": servico_tabela_precos,
    "tipos_veiculo": servico_tipos_veiculo,
    "descontos": servico_descontos,
    "cortesias": servico_cortesias,
    "mensalistas": servico_mensalistas,
    "convenios": servico_convenios,
    "contas_receber": servico_contas_receber,
    "estornos": servico_estornos,
    "clientes": servico_clientes,
    "nfse": servico_nfse,
    "lista_negra": servico_lista_negra,
    "reservas": servico_reservas,
    "ocorrencias": servico_ocorrencias,
})


def recarregar_services_por_empresa(empresa_id=None):
    """Recarrega todos os services de dados com o empresa_id ativo.

    Chamado no login e na troca de empresa para isolar os dados por CNPJ.
    Services globais (empresas, usuarios, perfis, permissoes, auditoria)
    nao sao recarregados.
    """
    eid = empresa_id
    servico.recarregar(eid)
    servico_financeiro.recarregar(eid)
    servico_caixa.recarregar(eid)
    servico_pagamentos.recarregar(eid)
    servico_formas_pagamento.recarregar(eid)
    servico_tabela_precos.recarregar(eid)
    servico_tipos_veiculo.recarregar(eid)
    servico_tabela_precos.definir_tipos_personalizados(
        servico_tipos_veiculo.listar(somente_ativos=True)
    )
    servico_descontos.recarregar(eid)
    servico_cortesias.recarregar(eid)
    servico_mensalistas.recarregar(eid)
    servico_convenios.recarregar(eid)
    servico_contas_receber.recarregar(eid)
    servico_estornos.recarregar(eid)
    servico_clientes.recarregar(eid)
    servico_nfse.recarregar(eid)
    servico_lista_negra.recarregar(eid)
    servico_reservas.recarregar(eid)
    servico_ocorrencias.recarregar(eid)
    servico_notificacao._mensalistas = servico_mensalistas
    servico_notificacao._nome_estacionamento = servico.config.nome_estacionamento


# ---------------------- AUTENTICACAO ----------------------

def usuario_logado():
    """Retorna o usuario autenticado na sessao, ou None."""
    id_usuario = session.get("usuario_id")
    if id_usuario is None:
        return None
    return servico_usuarios.buscar_por_id(id_usuario)


@app.route("/api/login", methods=["POST"])
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


@app.route("/api/logout", methods=["POST"])
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


@app.route("/api/trocar-senha", methods=["POST"])
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


@app.route("/api/sessao", methods=["GET"])
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


@app.route("/api/empresa/atual", methods=["GET"])
def api_empresa_atual():
    """Retorna a empresa ativa na sessao."""
    usuario = usuario_logado()
    if usuario is None:
        return jsonify({"erro": "Nao autenticado."}), 401
    empresa = servico_empresas.buscar_por_id(session.get("empresa_id")) if session.get("empresa_id") else None
    if empresa is None:
        return jsonify({"empresa": None})
    return jsonify({"empresa": empresa_para_dict(empresa)})


@app.route("/api/empresa/trocar", methods=["POST"])
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
    entrada = ticket.entrada or ""
    saida = ticket.saida or ""
    return {
        "numero": ticket.numero,
        "placa": ticket.placa,
        "vaga": ticket.vaga,
        "entrada": entrada,
        "entrada_data": entrada.split(" ")[0] if " " in entrada else entrada,
        "entrada_hora": entrada.split(" ")[1] if " " in entrada else "",
        "saida": saida,
        "saida_data": saida.split(" ")[0] if " " in saida else saida,
        "saida_hora": saida.split(" ")[1] if " " in saida else "",
        "valor": ticket.valor,
        "valor_pago": ticket.valor,
        "status": ticket.status,
        "tipo_veiculo": ticket.tipo_veiculo,
        "observacoes": ticket.observacoes,
        "forma_pagamento": ticket.forma_pagamento,
        "tempo_estacionado": tempo_estacionado(ticket),
    }


def config_para_dict() -> dict:
    """Serializa a configuracao atual (mais os contadores de vagas) em dict."""
    cfg = servico.config
    return {
        # Identificacao
        "nome_estacionamento": cfg.nome_estacionamento,
        "cnpj": cfg.cnpj,
        "telefone": cfg.telefone,
        "endereco": cfg.endereco,
        "cidade": cfg.cidade,
        "estado": cfg.estado,
        "cep": cfg.cep,
        # Vagas
        "total_vagas": cfg.total_vagas,
        "vagas_carro": cfg.vagas_carro,
        "vagas_moto": cfg.vagas_moto,
        "vagas_carro_grande": cfg.vagas_carro_grande,
        "vagas_caminhonete": cfg.vagas_caminhonete,
        "vagas_ocupadas": servico.vagas_ocupadas(),
        "vagas_livres": servico.vagas_livres(),
        # Precos
        "valor_primeira_hora": cfg.valor_primeira_hora,
        "valor_hora_adicional": cfg.valor_hora_adicional,
        "valor_mensal": cfg.valor_mensal,
        # Funcionamento
        "horario_abertura": cfg.horario_abertura,
        "horario_fechamento": cfg.horario_fechamento,
        # Ticket
        "cabecalho_ticket": cfg.cabecalho_ticket,
        "rodape_ticket": cfg.rodape_ticket,
        # Regras
        "bloquear_sem_vaga": cfg.bloquear_sem_vaga,
        "exigir_observacao": cfg.exigir_observacao,
        # Integracoes
        "pix_tipo": cfg.pix_tipo,
        "pix_chave": cfg.pix_chave,
    }


def usuario_para_dict(usuario) -> dict:
    """Serializa um Usuario para um dicionario simples (JSON-friendly), sem expor a senha."""
    dados = usuario.to_dict()
    dados.pop("senha", None)
    # Fallback: perfil admin sempre e tratado como master
    if usuario.perfil == "admin":
        dados["master"] = True
    return dados


def empresa_para_dict(empresa) -> dict:
    """Serializa uma Empresa para um dicionario simples (JSON-friendly)."""
    if empresa is None:
        return None
    dados = empresa.to_dict()
    # Inclui a quantidade de usuarios vinculados
    try:
        dados["usuarios"] = sum(
            1 for u in servico_usuarios.listar()
            if u.empresa_id == empresa.id
        )
    except Exception:
        dados["usuarios"] = 0
    return dados


def cliente_para_dict(cliente) -> dict:
    """Serializa um Cliente para um dicionario simples (JSON-friendly)."""
    return cliente.to_dict()


def lancamento_para_dict(lancamento) -> dict:
    """Serializa um Lancamento para um dicionario simples (JSON-friendly)."""
    return lancamento.to_dict()


# ---------------------- ROTA PRINCIPAL (FRONTEND) ----------------------

@app.route("/")
def index():
    """Serve a pagina principal (SPA) do sistema. Exige autenticacao."""
    if usuario_logado() is None:
        return redirect(url_for("login"))
    return render_template("index.html")


@app.route("/login")
def login():
    """Serve a pagina de login."""
    if usuario_logado() is not None:
        return redirect(url_for("index"))
    return render_template("login.html")


# ---------------------- API: VAGAS / STATUS ----------------------

@app.route("/api/status", methods=["GET"])
def api_status():
    """Retorna o resumo de vagas (total, ocupadas, livres) e configuracao atual."""
    ok, erro = verificar_permissao("operacao", "ver")
    if not ok:
        return erro
    return jsonify(config_para_dict())


@app.route("/api/vagas", methods=["GET"])
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
    ok, erro = verificar_permissao("operacao", "ver")
    if not ok:
        return erro
    resumo = servico.resumo_dashboard()
    return jsonify({
        "no_patio_agora": resumo["no_patio_agora"],
        "total_vagas": resumo["total_vagas"],
        "vagas_disponiveis": resumo["vagas_disponiveis"],
        "faturamento_hoje": resumo["faturamento_hoje"],
        "saidas_hoje": resumo["saidas_hoje"],
        "permanencia_media_minutos": resumo["permanencia_media_minutos"],
        "permanencia_media_texto": formatar_permanencia_media(resumo["permanencia_media_minutos"]),
    })


# ---------------------- API: HISTORICO ----------------------

@app.route("/api/historico", methods=["GET"])
def api_historico():
    """Retorna o historico de veiculos que ja sairam do estacionamento."""
    ok, erro = verificar_permissao("operacao", "ver")
    if not ok:
        return erro
    fechados = servico.listar_tickets_fechados()
    return jsonify({"veiculos": [ticket_para_dict(t) for t in fechados]})


# ---------------------- API: BUSCA ----------------------

@app.route("/api/buscar", methods=["GET"])
def api_buscar():
    """Busca tickets (abertos e fechados) por placa ou numero de ticket."""
    ok, erro = verificar_permissao("operacao", "ver")
    if not ok:
        return erro
    termo = request.args.get("q", "").strip()
    resultados = servico.buscar_tickets(termo)
    resultados = sorted(resultados, key=lambda t: t.numero, reverse=True)
    return jsonify({"veiculos": [ticket_para_dict(t) for t in resultados]})


# ---------------------- API: ENTRADA ----------------------

@app.route("/api/entrada", methods=["POST"])
def api_registrar_entrada():
    """Registra a entrada de um veiculo (emite ticket)."""
    ok, erro = verificar_permissao("operacao", "criar")
    if not ok:
        return erro

    dados = request.get_json(silent=True) or {}
    placa = (dados.get("placa") or "").strip()
    tipo_veiculo = (dados.get("tipo_veiculo") or "Carro").strip()
    observacoes = (dados.get("observacoes") or "").strip()

    if not placa:
        return jsonify({"erro": "Placa invalida."}), 400

    if not observacoes:
        return jsonify({"erro": "Informe as observacoes do veiculo (cor, modelo, etc.)."}), 400

    # Lista negra: bloqueia a entrada de veiculos sem autorizacao
    bloqueio = servico_lista_negra.verificar_placa(placa)
    if bloqueio is not None:
        motivo = f"Veiculo na lista negra: {bloqueio.motivo or 'sem motivo informado'}"
        return jsonify({"erro": motivo, "lista_negra": True}), 403

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
    ok, erro = verificar_permissao("operacao", "criar")
    if not ok:
        return erro

    dados = request.get_json(silent=True) or {}
    identificador = str(dados.get("identificador") or "").strip()
    forma_pagamento = (dados.get("forma_pagamento") or "").strip() or None

    if not identificador:
        return jsonify({"erro": "Informe o numero do ticket ou a placa do veiculo."}), 400

    ticket = servico.registrar_saida(identificador, forma_pagamento)

    if ticket is None:
        return jsonify({"erro": "Nenhum veiculo encontrado com esse ticket/placa (ou ja saiu)."}), 404

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


# ---------------------- API: RELATORIO ----------------------

@app.route("/api/relatorio", methods=["GET"])
def api_relatorio():
    """
    Gera o relatorio de movimentacao.
    Filtros: 'data' (dd/mm/aaaa) ou 'periodo' (diario|semanal|mensal).
    Retorna tambem o faturamento por forma de pagamento.
    """
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


# ---------------------- API: CONFIGURACOES ----------------------

@app.route("/api/configuracoes", methods=["GET"])
def api_obter_configuracoes():
    """Retorna as configuracoes atuais (precos e total de vagas)."""
    ok, erro = verificar_permissao("configuracoes", "ver")
    if not ok:
        return erro
    return jsonify(config_para_dict())


def _normalizar_valor_config(campo: str, valor) -> any:
    """Converte o valor recebido da API para o tipo adequado do campo."""
    if valor is None:
        return None
    campos_int = {
        "total_vagas", "vagas_carro", "vagas_moto",
        "vagas_carro_grande", "vagas_caminhonete",
    }
    campos_float = {"valor_primeira_hora", "valor_hora_adicional", "valor_mensal"}
    campos_bool = {"bloquear_sem_vaga", "exigir_observacao"}
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


@app.route("/api/configuracoes", methods=["POST"])
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
        "pix_tipo", "pix_chave",
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


# ---------------------- API: USUARIOS ----------------------

@app.route("/api/usuarios", methods=["GET"])
def api_listar_usuarios():
    """Retorna a lista de usuarios cadastrados."""
    ok, erro = verificar_permissao("usuarios", "ver")
    if not ok:
        return erro
    usuarios = servico_usuarios.listar()
    return jsonify({"usuarios": [usuario_para_dict(u) for u in usuarios]})


@app.route("/api/usuarios", methods=["POST"])
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


@app.route("/api/usuarios/<int:id_usuario>", methods=["DELETE"])
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

def apenas_master():
    """Bloqueia a acao para usuarios que nao sao master."""
    usuario = usuario_logado()
    if usuario is None:
        return False, (jsonify({"erro": "Nao autenticado."}), 401)
    eh_master = usuario.master or usuario.perfil == "admin"
    if not eh_master:
        return False, (jsonify({"erro": "Somente o usuario master pode realizar esta acao."}), 403)
    return True, None


@app.route("/api/empresas", methods=["GET"])
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


@app.route("/api/empresas", methods=["POST"])
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

    servico_auditoria.registrar("empresas", empresa.id, "criar", None, empresa.cnpj, usuario_logado().nome)
    return jsonify({"mensagem": "Empresa cadastrada com sucesso!", "empresa": empresa_para_dict(empresa)}), 201


@app.route("/api/empresas/<int:id_empresa>", methods=["GET"])
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


@app.route("/api/empresas/<int:id_empresa>", methods=["PUT"])
def api_atualizar_empresa(id_empresa: int):
    """Atualiza os dados de uma empresa (somente master)."""
    ok, erro = apenas_master()
    if not ok:
        return erro
    dados = request.get_json(silent=True) or {}

    campos = {
        "cnpj", "razao_social", "nome_fantasia", "telefone", "email",
        "endereco", "cidade", "estado", "cep", "ativo",
    }
    atualizacoes = {k: v for k, v in dados.items() if k in campos}

    try:
        empresa = servico_empresas.atualizar(id_empresa, **atualizacoes)
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400

    if empresa is None:
        return jsonify({"erro": "Empresa nao encontrada."}), 404

    servico_auditoria.registrar("empresas", empresa.id, "atualizar", None, empresa.cnpj, usuario_logado().nome)
    return jsonify({"mensagem": "Empresa atualizada com sucesso!", "empresa": empresa_para_dict(empresa)})


@app.route("/api/empresas/<int:id_empresa>/inativar", methods=["POST"])
def api_inativar_empresa(id_empresa: int):
    """Inativa uma empresa (somente master)."""
    ok, erro = apenas_master()
    if not ok:
        return erro
    if not servico_empresas.inativar(id_empresa):
        return jsonify({"erro": "Empresa nao encontrada."}), 404
    servico_auditoria.registrar("empresas", id_empresa, "inativar", None, None, usuario_logado().nome)
    return jsonify({"mensagem": "Empresa inativada com sucesso!"})


# ---------------------- API: PERMISSOES (FUNCOES E PERMISSOES) ----------------------

def verificar_permissao(modulo: str, acao: str = "ver"):
    """
    Verifica se o usuario logado possui a permissao no modulo.
    Retorna (ok, resposta_erro). Se nao ok, resposta_erro e um tuple (json, status).
    """
    usuario = usuario_logado()
    if usuario is None:
        return False, (jsonify({"erro": "Nao autenticado."}), 401)
    if not servico_permissao.pode(usuario.perfil, modulo, acao):
        return False, (jsonify({"erro": "Voce nao tem permissao para esta acao."}), 403)
    return True, None


@app.route("/api/permissoes", methods=["GET"])
def api_obter_permissoes():
    """Retorna a matriz de permissoes (modulo -> perfil -> acoes) e metadados.

    Acessivel a qualquer usuario autenticado: o frontend precisa desta matriz
    para montar o menu e ocultar telas/acoes sem permissao. As operacoes de
    edicao (PUT, perfis) continuam protegidas por 'usuarios/editar'.
    """
    if usuario_logado() is None:
        return jsonify({"erro": "Nao autenticado."}), 401
    return jsonify({
        "matriz": servico_permissao.matriz(),
        "perfis": list(servico_permissao.perfis_validos()),
        "modulos": list(servico_permissao.modulos()),
        "acoes": list(servico_permissao.acoes_validas()),
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


@app.route("/api/permissoes", methods=["PUT"])
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


@app.route("/api/permissoes/restaurar", methods=["POST"])
def api_restaurar_permissoes():
    """Restaura as permissoes padrao de todos os perfis."""
    ok, erro = verificar_permissao("usuarios", "editar")
    if not ok:
        return erro
    servico_permissao.restaurar_padrao()
    servico_auditoria.registrar("permissoes", None, "matriz", None, "restaurada_padrao", usuario_logado().nome)
    return jsonify({"mensagem": "Permissoes restauradas para o padrao!", "matriz": servico_permissao.matriz()})


# ---------------------- API: PERFIS ----------------------

def perfil_para_dict(perfil):
    """Converte um Perfil em dicionario para a API."""
    return {
        "id": perfil.id,
        "codigo": perfil.codigo,
        "nome": perfil.nome,
        "descricao": perfil.descricao,
        "ativo": perfil.ativo,
    }


@app.route("/api/perfis", methods=["GET"])
def api_listar_perfis():
    """Retorna todos os perfis cadastrados."""
    ok, erro = verificar_permissao("usuarios", "ver")
    if not ok:
        return erro
    return jsonify({
        "perfis": [perfil_para_dict(p) for p in servico_perfil.listar()],
        "ativos": [p.codigo for p in servico_perfil.listar_ativos()],
    })


@app.route("/api/perfis", methods=["POST"])
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


@app.route("/api/perfis/<int:id_perfil>", methods=["PUT"])
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


@app.route("/api/perfis/<int:id_perfil>/ativar", methods=["POST"])
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


@app.route("/api/perfis/<int:id_perfil>/inativar", methods=["POST"])
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


@app.route("/api/perfis/<int:id_perfil>/clonar", methods=["POST"])
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


# ---------------------- API: CLIENTES ----------------------

@app.route("/api/clientes", methods=["GET"])
def api_listar_clientes():
    """Retorna a lista de clientes (mensalistas) cadastrados."""
    ok, erro = verificar_permissao("clientes", "ver")
    if not ok:
        return erro
    clientes = servico_clientes.listar()
    return jsonify({"clientes": [cliente_para_dict(c) for c in clientes]})


@app.route("/api/clientes", methods=["POST"])
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

    return jsonify({"mensagem": "Cliente cadastrado com sucesso!", "cliente": cliente_para_dict(cliente)}), 201


@app.route("/api/clientes/<int:id_cliente>", methods=["GET"])
def api_obter_cliente(id_cliente: int):
    """Retorna um cliente especifico pelo id."""
    ok, erro = verificar_permissao("clientes", "ver")
    if not ok:
        return erro
    cliente = servico_clientes.buscar_por_id(id_cliente)
    if cliente is None:
        return jsonify({"erro": "Cliente nao encontrado."}), 404
    return jsonify({"cliente": cliente_para_dict(cliente)})


@app.route("/api/clientes/<int:id_cliente>", methods=["PUT"])
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

    return jsonify({"mensagem": "Cliente atualizado com sucesso!", "cliente": cliente_para_dict(cliente)})


@app.route("/api/clientes/<int:id_cliente>", methods=["DELETE"])
def api_excluir_cliente(id_cliente: int):
    """Desativa/exclui um cliente."""
    ok, erro = verificar_permissao("clientes", "excluir")
    if not ok:
        return erro
    if not servico_clientes.excluir(id_cliente):
        return jsonify({"erro": "Cliente nao encontrado."}), 404
    return jsonify({"mensagem": "Cliente desativado com sucesso!"})


# ---------------------- API: FINANCEIRO ----------------------

@app.route("/api/financeiro", methods=["GET"])
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
        "lancamentos": [lancamento_para_dict(l) for l in lancamentos],
        "formas_pagamento": FORMAS_PAGAMENTO_LABEL,
    })


@app.route("/api/financeiro", methods=["POST"])
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

    return jsonify({"mensagem": "Lancamento criado com sucesso!", "lancamento": lancamento_para_dict(lancamento)}), 201


@app.route("/api/financeiro/<int:id_lancamento>", methods=["GET"])
def api_obter_financeiro(id_lancamento: int):
    """Retorna um lancamento especifico pelo id."""
    ok, erro = verificar_permissao("financeiro", "ver")
    if not ok:
        return erro
    lancamento = servico_financeiro.buscar_por_id(id_lancamento)
    if lancamento is None:
        return jsonify({"erro": "Lancamento nao encontrado."}), 404
    return jsonify({"lancamento": lancamento_para_dict(lancamento)})


@app.route("/api/financeiro/<int:id_lancamento>", methods=["PUT"])
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

    return jsonify({"mensagem": "Lancamento atualizado com sucesso!", "lancamento": lancamento_para_dict(lancamento)})


@app.route("/api/financeiro/<int:id_lancamento>", methods=["DELETE"])
def api_excluir_financeiro(id_lancamento: int):
    """Exclui um lancamento financeiro."""
    ok, erro = verificar_permissao("financeiro", "excluir")
    if not ok:
        return erro
    if not servico_financeiro.excluir(id_lancamento):
        return jsonify({"erro": "Lancamento nao encontrado."}), 404
    return jsonify({"mensagem": "Lancamento excluido com sucesso!"})


@app.route("/api/financeiro/resumo", methods=["GET"])
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


# ---------------------- API: CAIXA ----------------------

@app.route("/api/caixa", methods=["GET"])
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


@app.route("/api/caixa", methods=["POST"])
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

    servico_auditoria.registrar("caixas", caixa.id, "status", None, "aberto", operador)
    return jsonify({"mensagem": "Caixa aberto com sucesso!", "caixa": caixa.to_dict()}), 201


@app.route("/api/caixa/<int:id_caixa>/fechar", methods=["POST"])
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
    servico_auditoria.registrar("caixas", caixa.id, "status", "aberto", "fechado", caixa.operador)
    return jsonify({
        "mensagem": "Caixa fechado com sucesso!",
        "caixa": caixa.to_dict(),
        "totais_por_forma": totais,
    })


@app.route("/api/caixa/<int:id_caixa>/sangria", methods=["POST"])
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


@app.route("/api/caixa/<int:id_caixa>/suprimento", methods=["POST"])
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


@app.route("/api/caixa/<int:id_caixa>/movimentacoes", methods=["GET"])
def api_movimentacoes_caixa(id_caixa: int):
    """Retorna as movimentacoes de um caixa."""
    movs = servico_caixa.movimentacoes_do_caixa(id_caixa)
    return jsonify({"movimentacoes": [m.to_dict() for m in movs]})


# ---------------------- API: PAGAMENTOS ----------------------

@app.route("/api/pagamentos", methods=["GET"])
def api_listar_pagamentos():
    """Retorna a lista de pagamentos."""
    ok, erro = verificar_permissao("pagamentos", "ver")
    if not ok:
        return erro
    pagamentos = servico_pagamentos.listar()
    return jsonify({"pagamentos": [p.to_dict() for p in pagamentos]})


@app.route("/api/pagamentos/<int:id_pagamento>/cancelar", methods=["POST"])
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
    servico_auditoria.registrar("pagamentos", pagamento.id, "status", "ativo", "cancelado", autorizador)
    return jsonify({"mensagem": "Pagamento cancelado!", "pagamento": pagamento.to_dict()})


@app.route("/api/pagamentos/<int:id_pagamento>/estornar", methods=["POST"])
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
    servico_auditoria.registrar("pagamentos", pagamento.id, "status", "ativo", "estornado", autorizador)
    return jsonify({"mensagem": "Pagamento estornado!", "pagamento": pagamento.to_dict()})


# ---------------------- API: FORMAS DE PAGAMENTO ----------------------

@app.route("/api/formas-pagamento", methods=["GET"])
def api_listar_formas_pagamento():
    """Retorna a lista de formas de pagamento."""
    formas = servico_formas_pagamento.listar()
    return jsonify({"formas_pagamento": [f.to_dict() for f in formas]})


@app.route("/api/formas-pagamento", methods=["POST"])
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


@app.route("/api/formas-pagamento/<int:id_forma>", methods=["PUT"])
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


# ---------------------- API: TABELA DE PRECOS ----------------------

@app.route("/api/tabela-precos", methods=["GET"])
def api_obter_tabela_precos():
    """Retorna a tabela de precos vigente."""
    tabela = servico_tabela_precos.obter_vigente()
    return jsonify({"tabela_precos": tabela.to_dict()})


@app.route("/api/tabela-precos/<int:id_tabela>", methods=["PUT"])
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


@app.route("/api/tabela-precos/calcular", methods=["POST"])
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


# ---------------------- API: TIPOS DE VEICULO ----------------------

@app.route("/api/tipos-veiculo", methods=["GET"])
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
            from services.tabela_preco_service import TIPO_VEICULO_CHAVE
            chave = TIPO_VEICULO_CHAVE.get(t.nome, "carro")
            for campo in ("primeira_hora", "hora_adicional", "diaria", "valor_minuto", "valor_maximo_diario", "mensal"):
                dados[campo] = (
                    getattr(tabela, campo) if chave == "carro"
                    else getattr(tabela, f"{chave}_{campo}")
                )
        resultado.append(dados)
    return jsonify({"tipos_veiculo": resultado})


@app.route("/api/tipos-veiculo", methods=["POST"])
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


@app.route("/api/tipos-veiculo/<int:id_tipo>", methods=["PUT"])
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


@app.route("/api/tipos-veiculo/<int:id_tipo>/alternar-ativo", methods=["POST"])
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


@app.route("/api/tipos-veiculo/<int:id_tipo>", methods=["DELETE"])
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


# ---------------------- API: DESCONTOS ----------------------

@app.route("/api/descontos", methods=["GET"])
def api_listar_descontos():
    """Retorna a lista de descontos."""
    ok, erro = verificar_permissao("descontos", "ver")
    if not ok:
        return erro
    descontos = servico_descontos.listar()
    return jsonify({"descontos": [d.to_dict() for d in descontos]})


@app.route("/api/descontos", methods=["POST"])
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


@app.route("/api/descontos/<int:id_desconto>", methods=["PUT"])
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


# ---------------------- API: CORTESIAS ----------------------

@app.route("/api/cortesias", methods=["GET"])
def api_listar_cortesias():
    """Retorna a lista de cortesias."""
    ok, erro = verificar_permissao("cortesias", "ver")
    if not ok:
        return erro
    cortesias = servico_cortesias.listar()
    return jsonify({"cortesias": [c.to_dict() for c in cortesias]})


@app.route("/api/cortesias", methods=["POST"])
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


@app.route("/api/cortesias/<int:id_cortesia>/cancelar", methods=["POST"])
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


# ---------------------- API: MENSALISTAS ----------------------

@app.route("/api/mensalistas", methods=["GET"])
def api_listar_mensalistas():
    """Retorna a lista de mensalistas."""
    ok, erro = verificar_permissao("mensalistas", "ver")
    if not ok:
        return erro
    servico_mensalistas.verificar_inadimplencia()
    mensalistas = servico_mensalistas.listar()
    return jsonify({"mensalistas": [m.to_dict() for m in mensalistas]})


@app.route("/api/mensalistas", methods=["POST"])
def api_criar_mensalista():
    """Cria um novo mensalista."""
    ok, erro = verificar_permissao("mensalistas", "criar")
    if not ok:
        return erro
    dados = request.get_json(silent=True) or {}
    try:
        mensalista = servico_mensalistas.criar(
            nome=dados.get("nome", ""),
            cpf_cnpj=dados.get("cpf_cnpj", ""),
            telefone=dados.get("telefone", ""),
            email=dados.get("email", ""),
            valor_mensal=dados.get("valor_mensal", 0),
            dia_vencimento=dados.get("dia_vencimento", 5),
            cliente_id=dados.get("cliente_id"),
        )
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    return jsonify({"mensagem": "Mensalista cadastrado!", "mensalista": mensalista.to_dict()}), 201


@app.route("/api/mensalistas/<int:id_mensalista>", methods=["PUT"])
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
        )
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    if mensalista is None:
        return jsonify({"erro": "Mensalista nao encontrado."}), 404
    return jsonify({"mensagem": "Mensalista atualizado!", "mensalista": mensalista.to_dict()})


@app.route("/api/mensalistas/<int:id_mensalista>/bloquear", methods=["POST"])
def api_bloquear_mensalista(id_mensalista: int):
    """Bloqueia um mensalista."""
    ok, erro = verificar_permissao("mensalistas", "editar")
    if not ok:
        return erro
    mensalista = servico_mensalistas.bloquear(id_mensalista)
    if mensalista is None:
        return jsonify({"erro": "Mensalista nao encontrado."}), 404
    return jsonify({"mensagem": "Mensalista bloqueado!", "mensalista": mensalista.to_dict()})


@app.route("/api/mensalistas/<int:id_mensalista>/desbloquear", methods=["POST"])
def api_desbloquear_mensalista(id_mensalista: int):
    """Desbloqueia um mensalista."""
    ok, erro = verificar_permissao("mensalistas", "editar")
    if not ok:
        return erro
    mensalista = servico_mensalistas.desbloquear(id_mensalista)
    if mensalista is None:
        return jsonify({"erro": "Mensalista nao encontrado."}), 404
    return jsonify({"mensagem": "Mensalista desbloqueado!", "mensalista": mensalista.to_dict()})


@app.route("/api/mensalistas/<int:id_mensalista>/mensalidades", methods=["GET"])
def api_mensalidades_mensalista(id_mensalista: int):
    """Retorna as mensalidades de um mensalista."""
    mensalidades = servico_mensalistas.mensalidades_do_mensalista(id_mensalista)
    return jsonify({"mensalidades": [m.to_dict() for m in mensalidades]})


@app.route("/api/mensalistas/<int:id_mensalista>/mensalidades", methods=["POST"])
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


@app.route("/api/mensalidades/<int:id_mensalidade>/pagar", methods=["POST"])
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


# ---------------------- API: CONVENIOS ----------------------

@app.route("/api/convenios", methods=["GET"])
def api_listar_convenios():
    """Retorna a lista de convenios."""
    ok, erro = verificar_permissao("convenios", "ver")
    if not ok:
        return erro
    convenios = servico_convenios.listar()
    return jsonify({"convenios": [c.to_dict() for c in convenios]})


@app.route("/api/convenios", methods=["POST"])
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


@app.route("/api/convenios/<int:id_convenio>", methods=["PUT"])
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


# ---------------------- API: CONTAS A RECEBER ----------------------

@app.route("/api/contas-receber", methods=["GET"])
def api_listar_contas_receber():
    """Retorna a lista de contas a receber."""
    ok, erro = verificar_permissao("contas_receber", "ver")
    if not ok:
        return erro
    contas = servico_contas_receber.listar()
    return jsonify({"contas_receber": [c.to_dict() for c in contas]})


@app.route("/api/contas-receber", methods=["POST"])
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


@app.route("/api/contas-receber/<int:id_conta>/baixar", methods=["POST"])
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


# ---------------------- API: ESTORNOS ----------------------

@app.route("/api/estornos", methods=["GET"])
def api_listar_estornos():
    """Retorna a lista de estornos."""
    estornos = servico_estornos.listar()
    return jsonify({"estornos": [e.to_dict() for e in estornos]})


# ---------------------- API: AUDITORIA ----------------------

@app.route("/api/auditoria", methods=["GET"])
def api_listar_auditoria():
    """Retorna os registros de auditoria."""
    ok, erro = verificar_permissao("auditoria", "ver")
    if not ok:
        return erro
    registros = servico_auditoria.listar()
    return jsonify({"auditoria": [a.to_dict() for a in registros]})


@app.route("/api/logs-acesso", methods=["GET"])
def api_listar_logs_acesso():
    """Retorna os logs de acesso."""
    ok, erro = verificar_permissao("auditoria", "ver")
    if not ok:
        return erro
    logs = servico_auditoria.listar_logs()
    return jsonify({"logs_acesso": [l.to_dict() for l in logs]})


# ---------------------- API: DASHBOARD FINANCEIRO ----------------------

@app.route("/api/dashboard-financeiro", methods=["GET"])
def api_dashboard_financeiro():
    """Retorna os indicadores do dashboard financeiro."""
    ok, erro = verificar_permissao("dashboard_financeiro", "ver")
    if not ok:
        return erro
    return jsonify(servico_dashboard_financeiro.gerar())


# ---------------------- API: RELATORIO FINANCEIRO ----------------------

@app.route("/api/relatorio-financeiro", methods=["GET"])
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


@app.route("/api/relatorio-financeiro/exportar", methods=["GET"])
def api_relatorio_financeiro_exportar():
    """Exporta o relatorio financeiro em CSV ou PDF."""
    ok, erro = verificar_permissao("relatorios", "ver")
    if not ok:
        return erro
    from flask import Response
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


# ---------------------- API: NFSE ----------------------

@app.route("/api/nfse", methods=["GET"])
def api_listar_nfse():
    """Retorna as notas fiscais emitidas."""
    ok, erro = verificar_permissao("nfse", "ver")
    if not ok:
        return erro
    notas = servico_nfse.listar()
    notas = sorted(notas, key=lambda n: n.numero, reverse=True)
    return jsonify({"notas": [n.to_dict() for n in notas]})


@app.route("/api/nfse", methods=["POST"])
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


@app.route("/api/nfse/<int:id_nota>/cancelar", methods=["POST"])
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

@app.route("/api/lista-negra", methods=["GET"])
def api_listar_lista_negra():
    """Retorna os veiculos bloqueados."""
    ok, erro = verificar_permissao("lista_negra", "ver")
    if not ok:
        return erro
    registros = servico_lista_negra.listar()
    registros = sorted(registros, key=lambda r: r.data, reverse=True)
    return jsonify({"registros": [r.to_dict() for r in registros]})


@app.route("/api/lista-negra", methods=["POST"])
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


@app.route("/api/lista-negra/<int:id_registro>", methods=["PUT"])
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


@app.route("/api/lista-negra/<int:id_registro>/alternar-ativo", methods=["POST"])
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


@app.route("/api/lista-negra/<int:id_registro>", methods=["DELETE"])
def api_excluir_lista_negra(id_registro: int):
    """Remove o bloqueio (exclusao logica)."""
    ok, erro = verificar_permissao("lista_negra", "excluir")
    if not ok:
        return erro
    if not servico_lista_negra.excluir(id_registro):
        return jsonify({"erro": "Registro nao encontrado."}), 404
    return jsonify({"mensagem": "Bloqueio removido!"})


# ---------------------- API: RESERVAS ----------------------

@app.route("/api/reservas", methods=["GET"])
def api_listar_reservas():
    """Retorna as reservas de vaga."""
    ok, erro = verificar_permissao("reservas", "ver")
    if not ok:
        return erro
    reservas = servico_reservas.listar()
    reservas = sorted(reservas, key=lambda r: r.data_inicio, reverse=True)
    return jsonify({"reservas": [r.to_dict() for r in reservas]})


@app.route("/api/reservas", methods=["POST"])
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


@app.route("/api/reservas/<int:id_reserva>", methods=["PUT"])
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


@app.route("/api/reservas/<int:id_reserva>/cancelar", methods=["POST"])
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

@app.route("/api/ocorrencias", methods=["GET"])
def api_listar_ocorrencias():
    """Retorna as ocorrencias registradas."""
    ok, erro = verificar_permissao("ocorrencias", "ver")
    if not ok:
        return erro
    ocorrencias = servico_ocorrencias.listar()
    ocorrencias = sorted(ocorrencias, key=lambda o: o.data, reverse=True)
    return jsonify({"ocorrencias": [o.to_dict() for o in ocorrencias]})


@app.route("/api/ocorrencias", methods=["POST"])
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


@app.route("/api/ocorrencias/<int:id_ocorrencia>", methods=["PUT"])
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

@app.route("/api/notificacoes-vencimento", methods=["GET"])
def api_notificacoes_vencimento():
    """Retorna a central de avisos de vencimento de mensalistas."""
    ok, erro = verificar_permissao("notificacoes", "ver")
    if not ok:
        return erro
    return jsonify(servico_notificacao.gerar_avisos())


# ---------------------- API: BACKUP / EXPORTACAO ----------------------

@app.route("/api/backup", methods=["GET"])
def api_backup():
    """Exporta o backup completo (JSON) da empresa ativa.
    Restrito a quem pode editar usuarios (na pratica, admin)."""
    ok, erro = verificar_permissao("usuarios", "editar")
    if not ok:
        return erro
    from flask import Response
    backup = servico_backup.gerar(nome_estacionamento=servico.config.nome_estacionamento)
    import json
    return Response(
        json.dumps(backup, ensure_ascii=False, indent=2, default=str),
        mimetype="application/json",
        headers={
            "Content-Disposition": (
                f"attachment; filename=backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
        },
    )


# ---------------------- API: RELATORIO DE OCUPACAO E DRE ----------------------

@app.route("/api/relatorio-ocupacao", methods=["GET"])
def api_relatorio_ocupacao():
    """Retorna a ocupacao atual e por tipo de veiculo."""
    ok, erro = verificar_permissao("relatorios", "ver")
    if not ok:
        return erro
    return jsonify(servico_relatorio.relatorio_ocupacao())


@app.route("/api/relatorio-dre", methods=["GET"])
def api_relatorio_dre():
    """Retorna o DRE simples (receita, descontos, cortesias, estornos)."""
    ok, erro = verificar_permissao("relatorios", "ver")
    if not ok:
        return erro
    return jsonify(servico_relatorio.relatorio_dre())


# ---------------------- API: TICKET PERDIDO ----------------------

@app.route("/api/ticket-perdido", methods=["POST"])
def api_ticket_perdido():
    """Registra um ticket perdido: cobra a tarifa de ticket perdido e
    gera pagamento + movimentacao + lancamento financeiro.
    Requer autorizacao (admin/supervisor) ou parametro 'autorizado'.
    """
    ok, erro = verificar_permissao("operacao", "criar")
    if not ok:
        return erro

    dados = request.get_json(silent=True) or {}
    placa = (dados.get("placa") or "").strip()
    observacoes = (dados.get("observacoes") or "").strip()
    forma_pagamento = (dados.get("forma_pagamento") or "dinheiro").strip() or "dinheiro"
    autorizador = (dados.get("autorizador") or "").strip()

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

    # Gera um ticket fechado (perdido) com o valor da tarifa
    import random
    numero = max(servico.config.proximo_numero_ticket, servico.persistencia.proximo_numero_global())
    from models.ticket import Ticket
    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    ticket = Ticket(
        numero=numero,
        placa=placa.upper() or f"PERDIDO-{numero}",
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


if __name__ == "__main__":
    app.run(debug=True)
