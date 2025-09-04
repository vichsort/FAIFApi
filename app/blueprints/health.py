import time
import os
import sys
import platform
import socket
from datetime import datetime
from flask import Blueprint, jsonify

bp = Blueprint("health", __name__)

def init_health(app, route="/health"):
    """
    Inicializa a rota de health check.
    Chame: init_health(app) no seu app.py
    """

    # define start time se não existir
    app.config.setdefault("APP_START_TIME", time.time())
    app.config.setdefault("APP_VERSION", os.getenv("APP_VERSION", "dev"))

    @app.route(route)
    def health():
        """
        Checagem de saúde do serviço.

        Uso:
            GET /health

        Retorno:
            {
                "status": "ok",
                "uptime_seconds": 123.4,
                "started_at": "2025-08-13T18:00:00Z",
                "pid": 12345,
                "host": "my-host",
                "platform": "...",
                "python_version": "...",
                "app_version": "...",
                "request_metrics": {
                    "total_requests": 10,
                    "failed_requests": 1,
                    "avg_duration_ms": 123
                },
                "db": {
                    "path": "/path/to/historico.db",
                    "exists": true,
                    "size_bytes": 12345,
                    "historico_rows": 42
                },
                "env": {
                    "TOKEN_PORTAL_present": true
                },
                "timestamp": "..."
            }
        """
        now = time.time()
        start = app.config.get("APP_START_TIME", now)
        uptime = now - start

        total_requests = app.config.get("TOTAL_REQUESTS", 0)
        failed_requests = app.config.get("FAILED_REQUESTS", 0)
        total_duration = app.config.get("TOTAL_DURATION_MS", 0)
        avg_duration = int(total_duration / total_requests) if total_requests > 0 else None

        payload = {
            "status": "ok",
            "uptime_seconds": round(uptime, 3),
            "started_at": datetime.utcfromtimestamp(start).isoformat() + "Z",
            "pid": os.getpid(),
            "host": socket.gethostname(),
            "platform": platform.platform(),
            "python_version": sys.version.splitlines()[0],
            "app_version": app.config.get("APP_VERSION"),
            "request_metrics": {
                "total_requests": total_requests,
                "failed_requests": failed_requests,
                "avg_duration_ms": avg_duration,
            },
            "env": {"TOKEN_PORTAL_present": bool(os.getenv("TOKEN_PORTAL"))},
            "timestamp": datetime.utcfromtimestamp(now).isoformat() + "Z",
        }

        return jsonify(payload)
