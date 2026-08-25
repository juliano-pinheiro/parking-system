"""
Servico de Convenios.

Cadastro de empresas conveniadas com faturamento posterior.
Cada lancamento gera uma Conta a Receber.
"""

from typing import List, Optional

from models.convenio import Convenio
from services.base_supabase_service import BaseSupabaseService


class ConvenioService(BaseSupabaseService):
    """Regras de negocio e persistencia dos convenios."""

    TABELA = "convenios"
    MODELO = Convenio
    CAMPOS_DATA = ("criado_em",)

    def __init__(self):
        self._registros: List[Convenio] = self._carregar()

    def criar(self, nome: str, cnpj: str = "", contato: str = "", ativo: bool = True) -> Convenio:
        nome = (nome or "").strip()
        if not nome:
            raise ValueError("Informe o nome do convenio.")

        convenio = Convenio(
            id=self._proximo_id(self._registros),
            nome=nome,
            cnpj=cnpj,
            contato=contato,
            ativo=bool(ativo),
        )
        self._registros.append(convenio)
        self._persistir()
        return convenio

    def atualizar(
        self,
        id_convenio: int,
        nome: str | None = None,
        cnpj: str | None = None,
        contato: str | None = None,
        ativo: bool | None = None,
    ) -> Optional[Convenio]:
        convenio = self.buscar_por_id(id_convenio)
        if convenio is None:
            return None
        if nome is not None:
            nome = nome.strip()
            if not nome:
                raise ValueError("Informe o nome do convenio.")
            convenio.nome = nome
        if cnpj is not None:
            convenio.cnpj = cnpj
        if contato is not None:
            convenio.contato = contato
        if ativo is not None:
            convenio.ativo = bool(ativo)
        self._persistir()
        return convenio

    def _persistir(self) -> None:
        self._salvar(self._registros)
