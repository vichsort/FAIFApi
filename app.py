import os
import logging
from typing import Any, Dict, Optional
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS

# ---------------------------------------------------------------------------
# Configuração básica
# ---------------------------------------------------------------------------

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tokens vindos do ambiente (.env / variáveis de ambiente)
token_cofiex = os.getenv("TOKEN_COFIEX")
token_cgu = os.getenv("TOKEN_CGU")  # carregado logo no início

TOKEN_PORTAL = os.getenv("TOKEN_PORTAL", "d1b5fac8951a331b63047753f1eaa2fb")

# Timeout padrão para chamadas externas (segundos)
DEFAULT_TIMEOUT = int(os.getenv("FAIF_HTTP_TIMEOUT", "10"))

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

# ---------------------------------------------------------------------------
# Helpers e Respostas
# ---------------------------------------------------------------------------

def sanitize_digits(value: str) -> str:
    return ''.join(filter(str.isdigit, value))

def success_response(data: Any, status_code: int = 200):
    return jsonify({"ok": True, "data": data}), status_code

def error_response_from_exception(exc: err):
    return jsonify(exc.to_dict()), exc.status_code

# ---------------------------------------------------------------------------
# Centro das requisições
# ---------------------------------------------------------------------------

def fetch_json(
    url: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, str]] = None,
    timeout: Optional[int] = None,
    not_found_message: str = "Recurso não encontrado.",
    not_found_error_code: str = "NOT_FOUND",
) -> Any:
    headers = headers or {}
    timeout = timeout or DEFAULT_TIMEOUT

    logger.info("[FAIFApi] GET %s params=%s", url, params)
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=timeout)
    except requests.RequestException as e:
        logger.exception("[FAIFApi] Erro de conexão com %s", url)
        raise ConnectionErrorUpstream("Erro de conexão com serviço externo.", details=str(e)) from e

    if resp.status_code == 404:
        raise ErrorNotFound(not_found_message, error_code=not_found_error_code, details=resp.text[:500])

    if not resp.ok:
        raise ErrorUpstream(
            "Erro ao consultar serviço externo.",
            upstream_status=resp.status_code,
            details=resp.text[:500],
        )

    try:
        return resp.json()
    except ValueError as e:
        logger.exception("[FAIFApi] JSON inválido de %s", url)
        raise InvalidJSON(details=str(e)) from e

# ---------------------------------------------------------------------------
# Rotas / Endpoints
# ---------------------------------------------------------------------------

@app.route("/faif/deputados/<deputado>")
def buscar_deputados(deputado: str):
    url = f"https://dadosabertos.camara.leg.br/api/v2/deputados?nome={deputado}"
    dados = fetch_json(
        url,
        headers={"Accept": "application/json"},
        not_found_message="Deputado(s) não encontrado(s).",
        not_found_error_code="DEPUTADO_NOT_FOUND",
    )
    lista = dados.get("dados", []) if isinstance(dados, dict) else dados
    return success_response(lista)

@app.route("/faif/cep/<cep>")
def consultar_cep(cep: str):
    digits = sanitize_digits(cep)
    url = f"https://brasilapi.com.br/api/cep/v2/{digits}"
    dados = fetch_json(url, not_found_message="CEP não encontrado.", not_found_error_code="CEP_NOT_FOUND")
    return success_response(dados)

@app.route("/faif/cnpj/<cnpj>")
def consultar_cnpj(cnpj: str):
    digits = sanitize_digits(cnpj)
    url = f"https://brasilapi.com.br/api/cnpj/v1/{digits}"
    dados = fetch_json(url, not_found_message="CNPJ não encontrado.", not_found_error_code="CNPJ_NOT_FOUND")
    return success_response(dados)

@app.route("/faif/servicos/orgao/<cod>")
def consultar_servicos_orgao(cod: str):
    url = f"https://www.servicos.gov.br/api/v1/orgao/{cod}"
    dados = fetch_json(url, not_found_message="Código SIORG não encontrado.", not_found_error_code="SIORG_NOT_FOUND")
    return success_response(dados)

@app.route("/faif/servicos/servico/<cod>")
def consultar_servicos_servico(cod: str):
    url = f"https://www.servicos.gov.br/api/v1/servicos/{cod}"
    dados = fetch_json(url, not_found_message="Código SIORG não encontrado.", not_found_error_code="SIORG_NOT_FOUND")
    return success_response(dados)

@app.route("/faif/portal-transparencia/pessoa-juridica/<cnpj>")
def buscar_pessoa_juridica(cnpj: str):
    cnpj = sanitize_digits(cnpj)
    url = f"https://api.portaldatransparencia.gov.br/api-de-dados/pessoa-juridica?cnpj={cnpj}"
    headers = {"Accept": "application/json", "chave-api-dados": TOKEN_PORTAL}
    dados = fetch_json(url, headers=headers, not_found_message="Pessoa jurídica não encontrada.", not_found_error_code="PESSOA_JURIDICA_NOT_FOUND")
    return success_response(dados)

