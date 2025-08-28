from typing import Dict
from flask import Blueprint, request, current_app
from utils.fetch import fetch_json, logger
from utils.helpers import success_response
from utils.exceptions import ErrorNotFound, err

bp = Blueprint("servidores", __name__, url_prefix="/faif/transparencia")


@bp.route("/servidores", methods=["GET"])
def buscar_servidores():
    """
    Busca pessoas físicas no Portal da Transparência e filtra aquelas cujo campo
    'vinculo' contenha a palavra 'Servidor'.

    Uso: /faif/transparencia/servidores?nome=Silva[&pagina=1]
    """
    nome = request.args.get("nome", "").strip()
    if not nome:
        raise err(
            "Parâmetro 'nome' é obrigatório.",
            status_code=400,
            error_code="MISSING_PARAM",
            details="Query param 'nome' ausente ou vazio.",
        )

    pagina_raw = request.args.get("pagina", "1").strip()
    try:
        pagina_int = int(pagina_raw)
        if pagina_int < 1:
            raise ValueError
    except ValueError:
        raise err(
            "Parâmetro 'pagina' deve ser inteiro >= 1.",
            status_code=400,
            error_code="INVALID_PAGE",
            details={"pagina": pagina_raw},
        )

    params: Dict[str, str] = {"nome": nome, "pagina": str(pagina_int)}

    url = "https://api.portaldatransparencia.gov.br/api-de-dados/pessoas-fisicas"
    headers = {"Accept": "application/json", "chave-api-dados": current_app.config["TOKEN_PORTAL"]}

    logger.info("[FAIFApi] buscar_servidores nome=%s pagina=%s", nome, pagina_int)

    dados = fetch_json(
        url,
        headers=headers,
        params=params,
        not_found_message="Nenhuma pessoa encontrada no Portal da Transparência.",
        not_found_error_code="PESSOA_FISICA_NOT_FOUND",
    )

    servidores = []
    if isinstance(dados, list):
        for p in dados:
            if isinstance(p, dict):
                vinculo = (p.get("vinculo") or "")
                if isinstance(vinculo, str) and "servidor" in vinculo.lower():
                    servidores.append(p)

    if not servidores:
        raise ErrorNotFound(
            "Nenhum servidor encontrado para este nome.",
            error_code="SERVIDOR_NOT_FOUND",
            details=f"nome={nome}",
        )

    return success_response(servidores)
