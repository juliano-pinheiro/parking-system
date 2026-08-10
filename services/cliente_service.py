"""
Servico de clientes (mensalistas).

Responsavel pelas regras de negocio e persistencia
dos clientes diretamente no Supabase.
"""

from datetime import datetime
from typing import List, Optional

from models.cliente import (
    Cliente,
    CATEGORIAS_VALIDAS,
    FORMATO_DATA
)

from supabase_client import supabase


class ClienteService:
    """Regras de negocio dos clientes mensalistas."""

    def __init__(self):
        self.clientes: List[Cliente] = self._carregar()

    # =====================================================
    # PERSISTENCIA
    # =====================================================

    def _carregar(self) -> List[Cliente]:
        """Carrega todos os clientes do Supabase."""

        resposta = (
            supabase
            .table("clientes")
            .select("*")
            .order("id")
            .execute()
        )

        return [
            Cliente.from_dict(self._converter_para_modelo(item))
            for item in resposta.data
        ]

    def _salvar(self) -> None:
        """
        Sincroniza os clientes em memoria com o Supabase.

        Nesta primeira etapa, substitui os registros existentes
        pela lista atual.
        """

        # Limpa os registros atuais
        supabase.table("clientes").delete().neq("id", -1).execute()

        if not self.clientes:
            return

        dados = [
            self._converter_para_banco(cliente)
            for cliente in self.clientes
        ]

        supabase.table("clientes").insert(dados).execute()

    # =====================================================
    # CONVERSAO
    # =====================================================

    @staticmethod
    def _converter_para_banco(cliente: Cliente) -> dict:
        """Converte Cliente para formato do PostgreSQL."""

        dados = cliente.to_dict()

        dados["data_inicio"] = (
            datetime.strptime(
                cliente.data_inicio,
                FORMATO_DATA
            ).strftime("%Y-%m-%d")
        )

        dados["data_fim"] = (
            datetime.strptime(
                cliente.data_fim,
                FORMATO_DATA
            ).strftime("%Y-%m-%d")
        )

        if cliente.data_cadastro:
            try:
                data_cadastro = datetime.strptime(
                    cliente.data_cadastro,
                    "%d/%m/%Y %H:%M:%S"
                )

                dados["data_cadastro"] = data_cadastro.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

            except ValueError:
                pass

        return dados

    @staticmethod
    def _converter_para_modelo(dados: dict) -> dict:
        """Converte dados do PostgreSQL para o modelo Cliente."""

        for campo in ["data_inicio", "data_fim"]:
            if dados.get(campo):
                data = str(dados[campo])

                if "-" in data:
                    data_obj = datetime.strptime(
                        data[:10],
                        "%Y-%m-%d"
                    )

                    dados[campo] = data_obj.strftime(
                        FORMATO_DATA
                    )

        if dados.get("data_cadastro"):
            data = str(dados["data_cadastro"])

            try:
                data_obj = datetime.fromisoformat(
                    data.replace("Z", "+00:00")
                )

                dados["data_cadastro"] = data_obj.strftime(
                    "%d/%m/%Y %H:%M:%S"
                )

            except ValueError:
                pass

        return dados

    # =====================================================
    # VALIDACOES
    # =====================================================

    def _proximo_id(self) -> int:
        """Retorna o proximo ID disponivel."""

        if not self.clientes:
            return 1

        return max(
            cliente.id
            for cliente in self.clientes
        ) + 1

    def _placa_existente(
        self,
        placa: str,
        ignorar_id: Optional[int] = None
    ) -> bool:

        placa = self._normalizar_placa(placa)

        for cliente in self.clientes:

            if (
                cliente.ativo
                and self._normalizar_placa(cliente.placa) == placa
                and cliente.id != ignorar_id
            ):
                return True

        return False

    @staticmethod
    def _normalizar_placa(placa: str) -> str:
        """Normaliza a placa."""

        return (
            (placa or "")
            .replace(" ", "")
            .upper()
        )

    @staticmethod
    def _validar_data(texto: str) -> bool:
        """Valida uma data no formato dd/mm/aaaa."""

        if not texto:
            return False

        try:
            datetime.strptime(
                texto.strip(),
                FORMATO_DATA
            )

            return True

        except ValueError:
            return False

    def _validar_vigencia(
        self,
        data_inicio: str,
        data_fim: str
    ) -> None:

        if not self._validar_data(data_inicio):
            raise ValueError(
                "Informe a data de início da vigência no formato dd/mm/aaaa."
            )

        if not self._validar_data(data_fim):
            raise ValueError(
                "Informe a data de fim da vigência no formato dd/mm/aaaa."
            )

        inicio = datetime.strptime(
            data_inicio.strip(),
            FORMATO_DATA
        )

        fim = datetime.strptime(
            data_fim.strip(),
            FORMATO_DATA
        )

        if fim < inicio:
            raise ValueError(
                "A data de fim da vigência não pode ser anterior "
                "à data de início."
            )

    # =====================================================
    # CRUD
    # =====================================================

    def criar(
        self,
        nome: str,
        telefone: str = "",
        placa: str = "",
        categoria: str = "carro_pequeno",
        data_inicio: str = "",
        data_fim: str = "",
    ) -> Cliente:

        nome = (nome or "").strip()
        telefone = (telefone or "").strip()
        placa = self._normalizar_placa(placa)
        categoria = (
            categoria or "carro_pequeno"
        ).strip()

        if not nome:
            raise ValueError(
                "Informe o nome do cliente."
            )

        if not telefone:
            raise ValueError(
                "Informe o telefone do cliente."
            )

        if not placa:
            raise ValueError(
                "Informe a placa do veículo."
            )

        if categoria not in CATEGORIAS_VALIDAS:
            raise ValueError(
                "Categoria inválida. "
                f"Use uma destas: {', '.join(CATEGORIAS_VALIDAS)}."
            )

        if self._placa_existente(placa):
            raise ValueError(
                "Já existe um cliente ativo com essa placa."
            )

        self._validar_vigencia(
            data_inicio,
            data_fim
        )

        cliente = Cliente(
            id=self._proximo_id(),
            nome=nome,
            telefone=telefone,
            placa=placa,
            categoria=categoria,
            data_inicio=data_inicio.strip(),
            data_fim=data_fim.strip(),
        )

        self.clientes.append(cliente)

        self._salvar()

        return cliente

    def listar(self) -> List[Cliente]:
        """Retorna todos os clientes."""

        return list(self.clientes)

    def buscar_por_id(
        self,
        id_cliente: int
    ) -> Optional[Cliente]:

        for cliente in self.clientes:

            if cliente.id == id_cliente:
                return cliente

        return None

    def atualizar(
        self,
        id_cliente: int,
        nome: Optional[str] = None,
        telefone: Optional[str] = None,
        placa: Optional[str] = None,
        categoria: Optional[str] = None,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None,
        ativo: Optional[bool] = None,
    ) -> Optional[Cliente]:

        cliente = self.buscar_por_id(id_cliente)

        if cliente is None:
            return None

        if nome is not None:

            nome = nome.strip()

            if not nome:
                raise ValueError(
                    "Informe o nome do cliente."
                )

            cliente.nome = nome

        if telefone is not None:

            telefone = telefone.strip()

            if not telefone:
                raise ValueError(
                    "Informe o telefone do cliente."
                )

            cliente.telefone = telefone

        if placa is not None:

            placa = self._normalizar_placa(
                placa
            )

            if not placa:
                raise ValueError(
                    "Informe a placa do veículo."
                )

            if self._placa_existente(
                placa,
                ignorar_id=id_cliente
            ):
                raise ValueError(
                    "Já existe um cliente ativo com essa placa."
                )

            cliente.placa = placa

        if categoria is not None:

            if categoria not in CATEGORIAS_VALIDAS:
                raise ValueError(
                    "Categoria inválida. "
                    f"Use uma destas: {', '.join(CATEGORIAS_VALIDAS)}."
                )

            cliente.categoria = categoria

        novo_inicio = (
            data_inicio.strip()
            if data_inicio is not None
            else cliente.data_inicio
        )

        novo_fim = (
            data_fim.strip()
            if data_fim is not None
            else cliente.data_fim
        )

        self._validar_vigencia(
            novo_inicio,
            novo_fim
        )

        if data_inicio is not None:
            cliente.data_inicio = novo_inicio

        if data_fim is not None:
            cliente.data_fim = novo_fim

        if ativo is not None:
            cliente.ativo = bool(ativo)

        self._salvar()

        return cliente

    def excluir(
        self,
        id_cliente: int
    ) -> bool:

        cliente = self.buscar_por_id(
            id_cliente
        )

        if cliente is None:
            return False

        cliente.ativo = False

        self._salvar()

        return True