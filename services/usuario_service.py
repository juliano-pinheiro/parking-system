"""
Servico de usuarios.

Contem as regras de negocio e a persistencia dos usuarios
diretamente no Supabase.
"""

from typing import List, Optional

from models.usuario import Usuario, PERFIS_VALIDOS
from supabase_client import supabase


class UsuarioService:
    """Regras de negocio e persistencia dos usuarios."""

    def __init__(self):
        self.usuarios: List[Usuario] = self._carregar()

    # =====================================================
    # PERSISTENCIA
    # =====================================================

    def _carregar(self) -> List[Usuario]:
        """Carrega todos os usuarios do Supabase."""

        resposta = (
            supabase
            .table("usuarios")
            .select("*")
            .order("id")
            .execute()
        )

        return [
            Usuario.from_dict(item)
            for item in resposta.data
        ]

    def _salvar(self) -> None:
        """
        Sincroniza os usuarios em memoria com o Supabase.
        """

        # Remove os registros atuais
        supabase.table("usuarios").delete().neq("id", -1).execute()

        if not self.usuarios:
            return

        dados = [
            usuario.to_dict()
            for usuario in self.usuarios
        ]

        supabase.table("usuarios").insert(dados).execute()

    # =====================================================
    # VALIDACOES
    # =====================================================

    def _proximo_id(self) -> int:
        """Retorna o proximo ID disponivel."""

        if not self.usuarios:
            return 1

        return max(
            usuario.id
            for usuario in self.usuarios
        ) + 1

    def _email_existente(
        self,
        email: str,
        ignorar_id: Optional[int] = None
    ) -> bool:
        """Verifica se o email ja esta cadastrado."""

        email = email.strip().lower()

        for usuario in self.usuarios:

            if (
                usuario.email.strip().lower() == email
                and usuario.id != ignorar_id
            ):
                return True

        return False

    # =====================================================
    # CRUD
    # =====================================================

    def criar(
        self,
        nome: str,
        email: str,
        perfil: str = "operador",
        ativo: bool = True
    ) -> Usuario:

        nome = (nome or "").strip()
        email = (email or "").strip().lower()

        if not nome:
            raise ValueError(
                "Informe o nome do usuario."
            )

        if not email:
            raise ValueError(
                "Informe o e-mail do usuario."
            )

        if perfil not in PERFIS_VALIDOS:
            raise ValueError(
                "Perfil invalido. "
                f"Use um destes: {', '.join(PERFIS_VALIDOS)}."
            )

        if self._email_existente(email):
            raise ValueError(
                "Ja existe um usuario com esse e-mail."
            )

        usuario = Usuario(
            id=self._proximo_id(),
            nome=nome,
            email=email,
            perfil=perfil,
            ativo=ativo,
        )

        self.usuarios.append(usuario)

        self._salvar()

        return usuario

    def listar(self) -> List[Usuario]:
        """Retorna todos os usuarios."""

        return list(self.usuarios)

    def buscar_por_id(
        self,
        id_usuario: int
    ) -> Optional[Usuario]:

        for usuario in self.usuarios:

            if usuario.id == id_usuario:
                return usuario

        return None

    def atualizar(
        self,
        id_usuario: int,
        nome: Optional[str] = None,
        email: Optional[str] = None,
        perfil: Optional[str] = None,
        ativo: Optional[bool] = None,
    ) -> Optional[Usuario]:

        usuario = self.buscar_por_id(
            id_usuario
        )

        if usuario is None:
            return None

        if nome is not None:

            nome = nome.strip()

            if not nome:
                raise ValueError(
                    "Informe o nome do usuario."
                )

            usuario.nome = nome

        if email is not None:

            email = email.strip().lower()

            if not email:
                raise ValueError(
                    "Informe o e-mail do usuario."
                )

            if self._email_existente(
                email,
                ignorar_id=id_usuario
            ):
                raise ValueError(
                    "Ja existe um usuario com esse e-mail."
                )

            usuario.email = email

        if perfil is not None:

            if perfil not in PERFIS_VALIDOS:
                raise ValueError(
                    "Perfil invalido. "
                    f"Use um destes: {', '.join(PERFIS_VALIDOS)}."
                )

            usuario.perfil = perfil

        if ativo is not None:
            usuario.ativo = bool(ativo)

        self._salvar()

        return usuario

    def excluir(
        self,
        id_usuario: int
    ) -> bool:
        """
        Desativa um usuario sem remover o registro.
        """

        usuario = self.buscar_por_id(
            id_usuario
        )

        if usuario is None:
            return False

        usuario.ativo = False

        self._salvar()

        return True