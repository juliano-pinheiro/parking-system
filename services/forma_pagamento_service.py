"""
Servico de Formas de Pagamento.

CRUD de formas de pagamento (Dinheiro, PIX, Cartao Credito, Cartao
Debito, Convenio, Mensalista, Cortesia) e cadastro de novas formas.
"""

from typing import List, Optional

from models.forma_pagamento import FormaPagamento
from services.base_supabase_service import BaseSupabaseService

# Formas padrao (codigo -> nome)
FORMAS_PADRAO = [
    ("dinheiro", "Dinheiro"),
    ("pix", "Pix"),
    ("cartao_credito", "Cartão de crédito"),
    ("cartao_debito", "Cartão de débito"),
    ("convenio", "Convênio"),
    ("mensalista", "Mensalista"),
    ("cortesia", "Cortesia"),
]


class FormaPagamentoService(BaseSupabaseService):
    """Regras de negocio e persistencia das formas de pagamento."""

    TABELA = "formas_pagamento"
    MODELO = FormaPagamento
    CAMPOS_DATA = ("criado_em",)

    def __init__(self):
        self._registros: List[FormaPagamento] = self._carregar()
        self._garantir_padrao()

    def _garantir_padrao(self) -> None:
        """Garante que as formas padrao existam."""
        codigos_existentes = {f.codigo for f in self._registros}
        alterado = False
        for codigo, nome in FORMAS_PADRAO:
            if codigo not in codigos_existentes:
                self._registros.append(FormaPagamento(
                    id=self._proximo_id(self._registros),
                    nome=nome,
                    codigo=codigo,
                    ativo=True,
                ))
                alterado = True
        if alterado:
            try:
                self._persistir()
            except ValueError:
                # Tabela ainda nao existe no Supabase: as formas padrao
                # serao persistidas quando a tabela for criada.
                pass

    def criar(self, nome: str, codigo: str, ativo: bool = True) -> FormaPagamento:
        nome = (nome or "").strip()
        codigo = (codigo or "").strip().lower().replace(" ", "_")
        if not nome or not codigo:
            raise ValueError("Informe nome e codigo da forma de pagamento.")
        if any(f.codigo == codigo for f in self._registros):
            raise ValueError("Ja existe uma forma de pagamento com esse codigo.")

        forma = FormaPagamento(
            id=self._proximo_id(self._registros),
            nome=nome,
            codigo=codigo,
            ativo=ativo,
        )
        self._registros.append(forma)
        self._persistir()
        return forma

    def atualizar(self, id_forma: int, nome: str | None = None, ativo: bool | None = None) -> Optional[FormaPagamento]:
        forma = self.buscar_por_id(id_forma)
        if forma is None:
            return None
        if nome is not None:
            nome = nome.strip()
            if not nome:
                raise ValueError("Informe o nome da forma de pagamento.")
            forma.nome = nome
        if ativo is not None:
            forma.ativo = bool(ativo)
        self._persistir()
        return forma

    def _persistir(self) -> None:
        self._salvar(self._registros)
