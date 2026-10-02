"""
Testes para o novo sistema granular de Funções e Permissões (RBAC).
Verifica:
1. Catálogo completo de módulos e categorias estruturadas.
2. Ações contextuais por módulo com nomes e descrições humanas.
3. Rota /api/permissoes com payload enriquecido para o frontend.
4. Liberação e bloqueio seguro por módulo e perfil.
5. Invariante do perfil Administrador (acesso total irrestrito).
6. Clonagem e restauração de perfis.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.permissao_service import PermissaoService, CATEGORIAS_MODULOS, ACOES_POR_MODULO, MODULOS
from app import app


def test_catalogo_modulos_e_categorias():
    serv = PermissaoService()

    catalogo = serv.catalogo_modulos()
    assert "categorias" in catalogo
    assert "acoes_por_modulo" in catalogo

    # 1. Deve possuir as 5 categorias de negócio
    categorias = catalogo["categorias"]
    assert len(categorias) == 5
    ids_categorias = [c["id"] for c in categorias]
    assert "operacao" in ids_categorias
    assert "comercial" in ids_categorias
    assert "tarifas" in ids_categorias
    assert "financeiro" in ids_categorias
    assert "admin" in ids_categorias

    # 2. Todos os módulos do sistema devem estar contemplados no catálogo de ações
    acoes_modulo = catalogo["acoes_por_modulo"]
    for mod in MODULOS:
        assert mod in acoes_modulo, f"Módulo '{mod}' ausente de acoes_por_modulo"
        info = acoes_modulo[mod]
        assert "nome" in info and len(info["nome"]) > 0
        assert "descricao" in info and len(info["descricao"]) > 0
        assert "acoes" in info and len(info["acoes"]) > 0
        for item in info["acoes"]:
            assert "acao" in item
            assert "nome" in item and len(item["nome"]) > 0
            assert "desc" in item and len(item["desc"]) > 0


def test_bloqueio_e_liberacao_modulo():
    serv = PermissaoService()

    # Inicializa com matriz padrão
    matriz = serv.matriz()
    assert "operador" in matriz["operacao"]
    assert "ver" in matriz["operacao"]["operador"]

    # 1. Operador tem permissão normal de ver pátio
    assert serv.pode("operador", "operacao", "ver") is True

    # 2. Bloqueia o módulo 'operacao' para o perfil operador (desmarca tudo)
    matriz_atualizada = {mod: dict(perfis) for mod, perfis in matriz.items()}
    matriz_atualizada["operacao"]["operador"] = []
    serv.salvar_matriz(matriz_atualizada)

    # Operador agora está bloqueado
    assert serv.pode("operador", "operacao", "ver") is False
    assert serv.pode("operador", "operacao", "criar") is False

    # 3. Administrador continua com acesso total garantido
    assert serv.pode("admin", "operacao", "ver") is True
    assert serv.pode("admin", "operacao", "excluir") is True

    # 4. Restaura padrão
    serv.restaurar_padrao()
    assert serv.pode("operador", "operacao", "ver") is True


def test_clonagem_perfil_com_permissoes():
    serv = PermissaoService()

    serv.matriz()  # Garante inicialização
    # Clona permissões de supervisor para 'operador'
    serv.clonar_perfil("supervisor", "operador")

    # Verifica se os privilégios foram replicados
    for mod in MODULOS:
        acoes_supervisor = serv.acoes_do_perfil("supervisor", mod)
        acoes_clone = serv.acoes_do_perfil("operador", mod)
        assert set(acoes_supervisor) == set(acoes_clone)

    # Restaura padrão para manter o estado limpo
    serv.restaurar_padrao()


def test_api_permissoes_retorna_catalogo():
    with app.test_client() as client:
        # Cria sessão de admin
        with client.session_transaction() as sess:
            sess["usuario_id"] = 1
            sess["usuario_nome"] = "Administrador"
            sess["usuario_login"] = "admin"
            sess["usuario_perfil"] = "admin"
            sess["usuario_empresa_id"] = 1

        resposta = client.get("/api/permissoes")
        assert resposta.status_code == 200
        dados = resposta.get_json()

        assert "categorias" in dados
        assert "acoes_por_modulo" in dados
        assert "matriz" in dados
        assert "perfis" in dados
        assert "modulos" in dados
        assert len(dados["categorias"]) == 5
        assert "caixa" in dados["acoes_por_modulo"]
        assert "nfse" in dados["acoes_por_modulo"]
        assert "reservas" in dados["acoes_por_modulo"]
        assert "lista_negra" in dados["acoes_por_modulo"]
        assert "ocorrencias" in dados["acoes_por_modulo"]


def test_operador_acesso_visao_geral_e_status():
    """Valida se um usuario com perfil 'operador' consegue carregar a Visao Geral sem erro 403."""
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["usuario_id"] = 4
            sess["usuario_nome"] = "Operador Teste"
            sess["usuario_login"] = "op_teste@teste.com"
            sess["usuario_perfil"] = "operador"
            sess["usuario_empresa_id"] = 1

        # Visao Geral consome status, vagas, dashboard e configuracoes para o ticket
        for rota in ["/api/status", "/api/dashboard", "/api/vagas", "/api/configuracoes"]:
            r = client.get(rota)
            assert r.status_code == 200, f"Rota {rota} falhou para operador com status {r.status_code}: {r.data}"

