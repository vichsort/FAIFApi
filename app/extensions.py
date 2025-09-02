from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS

# Crie as instâncias aqui, sem nenhuma aplicação associada ainda.
db = SQLAlchemy()
migrate = Migrate()
cors = CORS()