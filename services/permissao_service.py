"""
Servico de Permissoes.

Define as permissoes por modulo para cada perfil de acesso do sistema.
Cada modulo possui acoes (ver, criar, editar, excluir, autorizar,
fechar_caixa, estornar, cancelar). O perfil 'admin' sempre tem acesso total.

As permissoes podem ser personalizadas dinamicamente pela interface
"Funcoes e permissoes" (menu Configuracoes). Elas sao persistidas na
tabela 'permissoes' do Supabase. Se a tabela ainda nao existir, usa-se
a matriz padrao (fallback) definida em PERMISSOES_PADRAO.

Perfis personalizados (gerencia, supervisao, manobrista etc.) sao
obtidos do PerfilService e tambem participam da matriz de permissoes.
"""

from typing import List, Optional

from models.permissao import Permissao
from services.perfil_service import PerfilService
from supabase_client import supabase

# Acoes possiveis
ACAO_VER = "ver"
ACAO_CRIAR = "criar"
ACAO_EDITAR = "editar"
ACAO_EXCLUIR = "excluir"
ACAO_AUTORIZAR = "autorizar"
ACAO_FECHAR_CAIXA = "fechar_caixa"
ACAO_ESTORNAR = "estornar"
ACAO_CANCELAR = "cancelar"

ACOES_VALIDAS = (
    ACAO_VER, ACAO_CRIAR, ACAO_EDITAR, ACAO_EXCLUIR,
    ACAO_AUTORIZAR, ACAO_FECHAR_CAIXA, ACAO_ESTORNAR, ACAO_CANCELAR,
)

# Modulos do sistema (para a interface de permissoes)
MODULOS = (
    "operacao",
    "caixa",
    "pagamentos",
    "formas_pagamento",
    "tabela_precos",
    "descontos",
    "cortesias",
    "mensalistas",
    "convenios",
    "contas_receber",
    "estornos",
    "auditoria",
    "dashboard_financeiro",
    "relatorios",
    "usuarios",
    "clientes",
    "financeiro",
    "configuracoes",
    "nfse",
    "lista_negra",
    "reservas",
    "ocorrencias",
    "notificacoes",
)

CATEGORIAS_MODULOS = [
    {
        "id": "operacao",
        "nome": "Operação de Pátio & Caixa",
        "descricao": "Controle de pátio, emissão de tickets, cobrança, frente de caixa e movimentações",
        "modulos": ["operacao", "caixa", "pagamentos", "reservas", "lista_negra", "ocorrencias"],
    },
    {
        "id": "comercial",
        "nome": "Comercial & Clientes",
        "descricao": "Gestão de contratos mensalistas, convênios corporativos e avisos de vencimento",
        "modulos": ["mensalistas", "convenios", "contas_receber", "clientes", "notificacoes"],
    },
    {
        "id": "tarifas",
        "nome": "Tarifas & Benefícios",
        "descricao": "Tabelas de cobrança por tipo de veículo, regras de desconto e cortesias",
        "modulos": ["tabela_precos", "descontos", "cortesias", "formas_pagamento"],
    },
    {
        "id": "financeiro",
        "nome": "Financeiro & Fiscal",
        "descricao": "Livro financeiro, indicadores de faturamento, relatórios e emissão de NFSe",
        "modulos": ["financeiro", "dashboard_financeiro", "relatorios", "nfse"],
    },
    {
        "id": "admin",
        "nome": "Administração & Segurança",
        "descricao": "Controle de usuários, trilha de auditoria e configurações gerais do sistema",
        "modulos": ["usuarios", "auditoria", "configuracoes"],
    },
]

