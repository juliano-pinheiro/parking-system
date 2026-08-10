"""
Servico de persistencia de dados.

Configuracao e tickets sao armazenados no Supabase.
Clientes e usuarios continuam em JSON nesta etapa da migracao.
"""

import json
import os
from typing import List

from models.ticket import Ticket
from models.configuracao import Configuracao
from supabase_client import supabase


PASTA_DADOS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data"
)

ARQUIVO_CLIENTES = os.path.join(PASTA_DADOS, "clientes.json")
ARQUIVO_USUARIOS = os.path.join(PASTA_DADOS, "usuarios.json")


class PersistenciaService:
    """Cuida da persistencia dos dados."""

    def __init__(self):
        os.makedirs(PASTA_DADOS, exist_ok=True)

    # =====================================================
    # TICKETS - SUPABASE
    # =====================================================

    def carregar_tickets(self) -> List[Ticket]:
        """Carrega todos os tickets do Supabase."""

        resposta = (
            supabase
            .table("tickets")
            .select("*")
            .order("numero")
            .execute()
        )

        return [
            Ticket.from_dict(item)
            for item in resposta.data
        ]

    def salvar_tickets(self, tickets: List[Ticket]) -> None:
        """
        Sincroniza os tickets com o Supabase.

        Nesta primeira etapa, remove os registros atuais
        e grava novamente a lista completa.
        """

        # Remove os tickets existentes
        supabase.table("tickets").delete().neq("numero", -1).execute()

        # Se nao houver tickets, encerra
        if not tickets:
            return

        dados = []

        for ticket in tickets:
            dados.append({
                "numero": ticket.numero,
                "placa": ticket.placa,
                "entrada": self._converter_data(ticket.entrada),
                "saida": self._converter_data(ticket.saida),
                "valor": ticket.valor,
                "vaga": ticket.vaga,
                "status": ticket.status,
                "tipo_veiculo": ticket.tipo_veiculo,
                "observacoes": ticket.observacoes,
            })

        supabase.table("tickets").insert(dados).execute()

    # =====================================================
    # CONFIGURACAO - SUPABASE
    # =====================================================

    def carregar_configuracao(self) -> Configuracao:
        """Carrega a configuracao do Supabase."""

        resposta = (
            supabase
            .table("configuracao")
            .select("*")
            .eq("id", 1)
            .single()
            .execute()
        )

        if not resposta.data:
            raise RuntimeError(
                "Configuracao do estacionamento nao encontrada no Supabase."
            )

        return Configuracao.from_dict(resposta.data)

    def salvar_configuracao(self, config: Configuracao) -> None:
        """Salva a configuracao no Supabase."""

        dados = {
            "total_vagas": config.total_vagas,
            "valor_primeira_hora": config.valor_primeira_hora,
            "valor_hora_adicional": config.valor_hora_adicional,
            "valor_mensal": config.valor_mensal,
            "proximo_numero_ticket": config.proximo_numero_ticket,
        }

        (
            supabase
            .table("configuracao")
            .update(dados)
            .eq("id", 1)
            .execute()
        )

    # =====================================================
    # CONVERSAO DE DATAS
    # =====================================================

    @staticmethod
    def _converter_data(data: str | None) -> str | None:
        """
        Converte a data usada pelo sistema:
        DD/MM/YYYY HH:MM:SS

        para o formato aceito pelo PostgreSQL:
        YYYY-MM-DD HH:MM:SS
        """

        if not data:
            return None

        from datetime import datetime

        data_obj = datetime.strptime(
            data,
            "%d/%m/%Y %H:%M:%S"
        )

        return data_obj.strftime(
            "%Y-%m-%d %H:%M:%S"
        )