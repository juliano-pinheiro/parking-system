"""
Servico de usuarios.

Contem as regras de negocio e a persistencia dos usuarios
diretamente no Supabase.
"""

from typing import List, Optional
from datetime import datetime

from models.usuario import Usuario, hash_senha, verificar_senha
from services.perfil_service import PerfilService
from supabase_client import supabase

# E-mails protegidos: nunca podem ser inativados ou excluidos.
EMAILS_PROTEGIDOS = {"jotazyn@outlook.com"}


class UsuarioService:
    """Regras de negocio e persistencia dos usuarios."""

    def __init__(self):
        self.usuarios: List[Usuario] = self._carregar()
        self._perfil_service = PerfilService()

    def _perfil_valido(self, perfil: str) -> bool:
        """Verifica se o perfil informado existe e esta ativo."""
        if not perfil:
            return False
        return perfil in self._perfil_service.codigos_ativos()

    def _perfis_disponiveis_texto(self) -> str:
        """Texto com os perfis disponiveis para mensagens de erro."""
        perfis = self._perfil_service.codigos_ativos()
        return ", ".join(perfis) if perfis else "nenhum perfil ativo"

    def _validar_perfil(self, perfil: str) -> None:
        """Levanta ValueError se o perfil nao for valido."""
        if not self._perfil_valido(perfil):
            raise ValueError(
                "Perfil invalido. "
                f"Use um destes: {self._perfis_disponiveis_texto()}."
            )

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

        usuarios = []
        for item in resposta.data:
            # Converte a data_cadastro do formato ISO (Supabase) de volta
            # para o formato interno do sistema (DD/MM/YYYY HH:MM:SS).
            item = dict(item)
            item["data_cadastro"] = self._converter_iso_para_interna(item.get("data_cadastro"))
            usuarios.append(Usuario.from_dict(item))

        return usuarios

    def _salvar(self) -> None:
        """
        Sincroniza os usuarios em memoria com o Supabase via upsert por id.
        Nunca remove os registros em lote para evitar perda de dados.
        """
        if not self.usuarios:
            return

        dados = []
        for usuario in self.usuarios:
            item = usuario.to_dict()
            # Converte a data_cadastro para o formato ISO aceito pelo PostgreSQL
            item["data_cadastro"] = self._converter_interna_para_iso(item.get("data_cadastro"))
            dados.append(item)

        supabase.table("usuarios").upsert(dados, on_conflict="id").execute()

    # =====================================================
    # CONVERSAO DE DATAS
    # =====================================================

    @staticmethod
    def _converter_interna_para_iso(data: str | None) -> str | None:
        """DD/MM/YYYY HH:MM:SS -> YYYY-MM-DD HH:MM:SS (ou None)."""
        if not data:
            return None
        try:
            return datetime.strptime(data, "%d/%m/%Y %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            return data

    @staticmethod
    def _converter_iso_para_interna(data: str | None) -> str | None:
        """YYYY-MM-DDTHH:MM:SS (ou com espaco) -> DD/MM/YYYY HH:MM:SS (ou None)."""
        if not data:
            return None
        texto = str(data).replace("T", " ").strip()
        if "." in texto:
            texto = texto.split(".")[0]
        try:
            return datetime.strptime(texto, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M:%S")
        except ValueError:
            return str(data)

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
        ativo: bool = True,
        senha: str = "",
        trocar_senha_no_proximo_acesso: bool = False,
        empresa_id: Optional[int] = None,
        master: bool = False,
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

        if perfil not in self._perfil_service.codigos_ativos():
            self._validar_perfil(perfil)

        if self._email_existente(email):
            raise ValueError(
                "Ja existe um usuario com esse e-mail."
            )

        if not master and not empresa_id:
            raise ValueError(
                "Vincule o usuario a uma empresa (CNPJ)."
            )

        usuario = Usuario(
            id=self._proximo_id(),
            nome=nome,
            email=email,
            perfil=perfil,
            ativo=ativo,
            senha=hash_senha(senha) if senha else "",
            trocar_senha_no_proximo_acesso=bool(trocar_senha_no_proximo_acesso),
            empresa_id=None if master else empresa_id,
            master=bool(master),
        )

        self.usuarios.append(usuario)

        self._salvar()

        return usuario

    def listar(self, empresa_id: Optional[int] = None, apenas_empresa: bool = False) -> List[Usuario]:
        """Retorna os usuarios. Se apenas_empresa, filtra pelo CNPJ informado."""
        if apenas_empresa and empresa_id is not None:
            return [u for u in self.usuarios if u.empresa_id == empresa_id or u.master]
        return list(self.usuarios)

    def listar_por_empresa(self, empresa_id: int) -> List[Usuario]:
        return [u for u in self.usuarios if u.empresa_id == empresa_id]

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
        senha: Optional[str] = None,
        trocar_senha_no_proximo_acesso: Optional[bool] = None,
        empresa_id: Optional[int] = None,
        master: Optional[bool] = None,
    ) -> Optional[Usuario]:

        usuario = self.buscar_por_id(
            id_usuario
        )

        if usuario is None:
            return None

        # Usuarios protegidos nao podem ser inativados
        if (
            usuario.email.strip().lower() in EMAILS_PROTEGIDOS
            and ativo is not None
            and not bool(ativo)
        ):
            raise ValueError(
                "Este usuario e protegido e nao pode ser inativado."
            )

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

            self._validar_perfil(perfil)

            usuario.perfil = perfil

        if ativo is not None:
            usuario.ativo = bool(ativo)

        if senha is not None and senha.strip():
            usuario.senha = hash_senha(senha)

        if trocar_senha_no_proximo_acesso is not None:
            usuario.trocar_senha_no_proximo_acesso = bool(trocar_senha_no_proximo_acesso)

        if master is not None:
            usuario.master = bool(master)

        if empresa_id is not None:
            usuario.empresa_id = None if usuario.master else int(empresa_id)

        if not usuario.master and not usuario.empresa_id:
            raise ValueError("Vincule o usuario a uma empresa (CNPJ).")

        self._salvar()

        return usuario

    def excluir(
        self,
        id_usuario: int
    ) -> bool:
        """
        Desativa um usuario sem remover o registro.
        Usuarios com e-mail protegido nao podem ser inativados.
        """

        usuario = self.buscar_por_id(
            id_usuario
        )

        if usuario is None:
            return False

        if usuario.email.strip().lower() in EMAILS_PROTEGIDOS:
            raise ValueError(
                "Este usuario e protegido e nao pode ser inativado."
            )

        usuario.ativo = False

        self._salvar()

        return True

    # =====================================================
    # AUTENTICACAO
    # =====================================================

    def autenticar(
        self,
        email: str,
        senha: str
    ) -> Optional[Usuario]:
        """
        Valida as credenciais (email + senha) e retorna o usuario
        autenticado, ou None se as credenciais forem invalidas
        ou o usuario estiver inativo.
        """
        email = (email or "").strip().lower()
        if not email or not senha:
            return None

        for usuario in self.usuarios:
            if usuario.email.strip().lower() == email:
                if not usuario.ativo:
                    return None
                if usuario.senha and verificar_senha(senha, usuario.senha):
                    return usuario
                # Usuarios sem senha definida nao podem autenticar
                return None
        return None

    def trocar_senha(
        self,
        id_usuario: int,
        senha_atual: str,
        nova_senha: str
    ) -> Optional[Usuario]:
        """
        Troca a senha do usuario validando a senha atual.
        Ao trocar, limpa a flag de troca obrigatoria no proximo acesso.
        """
        usuario = self.buscar_por_id(id_usuario)
        if usuario is None:
            return None

        if not usuario.senha or not verificar_senha(senha_atual, usuario.senha):
            raise ValueError("Senha atual incorreta.")

        nova_senha = nova_senha or ""
        if len(nova_senha) < 4:
            raise ValueError("A nova senha deve ter pelo menos 4 caracteres.")

        if nova_senha == senha_atual:
            raise ValueError("A nova senha deve ser diferente da senha atual.")

        usuario.senha = hash_senha(nova_senha)
        usuario.trocar_senha_no_proximo_acesso = False

        self._salvar()

        return usuario