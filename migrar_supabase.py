"""
Script de migracao: dados dos arquivos JSON locais -> Supabase.

Os arquivos JSON locais (data/*.json) sao a fonte da verdade.
Este script SOBRESCREVE o conteudo das tabelas do Supabase com os
dados dos JSON, convertendo as datas para o formato do PostgreSQL.

Tabelas migradas: tickets, configuracao, clientes, usuarios.
"""

import json
import os
from datetime import datetime

from supabase_client import supabase

PASTA_DADOS = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "data"
)

FORMATO_DATA_HORA = "%d/%m/%Y %H:%M:%S"
FORMATO_DATA = "%d/%m/%Y"


def _converter_data_hora(valor):
    """DD/MM/YYYY HH:MM:SS -> YYYY-MM-DD HH:MM:SS (ou None)."""
    if not valor:
        return None
    return datetime.strptime(valor, FORMATO_DATA_HORA).strftime("%Y-%m-%d %H:%M:%S")


def _converter_data(valor):
    """DD/MM/YYYY -> YYYY-MM-DD (ou None)."""
    if not valor:
        return None
    return datetime.strptime(valor, FORMATO_DATA).strftime("%Y-%m-%d")


def _ler_json(nome_arquivo):
    caminho = os.path.join(PASTA_DADOS, nome_arquivo)
    with open(caminho, "r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def migrar_tickets():
    tickets = _ler_json("tickets.json")
    # Limpa a tabela
    supabase.table("tickets").delete().neq("numero", -1).execute()

    if not tickets:
        print("tickets: nenhum registro para migrar.")
        return

    # A tabela usa 'numero' como chave primaria unica. O JSON local pode conter
    # numeros duplicados (ex: ticket aberto reutilizando numero de um fechado).
    # Renumera os duplicados para o proximo numero livre, preservando a ordem.
    numeros_usados = set()
    proximo_livre = 1
    for t in tickets:
        numero = t["numero"]
        if numero in numeros_usados:
            # encontra o proximo numero livre
            while proximo_livre in numeros_usados:
                proximo_livre += 1
            numero = proximo_livre
        numeros_usados.add(numero)
        t["numero"] = numero

    dados = []
    for t in tickets:
        dados.append({
            "numero": t["numero"],
            "placa": t["placa"],
            "entrada": _converter_data_hora(t.get("entrada")),
            "saida": _converter_data_hora(t.get("saida")),
            "valor": t.get("valor"),
            "vaga": t.get("vaga"),
            "status": t.get("status"),
            "tipo_veiculo": t.get("tipo_veiculo"),
            "observacoes": t.get("observacoes", ""),
        })

    supabase.table("tickets").insert(dados).execute()
    print(f"tickets: {len(dados)} registros migrados.")


def migrar_configuracao():
    config = _ler_json("configuracao.json")
    dados = {
        "total_vagas": config.get("total_vagas", 20),
        "valor_primeira_hora": config.get("valor_primeira_hora", 5.0),
        "valor_hora_adicional": config.get("valor_hora_adicional", 3.0),
        "valor_mensal": config.get("valor_mensal", 150.0),
        "proximo_numero_ticket": config.get("proximo_numero_ticket", 1),
    }
    supabase.table("configuracao").update(dados).eq("id", 1).execute()
    print(f"configuracao: atualizada (id=1) -> {dados}")


def migrar_clientes():
    clientes = _ler_json("clientes.json")
    supabase.table("clientes").delete().neq("id", -1).execute()

    if not clientes:
        print("clientes: nenhum registro para migrar.")
        return

    dados = []
    for c in clientes:
        dados.append({
            "id": c["id"],
            "nome": c["nome"],
            "telefone": c.get("telefone", ""),
            "placa": c.get("placa", ""),
            "categoria": c.get("categoria", "carro_pequeno"),
            "data_inicio": _converter_data(c.get("data_inicio")),
            "data_fim": _converter_data(c.get("data_fim")),
            "ativo": c.get("ativo", True),
            "data_cadastro": _converter_data_hora(c.get("data_cadastro")),
        })

    supabase.table("clientes").insert(dados).execute()
    print(f"clientes: {len(dados)} registros migrados.")


def migrar_usuarios():
    usuarios = _ler_json("usuarios.json")
    supabase.table("usuarios").delete().neq("id", -1).execute()

    if not usuarios:
        print("usuarios: nenhum registro para migrar.")
        return

    dados = []
    for u in usuarios:
        dados.append({
            "id": u["id"],
            "nome": u["nome"],
            "email": u["email"],
            "perfil": u.get("perfil", "operador"),
            "ativo": u.get("ativo", True),
            "data_cadastro": _converter_data_hora(u.get("data_cadastro")),
        })

    supabase.table("usuarios").insert(dados).execute()
    print(f"usuarios: {len(dados)} registros migrados.")


if __name__ == "__main__":
    print("Iniciando migracao JSON -> Supabase...")
    migrar_tickets()
    migrar_configuracao()
    migrar_clientes()
    migrar_usuarios()
    print("Migracao concluida.")
