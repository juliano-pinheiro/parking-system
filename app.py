"""
Sistema de Estacionamento - Interface Web
==========================================

Ponto de entrada da aplicacao web. Expoe uma API REST (Flask) que
reaproveita as mesmas regras de negocio do terminal (EstacionamentoService)
e serve o frontend HTML/CSS/JS localizado em templates/ e static/.

As rotas da API foram organizadas em blueprints no pacote `routes/`
(auth, operacao, financeiro, precos, clientes, administracao,
relatorios, extras e paginas). As instancias dos servicos e os helpers
compartilhados (autenticacao, permissoes e serializacao) ficam em
`services_registry.py`.

Para executar:
    python app.py

Depois, acesse http://127.0.0.1:5000 no navegador.
"""

import os
from flask import Flask

from routes.auth import bp as bp_auth
from routes.operacao import bp as bp_operacao
from routes.financeiro import bp as bp_financeiro
from routes.precos import bp as bp_precos
from routes.clientes import bp as bp_clientes
from routes.administracao import bp as bp_administracao
from routes.relatorios import bp as bp_relatorios
from routes.extras import bp as bp_extras
from routes.paginas import bp as bp_paginas

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY") or os.urandom(32)

# Registro dos blueprints (cada um expoe um grupo de rotas da API/frontend)
for bp in (
    bp_auth,
    bp_operacao,
    bp_financeiro,
    bp_precos,
    bp_clientes,
    bp_administracao,
    bp_relatorios,
    bp_extras,
    bp_paginas,
):
    app.register_blueprint(bp)


if __name__ == "__main__":
    porta = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "").strip().lower() in {"1", "true"}
    app.run(host="0.0.0.0", port=porta, debug=debug)
