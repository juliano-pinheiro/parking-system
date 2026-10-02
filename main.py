"""
Sistema de Estacionamento - Controle por Ticket
=================================================

Ponto de entrada da aplicacao. Apresenta um menu interativo via terminal
para o operador do estacionamento realizar entrada/saida de veiculos,
consultar vagas, gerar relatorios e configurar precos.

Para executar:
    python main.py
"""

import os
import sys

from services.estacionamento_service import EstacionamentoService
from models.ticket import Ticket


def limpar_tela():
    """Limpa a tela do terminal (compatível com Windows e Linux/Mac)."""
    os.system("cls" if os.name == "nt" else "clear")


def pausar():
    """Pausa a execucao ate o usuario apertar ENTER."""
    input("\nPressione ENTER para continuar...")


def exibir_cabecalho(titulo: str):
    """Exibe um cabecalho padronizado para cada tela do menu."""
    print("=" * 50)
    print(f" {titulo}")
    print("=" * 50)


def exibir_ticket(ticket: Ticket):
    """Exibe os dados de um ticket de forma formatada."""
    print(f"  Ticket numero : {ticket.numero}")
    print(f"  Placa         : {ticket.placa}")
    print(f"  Vaga          : {ticket.vaga}")
    print(f"  Entrada       : {ticket.entrada}")
    if ticket.saida:
        print(f"  Saida         : {ticket.saida}")
    if ticket.valor is not None:
        print(f"  Valor a pagar : R$ {ticket.valor:.2f}")
    print(f"  Status        : {ticket.status}")


def menu_registrar_entrada(servico: EstacionamentoService):
    """Tela para registrar a entrada de um veiculo (emissao de ticket)."""
    limpar_tela()
    exibir_cabecalho("REGISTRAR ENTRADA DE VEICULO")

    print(f"Vagas livres: {servico.vagas_livres()} / {servico.config.total_vagas}\n")

    placa = input("Digite a placa do veiculo: ").strip().upper()
    if not placa:
        print("\nPlaca invalida.")
        pausar()
        return

    print("\nTipo de veiculo:")
    print("  1 - Carro (padrao)")
    print("  2 - Moto")
    print("  3 - Caminhonete")
    print("  4 - Carro Grande")
    opcao_tipo = input("Escolha o tipo [1]: ").strip()
    mapa_tipos = {"1": "Carro", "2": "Moto", "3": "Caminhonete", "4": "Carro Grande"}
    tipo_veiculo = mapa_tipos.get(opcao_tipo, "Carro")

    observacoes = input("\nObservacoes (ex: cor, modelo) [opcional]: ").strip()

    try:
        ticket = servico.registrar_entrada(placa, tipo_veiculo=tipo_veiculo, observacoes=observacoes)
    except ValueError as erro:
        print(f"\nErro: {erro}")
        pausar()
        return

    if ticket is None:
        print("\nNao ha vagas disponiveis no momento. Estacionamento cheio!")
    else:
        print("\nTicket emitido com sucesso!\n")
        exibir_ticket(ticket)

    pausar()


def menu_registrar_saida(servico: EstacionamentoService):
    """Tela para registrar a saida de um veiculo (calculo do valor)."""
    limpar_tela()
    exibir_cabecalho("REGISTRAR SAIDA DE VEICULO")

    identificador = input("Digite o numero do ticket ou a placa do veiculo: ").strip()
    if not identificador:
        print("\nDado invalido.")
        pausar()
        return

    print("\nForma de pagamento:")
    print("  1 - Dinheiro")
    print("  2 - Pix")
    print("  3 - Cartao de Credito")
    print("  4 - Cartao de Debito")
    opcao_forma = input("Escolha a forma de pagamento [1]: ").strip()
    mapa_formas = {
        "1": "dinheiro",
        "2": "pix",
        "3": "cartao_credito",
        "4": "cartao_debito",
    }
    forma_pagamento = mapa_formas.get(opcao_forma, "dinheiro")

    ticket = servico.registrar_saida(identificador, forma_pagamento)

    if ticket is None:
        print("\nNenhum veiculo encontrado com esse ticket/placa (ou ja saiu).")
    else:
        print("\nSaida registrada com sucesso!\n")
        exibir_ticket(ticket)

        # Integra com pagamentos/caixa/financeiro se disponivel
        try:
            from services_registry import servico_pagamentos
            servico_pagamentos.registrar_pagamento_ticket(
                ticket, forma_pagamento=forma_pagamento, operador="terminal"
            )
        except Exception:
            pass

    pausar()


def menu_controle_vagas(servico: EstacionamentoService):
    """Tela que exibe o controle de vagas do estacionamento."""
    limpar_tela()
    exibir_cabecalho("CONTROLE DE VAGAS")

    total = servico.config.total_vagas
    ocupadas = servico.vagas_ocupadas()
    livres = servico.vagas_livres()

    print(f"  Total de vagas   : {total}")
    print(f"  Vagas ocupadas   : {ocupadas}")
    print(f"  Vagas livres     : {livres}")

    veiculos = servico.listar_tickets_abertos()
    if veiculos:
        print("\n  Veiculos estacionados agora:")
        print("  " + "-" * 46)
        for ticket in sorted(veiculos, key=lambda t: t.vaga):
            print(f"  Vaga {ticket.vaga:>3} | Ticket {ticket.numero:>4} | Placa {ticket.placa} | Entrada {ticket.entrada}")
    else:
        print("\n  Nenhum veiculo estacionado no momento.")

    pausar()


