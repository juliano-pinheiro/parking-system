"""
Testes unitários e de integração para os 5 gaps corrigidos:
1. Persistência segura
2. Cobrança com tabela de preços (tolerância, tipo de veículo)
3. Comparação de datas e competências
4. Mensalista com placa e categoria
5. Segurança de rotas e senhas
"""

import sys
import os
import hashlib
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.usuario import hash_senha, verificar_senha
from models.mensalista import Mensalista
from services.mensalista_service import MensalistaService
from services.financeiro_service import FinanceiroService
from services.tabela_preco_service import TabelaPrecoService
from services.estacionamento_service import EstacionamentoService


def test_senha_pbkdf2_e_compatibilidade_legado():
    senha_plana = "minhaSenha123"
    # Novo formato com salt (pbkdf2)
    novo_hash = hash_senha(senha_plana)
    assert novo_hash.startswith("pbkdf2:")
    assert verificar_senha(senha_plana, novo_hash)
    assert not verificar_senha("senhaErrada", novo_hash)

    # Compatibilidade com hash SHA-256 legado
    hash_legado = hashlib.sha256(senha_plana.encode("utf-8")).hexdigest()
    assert verificar_senha(senha_plana, hash_legado)
    assert not verificar_senha("outraSenha", hash_legado)


def test_tabela_precos_calculo_tolerancia():
    tabela = TabelaPrecoService.__new__(TabelaPrecoService)
    tabela._empresa_id = None
    tabela.tipos_personalizados = {}
    from models.tabela_preco import TabelaPreco
    tabela._registros = [TabelaPreco(id=1, primeira_hora=10.0, hora_adicional=5.0, tolerancia_minutos=15)]
    
    # 10 minutos de permanencia (dentro da tolerancia de 15 min) -> R$ 0,00
    entrada = "02/09/2026 14:00:00"
    saida = "02/09/2026 14:10:00"
    valor = tabela.calcular_valor(entrada, saida, tipo_veiculo="Carro")
    assert valor == 0.0

    # 40 minutos de permanencia (acima da tolerancia) -> primeira hora = R$ 10,00
    saida2 = "02/09/2026 14:40:00"
    valor2 = tabela.calcular_valor(entrada, saida2, tipo_veiculo="Carro")
    assert valor2 == 10.0


def test_filtro_periodo_data_financeiro():
    serv = FinanceiroService.__new__(FinanceiroService)
    serv._empresa_id = None
    from models.lancamento import Lancamento
    serv.lancamentos = [
        Lancamento(id=1, tipo="entrada", descricao="Janeiro", valor=100.0, data="15/01/2026 10:00:00"),
        Lancamento(id=2, tipo="entrada", descricao="Agosto", valor=200.0, data="05/08/2026 10:00:00"),
        Lancamento(id=3, tipo="entrada", descricao="Dezembro", valor=300.0, data="25/12/2026 10:00:00"),
    ]

    # Filtra período de Agosto (01/08/2026 a 31/08/2026)
    filtrados = serv._filtrar_por_periodo("01/08/2026", "31/08/2026")
    assert len(filtrados) == 1
    assert filtrados[0].id == 2

    # Se usasse ordenação de string, "15/01/2026" poderia se misturar incorretamente
    filtrados_jan = serv._filtrar_por_periodo("01/01/2026", "31/01/2026")
    assert len(filtrados_jan) == 1
    assert filtrados_jan[0].id == 1


def test_parse_competencia_mensalistas():
    # Valida que Dezembro de 2025 é cronologicamente anterior a Setembro de 2026
    t_antiga = MensalistaService._parse_competencia("12/2025")
    t_atual = MensalistaService._parse_competencia("09/2026")
    assert t_antiga < t_atual  # (2025, 12) < (2026, 9)


def test_mensalista_buscar_por_placa():
    serv = MensalistaService.__new__(MensalistaService)
    serv._empresa_id = None
    serv._registros = [
        Mensalista(id=1, nome="João Silva", placa="ABC1234", tipo_veiculo="Carro", status="ativo"),
        Mensalista(id=2, nome="Maria Santos", placa="XYZ9876", tipo_veiculo="Moto", status="bloqueado"),
    ]

    # Busca com placa em maiúscula e minúscula
    m1 = serv.buscar_por_placa("abc1234")
    assert m1 is not None
    assert m1.nome == "João Silva"
    assert m1.tipo_veiculo == "Carro"

    m2 = serv.buscar_por_placa("XYZ9876")
    assert m2 is not None
    assert m2.status == "bloqueado"

    m_none = serv.buscar_por_placa("OUTRAPLACA")
    assert m_none is None


def test_dashboard_resumo_e_capacidade_patio():
    """Valida se o endpoint /api/dashboard retorna campos operacionais para a tela inicial."""
    from app import app
    cliente = app.test_client()
    with cliente.session_transaction() as sessao:
        sessao["usuario_id"] = 1
        sessao["usuario_nome"] = "Operador Teste"
        sessao["usuario_login"] = "operador"
        sessao["usuario_perfil"] = "operador"
        sessao["empresa_id"] = 1

    resp = cliente.get("/api/dashboard")
    assert resp.status_code == 200
    dados = resp.get_json()
    assert "no_patio_agora" in dados
    assert "vagas_disponiveis" in dados
    assert "faturamento_hoje" in dados
    assert "saidas_hoje" in dados
    assert "permanencia_media_texto" in dados


