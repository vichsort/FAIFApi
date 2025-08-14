# blueprints/servicos.py
from flask import Blueprint
from fetch import fetch_json, logger
from helpers import success_response

bp = Blueprint("servicos", __name__, url_prefix="/faif/servicos")


@bp.route("/orgao/<cod>", methods=["GET"])
def consultar_servicos_orgao(cod: str):
    """
    Consulta dados de um órgão via API de serviços do governo.
    Uso: /faif/servicos/orgao/<cod>
    """
    url = f"https://www.servicos.gov.br/api/v1/orgao/{cod}"
    dados = fetch_json(
        url,
        not_found_message="Código SIORG não encontrado.",
        not_found_error_code="SIORG_NOT_FOUND",
    )
    logger.info("[FAIFApi] consultar_servicos_orgao cod=%s -> %s", cod, "OK" if dados else "EMPTY")
    return success_response(dados)


@bp.route("/servico/<cod>", methods=["GET"])
def consultar_servicos_servico(cod: str):
    """
    Consulta dados de um serviço via API de serviços do governo.
    Uso: /faif/servicos/servico/<cod>
    """
    url = f"https://www.servicos.gov.br/api/v1/servicos/{cod}"
    dados = fetch_json(
        url,
        not_found_message="Código do serviço não encontrado.",
        not_found_error_code="SERVICO_NOT_FOUND",
    )
    logger.info("[FAIFApi] consultar_servicos_servico cod=%s -> %s", cod, "OK" if dados else "EMPTY")
    return success_response(dados)
