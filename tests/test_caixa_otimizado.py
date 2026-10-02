"""
Testes unitarios para a otimizacao do Caixa e Pagamentos (Fase 1).
Verifica:
1. Calculo contabil liquido por forma de pagamento (entradas, suprimentos, sangrias, estornos).
2. Resumo detalhado do turno.
3. Sincronizacao de estorno com caixa e financeiro.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.caixa import Caixa, MovimentacaoCaixa
from services.caixa_service import CaixaService


def test_totais_caixa_com_sangria_suprimento_e_estorno():
    serv = CaixaService.__new__(CaixaService)
    serv._empresa_id = None
    caixa = Caixa(id=10, operador="Carlos", valor_inicial=50.0, status="aberto")
    serv._registros = [caixa]
    
    # 1. Abertura registra suprimento de R$ 50 em dinheiro
    # 2. Venda de R$ 30 em dinheiro
    # 3. Venda de R$ 40 em PIX
    # 4. Sangria de R$ 15 em dinheiro
    # 5. Estorno de R$ 10 em dinheiro
    serv._movimentacoes = [
        MovimentacaoCaixa(id=1, caixa_id=10, tipo="suprimento", valor=50.0, forma_pagamento="dinheiro", descricao="Valor inicial de abertura"),
        MovimentacaoCaixa(id=2, caixa_id=10, tipo="entrada", valor=30.0, forma_pagamento="dinheiro", descricao="Ticket #1"),
        MovimentacaoCaixa(id=3, caixa_id=10, tipo="entrada", valor=40.0, forma_pagamento="pix", descricao="Ticket #2"),
        MovimentacaoCaixa(id=4, caixa_id=10, tipo="sangria", valor=15.0, forma_pagamento="dinheiro", descricao="Retirada para troco"),
        MovimentacaoCaixa(id=5, caixa_id=10, tipo="estorno", valor=10.0, forma_pagamento="dinheiro", descricao="Estorno Ticket #1"),
    ]

    totais = serv.totais_por_forma(10)
    
    # Dinheiro esperado em gaveta: 50 + 30 - 15 - 10 = R$ 55,00
    assert totais["dinheiro"] == 55.0
    # Pix esperado: R$ 40,00
    assert totais["pix"] == 40.0

    resumo = serv.resumo_detalhado(10)
    assert resumo["caixa_id"] == 10
    assert resumo["valor_inicial"] == 50.0
    assert resumo["total_entradas"] == 70.0  # 30 din + 40 pix
    assert resumo["total_sangrias"] == 15.0
    assert resumo["total_estornos"] == 10.0
    assert resumo["saldo_dinheiro"] == 55.0
    assert resumo["saldo_total"] == 95.0  # 55 din + 40 pix


def test_registro_estorno_caixa():
    serv = CaixaService.__new__(CaixaService)
    serv._empresa_id = None
    caixa = Caixa(id=20, operador="Ana", valor_inicial=0.0, status="aberto")
    serv._registros = [caixa]
    serv._movimentacoes = []

    # Mock de persistencia pontual
    serv._inserir_movimentacao = lambda mov: None

    mov = serv.estorno(
        id_caixa=20,
        valor=25.50,
        motivo="Cliente desistiu",
        forma_pagamento="pix",
        usuario="admin",
    )

    assert mov.tipo == "estorno"
    assert mov.valor == 25.50
    assert mov.forma_pagamento == "pix"
    assert mov.caixa_id == 20
    assert len(serv._movimentacoes) == 1


def test_api_movimentacoes_caixa_endpoint():
    """Valida se o endpoint /api/caixa/<id>/movimentacoes responde com lista de movimentacoes."""
    from app import app
    cliente = app.test_client()
    with cliente.session_transaction() as sessao:
        sessao["usuario_id"] = 1
        sessao["usuario_nome"] = "Administrador"
        sessao["usuario_login"] = "admin"
        sessao["usuario_perfil"] = "admin"
        sessao["empresa_id"] = 1

    resp = cliente.get("/api/caixa/1/movimentacoes")
    assert resp.status_code == 200
    dados = resp.get_json()
    assert "movimentacoes" in dados
    assert isinstance(dados["movimentacoes"], list)


def test_bloqueio_emissao_ticket_sem_caixa_aberto():
    """Valida se o sistema rejeita emitir ticket enquanto o caixa nao estiver aberto."""
    import time
    from app import app
    from services_registry import servico_caixa, servico

    cliente = app.test_client()
    with cliente.session_transaction() as sessao:
        sessao["usuario_id"] = 1
        sessao["usuario_nome"] = "Operador Caixa"
        sessao["usuario_login"] = "operador"
        sessao["usuario_perfil"] = "operador"
        sessao["empresa_id"] = 1

    placa_teste = f"CX{int(time.time() * 1000) % 1000000:06d}"
    servico.tickets = [t for t in servico.tickets if t.placa != placa_teste]

    try:
        # 1. Garante que todos os caixas estao fechados
        for c in servico_caixa._registros:
            c.status = "fechado"

        # Tentativa de emitir ticket com caixa fechado -> Deve falhar com 400
        resp = cliente.post("/api/entrada", json={
            "placa": placa_teste,
            "tipo_veiculo": "Carro",
            "observacoes": "Teste sem caixa",
        })
        assert resp.status_code == 400
        dados = resp.get_json()
        assert dados.get("caixa_fechado") is True
        assert "caixa" in dados.get("erro", "").lower()

        # 2. Abre o caixa
        caixa = servico_caixa.abrir(operador="Operador Caixa", valor_inicial=100.0)
        assert servico_caixa.caixa_aberto() is not None

        # Emissao com caixa aberto -> Deve ter sucesso (201)
        resp2 = cliente.post("/api/entrada", json={
            "placa": placa_teste,
            "tipo_veiculo": "Carro",
            "observacoes": "Teste com caixa aberto",
        })
        assert resp2.status_code == 201
        dados2 = resp2.get_json()
        assert "ticket" in dados2
        assert dados2["ticket"]["placa"] == placa_teste

        # 3. Fecha o caixa
        servico_caixa.fechar(caixa.id, valor_contado=100.0)
        assert servico_caixa.caixa_aberto() is None

        # Tentativa de nova emissao volta a ser bloqueada
        placa_teste_2 = f"CX{int(time.time() * 1000) % 1000000:06d}B"
        resp3 = cliente.post("/api/entrada", json={
            "placa": placa_teste_2,
            "tipo_veiculo": "Carro",
            "observacoes": "Teste apos fechar caixa",
        })
        assert resp3.status_code == 400
        assert resp3.get_json().get("caixa_fechado") is True
    finally:
        servico.tickets = [t for t in servico.tickets if t.placa not in (placa_teste,)]



