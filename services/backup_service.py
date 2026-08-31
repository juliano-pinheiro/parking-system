"""
Servico de Backup / Exportacao completa.

Reune todos os dados da empresa ativa em um unico dicionario
serializavel (JSON), para exportacao e migracao.
"""

from datetime import datetime


class BackupService:
    """Gera o backup completo dos dados da empresa ativa."""

    def __init__(self, services: dict = None):
        self.services = services or {}

    def gerar(self, nome_estacionamento: str = "") -> dict:
        """Retorna um dicionario com todos os dados da empresa ativa."""
        backup = {
            "sistema": "Estacionamento",
            "nome_estacionamento": nome_estacionamento,
            "gerado_em": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "dados": {},
        }

        # Mapeamento chave -> (service, metodo). 'config' e um atributo.
        mapeamento = {
            "tickets": ("servico", "listar_todos_tickets"),
            "financeiro": ("financeiro", "listar"),
            "caixas": ("caixa", "listar"),
            "pagamentos": ("pagamentos", "listar"),
            "formas_pagamento": ("formas_pagamento", "listar"),
            "tabela_precos": ("tabela_precos", "listar"),
            "tipos_veiculo": ("tipos_veiculo", "listar"),
            "descontos": ("descontos", "listar"),
            "cortesias": ("cortesias", "listar"),
            "mensalistas": ("mensalistas", "listar"),
            "mensalidades": ("mensalistas", "listar_mensalidades"),
            "convenios": ("convenios", "listar"),
            "contas_receber": ("contas_receber", "listar"),
            "estornos": ("estornos", "listar"),
            "clientes": ("clientes", "listar"),
            "nfse": ("nfse", "listar"),
            "lista_negra": ("lista_negra", "listar"),
            "reservas": ("reservas", "listar"),
            "ocorrencias": ("ocorrencias", "listar"),
        }

        for chave, (service_chave, metodo) in mapeamento.items():
            servico = self.services.get(service_chave)
            if servico is None:
                backup["dados"][chave] = []
                continue
            try:
                valor = getattr(servico, metodo)()
                backup["dados"][chave] = self._serializar(valor)
            except Exception:
                backup["dados"][chave] = []

        # Configuracao (atributo, nao metodo)
        try:
            backup["dados"]["config"] = self.services.get("servico").config.to_dict()
        except Exception:
            backup["dados"]["config"] = {}

        # Movimentacoes de caixa (por caixa)
        movimentacoes = []
        try:
            for caixa in self.services.get("caixa").listar():
                for mov in self.services.get("caixa").movimentacoes_do_caixa(caixa.id):
                    movimentacoes.append(mov.to_dict())
        except Exception:
            pass
        backup["dados"]["caixa_movimentacoes"] = movimentacoes

        return backup

    @staticmethod
    def _serializar(valor):
        if hasattr(valor, "to_dict"):
            return valor.to_dict()
        if isinstance(valor, list):
            return [item.to_dict() if hasattr(item, "to_dict") else item for item in valor]
        return valor
