"""
Servico de Perfis.

CRUD de perfis de acesso personalizados. Os perfis base
(admin, supervisor, operador) sao garantidos automaticamente.
"""

from typing import List, Optional

from models.perfil import Perfil
from services.base_supabase_service import BaseSupabaseService

# Perfis base do sistema
PERFIS_BASE = [
    Perfil(id=1, codigo="admin", nome="Administrador", descricao="Acesso total a todos os modulos e acoes do sistema.", ativo=True),
    Perfil(id=2, codigo="supervisor", nome="Supervisor", descricao="Gestao e autorizacoes, sem acesso total.", ativo=True),
    Perfil(id=3, codigo="operador", nome="Operador", descricao="Operacao diaria do estacionamento.", ativo=True),
]

# Perfis imutaveis (nao podem ser excluidos/inativados pelo usuario)
PERFIS_IMUTAVEIS = {"admin"}


class PerfilService(BaseSupabaseService):
    """Regras de negocio e persistencia dos perfis de acesso."""

    TABELA = "perfis"
    MODELO = Perfil
    CAMPOS_DATA = ("criado_em", "alterado_em")

    def __init__(self):
        self._registros: List[Perfil] = self._carregar()
        self._garantir_base()

    def _garantir_base(self) -> None:
        """Garante que os perfis base existam e estejam ativos."""
        codigos_existentes = {p.codigo for p in self._registros}
        alterado = False
        for perfil in PERFIS_BASE:
            if perfil.codigo not in codigos_existentes:
                self._registros.append(perfil)
                alterado = True
        if alterado:
            try:
                self._persistir()
            except ValueError:
                pass

    def _persistir(self) -> None:
        self._salvar(self._registros)

    def listar(self) -> List[Perfil]:
        """Retorna todos os perfis."""
        return list(self._registros)

    def listar_ativos(self) -> List[Perfil]:
        """Retorna apenas perfis ativos."""
        return [p for p in self._registros if p.ativo]

    def buscar_por_id(self, id_perfil: int) -> Optional[Perfil]:
        for perfil in self._registros:
            if perfil.id == id_perfil:
                return perfil
        return None

    def buscar_por_codigo(self, codigo: str) -> Optional[Perfil]:
        codigo = (codigo or "").strip().lower()
        for perfil in self._registros:
            if perfil.codigo.lower() == codigo:
                return perfil
        return None

    def codigos_ativos(self) -> List[str]:
        """Retorna os codigos dos perfis ativos."""
        return [p.codigo for p in self._registros if p.ativo]

    def codigos_todos(self) -> List[str]:
        """Retorna os codigos de todos os perfis (ativos e inativos)."""
        return [p.codigo for p in self._registros]

    def _codigo_valido(self, codigo: str) -> str:
        """Normaliza o codigo do perfil (slug)."""
        import re
        codigo = (codigo or "").strip().lower()
        codigo = re.sub(r"[^a-z0-9]+", "_", codigo)
        codigo = codigo.strip("_")
        return codigo

    def criar(self, nome: str, codigo: str, descricao: str = "", ativo: bool = True) -> Perfil:
        nome = (nome or "").strip()
        codigo = self._codigo_valido(codigo)
        descricao = (descricao or "").strip()

        if not nome:
            raise ValueError("Informe o nome do perfil.")
        if not codigo:
            raise ValueError("Informe um codigo valido para o perfil.")
        if self.buscar_por_codigo(codigo):
            raise ValueError("Ja existe um perfil com esse codigo.")

        perfil = Perfil(
            id=self._proximo_id(self._registros),
            codigo=codigo,
            nome=nome,
            descricao=descricao,
            ativo=bool(ativo),
        )
        self._registros.append(perfil)
        self._persistir()
        return perfil

    def atualizar(
        self,
        id_perfil: int,
        nome: Optional[str] = None,
        descricao: Optional[str] = None,
        ativo: Optional[bool] = None,
    ) -> Optional[Perfil]:
        perfil = self.buscar_por_id(id_perfil)
        if perfil is None:
            return None

        if perfil.codigo in PERFIS_IMUTAVEIS and ativo is not None and not bool(ativo):
            raise ValueError("O perfil Administrador nao pode ser inativado.")

        if nome is not None:
            nome = nome.strip()
            if not nome:
                raise ValueError("Informe o nome do perfil.")
            perfil.nome = nome

        if descricao is not None:
            perfil.descricao = descricao.strip()

        if ativo is not None:
            perfil.ativo = bool(ativo)

        perfil.alterado_em = ""
        self._persistir()
        return perfil

    def excluir(self, id_perfil: int) -> bool:
        """Inativa um perfil. Perfis imutaveis ou em uso nao podem ser inativados."""
        perfil = self.buscar_por_id(id_perfil)
        if perfil is None:
            return False
        if perfil.codigo in PERFIS_IMUTAVEIS:
            raise ValueError("O perfil Administrador nao pode ser inativado.")
        perfil.ativo = False
        perfil.alterado_em = ""
        self._persistir()
        return True
