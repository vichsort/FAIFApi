from flask import Blueprint, jsonify, request
from ..history import listar_historico
from ..utils.exceptions import err

bp = Blueprint("historico", __name__, url_prefix="/faif/historico")

@bp.route("", methods=["GET"])
def get_historico():
    """
    Endpoint para listar o histórico de requisições.
    Aceita um query param opcional `limit` para definir o número de resultados.
    Uso: GET /faif/historico
         GET /faif/historico?limit=10
    """

    limit_str = request.args.get('limit', '50')

    try:
        limit_int = int(limit_str)
        if limit_int <= 0:
            raise ValueError("O limite deve ser um número positivo.")
    except ValueError:
        raise err(
            "Parâmetro 'limit' inválido. Deve ser um número inteiro positivo.",
            status_code=400,
            error_code="INVALID_PARAM",
            details={"limit": limit_str}
        )

    resultados = listar_historico(limit=limit_int)

    return jsonify({"ok": True, "data": resultados})