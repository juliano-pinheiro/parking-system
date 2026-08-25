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
)

# Matriz padrao de permissoes: modulo -> perfil -> lista de acoes.
# Admin sempre tem todas as acoes (tratado no codigo).
# Aplica-se tambem a perfis personalizados como fallback ate que sejam
# configurados explicitamente.
PERMISSOES_PADRAO = {
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
        return [Permissao.from_dict(dict(item)) for item in resposta.data]

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
