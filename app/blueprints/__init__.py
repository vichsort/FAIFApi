def register_blueprints(app):
    """
    Registra todos os blueprints da aplicação, importando-os localmente
    para evitar dependências circulares durante a inicialização.
    """
    from . import cep
    from . import cnpj
    from . import cpf
    from . import deputados
    from . import emendas
    from . import ibge
    from . import servicos
    from . import servidores
    from . import historico

    app.register_blueprint(cep.bp)
    app.register_blueprint(cnpj.bp)
    app.register_blueprint(cpf.bp)
    app.register_blueprint(deputados.bp)
    app.register_blueprint(emendas.bp)
    app.register_blueprint(ibge.bp)
    app.register_blueprint(servicos.bp)
    app.register_blueprint(servidores.bp)
    app.register_blueprint(historico.bp)