from flask import Flask
from config import Config 

from .extensions import db, migrate, cors
from .blueprints import register_blueprints
from .utils.helpers import error_response_from_exception 
from .utils.exceptions import err, ErrorNotFound
from werkzeug.exceptions import NotFound as HTTPNotFound


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app)

    register_blueprints(app)

    @app.errorhandler(err)
    def handle_faif_error(exc):
        return error_response_from_exception(exc)

    @app.errorhandler(HTTPNotFound)
    def handle_404_error(exc):
        not_found = ErrorNotFound("Rota não encontrada.", error_code="ROUTE_NOT_FOUND")
        return error_response_from_exception(not_found)

    @app.errorhandler(Exception)
    def handle_unexpected_error(exc):
        fallback = err("Erro interno do servidor.")
        return error_response_from_exception(fallback)

    return app