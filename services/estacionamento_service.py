"""
Servico principal do estacionamento.

Contem toda a regra de negocio: emissao de tickets, registro de saida,
calculo de valores, controle de vagas e geracao de relatorios.
"""

from datetime import datetime
from typing import List, Optional, Tuple

from models.ticket import Ticket
from models.configuracao import Configuracao
from services.persistencia_service import PersistenciaService

FORMATO_DATA = "%d/%m/%Y %H:%M:%S"


class EstacionamentoService:
    """Regras de negocio do estacionamento."""

    def __init__(self):
        self.persistencia = PersistenciaService()
        self.tickets: List[Ticket] = self.persistencia.carregar_tickets()
        self.config: Configuracao = self.persistencia.carregar_configuracao()

    # ---------------------- ENTRADA ----------------------

    def registrar_entrada(
        self,
        placa: str,
        tipo_veiculo: str = "Carro",
        observacoes: str = "",
    ) -> Optional[Ticket]:
        """
        Registra a entrada de um veiculo, emitindo um novo ticket.
        Retorna None se nao houver vagas disponiveis.
        """
        placa = placa.strip().upper()

        # Verifica se ja existe um ticket aberto para essa placa
        if self._buscar_ticket_aberto_por_placa(placa) is not None:
            raise ValueError(f"O veiculo de placa {placa} ja esta no estacionamento.")

        vagas_livres = self.vagas_livres()
        if vagas_livres <= 0:
            return None  # Estacionamento cheio

        vaga_numero = self._proxima_vaga_disponivel()

        ticket = Ticket(
            numero=self.config.proximo_numero_ticket,
            placa=placa,
            entrada=datetime.now().strftime(FORMATO_DATA),
            vaga=vaga_numero,
            status="ABERTO",
            tipo_veiculo=(tipo_veiculo or "Carro").strip() or "Carro",
            observacoes=(observacoes or "").strip(),
        )

        self.tickets.append(ticket)
        self.config.proximo_numero_ticket += 1

        self._salvar_tudo()
        return ticket

    # ---------------------- SAIDA ----------------------

    def registrar_saida(self, identificador: str) -> Optional[Ticket]:
        """
        Registra a saida de um veiculo, calculando o valor a pagar.
        O identificador pode ser o numero do ticket ou a placa do veiculo.
        Retorna o ticket atualizado, ou None se nao for encontrado.
        """
        ticket = self._buscar_ticket_aberto(identificador)
        if ticket is None:
            return None

        agora = datetime.now()
        ticket.saida = agora.strftime(FORMATO_DATA)
        ticket.valor = self.calcular_valor(ticket.entrada, ticket.saida)
        ticket.status = "FECHADO"

        self._salvar_tudo()
        return ticket

    def calcular_valor(self, entrada_str: str, saida_str: str) -> float:
        """
        Calcula o valor a ser pago com base no tempo de permanencia.
        Regra: primeira hora (ou fracao) custa 'valor_primeira_hora';
        cada hora adicional (ou fracao) custa 'valor_hora_adicional'.
        """
        entrada = datetime.strptime(entrada_str, FORMATO_DATA)
        saida = datetime.strptime(saida_str, FORMATO_DATA)

        segundos_totais = (saida - entrada).total_seconds()
        if segundos_totais <= 0:
            segundos_totais = 1  # Evita valor negativo/zero por relogio igual

        horas_totais = segundos_totais / 3600

        # Primeira hora sempre e cobrada (mesmo que o veiculo fique poucos minutos)
        if horas_totais <= 1:
            return round(self.config.valor_primeira_hora, 2)

        # Horas adicionais: qualquer fracao de hora conta como uma hora cheia
        horas_adicionais = horas_totais - 1
        horas_adicionais_cobradas = self._arredondar_para_cima(horas_adicionais)

        valor = self.config.valor_primeira_hora + (horas_adicionais_cobradas * self.config.valor_hora_adicional)
        return round(valor, 2)

    @staticmethod
    def _arredondar_para_cima(valor: float) -> int:
        """Arredonda um numero fracionario para o proximo inteiro (fracao de hora conta como hora cheia)."""
        inteiro = int(valor)
        if valor > inteiro:
            return inteiro + 1
        return inteiro

    # ---------------------- CONTROLE DE VAGAS ----------------------

    def vagas_ocupadas(self) -> int:
        """Retorna a quantidade de vagas atualmente ocupadas."""
        return len([t for t in self.tickets if t.status == "ABERTO"])

    def vagas_livres(self) -> int:
        """Retorna a quantidade de vagas livres no momento."""
        return self.config.total_vagas - self.vagas_ocupadas()

    def _proxima_vaga_disponivel(self) -> int:
        """Encontra o menor numero de vaga livre entre 1 e total_vagas."""
        vagas_ocupadas = {t.vaga for t in self.tickets if t.status == "ABERTO"}
        for numero in range(1, self.config.total_vagas + 1):
            if numero not in vagas_ocupadas:
                return numero
        raise RuntimeError("Nao ha vagas disponiveis.")

    # ---------------------- CONSULTAS ----------------------

    def _buscar_ticket_aberto_por_placa(self, placa: str) -> Optional[Ticket]:
        """Busca um ticket aberto (veiculo ainda estacionado) pela placa."""
        placa = placa.strip().upper()
        for ticket in self.tickets:
            if ticket.placa == placa and ticket.status == "ABERTO":
                return ticket
        return None

    def _buscar_ticket_aberto(self, identificador: str) -> Optional[Ticket]:
        """
        Busca um ticket aberto pelo numero do ticket ou pela placa.
        Aceita tanto numero (ex: '3') quanto placa (ex: 'ABC1234').
        """
        identificador = identificador.strip().upper()

        # Tenta interpretar como numero de ticket
        if identificador.isdigit():
            numero = int(identificador)
            for ticket in self.tickets:
                if ticket.numero == numero and ticket.status == "ABERTO":
                    return ticket

        # Tenta interpretar como placa
        return self._buscar_ticket_aberto_por_placa(identificador)

    def listar_tickets_abertos(self) -> List[Ticket]:
        """Retorna a lista de veiculos atualmente estacionados."""
        return [t for t in self.tickets if t.status == "ABERTO"]

    def listar_todos_tickets(self) -> List[Ticket]:
        """Retorna todos os tickets (abertos e fechados)."""
        return self.tickets

    def listar_tickets_fechados(self) -> List[Ticket]:
        """Retorna a lista de veiculos que ja sairam (historico), mais recentes primeiro."""
        fechados = [t for t in self.tickets if t.status == "FECHADO"]
        return sorted(fechados, key=lambda t: t.numero, reverse=True)

    def buscar_tickets(self, termo: str) -> List[Ticket]:
        """Busca tickets (abertos e fechados) pela placa ou pelo numero do ticket."""
        termo = (termo or "").strip().upper()
        if not termo:
            return list(self.tickets)

        resultado = []
        for ticket in self.tickets:
            if termo in ticket.placa or termo in str(ticket.numero):
                resultado.append(ticket)
        return resultado

    # ---------------------- RELATORIOS ----------------------

    def relatorio_movimentacao(self, data: Optional[str] = None) -> dict:
        """
        Gera um relatorio de movimentacao do estacionamento.
        Se 'data' for informada (formato dd/mm/yyyy), filtra apenas esse dia;
        caso contrario, considera todos os registros.
        """
        entradas = []
        saidas = []
        faturamento_total = 0.0

        for ticket in self.tickets:
            data_entrada = ticket.entrada.split(" ")[0]
            if data is None or data_entrada == data:
                entradas.append(ticket)

            if ticket.saida:
                data_saida = ticket.saida.split(" ")[0]
                if data is None or data_saida == data:
                    saidas.append(ticket)
                    if ticket.valor:
                        faturamento_total += ticket.valor

        return {
            "total_entradas": len(entradas),
            "total_saidas": len(saidas),
            "faturamento_total": round(faturamento_total, 2),
            "veiculos_entrada": entradas,
            "veiculos_saida": saidas,
        }

    # ---------------------- DASHBOARD (RESUMO DO DIA) ----------------------

    def resumo_dashboard(self) -> dict:
        """
        Gera o resumo exibido nos cards do topo do dashboard:
        veiculos no patio agora, faturamento de hoje, saidas de hoje
        e permanencia media (baseada nos veiculos que ja sairam hoje).
        """
        hoje = datetime.now().strftime("%d/%m/%Y")

        faturamento_hoje = 0.0
        saidas_hoje = 0
        duracoes_segundos = []

        for ticket in self.tickets:
            if ticket.saida and ticket.saida.split(" ")[0] == hoje:
                saidas_hoje += 1
                if ticket.valor:
                    faturamento_hoje += ticket.valor

                entrada = datetime.strptime(ticket.entrada, FORMATO_DATA)
                saida = datetime.strptime(ticket.saida, FORMATO_DATA)
                duracoes_segundos.append((saida - entrada).total_seconds())

        permanencia_media_min = None
        if duracoes_segundos:
            media_segundos = sum(duracoes_segundos) / len(duracoes_segundos)
            permanencia_media_min = round(media_segundos / 60)

        return {
            "no_patio_agora": self.vagas_ocupadas(),
            "faturamento_hoje": round(faturamento_hoje, 2),
            "saidas_hoje": saidas_hoje,
            "permanencia_media_minutos": permanencia_media_min,
        }

    # ---------------------- CONFIGURACAO ----------------------

    def atualizar_configuracao(
        self,
        total_vagas: Optional[int] = None,
        valor_primeira_hora: Optional[float] = None,
        valor_hora_adicional: Optional[float] = None,
        valor_mensal: Optional[float] = None,
    ) -> Configuracao:
        """Atualiza os parametros de configuracao do estacionamento."""
        if total_vagas is not None:
            self.config.total_vagas = total_vagas
        if valor_primeira_hora is not None:
            self.config.valor_primeira_hora = valor_primeira_hora
        if valor_hora_adicional is not None:
            self.config.valor_hora_adicional = valor_hora_adicional
        if valor_mensal is not None:
            self.config.valor_mensal = valor_mensal

        self.persistencia.salvar_configuracao(self.config)
        return self.config

    # ---------------------- PERSISTENCIA INTERNA ----------------------

    def _salvar_tudo(self) -> None:
        """Salva tickets e configuracao em disco."""
        self.persistencia.salvar_tickets(self.tickets)
        self.persistencia.salvar_configuracao(self.config)