@app.route("/faif/portal-transparencia/pessoa-fisica/<cpf>&<nis>")
def buscar_pessoa_fisica(cpf: str, nis: str):
    cpf = sanitize_digits(cpf)
    nis = sanitize_digits(nis)
    url = f"https://api.portaldatransparencia.gov.br/api-de-dados/pessoa-fisica?cpf={cpf}&nis={nis}"
    headers = {"Accept": "application/json", "chave-api-dados": TOKEN_PORTAL}
    dados = fetch_json(url, headers=headers, not_found_message="Pessoa física não encontrada.", not_found_error_code="PESSOA_FISICA_NOT_FOUND")
    return success_response(dados)

@app.route("/faif/portal-transparencia/emendas/<page>")
def buscar_emendas_parlamentares(page: str):
    # Validar página
    try:
        page_num = int(page)
        if page_num < 1:
            raise ValueError
    except ValueError:
        raise err(
            "Parâmetro 'page' deve ser inteiro >= 1.",
            status_code=400,
            error_code="INVALID_PAGE",
            details={"page": page},
        )

    # Coletar filtros opcionais
    params: Dict[str, str] = {"pagina": str(page_num)}

    def _get_arg_str(name: str) -> Optional[str]:
        v = request.args.get(name)
        if v is None:
            return None
        v = v.strip()
        return v or None

    # Strings diretas
    for p_name in ("codigoEmenda", "numeroEmenda", "nomeAutor", "tipoEmenda", "codigoFuncao", "codigoSubfuncao"):
        v = _get_arg_str(p_name)
        if v is not None:
            params[p_name] = v

    # Ano precisa ser inteiro (positivo)
    ano_raw = _get_arg_str("ano")
    if ano_raw is not None:
        if not ano_raw.isdigit():
            raise err(
                "Parâmetro 'ano' deve ser inteiro.",
                status_code=400,
                error_code="INVALID_PARAM",
                details={"ano": ano_raw},
            )
        params["ano"] = ano_raw

    url = "https://api.portaldatransparencia.gov.br/api-de-dados/emendas"
    headers = {"Accept": "application/json", "chave-api-dados": TOKEN_PORTAL}

    logger.info("[FAIFApi] Emendas params=%s", params)

    dados = fetch_json(
        url,
        headers=headers,
        params=params,
        not_found_message="Nenhuma emenda encontrada.",
        not_found_error_code="EMENDA_NOT_FOUND",
    )

    return success_response(dados)

# SERVIDORES (Portal da Transparência) --------------------------------------
@app.route("/faif/servidores")
def buscar_servidores():
    """
    Busca pessoas físicas no Portal da Transparência e filtra aquelas cujo campo
    ``vinculo`` contenha a palavra "Servidor".

    Uso:
        /faif/servidores?nome=Silva[&pagina=1]

    Parâmetros:
        nome   (obrigatório) - parte do nome a pesquisar.
        pagina (opcional, default=1) - número da página na API externa.

    Retorno:
        {"ok": true, "data": [...lista de servidores...]}
    """
    nome = request.args.get("nome", "").strip()
    if not nome:
        raise err(
            "Parâmetro 'nome' é obrigatório.",
            status_code=400,
            error_code="MISSING_PARAM",
            details="Query param 'nome' ausente ou vazio.",
        )

    pagina_raw = request.args.get("pagina", "1").strip()
    try:
        pagina_int = int(pagina_raw)
        if pagina_int < 1:
            raise ValueError
    except ValueError:
        raise err(
            "Parâmetro 'pagina' deve ser inteiro >= 1.",
            status_code=400,
            error_code="INVALID_PAGE",
            details={"pagina": pagina_raw},
        )

    params: Dict[str, str] = {"nome": nome, "pagina": str(pagina_int)}

    url = "https://api.portaldatransparencia.gov.br/api-de-dados/pessoas-fisicas"
    headers = {"Accept": "application/json", "chave-api-dados": TOKEN_PORTAL}

    dados = fetch_json(
        url,
        headers=headers,
        params=params,
        not_found_message="Nenhuma pessoa encontrada no Portal da Transparência.",
        not_found_error_code="PESSOA_FISICA_NOT_FOUND",
    )

    # O endpoint retorna lista (mesmo quando vazia). Vamos filtrar por 'Servidor'.
    servidores = []
    if isinstance(dados, list):
        for p in dados:
            if isinstance(p, dict):
                vinculo = (p.get("vinculo") or "")
                if isinstance(vinculo, str) and "servidor" in vinculo.lower():
                    servidores.append(p)

    if not servidores:
        # Lança 404 padronizado
        raise ErrorNotFound(
            "Nenhum servidor encontrado para este nome.",
            error_code="SERVIDOR_NOT_FOUND",
            details=f"nome={nome}",
        )

    return success_response(servidores)

# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

@app.errorhandler(err)
def handle_faif_error(exc: err):
    logger.warning("[FAIFApi] %s", exc)
    return error_response_from_exception(exc)

@app.errorhandler(Exception)
def handle_unexpected_error(exc: Exception):
    logger.exception("[FAIFApi] Erro inesperado: %s", exc)
    fallback = err("Erro interno do servidor.")
    return error_response_from_exception(fallback)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
