from flask import request

# Importações relativas do pacote 'app'
from .extensions import db
from .models import Historico

def salvar_historico(endpoint: str, parametros: dict):
    """
    Salva informações de uma requisição no banco usando o modelo Historico.
    A sessão do SQLAlchemy gerencia a conexão e o cursor automaticamente.
    """
    novo_registro = Historico(
        endpoint=endpoint,
        parametros=parametros, # O SQLAlchemy converte o dict para JSON
        ip_cliente=request.remote_addr
    )
    
    db.session.add(novo_registro)
    db.session.commit()

def listar_historico(limit: int = 50):
    """
    Retorna as últimas N requisições usando uma query do SQLAlchemy,
    que é mais segura e legível que SQL puro.
    """
    registros = Historico.query.order_by(Historico.data_hora.desc()).limit(limit).all()
    
    # Usa o método to_dict() do modelo para formatar a saída
    return [registro.to_dict() for registro in registros]