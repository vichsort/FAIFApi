import os
from typing import Dict, Optional
from flask import Flask, request
from flask_cors import CORS
from exceptions import err, ErrorNotFound
from fetch import fetch_json, logger
from helpers import sanitize_digits, success_response, error_response_from_exception

# ---------------------------------------------------------------------------
# Configuração básica
# ---------------------------------------------------------------------------

app = Flask(__name__)
CORS(app)

TOKEN_PORTAL = os.getenv("TOKEN_PORTAL", "d1b5fac8951a331b63047753f1eaa2fb")


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

@app.route("/faif/cgu")
def listar_cgu():
    url = "https://dados.gov.br/dados/api/publico/conjuntos-dados/"
    dados = fetch_json(
        url,
        headers={"Accept": "application/json"},
        not_found_message="Nenhum conjunto de dados encontrado.",
        not_found_error_code="DADOS_NOT_FOUND",
    )
    return success_response(dados)


@app.route("/faif/cgu/<id>")
def detalhar_cgu(id: str):
    """
    Retorna detalhes de um conjunto de dados específico.
    """
    url = f"https://dados.gov.br/dados/api/publico/conjuntos-dados/{id}"
    dados = fetch_json(
        url,
        headers={"Accept": "application/json"},
        not_found_message="Conjunto de dados não encontrado.",
        not_found_error_code="DADOS_ID_NOT_FOUND",
    )
    return success_response(dados)


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
