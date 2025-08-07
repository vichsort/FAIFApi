from typing import Any, Dict, Optional

# ---------------------------------------------------------------------------
# Exceções customizadas
# ---------------------------------------------------------------------------


class err(Exception):
    def __init__(
        self,
        message: str,
        *,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Any] = None
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": False,
            "error": {
                "code": self.error_code,
                "message": self.message,
                "details": self.details,
            },
        }

class ErrorNotFound(err):
    def __init__(self, message: str, *, error_code: str = "NOT_FOUND", details: Optional[str] = None, upstream_status: Optional[int] = 404) -> None:
        super().__init__(message, status_code=404, error_code=error_code, details=details)

class ConnectionErrorUpstream(err):
    def __init__(self, message: str, *, details: Optional[str] = None) -> None:
        super().__init__(message, status_code=502, error_code="UPSTREAM_CONNECTION_ERROR", details=details)

class ErrorUpstream(err):
    def __init__(self, message: str, *, upstream_status: int, details: Optional[str] = None, error_code: str = "UPSTREAM_ERROR") -> None:
        super().__init__(message, status_code=502, error_code=error_code, details=details)

class InvalidJSON(err):
    def __init__(self, message: str = "Resposta JSON inválida do serviço externo.", *, upstream_status: Optional[int] = None, details: Optional[str] = None) -> None:
        super().__init__(message, status_code=502, error_code="INVALID_JSON", details=details)
