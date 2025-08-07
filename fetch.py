from typing import Any, Dict, Optional
from exceptions import ConnectionErrorUpstream, ErrorNotFound, ErrorUpstream, InvalidJSON
import requests
import logging
import os

# ---------------------------------------------------------------------------
# Centro das requisições
# ---------------------------------------------------------------------------

# Timeout padrão para chamadas externas (segundos)
DEFAULT_TIMEOUT = int(os.getenv("FAIF_HTTP_TIMEOUT", "10"))


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_json(
    url: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, str]] = None,
    timeout: Optional[int] = None,
    not_found_message: str = "Recurso não encontrado.",
    not_found_error_code: str = "NOT_FOUND",
) -> Any:
    headers = headers or {}
    timeout = timeout or DEFAULT_TIMEOUT

    logger.info("[FAIFApi] GET %s params=%s", url, params)
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=timeout)
    except requests.RequestException as e:
        logger.exception("[FAIFApi] Erro de conexão com %s", url)
        raise ConnectionErrorUpstream("Erro de conexão com serviço externo.", details=str(e)) from e

    if resp.status_code == 404:
        raise ErrorNotFound(not_found_message, error_code=not_found_error_code, details=resp.text[:500])

    if not resp.ok:
        raise ErrorUpstream(
            "Erro ao consultar serviço externo.",
            upstream_status=resp.status_code,
            details=resp.text[:500],
        )

    try:
        return resp.json()
    except ValueError as e:
        logger.exception("[FAIFApi] JSON inválido de %s", url)
        raise InvalidJSON(details=str(e)) from e
