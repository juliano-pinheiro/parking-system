import json
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:5000"


def get(path):
    with urllib.request.urlopen(BASE + path) as r:
        return r.status, json.loads(r.read())


def post(path, payload):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


s, d = get("/api/dashboard")
print("inicial:", d["no_patio_agora"], "ocupadas /", d["vagas_disponiveis"], "disponiveis /", d["total_vagas"], "total")

# Gerar 2 entradas reais com placas unicas
for placa in ["ZZZ9Z99", "YYY8Y88"]:
    s, r = post("/api/entrada", {"placa": placa, "tipo_veiculo": "Carro"})
    print("entrada", placa, "->", s, r.get("mensagem", r.get("erro")))

s, d = get("/api/dashboard")
print("apos 2 entradas:", d["no_patio_agora"], "ocupadas /", d["vagas_disponiveis"], "disponiveis")

# Fechar 1 ticket
s, r = post("/api/saida", {"placa": "ZZZ9Z99"})
print("saida ZZZ9Z99 ->", s, r.get("mensagem", r.get("erro")))

s, d = get("/api/dashboard")
print("apos saida:", d["no_patio_agora"], "ocupadas /", d["vagas_disponiveis"], "disponiveis")
