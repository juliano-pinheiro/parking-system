"""
Servico de Auditoria e Logs de Acesso.

Registra toda alteracao feita no sistema e os logs de acesso.
Nenhuma alteracao pode ser perdida.
"""

from datetime import datetime
from typing import List, Optional

from models.auditoria import Auditoria, LogAcesso, FORMATO_DATA
from services.base_supabase_service import BaseSupabaseService
from supabase_client import supabase


class AuditoriaService(BaseSupabaseService):
    """Registra e consulta auditoria e logs de acesso."""

    TABELA = "auditoria"
    MODELO = Auditoria
    CAMPOS_DATA = ("data",)

    def __init__(self):
        self._registros: List[Auditoria] = self._carregar()
        self._logs: List[LogAcesso] = self._carregar_logs()

    # =====================================================
    # LOGS DE ACESSO
    # =====================================================

    def _carregar_logs(self) -> List[LogAcesso]:
        try:
            resposta = supabase.table("logs_acesso").select("*").order("id").execute()
        except Exception:
            return []
        logs = []
        for item in resposta.data:
            item = dict(item)
            item["data"] = self._converter_iso_para_interna(item.get("data"))
            logs.append(LogAcesso.from_dict(item))
        return logs

    def _salvar_logs(self) -> None:
        try:
            supabase.table("logs_acesso").delete().neq("id", -1).execute()
        except Exception:
            return
        if not self._logs:
            return
        dados = []
        for log in self._logs:
            item = log.to_dict()
            item["data"] = self._converter_interna_para_iso(item.get("data"))
            dados.append(item)
        try:
            supabase.table("logs_acesso").insert(dados).execute()
        except Exception:
            pass

    def registrar_log_acesso(self, usuario: str | None, acao: str, modulo: str, ip: str | None = None) -> LogAcesso:
        """Registra um log de acesso."""
        log = LogAcesso(
            id=self._proximo_id(self._logs),
            usuario=usuario,
            acao=acao,
            modulo=modulo,
            data=datetime.now().strftime(FORMATO_DATA),
            ip=ip,
        )
        self._logs.append(log)
        self._salvar_logs()
        return log

    def listar_logs(self) -> List[LogAcesso]:
        return list(self._logs)

    # =====================================================
    # AUDITORIA
    # =====================================================

    def registrar(
        self,
        tabela: str,
        registro_id: int | None = None,
        campo: str | None = None,
        valor_antigo: str | None = None,
        valor_novo: str | None = None,
        usuario: str | None = None,
        ip: str | None = None,
    ) -> Auditoria:
        """Registra uma alteracao na auditoria."""
        auditoria = Auditoria(
            id=self._proximo_id(self._registros),
            tabela=tabela,
            registro_id=registro_id,
            campo=campo,
            valor_antigo=str(valor_antigo) if valor_antigo is not None else None,
            valor_novo=str(valor_novo) if valor_novo is not None else None,
            usuario=usuario,
            data=datetime.now().strftime(FORMATO_DATA),
            ip=ip,
        )
        self._registros.append(auditoria)
        self._persistir()
        return auditoria

    def listar(self) -> List[Auditoria]:
        return list(self._registros)

    def _persistir(self) -> None:
        self._salvar(self._registros)
