from typing import Dict, Optional
from flask import Blueprint, request, jsonify, current_app
from utils.exceptions import err 
from utils.fetch import fetch_json, logger

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
        return v.strip() if v else None

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

    if "nomeAutor" in params:
        params["nomeAutor"] = params["nomeAutor"].upper()

    url = "https://api.portaldatransparencia.gov.br/api-de-dados/emendas"
    headers = {
        "Accept": "application/json",
        "chave-api-dados": current_app.config["TOKEN_PORTAL"],
        "User-Agent": "FAIFApi/1.0",
    }

    logger.info("[FAIFApi] Emendas params=%s", params)
    
    dados = fetch_json(
        url,
        headers=headers,
        params=params,
        not_found_message="Nenhuma emenda encontrada.",
        not_found_error_code="EMENDA_NOT_FOUND",
    )

    logger.info("[FAIFApi] Resposta da API externa (emendas) -> %s", "OK" if dados else "EMPTY")

    return jsonify({"ok": True, "data": dados or []})