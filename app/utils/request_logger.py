# request_logger.py
import time
from typing import Any
from flask import request, g, current_app

from FAIFApi.app.history import salvar_historico

# Limites para truncamento - pra não ficar muito pesado
MAX_STR_LEN = 1000        # máximo de caracteres para strings salvas
MAX_DICT_DEPTH = 3        # profundidade máxima para truncar dicts
EXCLUDED_PATHS = ("/faif/historico", "/favicon.ico", "/health")  # caminhos a ignorar


def _truncate_value(value: Any, depth: int = 0) -> Any:
    """Trunca strings/listas/dicts recursivamente para evitar gravações enormes."""
    if value is None:
        return None

    if isinstance(value, str):
        if len(value) > MAX_STR_LEN:
            return value[:MAX_STR_LEN] + "...(truncated)"
        return value

    if isinstance(value, (int, float, bool)):
        return value

    if isinstance(value, list):
        if depth >= MAX_DICT_DEPTH:
            return f"[list:{len(value)}]"
        return [_truncate_value(v, depth + 1) for v in value[:30]]  # limite de itens

    if isinstance(value, dict):
        if depth >= MAX_DICT_DEPTH:
            return {k: f"<{type(v).__name__}>" for k, v in list(value.items())[:10]}
        out = {}
        for k, v in list(value.items())[:50]:  # evita dicts gigantes
            out[k] = _truncate_value(v, depth + 1)
        return out

    # fallback: stringify but truncate
    try:
        s = str(value)
        if len(s) > MAX_STR_LEN:
            return s[:MAX_STR_LEN] + "...(truncated)"
        return s
    except Exception:
        return f"<{type(value).__name__}>"


def init_request_logging(app):
    """
    Inicializa os hooks de request/response no Flask app para salvar histórico automaticamente.
    Chame: init_request_logging(app) no seu app.py após criar o `app`.
    """

    @app.before_request
    def _req_start():
        # marca o início para medir duração
        g.__req_start_time = time.time()

    @app.after_request
    def _req_log(response):
        try:
            path = request.path or ""
            # Ignora paths configurados (evita recursão no /faif/historico)
            if any(path.startswith(p) for p in EXCLUDED_PATHS):
                return response

            start = getattr(g, "__req_start_time", time.time())
            duration_ms = int((time.time() - start) * 1000)

            # coleta query params (simples dict)
            try:
                query = request.args.to_dict(flat=True)
            except Exception:
                query = {}

            # tenta obter JSON do body (silencioso)
            try:
                body_json = request.get_json(silent=True)
            except Exception:
                body_json = None

            # resumo do response (não pega corpo inteiro se muito grande)
            response_len = getattr(response, "content_length", None)
            response_snippet = None
            if response_len is None:
                # tenta pegar um snippet seguro
                try:
                    data = response.get_data(as_text=True)
                    if data:
                        response_snippet = data[:MAX_STR_LEN] + ("...(truncated)" if len(data) > MAX_STR_LEN else "")
                        response_len = len(data)
                except Exception:
                    response_snippet = f"<{type(response).__name__}>"
            else:
                # não ler o body se content_length grande; apenas anotar o tamanho
                if response_len and response_len <= MAX_STR_LEN:
                    try:
                        response_snippet = response.get_data(as_text=True)
                    except Exception:
                        response_snippet = f"<{type(response).__name__}>"

            payload = {
                "method": request.method,
                "path": path,
                "query": _truncate_value(query),
                "body": _truncate_value(body_json),
                "status_code": response.status_code,
                "response_length": response_len,
                "response_snippet": _truncate_value(response_snippet),
                "duration_ms": duration_ms,
            }

            # grava no histórico (endpoint = path)
            salvar_historico(endpoint=path, parametros=payload)

        except Exception as exc:
            # não interrompe a resposta em caso de erro no logger
            current_app.logger.exception("request_logger failed: %s", exc)

        return response