ACOES_POR_MODULO = {
    "operacao": {
        "nome": "Pátio & Operação",
        "descricao": "Visualização do pátio, mapa de vagas e registro de fluxo de veículos",
        "acoes": [
            {"acao": "ver", "nome": "Visualizar Pátio", "desc": "Consultar veículos no pátio e mapa de vagas"},
            {"acao": "criar", "nome": "Registrar Entrada", "desc": "Emitir ticket e dar entrada de veículo"},
            {"acao": "editar", "nome": "Registrar Saída", "desc": "Efetuar saída de veículo e cálculo de estadia"},
            {"acao": "autorizar", "nome": "Cobrar Ticket Perdido", "desc": "Aplicar tarifa especial de perda de ticket"},
        ],
    },
    "caixa": {
        "nome": "Caixa & Movimentações",
        "descricao": "Abertura, fechamento, conferência e controle físico de valores",
        "acoes": [
            {"acao": "ver", "nome": "Visualizar Caixa", "desc": "Consultar resumo financeiro e extrato do turno"},
            {"acao": "criar", "nome": "Abrir Caixa", "desc": "Iniciar expediente com valor inicial de abertura"},
            {"acao": "editar", "nome": "Sangria e Suprimento", "desc": "Lançar retiradas ou reforços de troco"},
            {"acao": "fechar_caixa", "nome": "Fechar Caixa", "desc": "Encerrar expediente com conferência cega"},
        ],
    },
    "pagamentos": {
        "nome": "Pagamentos & Devoluções",
        "descricao": "Processamento de pagamentos de tickets, cancelamentos e estornos",
        "acoes": [
            {"acao": "ver", "nome": "Visualizar Pagamentos", "desc": "Consultar lista de pagamentos do turno"},
            {"acao": "criar", "nome": "Receber Pagamentos", "desc": "Processar recebimento nas diversas formas"},
            {"acao": "cancelar", "nome": "Cancelar Pagamento", "desc": "Cancelar recebimento registrado por engano"},
            {"acao": "estornar", "nome": "Estornar Pagamento", "desc": "Devolver valor ao cliente e debitar do caixa"},
        ],
    },
    "reservas": {
        "nome": "Reservas de Vagas",
        "descricao": "Agendamento antecipado de vagas para clientes",
        "acoes": [
            {"acao": "ver", "nome": "Visualizar Reservas", "desc": "Consultar agenda e status das reservas"},
            {"acao": "criar", "nome": "Cadastrar Reserva", "desc": "Agendar vaga para cliente e período específico"},
            {"acao": "editar", "nome": "Editar / Concluir Reserva", "desc": "Alterar dados ou finalizar reserva"},
            {"acao": "excluir", "nome": "Cancelar Reserva", "desc": "Remover ou cancelar reserva agendada"},
        ],
    },
    "lista_negra": {
        "nome": "Lista Negra / Bloqueios",
        "descricao": "Bloqueio de veículos por sinistro, furto ou inadimplência",
        "acoes": [
            {"acao": "ver", "nome": "Visualizar Bloqueios", "desc": "Consultar placas impedidas de acessar o pátio"},
            {"acao": "criar", "nome": "Bloquear Veículo", "desc": "Inserir placa com motivo do impedimento"},
            {"acao": "excluir", "nome": "Desbloquear Veículo", "desc": "Liberar acesso de veículo anteriormente bloqueado"},
        ],
    },
    "ocorrencias": {
        "nome": "Ocorrências & Avarias",
        "descricao": "Termos de avaria de entrada, batidas, perdas e sinistros",
        "acoes": [
            {"acao": "ver", "nome": "Visualizar Ocorrências", "desc": "Consultar avarias e incidentes registrados"},
            {"acao": "criar", "nome": "Registrar Ocorrência", "desc": "Abrir novo termo de avaria ou sinistro"},
            {"acao": "editar", "nome": "Atualizar Ocorrência", "desc": "Alterar descrição, autorizador ou desfecho"},
        ],
    },
    "mensalistas": {
        "nome": "Mensalistas",
        "descricao": "Contratos de mensalistas, controle de vagas fixas e cobrança",
        "acoes": [
            {"acao": "ver", "nome": "Visualizar Mensalistas", "desc": "Consultar contratos e mensalidades ativas"},
            {"acao": "criar", "nome": "Cadastrar Mensalista", "desc": "Criar novo mensalista e dados do veículo"},
            {"acao": "editar", "nome": "Editar Mensalista", "desc": "Atualizar dados de contato, plano e placa"},
            {"acao": "autorizar", "nome": "Baixar Pagamento", "desc": "Registrar o pagamento da mensalidade"},
            {"acao": "excluir", "nome": "Bloquear / Inativar", "desc": "Suspender acesso de mensalista inadimplente"},
        ],
    },
    "convenios": {
        "nome": "Convênios",
        "descricao": "Parcerias com empresas e faturamento periódico agrupado",
        "acoes": [
            {"acao": "ver", "nome": "Visualizar Convênios", "desc": "Consultar empresas parceiras cadastradas"},
            {"acao": "criar", "nome": "Cadastrar Convênio", "desc": "Adicionar nova empresa conveniada"},
            {"acao": "editar", "nome": "Editar Convênio", "desc": "Atualizar dados ou regras do convênio"},
            {"acao": "excluir", "nome": "Inativar Convênio", "desc": "Suspender faturamento de empresa conveniada"},
        ],
    },
    "contas_receber": {
        "nome": "Contas a Receber",
        "descricao": "Faturas emitidas para empresas e controle de recebíveis",
        "acoes": [
            {"acao": "ver", "nome": "Visualizar Faturas", "desc": "Consultar títulos e datas de vencimento"},
            {"acao": "criar", "nome": "Lançar Cobrança", "desc": "Gerar fatura a receber para empresa conveniada"},
            {"acao": "editar", "nome": "Liquidar / Baixar", "desc": "Registrar recebimento de fatura faturada"},
            {"acao": "excluir", "nome": "Cancelar Fatura", "desc": "Cancelar título indevido ou estornado"},
        ],
    },
    "clientes": {
        "nome": "Base de Clientes",
        "descricao": "Cadastro central de clientes e histórico de contatos",
        "acoes": [
            {"acao": "ver", "nome": "Visualizar Clientes", "desc": "Consultar clientes cadastrados no sistema"},
            {"acao": "criar", "nome": "Cadastrar Cliente", "desc": "Cadastrar novos clientes avulsos ou mensalistas"},
            {"acao": "editar", "nome": "Editar Cliente", "desc": "Alterar dados de cadastro e telefone"},
            {"acao": "excluir", "nome": "Inativar Cliente", "desc": "Inativar registro de cliente da base"},
        ],
    },
    "notificacoes": {
        "nome": "Avisos de Vencimento",
        "descricao": "Central de alertas sobre cobranças a vencer e inadimplências",
        "acoes": [
            {"acao": "ver", "nome": "Visualizar Avisos", "desc": "Consultar mensalistas em atraso ou a vencer"},
        ],
    },
    "tabela_precos": {
        "nome": "Tabela de Preços",
        "descricao": "Tarifas por hora, períodos especiais, pernoite e tolerância",
        "acoes": [
            {"acao": "ver", "nome": "Visualizar Preços", "desc": "Consultar valores cobrados por tipo de veículo"},
            {"acao": "editar", "nome": "Alterar Tarifas", "desc": "Modificar preços, frações e minutos de tolerância"},
        ],
    },
    "descontos": {
        "nome": "Descontos Comerciais",
        "descricao": "Percentuais e valores fixos de desconto aplicáveis aos tickets",
        "acoes": [
            {"acao": "ver", "nome": "Visualizar Descontos", "desc": "Consultar regras de descontos disponíveis"},
            {"acao": "criar", "nome": "Criar Regra de Desconto", "desc": "Cadastrar nova modalidade de desconto"},
            {"acao": "editar", "nome": "Editar Regra", "desc": "Alterar valores ou condições de desconto"},
            {"acao": "autorizar", "nome": "Aplicar no Checkout", "desc": "Conceder abatimento no encerramento do ticket"},
        ],
    },
    "cortesias": {
        "nome": "Cortesias (Tarifa Zero)",
        "descricao": "Liberação sem cobrança para prestadores de serviço ou parceiros",
        "acoes": [
            {"acao": "ver", "nome": "Visualizar Cortesias", "desc": "Consultar histórico de veículos liberados sem custo"},
            {"acao": "criar", "nome": "Emitir Cortesia", "desc": "Liberar saída de veículo com tarifa zero"},
            {"acao": "autorizar", "nome": "Autorizar Cortesia", "desc": "Aprovar liberação extraordinária de veículo"},
        ],
    },
    "formas_pagamento": {
        "nome": "Formas de Pagamento",
        "descricao": "Gestão das modalidades aceitas no PDV (Dinheiro, PIX, Cartão)",
        "acoes": [
            {"acao": "ver", "nome": "Visualizar Formas", "desc": "Consultar formas de pagamento habilitadas"},
            {"acao": "criar", "nome": "Criar Nova Forma", "desc": "Cadastrar nova forma de recebimento no PDV"},
            {"acao": "editar", "nome": "Ativar / Inativar", "desc": "Modificar ou desativar forma de pagamento"},
        ],
    },
    "financeiro": {
        "nome": "Livro Financeiro",
        "descricao": "Lançamentos contábeis de receitas e despesas operacionais",
        "acoes": [
            {"acao": "ver", "nome": "Visualizar Lançamentos", "desc": "Consultar extrato de entradas e saídas gerais"},
            {"acao": "criar", "nome": "Lançar Despesa / Receita", "desc": "Registrar gastos avulsos (manutenção, energia, insumos)"},
            {"acao": "editar", "nome": "Editar Lançamento", "desc": "Corrigir valores ou descrições de despesas"},
            {"acao": "excluir", "nome": "Excluir Lançamento", "desc": "Remover lançamento financeiro incorreto"},
        ],
    },
    "dashboard_financeiro": {
        "nome": "Dashboard Financeiro",
        "descricao": "Gráficos de faturamento, ticket médio e curvas de horário",
        "acoes": [
            {"acao": "ver", "nome": "Visualizar Dashboard", "desc": "Acessar gráficos gerenciais e comparativos"},
        ],
    },
    "relatorios": {
        "nome": "Relatórios & DRE",
        "descricao": "Demonstrativo de Resultado do Exercício e exportações",
        "acoes": [
            {"acao": "ver", "nome": "Consultar Relatórios", "desc": "Acessar fechamento contábil e apuração de lucro"},
            {"acao": "criar", "nome": "Exportar Relatórios", "desc": "Baixar relatórios em formato CSV ou para impressão"},
        ],
    },
    "nfse": {
        "nome": "Notas Fiscais (NFSe)",
        "descricao": "Emissão e cancelamento de notas fiscais eletrônicas de serviço",
        "acoes": [
            {"acao": "ver", "nome": "Visualizar NFSe", "desc": "Consultar notas fiscais emitidas e canceladas"},
            {"acao": "criar", "nome": "Emitir NFSe", "desc": "Transmitir e emitir nota fiscal para cliente"},
            {"acao": "cancelar", "nome": "Cancelar NFSe", "desc": "Solicitar cancelamento de nota fiscal emitida"},
        ],
    },
    "usuarios": {
        "nome": "Usuários & Equipe",
        "descricao": "Cadastro de funcionários, operadores e redefinição de senhas",
        "acoes": [
            {"acao": "ver", "nome": "Visualizar Usuários", "desc": "Consultar lista de colaboradores cadastrados"},
            {"acao": "criar", "nome": "Cadastrar Usuário", "desc": "Criar login de acesso para funcionário"},
            {"acao": "editar", "nome": "Editar e Redefinir Senha", "desc": "Alterar perfil ou resetar senha de usuário"},
            {"acao": "excluir", "nome": "Inativar Usuário", "desc": "Revogar acesso de colaborador"},
        ],
    },
    "auditoria": {
        "nome": "Trilha de Auditoria",
        "descricao": "Rastreamento completo de acessos, logins e alterações de dados",
        "acoes": [
            {"acao": "ver", "nome": "Consultar Auditoria", "desc": "Ver logs de quem alterou registros ou fez login"},
        ],
    },
    "configuracoes": {
        "nome": "Configurações Gerais",
        "descricao": "Dados da empresa, capacidade de vagas, cupom e chaves",
        "acoes": [
            {"acao": "ver", "nome": "Visualizar Parâmetros", "desc": "Consultar informações do estacionamento"},
            {"acao": "editar", "nome": "Alterar Configurações", "desc": "Atualizar número de vagas, dados fiscais e cupom"},
        ],
    },
    "estornos": {
        "nome": "Estornos",
        "descricao": "Registro e histórico de devoluções de valores",
        "acoes": [
            {"acao": "ver", "nome": "Visualizar Estornos", "desc": "Consultar histórico de estornos"},
            {"acao": "estornar", "nome": "Autorizar Estorno", "desc": "Efetuar estorno de valor"},
        ],
    },
}

