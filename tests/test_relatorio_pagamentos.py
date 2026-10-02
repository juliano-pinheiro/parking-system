"""
Testes automatizados para o novo modelo de Relatorio de Pagamentos por Forma de Pagamento.
"""

import csv
import io
import json
from app import app


def test_relatorio_pagamentos_estrutura():
    """Valida se o endpoint /api/relatorio-pagamentos retorna as metricas e listas esperadas."""
    cliente = app.test_client()
    with cliente.session_transaction() as sessao:
        sessao["usuario_id"] = 1
        sessao["usuario_nome"] = "Administrador"
        sessao["usuario_login"] = "admin"
        sessao["usuario_perfil"] = "admin"
        sessao["empresa_id"] = 1

    resp = cliente.get("/api/relatorio-pagamentos")
    assert resp.status_code == 200
    dados = resp.get_json()

    assert "receita_total" in dados
    assert "quantidade_total" in dados
    assert "ticket_medio" in dados
    assert "resumo_formas" in dados
    assert "transacoes" in dados
    assert "filtros" in dados

    assert isinstance(dados["resumo_formas"], list)
    assert isinstance(dados["transacoes"], list)

    # Validacao de coerencia matematica
    if dados["quantidade_total"] > 0:
        soma_transacoes = round(sum(t["valor"] for t in dados["transacoes"]), 2)
        assert abs(soma_transacoes - dados["receita_total"]) < 0.05
        calc_medio = round(dados["receita_total"] / dados["quantidade_total"], 2)
        assert abs(calc_medio - dados["ticket_medio"]) < 0.05


def test_relatorio_pagamentos_filtro_forma():
    """Valida se a filtragem por forma de pagamento especifica retorna apenas transacoes daquela forma."""
    cliente = app.test_client()
    with cliente.session_transaction() as sessao:
        sessao["usuario_id"] = 1
        sessao["usuario_nome"] = "Administrador"
        sessao["usuario_login"] = "admin"
        sessao["usuario_perfil"] = "admin"
        sessao["empresa_id"] = 1

    resp = cliente.get("/api/relatorio-pagamentos?forma_pagamento=pix")
    assert resp.status_code == 200
    dados = resp.get_json()

    for t in dados["transacoes"]:
        assert t["forma_pagamento"] == "pix"

    if dados["resumo_formas"]:
        assert len(dados["resumo_formas"]) == 1
        assert dados["resumo_formas"][0]["codigo"] == "pix"


def test_relatorio_pagamentos_filtro_periodo():
    """Valida se filtros de data inicial e final delimitam corretamente os resultados."""
    cliente = app.test_client()
    with cliente.session_transaction() as sessao:
        sessao["usuario_id"] = 1
        sessao["usuario_nome"] = "Administrador"
        sessao["usuario_login"] = "admin"
        sessao["usuario_perfil"] = "admin"
        sessao["empresa_id"] = 1

    # Filtro com data no futuro nao deve retornar transacoes passadas
    resp = cliente.get("/api/relatorio-pagamentos?data_inicio=2099-01-01&data_fim=2099-12-31")
    assert resp.status_code == 200
    dados = resp.get_json()
    assert dados["quantidade_total"] == 0
    assert dados["receita_total"] == 0.0
    assert len(dados["transacoes"]) == 0


def test_relatorio_pagamentos_exportar_csv():
    """Valida se a exportacao em CSV gera o arquivo formatado com cabeçalho, resumo e detalhes."""
    cliente = app.test_client()
    with cliente.session_transaction() as sessao:
        sessao["usuario_id"] = 1
        sessao["usuario_nome"] = "Administrador"
        sessao["usuario_login"] = "admin"
        sessao["usuario_perfil"] = "admin"
        sessao["empresa_id"] = 1

    resp = cliente.get("/api/relatorio-pagamentos/exportar?forma_pagamento=todas")
    assert resp.status_code == 200
    assert resp.mimetype == "text/csv"
    assert "attachment" in resp.headers.get("Content-Disposition", "")

    conteudo = resp.data.decode("utf-8")
    assert "RELATORIO DE PAGAMENTOS POR FORMA DE PAGAMENTO" in conteudo
    assert "RESUMO GERAL" in conteudo
    assert "DISTRIBUICAO POR FORMA DE PAGAMENTO" in conteudo
    assert "DETALHAMENTO DE TRANSACOES" in conteudo


def test_relatorio_pagamentos_protecao_autenticacao():
    """Valida que chamadas sem sessao sao bloqueadas."""
    cliente = app.test_client()
    resp = cliente.get("/api/relatorio-pagamentos")
    assert resp.status_code == 401

    resp_csv = cliente.get("/api/relatorio-pagamentos/exportar")
    assert resp_csv.status_code == 401

