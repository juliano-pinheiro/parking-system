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

    def carregar_tickets(self, empresa_id: int | None = None) -> List[Ticket]:
        """Carrega os tickets do Supabase, filtrados pela empresa quando informado."""

        query = (
            supabase
            .table("tickets")
            .select("*")
            .order("numero")
        )
        if empresa_id is not None:
            query = query.eq("empresa_id", empresa_id)

        resposta = query.execute()

        tickets = []
        for item in resposta.data:
            item = dict(item)
            item["entrada"] = self._converter_data_iso_para_interna(item.get("entrada"))
            item["saida"] = self._converter_data_iso_para_interna(item.get("saida"))
            tickets.append(Ticket.from_dict(item))

        return tickets

    def _ticket_para_dados(self, ticket: Ticket, empresa_id: int | None = None) -> dict:
        """Converte um objeto Ticket em dicionario para o Supabase."""
        return {
            "numero": ticket.numero,
            "placa": ticket.placa,
            "entrada": self._converter_data(ticket.entrada),
            "saida": self._converter_data(ticket.saida),
            "valor": ticket.valor,
            "vaga": ticket.vaga,
            "status": ticket.status,
            "tipo_veiculo": ticket.tipo_veiculo,
            "observacoes": ticket.observacoes,
            "forma_pagamento": ticket.forma_pagamento,
            "empresa_id": empresa_id if empresa_id is not None else ticket.empresa_id,
        }

    def salvar_ticket_individual(self, ticket: Ticket, empresa_id: int | None = None) -> None:
        """Salva ou atualiza um unico ticket no Supabase (sem apagar os demais)."""
        dados = self._ticket_para_dados(ticket, empresa_id)
        try:
            supabase.table("tickets").upsert(dados, on_conflict="numero").execute()
        except Exception as erro:
            texto = str(erro)
            coluna_ausente = "PGRST204" in texto or "42703" in texto or "does not exist" in texto
            if coluna_ausente and "forma_pagamento" in dados:
                dados.pop("forma_pagamento", None)
                supabase.table("tickets").upsert(dados, on_conflict="numero").execute()
            else:
                raise

    def criar_ticket_individual(self, ticket: Ticket, empresa_id: int | None = None) -> None:
        """Insere um ticket sem sobrescrever outro com o mesmo numero."""
        dados = self._ticket_para_dados(ticket, empresa_id)
        try:
            supabase.table("tickets").insert(dados).execute()
        except Exception as erro:
            texto = str(erro)
            coluna_ausente = "PGRST204" in texto or "42703" in texto or "does not exist" in texto
            if coluna_ausente and "forma_pagamento" in dados:
                dados.pop("forma_pagamento", None)
                supabase.table("tickets").insert(dados).execute()
            else:
                raise

    def salvar_tickets(self, tickets: List[Ticket], empresa_id: int | None = None) -> None:
        """
        Sincroniza os tickets da empresa atual com o Supabase usando upsert.
        Nunca remove os dados fisicamente para evitar perda de dados.
        """
        if not tickets:
            return

        dados = [self._ticket_para_dados(t, empresa_id) for t in tickets]

        try:
            supabase.table("tickets").upsert(dados, on_conflict="numero").execute()
        except Exception as erro:
            texto = str(erro)
            coluna_ausente = (
                "PGRST204" in texto
                or "42703" in texto
                or "does not exist" in texto
            )
            if coluna_ausente and any("forma_pagamento" in item for item in dados):
                for item in dados:
                    item.pop("forma_pagamento", None)
                supabase.table("tickets").upsert(dados, on_conflict="numero").execute()
            else:
                raise

    def proximo_numero_global(self) -> int:
        """Proximo numero de ticket unico (evita conflito de PK entre empresas)."""
        try:
            resposta = (
                supabase
                .table("tickets")
                .select("numero")
                .order("numero", desc=True)
                .limit(1)
                .execute()
            )
            if resposta.data:
                return int(resposta.data[0]["numero"]) + 1
        except Exception:
            pass
        return 1

    # =====================================================
    # CONFIGURACAO - SUPABASE
    # =====================================================

    def carregar_configuracao(self, empresa_id: int | None = None) -> Configuracao:
        """Carrega a configuracao do estacionamento da empresa."""

        query = supabase.table("configuracao").select("*")
        if empresa_id is not None:
            query = query.eq("empresa_id", empresa_id)
        else:
            query = query.eq("id", 1)

        resposta = query.limit(1).execute()
        linhas = resposta.data or []
        if not linhas:
            return self.garantir_configuracao(empresa_id)

        return Configuracao.from_dict(linhas[0] if isinstance(linhas, list) else linhas)

    def garantir_configuracao(
        self,
        empresa_id: int | None = None,
        nome_estacionamento: str = "Estaciona Parking",
        cnpj: str = "",
    ) -> Configuracao:
        """Garante uma configuracao para a empresa, criando se nao existir."""
        if empresa_id is not None:
            existente = (
                supabase
                .table("configuracao")
                .select("*")
                .eq("empresa_id", empresa_id)
                .limit(1)
                .execute()
            )
            if existente.data:
                return Configuracao.from_dict(existente.data[0])

        dados = {
            "nome_estacionamento": nome_estacionamento or "Estaciona Parking",
            "cnpj": cnpj or "",
            "total_vagas": 20,
            "valor_primeira_hora": 5.0,
            "valor_hora_adicional": 3.0,
            "valor_mensal": 150.0,
            "bloquear_sem_vaga": False,
            "exigir_observacao": True,
            "proximo_numero_ticket": 1,
        }
        if empresa_id is not None:
            dados["empresa_id"] = empresa_id

        try:
            inserido = supabase.table("configuracao").insert(dados).execute()
        except Exception as erro:
            texto = str(erro)
            if "23505" in texto or "duplicate key" in texto:
                # Sequencia do id desatualizada (registros importados com id
                # explicito): calcula o proximo id e insere de forma explicita.
                ultimo = (
                    supabase
                    .table("configuracao")
                    .select("id")
                    .order("id", desc=True)
                    .limit(1)
                    .execute()
                )
                dados["id"] = (ultimo.data[0]["id"] + 1) if ultimo.data else 1
                inserido = supabase.table("configuracao").insert(dados).execute()
            else:
                raise
        if inserido.data:
            return Configuracao.from_dict(inserido.data[0])
        return Configuracao(nome_estacionamento=nome_estacionamento, cnpj=cnpj, empresa_id=empresa_id)

    def salvar_configuracao(self, config: Configuracao, empresa_id: int | None = None) -> None:
        """Salva a configuracao no Supabase."""

        eid = empresa_id if empresa_id is not None else config.empresa_id
        dados = {
            "nome_estacionamento": config.nome_estacionamento,
            "cnpj": config.cnpj,
            "telefone": config.telefone,
            "endereco": config.endereco,
            "cidade": config.cidade,
            "estado": config.estado,
            "cep": config.cep,
            "total_vagas": config.total_vagas,
            "vagas_carro": config.vagas_carro,
            "vagas_moto": config.vagas_moto,
            "vagas_carro_grande": config.vagas_carro_grande,
            "vagas_caminhonete": config.vagas_caminhonete,
            "valor_primeira_hora": config.valor_primeira_hora,
            "valor_hora_adicional": config.valor_hora_adicional,
            "valor_mensal": config.valor_mensal,
            "horario_abertura": config.horario_abertura or None,
            "horario_fechamento": config.horario_fechamento or None,
            "cabecalho_ticket": config.cabecalho_ticket,
            "rodape_ticket": config.rodape_ticket,
            "ticket_exibir_cnpj": config.ticket_exibir_cnpj,
            "ticket_exibir_contato": config.ticket_exibir_contato,
            "ticket_formato_papel": config.ticket_formato_papel,
            "ticket_exibir_codigo_barras": config.ticket_exibir_codigo_barras,
            "bloquear_sem_vaga": config.bloquear_sem_vaga,
            "exigir_observacao": config.exigir_observacao,
            "pix_tipo": config.pix_tipo,
            "pix_chave": config.pix_chave,
            "proximo_numero_ticket": config.proximo_numero_ticket,
        }
        if eid is not None:
            dados["empresa_id"] = eid

        if config.id:
            (
                supabase
                .table("configuracao")
                .update(dados)
                .eq("id", config.id)
                .execute()
            )
            return

        if eid is not None:
            (
                supabase
                .table("configuracao")
                .update(dados)
                .eq("empresa_id", eid)
                .execute()
            )
            return

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

    @staticmethod
    def _converter_data_iso_para_interna(data: str | None) -> str | None:
        """
        Converte a data no formato ISO (retornado pelo Supabase):
        YYYY-MM-DDTHH:MM:SS  (ou YYYY-MM-DD HH:MM:SS)

        de volta para o formato interno do sistema:
        DD/MM/YYYY HH:MM:SS
        """

        if not data:
            return None

        from datetime import datetime

        # Aceita tanto o separador 'T' quanto o espaco entre data e hora
        texto = str(data).replace("T", " ").strip()

        # Pode vir com fracoes de segundo (ex: 2026-08-10 14:38:18.123)
        if "." in texto:
            texto = texto.split(".")[0]

        data_obj = datetime.strptime(
            texto,
            "%Y-%m-%d %H:%M:%S"
        )

        return data_obj.strftime(
            "%d/%m/%Y %H:%M:%S"
        )