# Matriz padrao de permissoes: modulo -> perfil -> lista de acoes.
# Admin sempre tem todas as acoes (tratado no codigo).
# Aplica-se tambem a perfis personalizados como fallback ate que sejam
# configurados explicitamente.
PERMISSOES_PADRAO = {
    "operacao": {
        "operador": [ACAO_VER, ACAO_CRIAR],
        "supervisor": [ACAO_VER, ACAO_CRIAR],
        "manobrista": [ACAO_VER, ACAO_CRIAR],
    },
    "caixa": {
        "operador": [ACAO_VER, ACAO_CRIAR, ACAO_FECHAR_CAIXA],
        "supervisor": [ACAO_VER, ACAO_CRIAR, ACAO_EDITAR, ACAO_FECHAR_CAIXA],
        "manobrista": [ACAO_VER, ACAO_CRIAR],
    },
    "pagamentos": {
        "operador": [ACAO_VER, ACAO_CRIAR, ACAO_CANCELAR],
        "supervisor": [ACAO_VER, ACAO_CRIAR, ACAO_EDITAR, ACAO_CANCELAR, ACAO_ESTORNAR],
        "manobrista": [ACAO_VER, ACAO_CRIAR],
    },
    "formas_pagamento": {
        "operador": [ACAO_VER],
        "supervisor": [ACAO_VER, ACAO_CRIAR, ACAO_EDITAR],
        "manobrista": [ACAO_VER],
    },
    "tabela_precos": {
        "operador": [ACAO_VER],
        "supervisor": [ACAO_VER, ACAO_EDITAR],
        "manobrista": [ACAO_VER],
    },
    "descontos": {
        "operador": [ACAO_VER],
        "supervisor": [ACAO_VER, ACAO_CRIAR, ACAO_EDITAR, ACAO_AUTORIZAR],
        "manobrista": [ACAO_VER],
    },
    "cortesias": {
        "operador": [ACAO_VER, ACAO_CRIAR],
        "supervisor": [ACAO_VER, ACAO_CRIAR, ACAO_EDITAR, ACAO_AUTORIZAR],
        "manobrista": [ACAO_VER],
    },
    "mensalistas": {
        "operador": [ACAO_VER, ACAO_CRIAR, ACAO_EDITAR],
        "supervisor": [ACAO_VER, ACAO_CRIAR, ACAO_EDITAR, ACAO_EXCLUIR],
        "manobrista": [ACAO_VER, ACAO_CRIAR, ACAO_EDITAR],
    },
    "convenios": {
        "operador": [ACAO_VER],
        "supervisor": [ACAO_VER, ACAO_CRIAR, ACAO_EDITAR, ACAO_EXCLUIR],
        "manobrista": [ACAO_VER],
    },
    "contas_receber": {
        "operador": [ACAO_VER],
        "supervisor": [ACAO_VER, ACAO_CRIAR, ACAO_EDITAR, ACAO_EXCLUIR],
        "manobrista": [ACAO_VER],
    },
    "estornos": {
        "operador": [ACAO_VER],
        "supervisor": [ACAO_VER, ACAO_CRIAR, ACAO_ESTORNAR],
        "manobrista": [ACAO_VER],
    },
    "auditoria": {
        "operador": [ACAO_VER],
        "supervisor": [ACAO_VER],
        "manobrista": [ACAO_VER],
    },
    "dashboard_financeiro": {
        "operador": [ACAO_VER],
        "supervisor": [ACAO_VER],
        "manobrista": [ACAO_VER],
    },
    "relatorios": {
        "operador": [ACAO_VER],
        "supervisor": [ACAO_VER],
        "manobrista": [ACAO_VER],
    },
    "usuarios": {
        "operador": [ACAO_VER],
        "supervisor": [ACAO_VER, ACAO_CRIAR, ACAO_EDITAR],
        "manobrista": [ACAO_VER],
    },
    "clientes": {
        "operador": [ACAO_VER, ACAO_CRIAR, ACAO_EDITAR],
        "supervisor": [ACAO_VER, ACAO_CRIAR, ACAO_EDITAR, ACAO_EXCLUIR],
        "manobrista": [ACAO_VER],
    },
    "financeiro": {
        "operador": [ACAO_VER],
        "supervisor": [ACAO_VER, ACAO_CRIAR, ACAO_EDITAR, ACAO_EXCLUIR],
        "manobrista": [ACAO_VER],
    },
    # Configuracoes do estacionamento (nome, vagas, precos, ticket, PIX):
    # visualizacao para todos, edicao exclusiva de admin.
    "configuracoes": {
        "operador": [ACAO_VER],
        "supervisor": [ACAO_VER],
        "manobrista": [ACAO_VER],
    },
    # NFSe (emissao de nota fiscal de servico)
    "nfse": {
        "operador": [ACAO_VER],
        "supervisor": [ACAO_VER, ACAO_CRIAR, ACAO_CANCELAR],
        "manobrista": [ACAO_VER],
    },
    # Lista negra (bloqueio de veiculos)
    "lista_negra": {
        "operador": [ACAO_VER],
        "supervisor": [ACAO_VER, ACAO_CRIAR, ACAO_EDITAR, ACAO_EXCLUIR],
        "manobrista": [ACAO_VER],
    },
    # Reservas de vaga
    "reservas": {
        "operador": [ACAO_VER, ACAO_CRIAR, ACAO_EDITAR],
        "supervisor": [ACAO_VER, ACAO_CRIAR, ACAO_EDITAR, ACAO_EXCLUIR],
        "manobrista": [ACAO_VER],
    },
    # Ocorrencias / termo de avarias
    "ocorrencias": {
        "operador": [ACAO_VER, ACAO_CRIAR],
        "supervisor": [ACAO_VER, ACAO_CRIAR, ACAO_EDITAR],
        "manobrista": [ACAO_VER],
    },
    # Notificacoes de vencimento
    "notificacoes": {
        "operador": [ACAO_VER],
        "supervisor": [ACAO_VER],
        "manobrista": [ACAO_VER],
    },
}


