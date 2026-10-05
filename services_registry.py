"""
Registro central dos servicos e helpers compartilhados entre as rotas.

Evita importacao circular entre o app e os blueprints (routes/): as
instancias dos servicos, serializadores e verificacoes de permissao
vivem aqui e sao importados pelos modulos de rota.
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from flask import jsonify, session

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

# ------------------------------------------------------------------
# INSTANCIAS DOS SERVICOS
# ------------------------------------------------------------------

servico_tabela_precos = TabelaPrecoService()
servico = EstacionamentoService(tabela_preco_service=servico_tabela_precos)
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
    pagamento_service=servico_pagamentos,
    forma_pagamento_service=servico_formas_pagamento,
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
    services_empresa = (
        servico,
        servico_financeiro,
        servico_caixa,
        servico_pagamentos,
        servico_formas_pagamento,
        servico_tabela_precos,
        servico_tipos_veiculo,
        servico_descontos,
        servico_cortesias,
        servico_mensalistas,
        servico_convenios,
        servico_contas_receber,
        servico_estornos,
        servico_clientes,
        servico_nfse,
        servico_lista_negra,
        servico_reservas,
        servico_ocorrencias,
    )
    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(lambda service: service.recarregar(eid), services_empresa))

    servico_tabela_precos.definir_tipos_personalizados(
        servico_tipos_veiculo.listar(somente_ativos=True)
    )
    servico.tabela_preco_service = servico_tabela_precos
    servico_notificacao._mensalistas = servico_mensalistas
    servico_notificacao._nome_estacionamento = servico.config.nome_estacionamento
    servico_relatorio._pagamentos = servico_pagamentos
    servico_relatorio._formas_pagamento = servico_formas_pagamento
    servico_relatorio._nome_estacionamento = servico.config.nome_estacionamento


# ------------------------------------------------------------------
# AUTENTICACAO
# ------------------------------------------------------------------

def usuario_logado():
    """Retorna o usuario autenticado na sessao, ou None."""
    id_usuario = session.get("usuario_id")
    if id_usuario is None:
        return None
    return servico_usuarios.buscar_por_id(id_usuario)


# ------------------------------------------------------------------
# PERMISSOES
# ------------------------------------------------------------------

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


def apenas_master():
    """Bloqueia a acao para usuarios que nao sao master."""
    usuario = usuario_logado()
    if usuario is None:
        return False, (jsonify({"erro": "Nao autenticado."}), 401)
    eh_master = bool(usuario.master or (usuario.perfil == "admin" and not usuario.empresa_id))
    if not eh_master:
        return False, (jsonify({"erro": "Somente o usuario master pode realizar esta acao."}), 403)
    return True, None


# ------------------------------------------------------------------
# SERIALIZADORES
# ------------------------------------------------------------------

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

    # Se o ticket estiver aberto, calcula o valor acumulado em tempo real
    valor_estimado = ticket.valor
    if valor_estimado is None and ticket.status == "ABERTO" and entrada:
        try:
            agora_str = datetime.now().strftime(FORMATO_DATA)
            valor_estimado = servico.calcular_valor(entrada, agora_str, ticket.tipo_veiculo)
        except Exception:
            valor_estimado = 0.0

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
        "valor_estimado": valor_estimado,
        "status": ticket.status,
        "tipo_veiculo": ticket.tipo_veiculo,
        "observacoes": ticket.observacoes,
        "forma_pagamento": ticket.forma_pagamento,
        "tempo_estacionado": tempo_estacionado(ticket),
    }


def config_para_dict() -> dict:
    """Serializa a configuracao atual (mais os contadores de vagas) em dict."""
    cfg = servico.config
    nome = cfg.nome_estacionamento
    cnpj = cfg.cnpj
    if servico.empresa_id:
        try:
            emp = servico_empresas.buscar_por_id(servico.empresa_id)
            if emp:
                if not nome or nome == "Estaciona Parking":
                    nome = emp.nome_fantasia or emp.razao_social or nome
                if not cnpj:
                    cnpj = emp.cnpj or cnpj
        except Exception:
            pass
    return {
        # Identificacao
        "nome_estacionamento": nome,
        "cnpj": cnpj,
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
        "ticket_formato_papel": getattr(cfg, "ticket_formato_papel", "80mm"),
        "ticket_exibir_cnpj": getattr(cfg, "ticket_exibir_cnpj", True),
        "ticket_exibir_contato": getattr(cfg, "ticket_exibir_contato", True),
        "ticket_exibir_codigo_barras": getattr(cfg, "ticket_exibir_codigo_barras", True),
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
