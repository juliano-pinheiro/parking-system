"""
Testes de integracao leves da interface web (blueprints).

Cobrem: paginas publicas, rotas publicas da API, autenticacao e a
protecao das rotas que exigem sessao. Nao dependem de credenciais reais
nem de dados do banco (usam o test client do Flask em memoria).
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app as appmod

client = appmod.app.test_client()

ROTAS_PUBLICAS = [
    "/api/estornos",
    "/api/formas-pagamento",
    "/api/tabela-precos",
    "/api/relatorio",
]

ROTAS_PROTEGIDAS = [
    "/api/status", "/api/vagas", "/api/dashboard", "/api/historico", "/api/buscar",
    "/api/financeiro", "/api/caixa", "/api/pagamentos", "/api/dashboard-financeiro",
    "/api/configuracoes", "/api/tipos-veiculo", "/api/descontos", "/api/cortesias",
    "/api/clientes", "/api/mensalistas", "/api/convenios", "/api/contas-receber",
    "/api/usuarios", "/api/empresas", "/api/perfis", "/api/auditoria", "/api/logs-acesso",
    "/api/relatorio-financeiro", "/api/relatorio-ocupacao", "/api/relatorio-dre",
    "/api/nfse", "/api/lista-negra", "/api/reservas", "/api/ocorrencias",
    "/api/notificacoes-vencimento", "/api/backup", "/api/empresa/atual",
]


def test_pagina_raiz_redireciona_para_login():
    r = client.get("/")
    assert r.status_code == 302
    assert "/login" in r.headers.get("Location", "")


def test_pagina_login_carrega_template():
    assert client.get("/login").status_code == 200


def test_rotas_publicas_respondem():
    for rota in ROTAS_PUBLICAS:
        r = client.get(rota)
        assert r.status_code == 200
        assert r.get_json() is not None


def test_rotas_protegidas_exigem_sessao():
    for rota in ROTAS_PROTEGIDAS:
        r = client.get(rota)
        assert r.status_code == 401, f"{rota} deveria retornar 401, retornou {r.status_code}"


def test_login_sem_dados_retorna_400():
    assert client.post("/api/login", json={}).status_code == 400


def test_login_invalido_retorna_401():
    resp = client.post("/api/login", json={"email": "naoexiste@x.com", "senha": "errada"})
    assert resp.status_code == 401


def test_logout_retorna_200():
    assert client.post("/api/logout").status_code == 200