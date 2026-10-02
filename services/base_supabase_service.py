"""
Servico base para persistencia no Supabase.

Centraliza a conversao de datas (ISO <-> interno) e operacoes comuns
de CRUD, seguindo o padrao ja usado no FinanceiroService e no
PersistenciaService. As subclasses definem a tabela e o modelo.
"""

from datetime import datetime
from typing import List, Optional

from supabase_client import supabase

FORMATO_DATA = "%d/%m/%Y %H:%M:%S"


class BaseSupabaseService:
    """Base para servicos que persistem no Supabase."""

    TABELA = ""          # nome da tabela no Supabase
    MODELO = None        # dataclass do modelo

    # Campos de data que precisam de conversao ISO <-> interno
    CAMPOS_DATA = ()

    # Quando True, carrega/salva apenas registros da empresa ativa
    SCOPED_EMPRESA = False

    def recarregar(self, empresa_id=None) -> None:
        """Recarrega os registros, filtrando pela empresa quando aplicavel."""
        self._empresa_id = empresa_id
        self._registros = self._carregar(empresa_id)

    @staticmethod
    def _converter_interna_para_iso(data):
        """DD/MM/YYYY HH:MM:SS -> YYYY-MM-DD HH:MM:SS (ou None)."""
        if not data:
            return None
        try:
            return datetime.strptime(data, FORMATO_DATA).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            return data

    @staticmethod
    def _converter_iso_para_interna(data):
        """YYYY-MM-DDTHH:MM:SS (ou com espaco) -> DD/MM/YYYY HH:MM:SS (ou None)."""
        if not data:
            return None
        texto = str(data).replace("T", " ").strip()
        if "." in texto:
            texto = texto.split(".")[0]
        try:
            return datetime.strptime(texto, "%Y-%m-%d %H:%M:%S").strftime(FORMATO_DATA)
        except ValueError:
            return str(data)

    # =====================================================
    # PERSISTENCIA
    # =====================================================

    def _carregar(self, empresa_id=None) -> List:
        """Carrega os registros da tabela. Retorna lista vazia se a tabela nao existir."""
        try:
            query = supabase.table(self.TABELA).select("*").order("id")
            eid = empresa_id if empresa_id is not None else getattr(self, "_empresa_id", None)
            if self.SCOPED_EMPRESA and eid is not None:
                query = query.eq("empresa_id", eid)
            resposta = query.execute()
        except Exception:
            return []

        registros = []
        for item in resposta.data:
            item = dict(item)
            for campo in self.CAMPOS_DATA:
                if campo in item:
                    item[campo] = self._converter_iso_para_interna(item.get(campo))
            registros.append(self.MODELO.from_dict(item))
        return registros

    def _salvar(self, registros: List) -> None:
        """Sincroniza a lista em memoria com o Supabase (upsert por id).

        Usa upsert (on_conflict=id) em vez de delete+insert para nao violar
        chaves estrangeiras de tabelas dependentes (ex.: movimentacoes_caixa
        referencia caixas). Registros removidos da lista em memoria nao sao
        apagados fisicamente (exclusao logica via status/ativo).
        """
        if not registros:
            return

        eid = getattr(self, "_empresa_id", None)
        dados = []
        for registro in registros:
            item = registro.to_dict()
            for campo in self.CAMPOS_DATA:
                if campo in item:
                    item[campo] = self._converter_interna_para_iso(item.get(campo))
            if self.SCOPED_EMPRESA and eid is not None:
                item["empresa_id"] = eid
            dados.append(item)

        try:
            supabase.table(self.TABELA).upsert(dados, on_conflict="id").execute()
        except Exception as erro:
            texto = str(erro).lower()
            if "getaddrinfo" in texto or "connect" in texto or "network" in texto or "timeout" in texto:
                return
            raise ValueError(
                f"Nao foi possivel salvar na tabela '{self.TABELA}'. "
                "Verifique se ela foi criada no Supabase (execute o script sql/criar_tabelas_financeiro.sql)."
            ) from erro

    # =====================================================
    # CRUD GENERICO
    # =====================================================

    def _proximo_id(self, registros: List) -> int:
        if not registros:
            return 1
        return max(r.id for r in registros) + 1

    def listar(self) -> List:
        return list(self._registros)

    def buscar_por_id(self, id_registro: int) -> Optional:
        for registro in self._registros:
            if registro.id == id_registro:
                return registro
        return None

    def excluir(self, id_registro: int) -> bool:
        """Exclusao logica: marca como inativo/cancelado quando possivel."""
        registro = self.buscar_por_id(id_registro)
        if registro is None:
            return False
        if hasattr(registro, "ativo"):
            registro.ativo = False
        elif hasattr(registro, "status"):
            registro.status = "cancelado"
        self._persistir()
        return True
