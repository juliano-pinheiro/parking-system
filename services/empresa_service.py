"""
Servico de Empresas.

CRUD de empresas/estacionamentos e consulta da empresa padrao.
"""

from typing import List, Optional

from models.empresa import Empresa
from services.base_supabase_service import BaseSupabaseService
from supabase_client import supabase


class EmpresaService(BaseSupabaseService):
    """Regras de negocio e persistencia das empresas."""

    TABELA = "empresas"
    MODELO = Empresa
    CAMPOS_DATA = ("criado_em", "alterado_em")

    def __init__(self):
        self._registros: List[Empresa] = self._carregar()
        self._garantir_padrao()

    def _garantir_padrao(self) -> None:
        """Garante que exista pelo menos a empresa padrao."""
        if not self._registros:
            try:
                self.criar(
                    cnpj="00.000.000/0001-00",
                    razao_social="Empresa Padrao",
                    nome_fantasia="Estacionamento Padrao",
                    ativo=True,
                )
            except ValueError:
                pass

    def _persistir(self) -> None:
        try:
            self._salvar(self._registros)
        except ValueError as erro:
            raise ValueError(
                "Nao foi possivel salvar a empresa. "
                "Verifique se a tabela 'empresas' foi criada no Supabase "
                "(execute o script sql/criar_multi_empresa.sql)."
            ) from erro

    def listar(self, ativos: Optional[bool] = None) -> List[Empresa]:
        if ativos is None:
            return list(self._registros)
        return [e for e in self._registros if e.ativo == ativos]

    def buscar_por_id(self, id_empresa: int) -> Optional[Empresa]:
        for empresa in self._registros:
            if empresa.id == id_empresa:
                return empresa
        return None

    def buscar_por_cnpj(self, cnpj: str) -> Optional[Empresa]:
        cnpj = (cnpj or "").strip()
        for empresa in self._registros:
            if empresa.cnpj == cnpj:
                return empresa
        return None

    def buscar_padrao(self) -> Empresa:
        """Retorna a empresa padrao (primeira ativa)."""
        ativas = self.listar(ativos=True)
        if ativas:
            return ativas[0]
        return self._registros[0]

    def _proximo_id(self, registros: List[Empresa]) -> int:
        if not registros:
            return 1
        return max(r.id for r in registros) + 1

    def _validar_cnpj(self, cnpj: str) -> str:
        """Validacao basica de CNPJ (apenas digitos)."""
        import re
        cnpj = re.sub(r"[^0-9]", "", cnpj or "")
        if len(cnpj) != 14:
            raise ValueError("CNPJ invalido. Informe um CNPJ com 14 digitos.")
        return cnpj

    def criar(
        self,
        cnpj: str,
        razao_social: str,
        nome_fantasia: str,
        telefone: str = "",
        email: str = "",
        endereco: str = "",
        cidade: str = "",
        estado: str = "",
        cep: str = "",
        ativo: bool = True,
    ) -> Empresa:
        cnpj = self._validar_cnpj(cnpj)
        razao_social = (razao_social or "").strip()
        nome_fantasia = (nome_fantasia or "").strip()

        if not razao_social:
            raise ValueError("Informe a razao social.")
        if not nome_fantasia:
            raise ValueError("Informe o nome fantasia.")
        if self.buscar_por_cnpj(cnpj):
            raise ValueError("Ja existe uma empresa com esse CNPJ.")

        empresa = Empresa(
            id=self._proximo_id(self._registros),
            cnpj=cnpj,
            razao_social=razao_social,
            nome_fantasia=nome_fantasia,
            telefone=(telefone or "").strip(),
            email=(email or "").strip().lower(),
            endereco=(endereco or "").strip(),
            cidade=(cidade or "").strip(),
            estado=(estado or "").strip().upper(),
            cep=(cep or "").strip(),
            ativo=bool(ativo),
        )
        self._registros.append(empresa)
        self._persistir()
        return empresa

    def atualizar(self, id_empresa: int, **kwargs) -> Optional[Empresa]:
        empresa = self.buscar_por_id(id_empresa)
        if empresa is None:
            return None

        campos_texto = {
            "razao_social", "nome_fantasia", "telefone", "email",
            "endereco", "cidade", "estado", "cep",
        }
        for campo, valor in kwargs.items():
            if campo == "cnpj" and valor is not None:
                empresa.cnpj = self._validar_cnpj(valor)
            elif campo in campos_texto and valor is not None:
                setattr(empresa, campo, str(valor).strip())
            elif campo == "ativo" and valor is not None:
                empresa.ativo = bool(valor)

        empresa.alterado_em = ""
        self._persistir()
        return empresa

    def inativar(self, id_empresa: int) -> bool:
        empresa = self.buscar_por_id(id_empresa)
        if empresa is None:
            return False

        try:
            supabase.table(self.TABELA).update({"ativo": False}).eq("id", id_empresa).execute()
        except Exception as erro:
            raise ValueError("Nao foi possivel inativar a empresa no banco de dados.") from erro

        empresa.ativo = False
        return True
