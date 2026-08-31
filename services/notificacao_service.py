"""
Servico de Notificacoes de Vencimento.

Gera a central de avisos com mensalistas inadimplentes e a vencer
(proximos 5 dias), com template de mensagem pronta para WhatsApp
(wa.me) e e-mail (mailto).
"""

from datetime import datetime
from typing import List

from models.mensalista import (
    MENSALIDADE_PENDENTE,
    MENSALIDADE_ATRASADO,
    STATUS_ATIVO,
)

FORMATO_DATA = "%d/%m/%Y %H:%M:%S"


class NotificacaoService:
    """Gera avisos de vencimento para mensalistas."""

    def __init__(self, mensalista_service=None, nome_estacionamento="Estacionamento"):
        self._mensalistas = mensalista_service
        self._nome_estacionamento = nome_estacionamento or "Estacionamento"

    def _hoje(self) -> datetime:
        return datetime.now()

    def gerar_avisos(self) -> dict:
        """Retorna a central de avisos: inadimplentes + a vencer."""
        if self._mensalistas is None:
            return {"avisos": [], "inadimplentes": 0, "a_vencer": 0, "mensagem_geral": ""}

        try:
            self._mensalistas.verificar_inadimplencia()
        except Exception:
            pass

        hoje = self._hoje()
        mes_atual = hoje.strftime("%m/%Y")

        avisos = []
        inadimplentes = 0
        a_vencer = 0

        for mensalista in self._mensalistas.listar():
            if mensalista.status != STATUS_ATIVO:
                continue
            mensalidades = self._mensalistas.mensalidades_do_mensalista(mensalista.id)
            pendente = next((m for m in mensalidades if m.status == MENSALIDADE_PENDENTE), None)
            atrasado = next((m for m in mensalidades if m.status == MENSALIDADE_ATRASADO), None)
            ultima = next((m for m in sorted(mensalidades, key=lambda m: m.competencia, reverse=True)), None)

            if atrasado is not None:
                inadimplentes += 1
                avisos.append(self._montar_aviso(mensalista, atrasado, "inadimplente"))
            elif pendente is not None and pendente.competencia <= mes_atual:
                inadimplentes += 1
                avisos.append(self._montar_aviso(mensalista, pendente, "inadimplente"))
            elif ultima is not None and pendente is None:
                # Proxima competencia dentro de 5 dias do dia de vencimento
                if self._vence_em_dias(mensalista.dia_vencimento, dias=5):
                    a_vencer += 1
                    avisos.append(self._montar_aviso(mensalista, ultima, "a_vencer"))

        return {
            "avisos": avisos,
            "inadimplentes": inadimplentes,
            "a_vencer": a_vencer,
            "mensagem_geral": self._mensagem_geral(inadimplentes, a_vencer),
        }

    def _montar_aviso(self, mensalista, mensalidade, situacao: str) -> dict:
        mensagem = (
            f"Olá, {mensalista.nome}! Informamos que a sua mensalidade "
            f"({mensalidade.competencia}) no valor de R$ {mensalidade.valor:.2f} "
            f"referente ao {self._nome_estacionamento} "
            f"{'está em aberto. Para regularizar, realize o pagamento ou fale conosco.' if situacao == 'inadimplente' else 'vence em breve. Para mais informações, fale conosco.'}"
        )
        telefone = "".join(c for c in mensalista.telefone if c.isdigit())
        whatsapp = f"https://wa.me/55{telefone}?text={urllib_parse_quote(mensagem)}" if telefone else ""
        email = mensalista.email
        mailto = f"mailto:{email}?subject={urllib_parse_quote('Mensalidade - ' + self._nome_estacionamento)}&body={urllib_parse_quote(mensagem)}" if email else ""
        return {
            "id": mensalista.id,
            "nome": mensalista.nome,
            "telefone": mensalista.telefone,
            "email": email,
            "competencia": mensalidade.competencia,
            "valor": mensalidade.valor,
            "situacao": situacao,
            "mensagem": mensagem,
            "whatsapp": whatsapp,
            "mailto": mailto,
        }

    def _vence_em_dias(self, dia_vencimento: int, dias: int = 5) -> bool:
        from datetime import timedelta
        hoje = self._hoje()
        for delta in range(1, dias + 1):
            data = hoje + timedelta(days=delta)
            if data.day == dia_vencimento:
                return True
        return False

    def _mensagem_geral(self, inadimplentes: int, a_vencer: int) -> str:
        partes = []
        if inadimplentes:
            partes.append(f"{inadimplentes} mensalista(s) inadimplente(s)")
        if a_vencer:
            partes.append(f"{a_vencer} mensalidade(s) vence(m) nos próximos 5 dias")
        if not partes:
            return "Nenhuma pendência de vencimento no momento."
        return " e ".join(partes)


def urllib_parse_quote(texto: str) -> str:
    """Codifica texto para uso em URLs (querystring de wa.me/mailto)."""
    from urllib.parse import quote
    return quote(texto or "")
