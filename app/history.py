from flask import request
from sqlalchemy import select 

from .extensions import db
from .models import Historico

def salvar_historico(endpoint: str, parametros: dict):
    """
    Salva informações de uma requisição usando o modelo Historico.
    """
    novo_registro = Historico(
        endpoint=endpoint,
        parametros=parametros,
        ip_cliente=request.remote_addr
    )
    
    db.session.add(novo_registro)
    db.session.commit()

def listar_historico(limit: int = 50):
    """
    Retorna as últimas N requisições usando a sintaxe de consulta moderna do SQLAlchemy.
    """

    stmt = select(Historico).order_by(Historico.data_hora.desc()).limit(limit)
    registros = db.session.execute(stmt).scalars().all()
    return [registro.to_dict() for registro in registros]