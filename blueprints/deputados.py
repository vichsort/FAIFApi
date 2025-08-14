# blueprints/deputados.py
from flask import Blueprint, jsonify
from fetch import fetch_json
from fetch import logger
from services.normalizers import normalize_deputados_list

bp = Blueprint("deputados", __name__, url_prefix="/faif/deputados")


@bp.route("/<deputado>", methods=["GET"])
def buscar_deputados(deputado: str):
    """
    Busca deputados pela API da Câmara e normaliza os campos esperados pelo app.
    Uso: /faif/deputados/<nome>
    """
    url = f"https://dadosabertos.camara.leg.br/api/v2/deputados?nome={deputado}"
    dados = fetch_json(
        url,
        headers={"Accept": "application/json"},
        not_found_message="Deputado(s) não encontrado(s).",
        not_found_error_code="DEPUTADO_NOT_FOUND",
    )

    normalizado = normalize_deputados_list(dados)
    logger.info("[FAIFApi] buscar_deputados(%s) -> %d itens", deputado, len(normalizado))
    return jsonify(normalizado)
