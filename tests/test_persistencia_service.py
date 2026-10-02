from unittest.mock import Mock, patch

import services.persistencia_service as persistencia_module
from models.configuracao import Configuracao
from models.ticket import Ticket
from services.persistencia_service import PersistenciaService


def test_criar_ticket_individual_nao_usa_upsert():
    supabase = Mock()
    tabela = Mock()
    supabase.table.return_value = tabela
    tabela.insert.return_value = tabela

    ticket = Ticket(numero=123, placa="ABC1234", entrada="01/10/2026 10:00:00")
    with patch.object(persistencia_module, "supabase", supabase):
        PersistenciaService.__new__(PersistenciaService).criar_ticket_individual(ticket)

    tabela.insert.assert_called_once()
    tabela.upsert.assert_not_called()


def test_salvar_configuracao_persiste_preferencias_do_ticket():
    supabase = Mock()
    tabela = Mock()
    supabase.table.return_value = tabela
    tabela.update.return_value = tabela
    tabela.eq.return_value = tabela

    config = Configuracao(
        id=1,
        ticket_exibir_cnpj=False,
        ticket_exibir_contato=False,
        ticket_formato_papel="58mm",
        ticket_exibir_codigo_barras=False,
    )
    with patch.object(persistencia_module, "supabase", supabase):
        PersistenciaService.__new__(PersistenciaService).salvar_configuracao(config)

    dados = tabela.update.call_args.args[0]
    assert dados["ticket_exibir_cnpj"] is False
    assert dados["ticket_exibir_contato"] is False
    assert dados["ticket_formato_papel"] == "58mm"
    assert dados["ticket_exibir_codigo_barras"] is False
