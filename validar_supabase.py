"""
Script de diagnóstico e validação do Supabase para o Parking System.
Verifica variáveis de ambiente, conexão DNS, autenticação e a existência de todas as 29 tabelas.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

TABELAS_ESPERADAS = [
    "empresas",
    "perfis",
    "usuarios",
    "permissoes",
    "configuracao",
    "tickets",
    "clientes",
    "tipos_veiculo",
    "caixas",
    "movimentacoes_caixa",
    "formas_pagamento",
    "tabela_precos",
    "pagamentos",
    "descontos",
    "cortesias",
    "mensalistas",
    "mensalidades",
    "convenios",
    "contas_receber",
    "sangrias",
    "suprimentos",
    "estornos",
    "financeiro",
    "auditoria",
    "logs_acesso",
    "nfse",
    "lista_negra",
    "reservas",
    "ocorrencias",
]


def diagnosticar():
    print("=" * 70)
    print("DIAGNÓSTICO E VALIDAÇÃO DO SUPABASE - PARKING SYSTEM")
    print("=" * 70)

    url = os.getenv("SUPABASE_URL", "").strip()
    key = os.getenv("SUPABASE_KEY", "").strip()

    if not url:
        print("[ERRO] SUPABASE_URL não configurada no arquivo .env!")
        return False
    if not key:
        print("[ERRO] SUPABASE_KEY não configurada no arquivo .env!")
        return False

    print(f"[OK] SUPABASE_URL encontrada: {url}")
    print(f"[OK] SUPABASE_KEY encontrada: {key[:15]}...{key[-5:] if len(key) > 20 else ''}")

    print("\nTestando conectividade de rede com o Supabase...")
    try:
        from supabase_client import supabase
    except Exception as e:
        print(f"[ERRO] Falha ao importar supabase_client: {e}")
        return False

    tabelas_ok = []
    tabelas_faltando = []

    print("\nVerificando as 29 tabelas no banco de dados...")
    for tab in TABELAS_ESPERADAS:
        try:
            resp = supabase.table(tab).select("*").limit(1).execute()
            tabelas_ok.append(tab)
            print(f"  [OK] {tab}")
        except Exception as e:
            tabelas_faltando.append((tab, str(e)))
            print(f"  [FALHOU] {tab}: {e}")

    print("\n" + "=" * 70)
    print(f"RESUMO: {len(tabelas_ok)} / {len(TABELAS_ESPERADAS)} tabelas prontas.")
    if tabelas_faltando:
        print("\nTabelas pendentes ou inacessíveis:")
        for t, err in tabelas_faltando:
            print(f"  - {t}")
        print("\nPara resolver, execute o script 'sql/preparar_supabase_completo.sql'")
        print("no SQL Editor do seu painel do Supabase.")
        return False
    else:
        print("\nPARABÉNS! Todas as tabelas do Supabase estão configuradas e acessíveis!")
        return True


if __name__ == "__main__":
    sucesso = diagnosticar()
    sys.exit(0 if sucesso else 1)
