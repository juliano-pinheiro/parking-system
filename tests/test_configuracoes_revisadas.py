"""
Testes unitarios e de integracao para o Menu de Configuracoes Revisado.
Valida:
- Atualizacao e persistencia dos novos campos de ticket/cupom (formato, cnpj, contato, barcode)
- Validacao da capacidade total de vagas vs ocupadas
- Sincronizacao de tarifas
- Endpoint de exportacao de backup JSON
"""

import json
from unittest.mock import Mock, patch

from app import app
import services.empresa_service as empresa_service_module
from models.empresa import Empresa
from services.empresa_service import EmpresaService
from services_registry import servico, servico_tabela_precos


def test_atualizacao_configuracao_novos_campos():
    """Valida se o servico atualiza e persiste os novos campos de cupom."""
    config = servico.atualizar_configuracao(
        nome_estacionamento="Estaciona Teste Pro",
        ticket_formato_papel="58mm",
        ticket_exibir_cnpj=False,
        ticket_exibir_contato=True,
        ticket_exibir_codigo_barras=False,
        bloquear_sem_vaga=True,
    )
    assert config.nome_estacionamento == "Estaciona Teste Pro"
    assert config.ticket_formato_papel == "58mm"
    assert config.ticket_exibir_cnpj is False
    assert config.ticket_exibir_contato is True
    assert config.ticket_exibir_codigo_barras is False
    assert config.bloquear_sem_vaga is True


