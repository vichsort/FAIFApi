from .extensions import db

class Historico(db.Model):
    """
    Representa um registro de uma requisição feita à API.
    """
    __tablename__ = 'historico'

    id = db.Column(db.Integer, primary_key=True)
    endpoint = db.Column(db.String(255), nullable=False)
    parametros = db.Column(db.JSON)
    ip_cliente = db.Column(db.String(45))
    data_hora = db.Column(db.DateTime, server_default=db.func.now())

    def to_dict(self):
        """Converte o objeto para um dicionário, útil para respostas JSON."""
        return {
            'id': self.id,
            'endpoint': self.endpoint,
            'parametros': self.parametros,
            'ip_cliente': self.ip_cliente,
            'data_hora': self.data_hora.isoformat() if self.data_hora else None
        }