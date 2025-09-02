from flask import jsonify
from typing import Any
from .exceptions import err

# ---------------------------------------------------------------------------
# Helpers e Respostas
# ---------------------------------------------------------------------------

def sanitize_digits(value: str) -> str:
    return ''.join(filter(str.isdigit, value))

def success_response(data: Any, status_code: int = 200):
    return jsonify({"ok": True, "data": data}), status_code

def error_response_from_exception(exc: err):
    return jsonify(exc.to_dict()), exc.status_code

