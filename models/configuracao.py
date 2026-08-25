"""
Modelo de configuracao do estacionamento.

Guarda as preferencias e parametros operacionais do estacionamento:
identificacao, precos, vagas, horario de funcionamento, regras do ticket
e integracoes (ex: PIX).
"""

from dataclasses import dataclass, asdict


@dataclass
class Configuracao:
    """Representa as configuracoes gerais do estacionamento."""

    # Identificacao
    nome_estacionamento: str = "Estaciona Parking"
    cnpj: str = ""
    telefone: str = ""
    endereco: str = ""
    cidade: str = ""
    estado: str = ""
    cep: str = ""

    # Vagas
    total_vagas: int = 20
    vagas_carro: int = 0
    vagas_moto: int = 0
    vagas_carro_grande: int = 0
    vagas_caminhonete: int = 0

    # Precos (avulsos - legado, usado quando nao ha tabela de precos)
    valor_primeira_hora: float = 5.0
    valor_hora_adicional: float = 3.0
    valor_mensal: float = 150.0

    # Funcionamento
    horario_abertura: str = ""
    horario_fechamento: str = ""

    # Ticket / cupom
    cabecalho_ticket: str = ""
    rodape_ticket: str = ""

    # Regras de operacao
    bloquear_sem_vaga: bool = False
    exigir_observacao: bool = True

    # Integracao PIX
    pix_tipo: str = ""
    pix_chave: str = ""

    # Controle interno
    proximo_numero_ticket: int = 1
    id: int | None = None
    empresa_id: int | None = None

    def to_dict(self) -> dict:
        """Converte a configuracao em um dicionario (para salvar em JSON)."""
        return asdict(self)

    @staticmethod
    def from_dict(dados: dict) -> "Configuracao":
        """Cria um objeto Configuracao a partir de um dicionario."""
        return Configuracao(
            nome_estacionamento=dados.get("nome_estacionamento", "Estaciona Parking"),
            cnpj=dados.get("cnpj", ""),
            telefone=dados.get("telefone", ""),
            endereco=dados.get("endereco", ""),
            cidade=dados.get("cidade", ""),
            estado=dados.get("estado", ""),
            cep=dados.get("cep", ""),
            total_vagas=dados.get("total_vagas", 20),
            vagas_carro=dados.get("vagas_carro", 0),
            vagas_moto=dados.get("vagas_moto", 0),
            vagas_carro_grande=dados.get("vagas_carro_grande", 0),
            vagas_caminhonete=dados.get("vagas_caminhonete", 0),
            valor_primeira_hora=dados.get("valor_primeira_hora", 5.0),
            valor_hora_adicional=dados.get("valor_hora_adicional", 3.0),
            valor_mensal=dados.get("valor_mensal", 150.0),
            horario_abertura=dados.get("horario_abertura", ""),
            horario_fechamento=dados.get("horario_fechamento", ""),
            cabecalho_ticket=dados.get("cabecalho_ticket", ""),
            rodape_ticket=dados.get("rodape_ticket", ""),
            bloquear_sem_vaga=dados.get("bloquear_sem_vaga", False),
            exigir_observacao=dados.get("exigir_observacao", True),
            pix_tipo=dados.get("pix_tipo", ""),
            pix_chave=dados.get("pix_chave", ""),
            proximo_numero_ticket=dados.get("proximo_numero_ticket", 1),
            id=dados.get("id"),
            empresa_id=dados.get("empresa_id"),
        )
