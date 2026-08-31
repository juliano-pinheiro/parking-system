"""
Servico de Tipos de Veiculo.

CRUD dos tipos de veiculo por empresa. Os quatro tipos do sistema
(Carro, Moto, Carro Grande, Caminhonete) sao semeados automaticamente
e nao podem ser excluidos, pois alimentam vagas e tabela de precos.
Tipos personalizados podem ter precos proprios; campos zerados herdam
os precos de carro (ver TabelaPrecoService.precos_por_tipo).
"""

from datetime import datetime
from typing import List, Optional

from models.tipo_veiculo import TipoVeiculo, TIPOS_SISTEMA, CAMPOS_PRECO
from services.base_supabase_service import (
    BaseSupabaseService, FORMATO_DATA,
)
from supabase_client import supabase


class TipoVeiculoService(BaseSupabaseService):
    """Regras de negocio e persistencia dos tipos de veiculo."""

    TABELA = "tipos_veiculo"
    SCOPED_EMPRESA = True
    MODELO = TipoVeiculo
    CAMPOS_DATA = ("criado_em",)

    def __init__(self, empresa_id: Optional[int] = None):
        self._empresa_id = empresa_id
        self._registros: List[TipoVeiculo] = self._carregar(empresa_id)
        self._semear_tipos_sistema()

    # =====================================================
    # SEMEADURA
    # =====================================================

    def recarregar(self, empresa_id=None) -> None:
        """Recarrega os tipos da empresa e re-semeia os tipos do sistema."""
        super().recarregar(empresa_id)
        self._semear_tipos_sistema()

    def _semear_tipos_sistema(self) -> None:
        """Cria os tipos do sistema na primeira carga (uma vez por empresa)."""
        nomes_existentes = {t.nome.lower() for t in self._registros}
        faltantes = [n for n in TIPOS_SISTEMA if n.lower() not in nomes_existentes]
        if not faltantes:
            return
        for nome in faltantes:
            tipo = TipoVeiculo(
                id=self._proximo_id(self._registros),
                nome=nome,
                ativo=True,
                criado_em=datetime.now().strftime(FORMATO_DATA),
            )
            self._registros.append(tipo)
        try:
            self._persistir()
        except ValueError:
            # Tabela ainda nao existe no Supabase: semeia quando for criada.
            pass

    # =====================================================
    # CRUD
    # =====================================================

    def listar(self, somente_ativos: bool = False) -> List[TipoVeiculo]:
        tipos = list(self._registros)
        if somente_ativos:
            tipos = [t for t in tipos if t.ativo]
        # Tipos do sistema primeiro, depois personalizados em ordem alfabetica
        return sorted(
            tipos,
            key=lambda t: (not t.sistema, t.nome.lower()),
        )

    def criar(
        self,
        nome: str,
        precos: Optional[dict] = None,
    ) -> TipoVeiculo:
        """Cria um tipo de veiculo personalizado."""
        nome = (nome or "").strip()
        if not nome:
            raise ValueError("Informe o nome do tipo de veiculo.")
        if len(nome) > 40:
            raise ValueError("O nome do tipo deve ter no maximo 40 caracteres.")
        if any(t.nome.lower() == nome.lower() for t in self._registros):
            raise ValueError(f"Ja existe um tipo de veiculo chamado '{nome}'.")

        tipo = TipoVeiculo(
            id=self._proximo_id(self._registros),
            nome=nome,
            ativo=True,
            criado_em=datetime.now().strftime(FORMATO_DATA),
        )
        for campo in CAMPOS_PRECO:
            if precos and precos.get(campo) is not None:
                try:
                    setattr(tipo, campo, round(float(precos[campo]), 2))
                except (TypeError, ValueError):
                    pass

        self._registros.append(tipo)
        self._persistir()
        return tipo

    def atualizar_precos(self, id_tipo: int, precos: dict) -> Optional[TipoVeiculo]:
        """Atualiza os precos proprios de um tipo de veiculo."""
        tipo = self.buscar_por_id(id_tipo)
        if tipo is None:
            return None
        for campo in CAMPOS_PRECO:
            if campo in precos and precos[campo] is not None:
                try:
                    setattr(tipo, campo, round(float(precos[campo]), 2))
                except (TypeError, ValueError):
                    pass
        self._persistir()
        return tipo

    def atualizar(self, id_tipo: int, nome: str, precos: Optional[dict] = None) -> Optional[TipoVeiculo]:
        """Atualiza nome e precos de um tipo personalizado."""
        tipo = self.buscar_por_id(id_tipo)
        if tipo is None:
            return None
        if tipo.sistema:
            raise ValueError("Tipos do sistema nao podem ser editados.")

        nome = (nome or "").strip()
        if not nome:
            raise ValueError("Informe o nome do tipo de veiculo.")
        if len(nome) > 40:
            raise ValueError("O nome do tipo deve ter no maximo 40 caracteres.")
        if any(
            t.id != id_tipo and t.nome.lower() == nome.lower()
            for t in self._registros
        ):
            raise ValueError(f"Ja existe um tipo de veiculo chamado '{nome}'.")

        tipo.nome = nome
        for campo in CAMPOS_PRECO:
            if precos and precos.get(campo) is not None:
                try:
                    setattr(tipo, campo, round(float(precos[campo]), 2))
                except (TypeError, ValueError):
                    pass
        self._persistir()
        return tipo

    def alternar_ativo(self, id_tipo: int) -> Optional[TipoVeiculo]:
        """Ativa/inativa um tipo personalizado. Inativo some do Emitir Ticket."""
        tipo = self.buscar_por_id(id_tipo)
        if tipo is None:
            return None
        if tipo.sistema:
            raise ValueError("Tipos do sistema nao podem ser inativados.")
        tipo.ativo = not tipo.ativo
        self._persistir()
        return tipo

    def excluir(self, id_tipo: int) -> bool:
        """Exclui um tipo personalizado. Tipos do sistema nao podem ser excluidos."""
        tipo = self.buscar_por_id(id_tipo)
        if tipo is None:
            return False
        if tipo.sistema:
            raise ValueError(
                f"O tipo '{tipo.nome}' e um tipo do sistema e nao pode ser excluido."
            )
        self._registros.remove(tipo)
        self._persistir()
        # upsert nunca apaga: remove o registro fisicamente
        try:
            supabase.table(self.TABELA).delete().eq("id", id_tipo).execute()
        except Exception as erro:
            raise ValueError("Nao foi possivel excluir o tipo de veiculo.") from erro
        return True

    def _persistir(self) -> None:
        self._salvar(self._registros)