def test_api_configuracoes_post_e_get():
    """Valida POST e GET na rota /api/configuracoes com os novos campos."""
    cliente = app.test_client()
    with cliente.session_transaction() as sessao:
        sessao["usuario_id"] = 1
        sessao["usuario_nome"] = "Administrador"
        sessao["usuario_login"] = "admin"
        sessao["usuario_perfil"] = "admin"
        sessao["usuario_empresa_id"] = 1

    payload = {
        "nome_estacionamento": "Estaciona Central VIP",
        "cnpj": "12.345.678/0001-90",
        "telefone": "(11) 98765-4321",
        "total_vagas": 40,
        "vagas_carro": 25,
        "vagas_moto": 10,
        "vagas_carro_grande": 3,
        "vagas_caminhonete": 2,
        "ticket_formato_papel": "80mm",
        "ticket_exibir_cnpj": True,
        "ticket_exibir_contato": True,
        "ticket_exibir_codigo_barras": True,
        "bloquear_sem_vaga": False,
        "exigir_observacao": True,
    }

    resp = cliente.post(
        "/api/configuracoes",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert resp.status_code == 200, f"Erro: {resp.data}"
    dados = resp.get_json()
    assert dados["configuracao"]["nome_estacionamento"] == "Estaciona Central VIP"
    assert dados["configuracao"]["ticket_formato_papel"] == "80mm"
    assert dados["configuracao"]["ticket_exibir_cnpj"] is True
    assert dados["configuracao"]["total_vagas"] == 40

    resp_get = cliente.get("/api/configuracoes")
    assert resp_get.status_code == 200
    dados_get = resp_get.get_json()
    assert dados_get["nome_estacionamento"] == "Estaciona Central VIP"
    assert dados_get["ticket_formato_papel"] == "80mm"


def test_validacao_vagas_menor_que_ocupadas():
    """Valida se a API rejeita definir total_vagas menor que veiculos atualmente estacionados."""
    cliente = app.test_client()
    with cliente.session_transaction() as sessao:
        sessao["usuario_id"] = 1
        sessao["usuario_nome"] = "Administrador"
        sessao["usuario_login"] = "admin"
        sessao["usuario_perfil"] = "admin"
        sessao["usuario_empresa_id"] = 1

    vagas_ocupadas = servico.vagas_ocupadas()
    if vagas_ocupadas > 0:
        resp = cliente.post(
            "/api/configuracoes",
            data=json.dumps({"total_vagas": vagas_ocupadas - 1}),
            content_type="application/json",
        )
        assert resp.status_code == 400
        dados = resp.get_json()
        assert "Nao e possivel definir" in dados["erro"]


def test_exportacao_backup_endpoint():
    """Valida se a rota /api/backup retorna o arquivo JSON completo com os dados da empresa."""
    cliente = app.test_client()
    with cliente.session_transaction() as sessao:
        sessao["usuario_id"] = 1
        sessao["usuario_nome"] = "Administrador"
        sessao["usuario_login"] = "admin"
        sessao["usuario_perfil"] = "admin"
        sessao["usuario_empresa_id"] = 1

    resp = cliente.get("/api/backup")
    assert resp.status_code == 200
    assert resp.mimetype == "application/json"
    backup = json.loads(resp.data.decode("utf-8"))
    assert "sistema" in backup
    assert "dados" in backup
    assert "tabela_precos" in backup["dados"]
    assert "formas_pagamento" in backup["dados"]
    assert "configuracao" in backup["dados"]


def test_exportacao_backup_exige_permissao_de_edicao():
    """Usuários que apenas visualizam configurações não podem exportar o backup."""
    cliente = app.test_client()
    with cliente.session_transaction() as sessao:
        sessao["usuario_id"] = 4
        sessao["usuario_nome"] = "Operador"
        sessao["usuario_login"] = "operador"
        sessao["usuario_perfil"] = "operador"
        sessao["usuario_empresa_id"] = 1

    resp = cliente.get("/api/backup")
    assert resp.status_code == 403


def test_troca_empresa_multi_cnpj_atualiza_nome_estacionamento():
    """Valida se ao trocar de empresa no Multi-CNPJ o nome do respectivo estacionamento e refletido na sessao e configuracao."""
    cliente = app.test_client()
    with cliente.session_transaction() as sessao:
        sessao["usuario_id"] = 1
        sessao["usuario_nome"] = "Administrador"
        sessao["usuario_login"] = "admin"
        sessao["usuario_perfil"] = "admin"
        sessao["usuario_master"] = True
        sessao["empresa_id"] = 1

    # Troca para empresa 2 (Centro Park)
    resp_troca = cliente.post("/api/empresa/trocar", json={"empresa_id": 2})
    assert resp_troca.status_code == 200
    assert "Centro Park" in resp_troca.get_json()["mensagem"]

    # Sessao deve conter a nova empresa com seu nome fantasia
    resp_sessao = cliente.get("/api/sessao")
    assert resp_sessao.status_code == 200
    dados_sessao = resp_sessao.get_json()
    assert dados_sessao["usuario"]["empresa"]["nome_fantasia"] == "Centro Park"

    # Configuracao e Status devem refletir o nome do estacionamento da empresa
    resp_cfg = cliente.get("/api/configuracoes")
    assert resp_cfg.status_code == 200
    assert resp_cfg.get_json()["nome_estacionamento"] == "Centro Park"

    resp_status = cliente.get("/api/status")
    assert resp_status.status_code == 200
    assert resp_status.get_json()["nome_estacionamento"] == "Centro Park"

    # Restaura para empresa 1
    cliente.post("/api/empresa/trocar", json={"empresa_id": 1})


def test_inativar_empresa_atualiza_apenas_empresa_selecionada():
    empresa = Empresa(
        id=17,
        cnpj="12345678000190",
        razao_social="Empresa duplicada",
        nome_fantasia="Empresa duplicada",
    )
    service = EmpresaService.__new__(EmpresaService)
    service._registros = [empresa]
    supabase = Mock()
    tabela = Mock()
    supabase.table.return_value = tabela
    tabela.update.return_value = tabela
    tabela.eq.return_value = tabela

    with patch.object(empresa_service_module, "supabase", supabase):
        assert service.inativar(17) is True

    supabase.table.assert_called_once_with("empresas")
    tabela.update.assert_called_once_with({"ativo": False})
    tabela.eq.assert_called_once_with("id", 17)
    assert empresa.ativo is False


def test_inativar_empresa_preserva_estado_se_banco_falhar():
    empresa = Empresa(
        id=18,
        cnpj="12345678000190",
        razao_social="Empresa duplicada",
        nome_fantasia="Empresa duplicada",
    )
    service = EmpresaService.__new__(EmpresaService)
    service._registros = [empresa]
    supabase = Mock()
    supabase.table.return_value.update.return_value.eq.return_value.execute.side_effect = RuntimeError(
        "database unavailable"
    )

    with patch.object(empresa_service_module, "supabase", supabase):
        try:
            service.inativar(18)
        except ValueError as erro:
            assert "Nao foi possivel inativar" in str(erro)
        else:
            raise AssertionError("A falha ao salvar deveria ser reportada.")

    assert empresa.ativo is True
