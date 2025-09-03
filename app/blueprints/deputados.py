from flask import Blueprint, jsonify, request
from utils.fetch import fetch_json, logger
from utils.exceptions import err
from services.normalizers import normalize_deputados_list, normalize_deputado_details

bp = Blueprint("deputados", __name__, url_prefix="/faif/deputados")

@bp.route("", methods=["GET"])
def buscar_deputados_por_nome():
    """
    Busca deputados por nome via query param e retorna uma lista simplificada.
    Uso: GET /faif/deputados?nome=<nome>
    """
    nome = request.args.get("nome", "").strip()
    if not nome:
        raise err(
            "Parâmetro 'nome' é obrigatório.",
            status_code=400,
            error_code="MISSING_PARAM",
            details="Query param 'nome' ausente ou vazio.",
        )

    url = f"https://dadosabertos.camara.leg.br/api/v2/deputados?nome={nome}"
    dados = fetch_json(
        url,
        headers={"Accept": "application/json"},
        not_found_message="Nenhum deputado encontrado para este nome.",
        not_found_error_code="DEPUTADO_NOT_FOUND",
    )

    normalizado = normalize_deputados_list(dados)
    logger.info("[FAIFApi] buscar_deputados(nome=%s) -> %d itens", nome, len(normalizado))
    return jsonify({"ok": True, "data": normalizado})


@bp.route("/<int:deputado_id>", methods=["GET"])
def obter_detalhes_deputado(deputado_id: int):
    """
    Obtém os dados detalhados de um deputado específico pelo seu ID.
    Uso: GET /faif/deputados/<id>
    """
    url = f"https://dadosabertos.camara.leg.br/api/v2/deputados/{deputado_id}"
    dados = fetch_json(
        url,
        headers={"Accept": "application/json"},
        not_found_message="ID de deputado não encontrado.",
        not_found_error_code="DEPUTADO_ID_NOT_FOUND",
    )

    dados_do_deputado = dados.get("dados", {})

    normalizado = normalize_deputado_details(dados_do_deputado)
    logger.info("[FAIFApi] obter_detalhes_deputado(id=%d) -> OK", deputado_id)
    return jsonify({"ok": True, "data": normalizado})
