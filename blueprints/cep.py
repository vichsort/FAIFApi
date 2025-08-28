from flask import Blueprint, jsonify
from utils.fetch import fetch_json
from utils.helpers import sanitize_digits
from utils.fetch import logger

bp = Blueprint("cep", __name__, url_prefix="/faif/cep")


@bp.route("/<cep>", methods=["GET"])
def consultar_cep(cep: str):
    """
    Consulta endereço por CEP via BrasilAPI.
    Uso: /faif/cep/<cep>
    """
    digits = sanitize_digits(cep)
    url = f"https://brasilapi.com.br/api/cep/v2/{digits}"
    dados = fetch_json(
        url,
        not_found_message="CEP não encontrado.",
        not_found_error_code="CEP_NOT_FOUND",
    )
    logger.info("[FAIFApi] consultar_cep(%s) -> %s", digits, "OK" if dados else "EMPTY")
    return jsonify(dados)
