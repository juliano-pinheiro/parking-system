"""
Blueprint de paginas (frontend): rotas que servem os templates SPA.
"""

from flask import Blueprint, redirect, render_template, url_for

from services_registry import usuario_logado

bp = Blueprint("paginas", __name__)


@bp.route("/")
def index():
    """Serve a pagina principal (SPA) do sistema. Exige autenticacao."""
    if usuario_logado() is None:
        return redirect(url_for("paginas.login"))
    return render_template("index.html")


@bp.route("/login")
def login():
    """Serve a pagina de login."""
    if usuario_logado() is not None:
        return redirect(url_for("paginas.index"))
    return render_template("login.html")