def test_dashboard_financeiro_indicadores_completos():
    """Valida se o endpoint /api/dashboard-financeiro entrega toda a estrutura rica de KPIs e series temporais."""
    from app import app
    cliente = app.test_client()
    with cliente.session_transaction() as sessao:
        sessao["usuario_id"] = 1
        sessao["usuario_nome"] = "Administrador"
        sessao["usuario_login"] = "admin"
        sessao["usuario_perfil"] = "admin"
        sessao["empresa_id"] = 1

    resp = cliente.get("/api/dashboard-financeiro")
    assert resp.status_code == 200
    dados = resp.get_json()

    # Indicadores principais
    assert "receita_dia" in dados
    assert "receita_mes" in dados
    assert "receita_ano" in dados
    assert "quantidade_tickets" in dados
    assert "ticket_medio" in dados
    assert "media_diaria_mes" in dados

    # Séries temporais (30 dias, 12 meses, 5 anos)
    assert len(dados["grafico_diario"]["labels"]) == 30
    assert len(dados["grafico_diario"]["valores"]) == 30
    assert len(dados["grafico_mensal"]["labels"]) == 12
    assert len(dados["grafico_mensal"]["valores"]) == 12
    assert len(dados["grafico_anual"]["labels"]) == 5
    assert len(dados["grafico_anual"]["valores"]) == 5

    # Distribuição e comparativo
    assert "receita_por_forma" in dados
    assert "receita_por_horario" in dados
    assert "comparativo_mensal" in dados
    assert "mes_atual" in dados["comparativo_mensal"]
    assert "mes_anterior" in dados["comparativo_mensal"]
    assert "variacao_percentual" in dados["comparativo_mensal"]
    assert "top_operadores" in dados


def test_operacao_patio_calculo_previa_e_ticket_perdido_libera_vaga():
    """Valida o pre-calculo de saida e a liberacao da vaga ao cobrar ticket perdido."""
    import time
    from app import app
    from services_registry import servico, servico_caixa

    cliente = app.test_client()
    with cliente.session_transaction() as sessao:
        sessao["usuario_id"] = 1
        sessao["usuario_nome"] = "Operador Patio"
        sessao["usuario_login"] = "operador"
        sessao["usuario_perfil"] = "admin"
        sessao["empresa_id"] = 1

    placa_teste = f"PAT{int(time.time() * 1000) % 1000000:06d}"
    servico.tickets = [t for t in servico.tickets if t.placa != placa_teste]

    try:
        # Garante caixa aberto
        caixa = servico_caixa.caixa_aberto()
        if not caixa:
            caixa = servico_caixa.abrir(operador="Operador Patio", valor_inicial=50.0)

        # 1. Registra entrada
        resp_ent = cliente.post("/api/entrada", json={
            "placa": placa_teste,
            "tipo_veiculo": "Carro",
            "observacoes": "Veiculo para teste de checkout",
        })
        assert resp_ent.status_code == 201
        num_ticket = resp_ent.get_json()["ticket"]["numero"]

        # 2. Testa prévia de cálculo de saída (/api/saida/calcular)
        resp_calc = cliente.get(f"/api/saida/calcular?identificador={num_ticket}")
        assert resp_calc.status_code == 200
        dados_calc = resp_calc.get_json()
        assert "tempo_permanencia" in dados_calc
        assert "valor" in dados_calc
        assert dados_calc["ticket"]["placa"] == placa_teste
        assert dados_calc["eh_mensalista"] is False

        # 3. Testa ticket perdido com encerramento e liberação de vaga
        abertos_antes = [t for t in servico.listar_tickets_abertos() if t.placa == placa_teste]
        assert len(abertos_antes) == 1

        resp_tp = cliente.post("/api/ticket-perdido", json={
            "placa": placa_teste,
            "valor": 30.0,
            "forma_pagamento": "pix",
            "observacoes": "Perdeu o ticket físico",
            "autorizador": "admin",
        })
        assert resp_tp.status_code == 201
        dados_tp = resp_tp.get_json()
        assert dados_tp["ticket"]["status"] == "FECHADO"
        assert dados_tp["ticket"]["valor"] == 30.0

        # Verifica que a vaga foi liberada e o ticket original foi fechado
        abertos_depois = [t for t in servico.listar_tickets_abertos() if t.placa == placa_teste]
        assert len(abertos_depois) == 0

    finally:
        servico.tickets = [t for t in servico.tickets if t.placa != placa_teste]


def test_info_acesso_mobile_endpoint():
    """Valida se o endpoint /api/acesso-mobile retorna IP, porta e URL de conexao local."""
    from app import app
    cliente = app.test_client()
    with cliente.session_transaction() as sessao:
        sessao["usuario_id"] = 1
        sessao["usuario_nome"] = "Operador Mobile"
        sessao["usuario_login"] = "operador"
        sessao["usuario_perfil"] = "operador"
        sessao["empresa_id"] = 1

    resp = cliente.get("/api/acesso-mobile")
    assert resp.status_code == 200
    dados = resp.get_json()
    assert "ip_local" in dados
    assert "porta" in dados
    assert "url_acesso" in dados
    assert "hostname" in dados
    assert dados["url_acesso"].startswith("http")





