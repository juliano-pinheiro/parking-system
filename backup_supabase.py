"""Backup do estado atual das tabelas do Supabase para arquivos JSON."""
import json
import os
from datetime import datetime

from supabase_client import supabase

PASTA_BACKUP = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "data",
    "backup_supabase"
)
os.makedirs(PASTA_BACKUP, exist_ok=True)

TABELAS = ["tickets", "configuracao", "clientes", "usuarios"]

for tabela in TABELAS:
    resposta = supabase.table(tabela).select("*").execute()
    dados = resposta.data
    caminho = os.path.join(PASTA_BACKUP, f"{tabela}.json")
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=4)
    print(f"backup {tabela}: {len(dados)} registros -> {caminho}")

print("Backup concluido.")
