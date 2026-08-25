from supabase_client import supabase

tabelas = [
    "financeiro", "pagamentos", "caixas", "movimentacoes_caixa",
    "mensalistas", "mensalidades", "convenios", "contas_receber",
    "descontos", "cortesias", "estornos", "formas_pagamento",
    "tabela_precos", "clientes",
]

for t in tabelas:
    try:
        r = supabase.table(t).select("*").limit(1).execute()
        cols = sorted(r.data[0].keys()) if r.data else []
        has = "empresa_id" in cols
        print(f"{t:22} tem empresa_id={has} | cols={len(cols)}")
        if not has and r.data:
            print("   colunas:", cols)
    except Exception as e:
        msg = str(e)
        if "PGRST205" in msg:
            print(f"{t:22} FALTA tabela")
        else:
            print(f"{t:22} ERRO: {msg[:80]}")
