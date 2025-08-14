# blueprints/emendas.py
from typing import Dict, Optional
from flask import Blueprint, request, jsonify, current_app
from fetch import fetch_json, logger
from exceptions import InvalidJSON, ErrorUpstream, ConnectionErrorUpstream, ErrorNotFound, err

bp = Blueprint("emendas", __name__, url_prefix="/faif/transparencia")


@bp.route("/emendas/<page>", methods=["GET"])
def buscar_emendas_parlamentares(page: str):
    """
    Busca emendas parlamentares no Portal da Transparência, validando o parâmetro de página.
    Uso: /faif/transparencia/emendas/<page>
    Query params opcionais: codigoEmenda, numeroEmenda, nomeAutor, ano, tipoEmenda, codigoFuncao, codigoSubfuncao
    """

    try:
        page_num = int(page)
        if page_num < 1:
            raise ValueError
    except ValueError as exc:
        raise err(
            "Parâmetro 'page' deve ser inteiro >= 1.",
            status_code=400,
            error_code="INVALID_PAGE",
            details={"page": page},
        ) from exc

    params: Dict[str, str] = {"pagina": str(page_num)}

    def _get_arg_str(name: str) -> Optional[str]:
        v = request.args.get(name)
        if v is None:
            return None
        v = v.strip()
        return v or None

    for p_name in ("codigoEmenda", "numeroEmenda", "nomeAutor", "tipoEmenda", "codigoFuncao", "codigoSubfuncao"):
        v = _get_arg_str(p_name)
        if v is not None:
            params[p_name] = v

    ano_raw = _get_arg_str("ano")
    if ano_raw is not None:
        if not ano_raw.isdigit():
            raise err(
                "Parâmetro 'ano' deve ser inteiro.",
                status_code=400,
                error_code="INVALID_PARAM",
                details={"ano": ano_raw},
            )
        params["ano"] = ano_raw

    if "nomeAutor" in params and isinstance(params["nomeAutor"], str):
        params["nomeAutor"] = params["nomeAutor"].upper()

    url = "https://api.portaldatransparencia.gov.br/api-de-dados/emendas"
    headers = {
        "Accept": "application/json",
        "chave-api-dados": current_app.config["TOKEN_PORTAL"],
        "User-Agent": "FAIFApi/1.0",
    }

    logger.info("[FAIFApi] Emendas params=%s", params)
    logger.info("[FAIFApi] Token usado: %s", current_app.config["TOKEN_PORTAL"][:10] + "...")

    try:
        dados = fetch_json(
            url,
            headers=headers,
            params=params,
            not_found_message="Nenhuma emenda encontrada.",
            not_found_error_code="EMENDA_NOT_FOUND",
        )

        logger.info("[FAIFApi] Resposta da API externa (emendas) -> tipo=%s", type(dados).__name__)

        # Se a API externa devolver vazio, devolvemos lista vazia para compatibilidade com o aplic
        if not dados or (isinstance(dados, list) and len(dados) == 0):
            logger.warning("[FAIFApi] API externa retornou dados vazios para emendas")
            return jsonify([])

        return jsonify(dados)
    except (InvalidJSON, ErrorUpstream, ConnectionErrorUpstream, ErrorNotFound) as e:
        logger.warning("[FAIFApi] Falha ao obter emendas (page=%s, params=%s): %s", page, params, e)
        return jsonify([])