def _acoes_padrao(perfil: str, modulo: str) -> list:
    """Retorna as acoes padrao para um perfil/modulo (fallback)."""
    return list(PERMISSOES_PADRAO.get(modulo, {}).get(perfil, []))


class PermissaoService:
    """Verifica se um perfil possui determinada acao em um modulo."""

    def __init__(self, perfil_service: Optional[PerfilService] = None):
        self._perfil_service = perfil_service
        # Carrega as permissoes personalizadas do Supabase (se a tabela existir).
        self._permissoes: List[Permissao] = self._carregar()

    # =====================================================
    # PERSISTENCIA
    # =====================================================

    def _carregar(self) -> List[Permissao]:
        """Carrega as permissoes personalizadas do Supabase."""
        try:
            resposta = supabase.table("permissoes").select("*").order("id").execute()
        except Exception:
            return []
        permissoes = [Permissao.from_dict(dict(item)) for item in resposta.data]

        # Migracao: modulos adicionados depois que os perfis foram salvos
        # (ex.: 'operacao', 'clientes', 'financeiro') nao possuem linhas no
        # banco. Semeia os valores padrao uma unica vez para que os perfis
        # personalizados nao percam acesso aos menus novos.
        modulos_sem_linha = [
            m for m in MODULOS
            if not any(p.modulo == m for p in permissoes)
        ]
        if modulos_sem_linha:
            proximo_id = 1
            if permissoes:
                proximo_id = max(p.id for p in permissoes) + 1
            for perfil in self.perfis_editaveis():
                for modulo in modulos_sem_linha:
                    for acao in _acoes_padrao(perfil, modulo):
                        permissoes.append(Permissao(
                            id=proximo_id,
                            perfil=perfil,
                            modulo=modulo,
                            acao=acao,
                        ))
                        proximo_id += 1
            self._permissoes = permissoes
            try:
                self._salvar()
            except Exception:
                pass

        return permissoes

    def _salvar(self) -> None:
        """
        Sincroniza as permissoes em memoria com o Supabase.

        Como a tabela 'permissoes' nao possui chaves estrangeiras apontando
        para ela, usa delete + insert (a constraint unica perfil/modulo/acao
        impede duplicatas e o upsert por id nao resolve esse conflito).
        """
        try:
            supabase.table("permissoes").delete().neq("id", -1).execute()
        except Exception as erro:
            raise ValueError(
                "Nao foi possivel salvar as permissoes. "
                "Verifique se a tabela 'permissoes' foi criada no Supabase "
                "(execute o script sql/criar_tabela_permissoes.sql)."
            ) from erro

        if not self._permissoes:
            return

        # Remove o 'id' e o 'criado_em' vazio para que o banco gere via
        # identity/default.
        dados = []
        for p in self._permissoes:
            item = p.to_dict()
            item.pop("id", None)
            if not item.get("criado_em"):
                item.pop("criado_em", None)
            dados.append(item)
        try:
            supabase.table("permissoes").insert(dados).execute()
        except Exception as erro:
            raise ValueError(
                "Nao foi possivel salvar as permissoes. "
                "Verifique se a tabela 'permissoes' foi criada no Supabase "
                "(execute o script sql/criar_tabela_permissoes.sql)."
            ) from erro

    # =====================================================
    # PERFIS
    # =====================================================

    def perfis_validos(self) -> tuple:
        """Retorna os codigos dos perfis ativos (admin sempre incluido)."""
        if self._perfil_service:
            perfis = self._perfil_service.codigos_ativos()
            if "admin" not in perfis:
                perfis = ["admin"] + perfis
            return tuple(perfis)
        return ("admin", "supervisor", "operador")

    def perfis_editaveis(self) -> tuple:
        """Retorna os perfis que podem ter permissoes editadas (exclui admin)."""
        return tuple(p for p in self.perfis_validos() if p != "admin")

    @staticmethod
    def modulos() -> tuple:
        return MODULOS

    @staticmethod
    def acoes_validas() -> tuple:
        return ACOES_VALIDAS

    def _acoes_personalizadas(self, perfil: str, modulo: str) -> list:
        """Retorna as acoes personalizadas salvas para o perfil/modulo."""
        return [
            p.acao
            for p in self._permissoes
            if p.perfil == perfil and p.modulo == modulo
        ]

    def _tem_permissoes_personalizadas(self, perfil: str) -> bool:
        """Verifica se existe alguma permissao personalizada para o perfil."""
        return any(p.perfil == perfil for p in self._permissoes)

    def pode(self, perfil: str, modulo: str, acao: str = ACAO_VER) -> bool:
        """Retorna True se o perfil pode executar a acao no modulo."""
        if perfil == "admin":
            return True
        if perfil not in self.perfis_validos():
            return False

        # Se ha permissoes personalizadas para o perfil, usa-as.
        if self._tem_permissoes_personalizadas(perfil):
            return acao in self._acoes_personalizadas(perfil, modulo)

        # Fallback: matriz padrao.
        return acao in _acoes_padrao(perfil, modulo)

    def acoes_do_perfil(self, perfil: str, modulo: str) -> list:
        """Retorna a lista de acoes permitidas para o perfil no modulo."""
        if perfil == "admin":
            return list(ACOES_VALIDAS)
        if self._tem_permissoes_personalizadas(perfil):
            return self._acoes_personalizadas(perfil, modulo)
        return _acoes_padrao(perfil, modulo)

    # =====================================================
    # MATRIZ COMPLETA (para a interface)
    # =====================================================

    def matriz(self) -> dict:
        """
        Retorna a matriz completa de permissoes: modulo -> perfil -> [acoes].
        Usa as permissoes personalizadas se existirem, senao a padrao.
        """
        matriz = {}
        perfis = self.perfis_validos()
        for modulo in MODULOS:
            matriz[modulo] = {}
            for perfil in perfis:
                if perfil == "admin":
                    matriz[modulo][perfil] = list(ACOES_VALIDAS)
                elif self._tem_permissoes_personalizadas(perfil):
                    matriz[modulo][perfil] = self._acoes_personalizadas(perfil, modulo)
                else:
                    matriz[modulo][perfil] = _acoes_padrao(perfil, modulo)
        return matriz

    # =====================================================
    # ATUALIZACAO (via interface)
    # =====================================================

    def salvar_matriz(self, nova_matriz: dict) -> None:
        """
        Substitui as permissoes personalizadas pela matriz informada.
        nova_matriz: { modulo: { perfil: [acoes] } }
        """
        if not isinstance(nova_matriz, dict):
            raise ValueError("Matriz de permissoes invalida.")

        perfis_validos = set(self.perfis_validos())
        novas: List[Permissao] = []
        proximo_id = 1
        for modulo, por_perfil in nova_matriz.items():
            if modulo not in MODULOS:
                continue
            if not isinstance(por_perfil, dict):
                continue
            for perfil, acoes in por_perfil.items():
                # O perfil admin sempre tem acesso total (tratado no codigo).
                if perfil == "admin":
                    continue
                if perfil not in perfis_validos:
                    continue
                if not isinstance(acoes, (list, tuple, set)):
                    continue
                for acao in acoes:
                    if acao not in ACOES_VALIDAS:
                        continue
                    novas.append(Permissao(
                        id=proximo_id,
                        perfil=perfil,
                        modulo=modulo,
                        acao=acao,
                    ))
                    proximo_id += 1

        self._permissoes = novas
        self._salvar()

    def restaurar_padrao(self) -> None:
        """
        Restaura as permissoes padrao (matriz embutida), apagando as
        personalizacoes salvas. Perfis personalizados recebem as acoes
        padrao de 'operador' quando nao houver regra especifica.
        """
        novas: List[Permissao] = []
        proximo_id = 1
        for perfil in self.perfis_editaveis():
            for modulo in MODULOS:
                for acao in _acoes_padrao(perfil, modulo):
                    novas.append(Permissao(
                        id=proximo_id,
                        perfil=perfil,
                        modulo=modulo,
                        acao=acao,
                    ))
                    proximo_id += 1
        self._permissoes = novas
        self._salvar()

    def clonar_perfil(self, origem: str, destino: str) -> None:
        """
        Copia as permissoes de um perfil para outro (util ao criar um
        novo perfil baseado em outro).
        """
        if origem not in self.perfis_validos() or destino not in self.perfis_validos():
            raise ValueError("Perfil de origem ou destino invalido.")

        # Remove permissoes existentes do destino
        self._permissoes = [p for p in self._permissoes if p.perfil != destino]

        proximo_id = 1
        if self._permissoes:
            proximo_id = max(p.id for p in self._permissoes) + 1

        for modulo in MODULOS:
            for acao in self.acoes_do_perfil(origem, modulo):
                self._permissoes.append(Permissao(
                    id=proximo_id,
                    perfil=destino,
                    modulo=modulo,
                    acao=acao,
                ))
                proximo_id += 1
        self._salvar()

    @staticmethod
    def catalogo_modulos() -> dict:
        """Retorna o catalogo completo de modulos agrupados e acoes contextuais."""
        return {
            "categorias": CATEGORIAS_MODULOS,
            "acoes_por_modulo": ACOES_POR_MODULO,
        }

