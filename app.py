# app.py
import os
from flask import Flask
from flask_cors import CORS
from werkzeug.exceptions import NotFound as HTTPNotFound

import db as db_module
from request_logger import init_request_logging
from helpers import error_response_from_exception
from exceptions import err, ErrorNotFound
from blueprints import register_blueprints
from fetch import logger


class Config:
    APP_VERSION = os.getenv("APP_VERSION", "dev")
    TOKEN_PORTAL = os.getenv("TOKEN_PORTAL", "d1b5fac8951a331b63047753f1eaa2fb")
    JSON_SORT_KEYS = False
    PROPAGATE_EXCEPTIONS = False


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app)

    try:
        db_module.init_db()
    except Exception as e:
        logger.warning("[FAIFApi] init_db falhou durante startup: %s", e)

    init_request_logging(app)

    register_blueprints(app)

    register_error_handlers(app)

    return app


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(err)
    def handle_faif_error(exc):
        logger.warning("[FAIFApi] %s", exc)
        return error_response_from_exception(exc)

    @app.errorhandler(HTTPNotFound)
    def handle_404_error(exc):
        not_found = ErrorNotFound(
            "Rota não encontrada.",
            error_code="ROUTE_NOT_FOUND",
            details=str(exc),
        )
        return error_response_from_exception(not_found)

    @app.errorhandler(Exception)
    def handle_unexpected_error(exc):
        logger.exception("[FAIFApi] Erro inesperado: %s", exc)
        fallback = err("Erro interno do servidor.")
        return error_response_from_exception(fallback)


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)
