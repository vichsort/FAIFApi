# blueprints/cnpj.py
from flask import Blueprint, jsonify
from fetch import fetch_json, logger
from helpers import sanitize_digits
from services.normalizers import map_cnpj_data

bp = Blueprint("cnpj", __name__, url_prefix="/faif")

@bp.route("/cnpj/<path:cnpj>", methods=["GET"])
def consultar_cnpj(cnpj: str):
    digits = sanitize_digits(cnpj)
    url = f"https://brasilapi.com.br/api/cnpj/v1/{digits}"
    dados = fetch_json(
        url,
        not_found_message="CNPJ não encontrado.",
        not_found_error_code="CNPJ_NOT_FOUND",
    )

    mapped = map_cnpj_data(dados, digits=digits)
    logger.info("[FAIFApi] consultar_cnpj %s -> %s", digits, "OK" if dados else "EMPTY")
    return jsonify(mapped)
