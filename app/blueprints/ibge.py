from flask import Blueprint, request, jsonify
from ..utils.fetch import fetch_json, logger

bp = Blueprint("ibge", __name__, url_prefix="/faif/ibge")

@bp.route("", methods=["GET"])
def buscar_ibge():
    """
    Busca dados do IBGE com base no termo de pesquisa fornecido.
    Uso: GET /faif/ibge?q=termo
    """
    termo = (request.args.get("q") or "").strip()
    if not termo:
        return jsonify({"ok": True, "data": []})

    url = "https://servicodados.ibge.gov.br/api/v2/metadados/Pesquisa"
    params = {"q": termo}
    logger.info("[FAIFApi] IBGE busca q=%s", termo)

    dados = fetch_json(
        url,
        params=params,
        headers={"Accept": "application/json"},
        not_found_message="Nenhum resultado encontrado no IBGE.",
        not_found_error_code="IBGE_NOT_FOUND",
    )

    return jsonify({"ok": True, "data": dados})