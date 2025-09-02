import os

class Config:
    APP_VERSION = os.getenv("APP_VERSION", "dev")
    JSON_SORT_KEYS = False
    PROPAGATE_EXCEPTIONS = False
    
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", 
        "postgresql+psycopg://postgres:ifc@localhost:5432/faif"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False