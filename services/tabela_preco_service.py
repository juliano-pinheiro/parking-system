"""
Servico de Tabela de Precos.

CRUD da tabela de precos e calculo automatico do valor do ticket
com base nas regras configuradas (primeira hora, hora adicional,
diaria, valor por minuto, valor maximo diario, tolerancia, noturno,
fim de semana e feriados).

Suporta precos diferenciados por tipo de veiculo (carro, moto, carro
grande, caminhonete), fracionamento de cobranca, tarifa minima e
meia estadia.
"""

from datetime import datetime, timedelta
from typing import List, Optional

from models.tabela_preco import (
    TabelaPreco, FORMATO_DATA, TIPOS_VEICULO, CAMPOS_PRECO_TIPO,
)
from services.base_supabase_service import BaseSupabaseService

# Mapeia o nome do tipo de veiculo (como vem do frontend) para a chave interna
TIPO_VEICULO_CHAVE = {
    "carro": "carro",
    "moto": "moto",
    "carro_grande": "carro_grande",
    "caminhonete": "caminhonete",
    "Carro": "carro",
    "Moto": "moto",
    "Carro Grande": "carro_grande",
    "Caminhonete": "caminhonete",
}


class TabelaPrecoService(BaseSupabaseService):
    """Regras de negocio e persistencia da tabela de precos."""

    TABELA = "tabela_precos"
    SCOPED_EMPRESA = True
    MODELO = TabelaPreco
    CAMPOS_DATA = ("criado_em", "alterado_em")

    def __init__(self, empresa_id: Optional[int] = None):
        self._empresa_id = empresa_id
        # Tipos de veiculo personalizados (TipoVeiculoService): nome em
        # minusculo -> dict de precos. Atualizado pelo app.py.
        self.tipos_personalizados: dict = {}
        self._registros: List[TabelaPreco] = self._carregar()
        if not self._registros:
            self._registros.append(TabelaPreco(id=1, empresa_id=getattr(self, "_empresa_id", None)))
            try:
                self._persistir()
            except ValueError:
                # Tabela ainda nao existe no Supabase: a tabela padrao
                # sera persistida quando a tabela for criada.
                pass

    def definir_tipos_personalizados(self, tipos: List) -> None:
        """Recebe os tipos personalizados (models TipoVeiculo) para o calculo."""
        self.tipos_personalizados = {
            t.nome.lower(): {
                "primeira_hora": t.primeira_hora,
                "hora_adicional": t.hora_adicional,
                "diaria": t.diaria,
                "valor_minuto": t.valor_minuto,
                "valor_maximo_diario": t.valor_maximo_diario,
                "mensal": t.mensal,
            }
            for t in tipos
            if getattr(t, "ativo", True)
        }

    def obter_vigente(self) -> TabelaPreco:
        """Retorna a tabela de precos ativa (ou a primeira)."""
        for tabela in self._registros:
            if tabela.ativo:
                return tabela
        return self._registros[0] if self._registros else TabelaPreco(id=1)

    def atualizar_precos_por_nome_tipo(self, tipo_veiculo: str, precos: dict) -> Optional[TabelaPreco]:
        """Atualiza os precos de um tipo do sistema (Carro, Moto, Carro Grande,
        Caminhonete) diretamente na tabela de precos."""
        chave = TIPO_VEICULO_CHAVE.get((tipo_veiculo or "").strip())
        if not chave:
            return None
        tabela = self.obter_vigente()

        dados = {}
        for campo in CAMPOS_PRECO_TIPO:
            valor = (precos or {}).get(campo)
            if valor is None:
                continue
            destino = campo if chave == "carro" else f"{chave}_{campo}"
            dados[destino] = valor

        if not dados:
            return tabela
        return self.atualizar(tabela.id, dados)

    def atualizar(self, id_tabela: int, dados: dict) -> Optional[TabelaPreco]:
        tabela = self.buscar_por_id(id_tabela)
        if tabela is None:
            return None

        campos = [
            "primeira_hora", "hora_adicional", "diaria", "mensal",
            "valor_minuto", "valor_maximo_diario", "tolerancia_minutos",
            "valor_noturno", "fim_semana", "feriados", "ativo",
            "fracionamento_minutos", "tarifa_minima",
            "meia_estadia_minutos", "meia_estadia_valor",
            "valor_ticket_perdido", "pernoite_valor", "pernoite_a_partir_horas",
        ]
        # Campos de preco por tipo de veiculo
        for tipo in TIPOS_VEICULO:
            if tipo == "carro":
                continue  # usa os campos padrao
            for campo in CAMPOS_PRECO_TIPO:
                campos.append(f"{tipo}_{campo}")

        for campo in campos:
            if campo in dados and dados[campo] is not None:
                valor = dados[campo]
                if campo in ("tolerancia_minutos", "fracionamento_minutos", "meia_estadia_minutos", "pernoite_a_partir_horas"):
                    setattr(tabela, campo, int(valor))
                elif campo == "ativo":
                    setattr(tabela, campo, bool(valor))
                else:
                    setattr(tabela, campo, float(valor))

        tabela.alterado_em = datetime.now().strftime(FORMATO_DATA)
        self._persistir()
        return tabela

    # =====================================================
    # PRECOS POR TIPO DE VEICULO
    # =====================================================

    def precos_por_tipo(self, tipo_veiculo: str) -> dict:
        """
        Retorna um dicionario com os precos do tipo de veiculo informado.
        Para 'carro' (ou tipo desconhecido) usa os campos padrao.
        Tipos personalizados usam seus precos proprios; campos zerados
        herdam o preco de carro.
        """
        tabela = self.obter_vigente()
        chave = TIPO_VEICULO_CHAVE.get(tipo_veiculo, "carro")
        if chave == "carro":
            precos_carro = {
                "primeira_hora": tabela.primeira_hora,
                "hora_adicional": tabela.hora_adicional,
                "diaria": tabela.diaria,
                "valor_minuto": tabela.valor_minuto,
                "valor_maximo_diario": tabela.valor_maximo_diario,
                "mensal": tabela.mensal,
            }
            # Tipo personalizado (ou nome nao mapeado): preco proprio se houver
            personalizado = self.tipos_personalizados.get((tipo_veiculo or "").lower())
            if personalizado:
                return {
                    campo: personalizado.get(campo) or precos_carro[campo]
                    for campo in precos_carro
                }
            return precos_carro
        return {
            "primeira_hora": getattr(tabela, f"{chave}_primeira_hora"),
            "hora_adicional": getattr(tabela, f"{chave}_hora_adicional"),
            "diaria": getattr(tabela, f"{chave}_diaria"),
            "valor_minuto": getattr(tabela, f"{chave}_valor_minuto"),
            "valor_maximo_diario": getattr(tabela, f"{chave}_valor_maximo_diario"),
            "mensal": getattr(tabela, f"{chave}_mensal"),
        }

    # =====================================================
    # CALCULO DO VALOR DO TICKET
    # =====================================================

    def calcular_valor(
        self,
        entrada: str,
        saida: str,
        tipo_veiculo: str = "Carro",
        noturno: bool = False,
        fim_semana: bool = False,
        feriado: bool = False,
    ) -> float:
        """
        Calcula o valor a pagar de um ticket com base na tabela de precos.

        Regras:
        - Usa os precos do tipo de veiculo informado.
        - Se houver valor_minuto, calcula por minuto.
        - Caso contrario, cobra a primeira hora + horas adicionais,
          respeitando o fracionamento configurado.
        - Aplica meia estadia quando aplicavel.
        - Aplica tarifa_minima como piso.
        - Aplica valor_maximo_diario como teto.
        - Aplica valor_noturno / fim_semana / feriado quando aplicavel.
        """
        tabela = self.obter_vigente()
        precos = self.precos_por_tipo(tipo_veiculo)

        try:
            entrada_dt = datetime.strptime(entrada, FORMATO_DATA)
            saida_dt = datetime.strptime(saida, FORMATO_DATA)
        except (ValueError, TypeError):
            return 0.0

        if saida_dt <= entrada_dt:
            return 0.0

        minutos = int((saida_dt - entrada_dt).total_seconds() // 60)

        # Tolerancia: nao cobra se dentro da tolerancia
        if minutos <= tabela.tolerancia_minutos:
            return 0.0

        # Meia estadia: se dentro do limite, cobra o valor da meia estadia
        if (
            tabela.meia_estadia_minutos > 0
            and minutos <= tabela.meia_estadia_minutos
            and tabela.meia_estadia_valor > 0
        ):
            valor = tabela.meia_estadia_valor
        # Calculo por minuto
        elif precos["valor_minuto"] and precos["valor_minuto"] > 0:
            valor = minutos * precos["valor_minuto"]
        else:
            # Fracionamento: define a unidade de cobranca (15/30/60)
            fracao = tabela.fracionamento_minutos or 60
            if minutos <= fracao:
                valor = precos["primeira_hora"]
            else:
                # Horas adicionais arredondadas para cima na fracao
                adicionais = (minutos - fracao + fracao - 1) // fracao
                valor = precos["primeira_hora"] + adicionais * precos["hora_adicional"]

        # Tarifa minima
        if tabela.tarifa_minima and tabela.tarifa_minima > 0:
            valor = max(valor, tabela.tarifa_minima)

        # Teto diario
        if precos["valor_maximo_diario"] and precos["valor_maximo_diario"] > 0:
            valor = min(valor, precos["valor_maximo_diario"])

        # Pernoite: a partir de X horas, aplica a tarifa de pernoite
        # como teto (nunca cobra mais que a tarifa de pernoite).
        if (
            tabela.pernoite_valor and tabela.pernoite_valor > 0
            and tabela.pernoite_a_partir_horas and tabela.pernoite_a_partir_horas > 0
            and minutos >= tabela.pernoite_a_partir_horas * 60
        ):
            valor = min(valor, tabela.pernoite_valor)

        # Regras especiais (noturno, fim de semana, feriado)
        if noturno and tabela.valor_noturno and tabela.valor_noturno > 0:
            valor = tabela.valor_noturno
        elif fim_semana and tabela.fim_semana and tabela.fim_semana > 0:
            valor = tabela.fim_semana
        elif feriado and tabela.feriados and tabela.feriados > 0:
            valor = tabela.feriados

        return round(valor, 2)

    def _persistir(self) -> None:
        self._salvar(self._registros)