def menu_relatorio(servico: EstacionamentoService):
    """Tela de relatorio de movimentacao (entradas, saidas e faturamento)."""
    limpar_tela()
    exibir_cabecalho("RELATORIO DE MOVIMENTACAO")

    print("Deixe em branco para ver o relatorio completo (todos os dias).")
    data = input("Filtrar por data (dd/mm/aaaa) ou ENTER: ").strip()
    data = data if data else None

    relatorio = servico.relatorio_movimentacao(data)

    print("\n" + "-" * 50)
    print(f"  Total de entradas : {relatorio['total_entradas']}")
    print(f"  Total de saidas   : {relatorio['total_saidas']}")
    print(f"  Faturamento total : R$ {relatorio['faturamento_total']:.2f}")
    print("-" * 50)

    if relatorio["veiculos_entrada"]:
        print("\n  Veiculos que entraram:")
        for ticket in relatorio["veiculos_entrada"]:
            print(f"   - Ticket {ticket.numero} | Placa {ticket.placa} | Entrada {ticket.entrada}")

    if relatorio["veiculos_saida"]:
        print("\n  Veiculos que sairam:")
        for ticket in relatorio["veiculos_saida"]:
            valor = f"R$ {ticket.valor:.2f}" if ticket.valor is not None else "-"
            print(f"   - Ticket {ticket.numero} | Placa {ticket.placa} | Saida {ticket.saida} | Valor {valor}")

    pausar()


def menu_configuracoes(servico: EstacionamentoService):
    """Tela para configurar a tabela de precos e o total de vagas."""
    limpar_tela()
    exibir_cabecalho("CONFIGURACOES DO ESTACIONAMENTO")

    config = servico.config
    print(f"  1. Total de vagas atual         : {config.total_vagas}")
    print(f"  2. Valor da primeira hora atual : R$ {config.valor_primeira_hora:.2f}")
    print(f"  3. Valor da hora adicional atual : R$ {config.valor_hora_adicional:.2f}")
    print("\nDeixe em branco em qualquer campo para manter o valor atual.\n")

    entrada_vagas = input(f"Novo total de vagas [{config.total_vagas}]: ").strip()
    entrada_primeira_hora = input(f"Novo valor da primeira hora [{config.valor_primeira_hora}]: ").strip()
    entrada_hora_adicional = input(f"Novo valor da hora adicional [{config.valor_hora_adicional}]: ").strip()

    novo_total_vagas = None
    novo_valor_primeira_hora = None
    novo_valor_hora_adicional = None

    try:
        if entrada_vagas:
            novo_total_vagas = int(entrada_vagas)
        if entrada_primeira_hora:
            novo_valor_primeira_hora = float(entrada_primeira_hora.replace(",", "."))
        if entrada_hora_adicional:
            novo_valor_hora_adicional = float(entrada_hora_adicional.replace(",", "."))
    except ValueError:
        print("\nValor invalido informado. Nenhuma alteracao foi salva.")
        pausar()
        return

    # Impede reduzir o total de vagas para um numero menor que as vagas ja ocupadas
    if novo_total_vagas is not None and novo_total_vagas < servico.vagas_ocupadas():
        print(f"\nNao e possivel definir {novo_total_vagas} vagas: ja existem {servico.vagas_ocupadas()} veiculos estacionados.")
        pausar()
        return

    servico.atualizar_configuracao(
        total_vagas=novo_total_vagas,
        valor_primeira_hora=novo_valor_primeira_hora,
        valor_hora_adicional=novo_valor_hora_adicional,
    )

    print("\nConfiguracoes atualizadas com sucesso!")
    pausar()


def exibir_menu_principal(servico: EstacionamentoService):
    """Exibe o menu principal do sistema."""
    limpar_tela()
    exibir_cabecalho("SISTEMA DE ESTACIONAMENTO - MENU PRINCIPAL")
    print(f"  Vagas livres: {servico.vagas_livres()} / {servico.config.total_vagas}\n")
    print("  1 - Registrar entrada de veiculo (emitir ticket)")
    print("  2 - Registrar saida de veiculo (calcular valor)")
    print("  3 - Controle de vagas")
    print("  4 - Relatorio de movimentacao")
    print("  5 - Configuracoes (precos e vagas)")
    print("  0 - Sair")
    print("=" * 50)


def main():
    """Funcao principal: inicializa o servico e roda o loop do menu."""
    try:
        from services_registry import servico as servico_compartilhado
        servico = servico_compartilhado
    except Exception:
        servico = EstacionamentoService()

    opcoes = {
        "1": menu_registrar_entrada,
        "2": menu_registrar_saida,
        "3": menu_controle_vagas,
        "4": menu_relatorio,
        "5": menu_configuracoes,
    }

    while True:
        exibir_menu_principal(servico)
        opcao = input("Escolha uma opcao: ").strip()

        if opcao == "0":
            print("\nEncerrando o sistema. Ate logo!")
            sys.exit(0)

        funcao = opcoes.get(opcao)
        if funcao:
            funcao(servico)
        else:
            print("\nOpcao invalida.")
            pausar()


if __name__ == "__main__":
    main()
