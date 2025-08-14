# blueprints/ibge.py
from flask import Blueprint, request, jsonify
from fetch import fetch_json, logger
from exceptions import InvalidJSON, ErrorUpstream, ConnectionErrorUpstream, ErrorNotFound

bp = Blueprint("ibge", __name__, url_prefix="/faif/ibge")

@bp.route("", methods=["GET"])
def buscar_ibge():
    """
    Proxy para https://servicodados.ibge.gov.br/api/v2/metadados/Pesquisa?q=<termo>
    Uso: GET /faif/ibge?q=termo
    Retorna: lista JSON (mesmo formato que o IBGE)
    """
    termo = (request.args.get("q") or "").strip()
    if not termo:
        return jsonify([])

    url = "https://servicodados.ibge.gov.br/api/v2/metadados/Pesquisa"
    params = {"q": termo}
    logger.info("[FAIFApi] IBGE busca q=%s", termo)

    try:
        dados = fetch_json(
            url,
            params=params,
            headers={"Accept": "application/json"},
            not_found_message="Nenhum resultado IBGE.",
            not_found_error_code="IBGE_NOT_FOUND",
        )

        return jsonify(dados)
    except (InvalidJSON, ErrorUpstream, ConnectionErrorUpstream, ErrorNotFound) as e:
        logger.warning("[FAIFApi] Falha ao consultar IBGE q=%s: %s", termo, e)
        return jsonify([])
