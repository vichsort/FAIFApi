import json
from flask import request
from db import get_connection

def salvar_historico(endpoint: str, parametros: dict):
    """Salva informações de uma requisição no banco."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO historico (endpoint, parametros, ip_cliente)
        VALUES (?, ?, ?)
    """, (
        endpoint,
        json.dumps(parametros, ensure_ascii=False),
        request.remote_addr
    ))

    conn.commit()
    conn.close()

def listar_historico(limit: int = 50):
    """Retorna as últimas N requisições."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, endpoint, parametros, ip_cliente, data_hora
        FROM historico
        ORDER BY data_hora DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]
