from flask import Flask
from . import health, deputados, cep, cnpj
from . import emendas, servicos, servidores


def register_blueprints(app: Flask) -> None:
    """
    Registra todos os blueprints do pacote blueprints.
    """
    app.register_blueprint(health.bp)
    app.register_blueprint(deputados.bp)
    app.register_blueprint(cep.bp)
    app.register_blueprint(cnpj.bp)  
    app.register_blueprint(emendas.bp)  
    app.register_blueprint(servicos.bp) 
    app.register_blueprint(servidores.bp) 
