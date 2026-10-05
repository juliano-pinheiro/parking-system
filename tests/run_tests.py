"""
Script executor de testes nativo (Python unittest) sem depender de bibliotecas externas instaladas globalmente.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from tests.test_routes import *
from tests.test_fluxos_principais import *
from tests.test_caixa_otimizado import *
from tests.test_permissoes_detalhadas import *
from tests.test_configuracoes_revisadas import *
from tests.test_relatorio_pagamentos import *
from tests.test_persistencia_service import *

class TestSistemaEstacionamento(unittest.TestCase):

    def test_routes_publicas_respondem(self):
        test_rotas_publicas_respondem()

    def test_routes_protegidas_exigem_sessao(self):
        test_rotas_protegidas_exigem_sessao()

    def test_pagina_raiz(self):
        test_pagina_raiz_redireciona_para_login()

    def test_pagina_login(self):
        test_pagina_login_carrega_template()

    def test_login_invalido(self):
        test_login_invalido_retorna_401()

    def test_logout(self):
        test_logout_retorna_200()

    def test_senha_pbkdf2(self):
        test_senha_pbkdf2_e_compatibilidade_legado()

    def test_tabela_precos_tolerancia(self):
        test_tabela_precos_calculo_tolerancia()

    def test_filtro_periodo_data(self):
        test_filtro_periodo_data_financeiro()

    def test_parse_competencia(self):
        test_parse_competencia_mensalistas()

    def test_mensalista_buscar_placa(self):
        test_mensalista_buscar_por_placa()

    def test_dashboard_resumo_e_capacidade_patio(self):
        test_dashboard_resumo_e_capacidade_patio()

    def test_dashboard_financeiro_indicadores_completos(self):
        test_dashboard_financeiro_indicadores_completos()

    def test_operacao_patio_calculo_previa_e_ticket_perdido_libera_vaga(self):
        test_operacao_patio_calculo_previa_e_ticket_perdido_libera_vaga()

    def test_info_acesso_mobile_endpoint(self):
        test_info_acesso_mobile_endpoint()

    def test_totais_caixa_sangria_suprimento_estorno(self):
        test_totais_caixa_com_sangria_suprimento_e_estorno()

    def test_estorno_caixa(self):
        test_registro_estorno_caixa()

    def test_api_movimentacoes_caixa_endpoint(self):
        test_api_movimentacoes_caixa_endpoint()

    def test_bloqueio_emissao_ticket_sem_caixa_aberto(self):
        test_bloqueio_emissao_ticket_sem_caixa_aberto()

    def test_catalogo_modulos_e_categorias_rbac(self):
        test_catalogo_modulos_e_categorias()

    def test_bloqueio_e_liberacao_modulo_rbac(self):
        test_bloqueio_e_liberacao_modulo()

    def test_clonagem_perfil_com_permissoes_rbac(self):
        test_clonagem_perfil_com_permissoes()

    def test_api_permissoes_retorna_catalogo_rbac(self):
        test_api_permissoes_retorna_catalogo()

    def test_atualizacao_configuracao_novos_campos_revisados(self):
        test_atualizacao_configuracao_novos_campos()

    def test_api_configuracoes_post_e_get_revisados(self):
        test_api_configuracoes_post_e_get()

    def test_validacao_vagas_menor_que_ocupadas_revisados(self):
        test_validacao_vagas_menor_que_ocupadas()

    def test_exportacao_backup_endpoint_revisados(self):
        test_exportacao_backup_endpoint()

    def test_exportacao_backup_exige_permissao_de_edicao(self):
        test_exportacao_backup_exige_permissao_de_edicao()

    def test_criar_ticket_individual_nao_usa_upsert(self):
        test_criar_ticket_individual_nao_usa_upsert()

    def test_salvar_configuracao_persiste_preferencias_do_ticket(self):
        test_salvar_configuracao_persiste_preferencias_do_ticket()

    def test_operador_acesso_visao_geral_e_status(self):
        test_operador_acesso_visao_geral_e_status()

    def test_troca_empresa_multi_cnpj_atualiza_nome_estacionamento(self):
        test_troca_empresa_multi_cnpj_atualiza_nome_estacionamento()

    def test_inativar_empresa_atualiza_apenas_empresa_selecionada(self):
        test_inativar_empresa_atualiza_apenas_empresa_selecionada()

    def test_inativar_empresa_preserva_estado_se_banco_falhar(self):
        test_inativar_empresa_preserva_estado_se_banco_falhar()

    def test_relatorio_pagamentos_estrutura(self):
        test_relatorio_pagamentos_estrutura()

    def test_relatorio_pagamentos_filtro_forma(self):
        test_relatorio_pagamentos_filtro_forma()

    def test_relatorio_pagamentos_filtro_periodo(self):
        test_relatorio_pagamentos_filtro_periodo()

    def test_relatorio_pagamentos_exportar_csv(self):
        test_relatorio_pagamentos_exportar_csv()

    def test_relatorio_pagamentos_protecao_autenticacao(self):
        test_relatorio_pagamentos_protecao_autenticacao()


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSistemaEstacionamento)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
