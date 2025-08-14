# blueprints/cpf.py
from flask import Blueprint, jsonify, current_app
from fetch import fetch_json
from helpers import sanitize_digits
from fetch import logger

bp = Blueprint("cpf", __name__, url_prefix="/faif/transparencia/pessoa-fisica")


@bp.route("/<cpf>&<nis>", methods=["GET"])
def buscar_pessoa_fisica(cpf: str, nis: str):
    """
    Consulta pessoa física no Portal da Transparência usando CPF e NIS.
    Uso: /faif/transparencia/pessoa-fisica/<cpf>&<nis>
    """
    cpf = sanitize_digits(cpf)
    nis = sanitize_digits(nis)

    url = f"https://api.portaldatransparencia.gov.br/api-de-dados/pessoa-fisica?cpf={cpf}&nis={nis}"
    headers = {
        "Accept": "application/json",
        "chave-api-dados": current_app.config["TOKEN_PORTAL"],
        "User-Agent": "FAIFApi/1.0",
    }

    dados = fetch_json(
        url,
        headers=headers,
        not_found_message="Pessoa física não encontrada.",
        not_found_error_code="PESSOA_FISICA_NOT_FOUND",
    )

    logger.info("[FAIFApi] buscar_pessoa_fisica cpf=%s nis=%s -> %s", cpf, nis, "OK" if dados else "EMPTY")
    return jsonify(dados)
