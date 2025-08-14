import os
from typing import Dict, Optional
from flask import Flask, Blueprint, request, jsonify, current_app
from werkzeug.exceptions import NotFound as HTTPNotFound
from flask_cors import CORS

from exceptions import (
    err, ErrorNotFound, InvalidJSON, ErrorUpstream, ConnectionErrorUpstream
)
from fetch import fetch_json, logger
from db import init_db
from helpers import sanitize_digits, success_response, error_response_from_exception
from history import listar_historico
from health import init_health
from request_logger import init_request_logging


# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------
class Config:
    APP_VERSION = os.getenv("APP_VERSION", "dev")
    TOKEN_PORTAL = os.getenv("TOKEN_PORTAL", "d1b5fac8951a331b63047753f1eaa2fb")
    JSON_SORT_KEYS = False
    PROPAGATE_EXCEPTIONS = False


# -----------------------------------------------------------------------------
# Application factory
# -----------------------------------------------------------------------------
def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app)

    init_db()
    init_request_logging(app)
    init_health(app) 

    app.register_blueprint(build_faif_blueprint())

    register_error_handlers(app)

    return app


# -----------------------------------------------------------------------------
# Blueprint /faif
# -----------------------------------------------------------------------------
def build_faif_blueprint() -> Blueprint:
    bp = Blueprint("faif", __name__, url_prefix="/faif")

    # ------------------------ Deputados ------------------------
    @bp.route("/deputados/<deputado>")
    def buscar_deputados(deputado: str):
        """
        Busca deputados pela API da Câmara e normaliza os campos esperados pelo app.

        Uso:
            /faif/deputados/<nome>

        Parâmetros:
            deputado (path) - parte do nome do deputado a pesquisar.

        Retorno:
            Lista crua de objetos com campos: nome, email, id, siglaPartido, siglaUf, urlFoto
        """
        url = f"https://dadosabertos.camara.leg.br/api/v2/deputados?nome={deputado}"
        dados = fetch_json(
            url,
            headers={"Accept": "application/json"},
            not_found_message="Deputado(s) não encontrado(s).",
            not_found_error_code="DEPUTADO_NOT_FOUND",
        )
        lista = dados.get("dados", []) if isinstance(dados, dict) else dados

        normalizado = []
        if isinstance(lista, list):
            for d in lista:
                if isinstance(d, dict):
                    normalizado.append(
                        {
                            "nome": d.get("nome"),
                            "email": d.get("email") or "",
                            "id": d.get("id"),
                            "siglaPartido": d.get("siglaPartido"),
                            "siglaUf": d.get("siglaUf"),
                            "urlFoto": d.get("urlFoto"),
                        }
                    )
        # Flutter espera lista crua
        return jsonify(normalizado)

    # ------------------------ CEP ------------------------
    @bp.route("/cep/<cep>")
    def consultar_cep(cep: str):
        """
        Consulta endereço por CEP via BrasilAPI e retorna o objeto encontrado.

        Uso:
            /faif/cep/<cep>

        Parâmetros:
            cep (path) - CEP a ser consultado (pode vir com ou sem máscara).

        Retorno:
            Objeto JSON com os dados do endereço.
        """
        digits = sanitize_digits(cep)
        url = f"https://brasilapi.com.br/api/cep/v2/{digits}"
        dados = fetch_json(
            url,
            not_found_message="CEP não encontrado.",
            not_found_error_code="CEP_NOT_FOUND",
        )
        return jsonify(dados)

    # ------------------------ Pessoa Jurídica ------------------------
    @bp.route("/portal-transparencia/pessoa-juridica/<cnpj>")
    def buscar_pessoa_juridica(cnpj: str):
        """
        Consulta pessoa jurídica no Portal da Transparência usando CNPJ.

        Uso:
            /faif/portal-transparencia/pessoa-juridica/<cnpj>

        Parâmetros:
            cnpj (path) - CNPJ (apenas dígitos ou formatado).

        Retorno:
            Objeto JSON retornado pelo Portal da Transparência para pessoa jurídica.
        """
        cnpj = sanitize_digits(cnpj)
        url = f"https://api.portaldatransparencia.gov.br/api-de-dados/pessoa-juridica?cnpj={cnpj}"
        headers = {
            "Accept": "application/json",
            "chave-api-dados": current_app.config["TOKEN_PORTAL"],
            "User-Agent": "FAIFApi/1.0",
        }
        dados = fetch_json(
            url,
            headers=headers,
            not_found_message="Pessoa jurídica não encontrada.",
            not_found_error_code="PESSOA_JURIDICA_NOT_FOUND",
        )
        return jsonify(dados)

    # ------------------------ CPF & NIS ------------------------
    @bp.route("/portal-transparencia/pessoa-fisica/<cpf>&<nis>")
    def buscar_pessoa_fisica(cpf: str, nis: str):
        """
        Consulta pessoa física no Portal da Transparência usando CPF e NIS.

        Uso:
            /faif/portal-transparencia/pessoa-fisica/<cpf>&<nis>

        Parâmetros:
            cpf (path) - CPF (apenas dígitos ou formatado).
            nis (path) - NIS (apenas dígitos ou formatado).

        Retorno:
            Objeto JSON retornado pelo Portal da Transparência para pessoa física.
        """
        cpf = sanitize_digits(cpf)
        nis = sanitize_digits(nis)
        url = f"https://api.portaldatransparencia.gov.br/api-de-dados/pessoa-fisica?cpf={cpf}&nis={nis}"
        headers = {
            "Accept": "application/json",
            "chave-api-dados": current_app.config["TOKEN_PORTAL"],
            "User-Agent": "FAIFApi/1.0",
        }
        dados = fetch_json(
            url,
            headers=headers,
            not_found_message="Pessoa física não encontrada.",
            not_found_error_code="PESSOA_FISICA_NOT_FOUND",
        )
        return jsonify(dados)

    # ------------------------ CNPJ ------------------------
    @bp.route("/cnpj/<path:cnpj>")
    def consultar_cnpj(cnpj: str):
        """
        Consulta CNPJ via BrasilAPI e mapeia para a estrutura esperada pelo app.

        Uso:
            /faif/cnpj/<cnpj>

        Parâmetros:
            cnpj (path) - CNPJ (apenas dígitos ou formatado).

        Retorno:
            Objeto JSON mapeado com campos relevantes (nome, fantasia, atividades, qsa, endereço, etc).
        """
        digits = sanitize_digits(cnpj)
        url = f"https://brasilapi.com.br/api/cnpj/v1/{digits}"
        dados = fetch_json(
            url,
            not_found_message="CNPJ não encontrado.",
            not_found_error_code="CNPJ_NOT_FOUND",
        )

        principal_code = dados.get("cnae_fiscal")
        principal_desc = dados.get("cnae_fiscal_descricao") or ""
        atividades_secundarias_brasilapi = dados.get("cnaes_secundarios") or []

        atividades_principal = []
        if principal_code or principal_desc:
            atividades_principal.append(
                {
                    "code": str(principal_code) if principal_code is not None else "",
                    "text": principal_desc or "",
                }
            )

        atividades_secundarias = []
        for item in atividades_secundarias_brasilapi:
            atividades_secundarias.append(
                {
                    "code": str(item.get("codigo") or ""),
                    "text": item.get("descricao") or "",
                }
            )

        qsa_brasilapi = dados.get("qsa") or []
        qsa = []
        for s in qsa_brasilapi:
            qsa.append(
                {
                    "qual": s.get("qualificacao_socio") or s.get("qualificacao") or "",
                    "nome": s.get("nome_socio") or s.get("nome") or "",
                }
            )

        mapped = {
            "cnpj": digits,
            "nome": dados.get("razao_social") or dados.get("nome") or "",
            "fantasia": dados.get("nome_fantasia") or dados.get("fantasia") or "",
            "natureza_juridica": dados.get("natureza_juridica") or "",
            "porte": dados.get("descricao_porte") or dados.get("porte") or "",
            "abertura": dados.get("data_inicio_atividade") or dados.get("abertura") or "",
            "atividade_principal": atividades_principal,
            "atividades_secundarias": atividades_secundarias,
            "logradouro": dados.get("logradouro") or "",
            "numero": dados.get("numero") or "",
            "complemento": dados.get("complemento") or "",
            "bairro": dados.get("bairro") or "",
            "municipio": dados.get("municipio") or "",
            "uf": dados.get("uf") or "",
            "cep": dados.get("cep") or "",
            "situacao": dados.get("descricao_situacao_cadastral") or dados.get("situacao") or "",
            "data_situacao": dados.get("data_situacao_cadastral") or dados.get("data_situacao") or "",
            "capital_social": dados.get("capital_social") or "",
            "motivo_situacao": dados.get("descricao_motivo_situacao_cadastral") or dados.get("motivo_situacao") or "",
            "situacao_especial": dados.get("situacao_especial") or "",
            "data_situacao_especial": dados.get("data_situacao_especial") or "",
            "qsa": qsa,
        }

        # Flutter espera objeto cru
        return jsonify(mapped)

    # ------------------------ Serviços (Orgao) ------------------------
    @bp.route("/servicos/orgao/<cod>")
    def consultar_servicos_orgao(cod: str):
        """
        Consulta dados de um órgão via API de serviços do governo.

        Uso:
            /faif/servicos/orgao/<cod>

        Parâmetros:
            cod (path) - código do órgão (SIORG).

        Retorno:
            success_response contendo os dados do órgão.
        """
        url = f"https://www.servicos.gov.br/api/v1/orgao/{cod}"
        dados = fetch_json(
            url,
            not_found_message="Código SIORG não encontrado.",
            not_found_error_code="SIORG_NOT_FOUND",
        )
        return success_response(dados)

    # ------------------------ Serviços (Servico) ------------------------
    @bp.route("/servicos/servico/<cod>")
    def consultar_servicos_servico(cod: str):
        """
        Consulta dados de um serviço via API de serviços do governo.

        Uso:
            /faif/servicos/servico/<cod>

        Parâmetros:
            cod (path) - código do serviço.

        Retorno:
            success_response contendo os dados do serviço.
        """
        url = f"https://www.servicos.gov.br/api/v1/servicos/{cod}"
        dados = fetch_json(
            url,
            not_found_message="Código SIORG não encontrado.",
            not_found_error_code="SIORG_NOT_FOUND",
        )
        return success_response(dados)

    # ------------------------ Transparência (Emendas) ------------------------
    @bp.route("/portal-transparencia/emendas/<page>")
    def buscar_emendas_parlamentares(page: str):
        """
        Busca emendas parlamentares no Portal da Transparência, validando o parâmetro de página.

        Uso:
            /faif/transparencia/emendas/<page>
            [?codigoEmenda=...&numeroEmenda=...&nomeAutor=...&ano=...&tipoEmenda=...&codigoFuncao=...&codigoSubfuncao=...]

        Parâmetros:
            page (path) - número da página (inteiro >= 1).
            filtros via querystring - codigoEmenda, numeroEmenda, nomeAutor, ano (inteiro), tipoEmenda, codigoFuncao, codigoSubfuncao

        Retorno:
            success_response com os dados retornados pelo Portal da Transparência.
        """
        try:
            page_num = int(page)
            if page_num < 1:
                raise ValueError
        except ValueError as exc:
            raise err(
                "Parâmetro 'page' deve ser inteiro >= 1.",
                status_code=400,
                error_code="INVALID_PAGE",
                details={"page": page},
            ) from exc

        params: Dict[str, str] = {"pagina": str(page_num)}

        def _get_arg_str(name: str) -> Optional[str]:
            v = request.args.get(name)
            if v is None:
                return None
            v = v.strip()
            return v or None

        for p_name in ("codigoEmenda", "numeroEmenda", "nomeAutor", "tipoEmenda", "codigoFuncao", "codigoSubfuncao"):
            v = _get_arg_str(p_name)
            if v is not None:
                params[p_name] = v

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

        if "nomeAutor" in params and isinstance(params["nomeAutor"], str):
            params["nomeAutor"] = params["nomeAutor"].upper()

        url = "https://api.portaldatransparencia.gov.br/api-de-dados/emendas"
        headers = {
            "Accept": "application/json",
            "chave-api-dados": current_app.config["TOKEN_PORTAL"],
            "User-Agent": "FAIFApi/1.0",
        }

        logger.info("[FAIFApi] Emendas params=%s", params)
        logger.info("[FAIFApi] Token usado: %s", current_app.config["TOKEN_PORTAL"][:10] + "...")

        try:
            dados = fetch_json(
                url,
                headers=headers,
                params=params,
                not_found_message="Nenhuma emenda encontrada.",
                not_found_error_code="EMENDA_NOT_FOUND",
            )
            
            # Log da resposta para debug
            logger.info("[FAIFApi] Resposta da API externa: %s", dados)
            
            # Verificar se a resposta está vazia ou é uma lista vazia
            if not dados or (isinstance(dados, list) and len(dados) == 0):
                logger.warning("[FAIFApi] API externa retornou dados vazios para emendas")
                return jsonify([])
            
            # Flutter espera dados crus, não wrapped em success_response
            return jsonify(dados)
        except (InvalidJSON, ErrorUpstream, ConnectionErrorUpstream, ErrorNotFound) as e:
            logger.warning("[FAIFApi] Falha ao obter emendas (page=%s, params=%s): %s", page, params, e)
            # Retornar lista vazia em vez de erro para compatibilidade com o app
            return jsonify([])

    # ------------------------ Transparência (Servidores) ------------------------
    @bp.route("/portal-transparencia/servidores")
    def buscar_servidores():
        """
        Busca pessoas físicas no Portal da Transparência e filtra aquelas cujo campo
        ``vinculo`` contenha a palavra "Servidor".

        Uso:
            /faif/transparencia/servidores?nome=Silva[&pagina=1]

        Parâmetros:
            nome   (query, obrigatório) - parte do nome a pesquisar.
            pagina (query, opcional)   - número da página na API externa.

        Retorno:
            success_response com a lista de servidores encontrados.
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
        headers = {"Accept": "application/json", "chave-api-dados": current_app.config["TOKEN_PORTAL"]}

        dados = fetch_json(
            url,
            headers=headers,
            params=params,
            not_found_message="Nenhuma pessoa encontrada no Portal da Transparência.",
            not_found_error_code="PESSOA_FISICA_NOT_FOUND",
        )

        servidores = []
        if isinstance(dados, list):
            for p in dados:
                if isinstance(p, dict):
                    vinculo = (p.get("vinculo") or "")
                    if isinstance(vinculo, str) and "servidor" in vinculo.lower():
                        servidores.append(p)

        if not servidores:
            raise ErrorNotFound(
                "Nenhum servidor encontrado para este nome.",
                error_code="SERVIDOR_NOT_FOUND",
                details=f"nome={nome}",
            )

        return success_response(servidores)

    # ------------------------ CGU (lista) ------------------------
    @bp.route("/cgu")
    def listar_cgu():
        """
        Lista conjuntos de dados (CKAN + fallback público) e aplica filtro local pelo termo.

        Uso:
            /faif/cgu[?q=termo]

        Parâmetros:
            q (query, opcional) - termo para filtrar título/descrição.

        Retorno:
            Lista de conjuntos de dados normalizados.
        """
        termo = (request.args.get("q") or "").strip()

        def _normalize_ckan_list(dados_ckan: Dict) -> list:
            pkgs = []
            if isinstance(dados_ckan, dict):
                result_obj = dados_ckan.get("result")
                if isinstance(result_obj, dict):
                    pkgs = result_obj.get("results") or []
            itens: list = []
            if isinstance(pkgs, list):
                for pkg in pkgs:
                    if isinstance(pkg, dict):
                        itens.append(
                            {
                                "id": str(pkg.get("id") or ""),
                                "titulo": str(pkg.get("title") or pkg.get("name") or ""),
                                "descricao": str(pkg.get("notes") or ""),
                            }
                        )
            return itens

        def _normalize_public_list(dados_pub: Dict) -> list:
            raw_items = []
            if isinstance(dados_pub, list):
                raw_items = dados_pub
            elif isinstance(dados_pub, dict):
                for key in ("results", "itens", "items", "dados", "data"):
                    value = dados_pub.get(key)
                    if isinstance(value, list):
                        raw_items = value
                        break
            itens: list = []
            for it in raw_items:
                if isinstance(it, dict):
                    id_val = it.get("id") or it.get("identificador") or it.get("url") or ""
                    titulo_val = it.get("titulo") or it.get("title") or it.get("nome") or ""
                    desc_val = it.get("descricao") or it.get("resumo") or it.get("description") or ""
                    itens.append(
                        {
                            "id": str(id_val) if id_val is not None else "",
                            "titulo": str(titulo_val) if titulo_val is not None else "",
                            "descricao": str(desc_val) if desc_val is not None else "",
                        }
                    )
            return itens

        try:
            params: Dict[str, str] = {"rows": "100", "sort": "metadata_modified desc"}
            params["q"] = termo if termo else "*:*"
            dados_ckan = fetch_json(
                "https://dados.gov.br/api/3/action/package_search",
                headers={"Accept": "application/json", "User-Agent": "FAIFApi/1.0"},
                params=params,
                not_found_message="Nenhum conjunto de dados encontrado.",
                not_found_error_code="DADOS_NOT_FOUND",
            )
        except (InvalidJSON, ErrorUpstream, ConnectionErrorUpstream) as e:
            logger.warning("[FAIFApi] Falha na busca CKAN: %s", e)
            dados_ckan = {"result": {"results": []}}

        itens_norm = _normalize_ckan_list(dados_ckan)

        if not itens_norm:
            try:
                dados_pub = fetch_json(
                    "https://dados.gov.br/dados/api/publico/conjuntos-dados/",
                    headers={"Accept": "application/json", "User-Agent": "FAIFApi/1.0"},
                    not_found_message="Nenhum conjunto de dados encontrado.",
                    not_found_error_code="DADOS_NOT_FOUND",
                )
            except (InvalidJSON, ErrorUpstream, ConnectionErrorUpstream) as e:
                logger.warning("[FAIFApi] Falha no endpoint público CGU: %s", e)
                dados_pub = []

            itens_norm = _normalize_public_list(dados_pub)
            if termo:
                termo_l = termo.lower()
                itens_norm = [
                    i
                    for i in itens_norm
                    if termo_l in (i.get("titulo", "").lower())
                    or termo_l in (i.get("descricao", "").lower())
                ]

        return jsonify(itens_norm)

    # ------------------------ CGU (detalhe) ------------------------
    @bp.route("/cgu/<id>")
    def detalhar_cgu(id: str):
        """
        Retorna detalhes de um conjunto de dados específico (CKAN/package_show).

        Uso:
            /faif/cgu/<id>

        Parâmetros:
            id (path) - identificador do conjunto de dados.

        Retorno:
            Objeto JSON com os detalhes do conjunto de dados.
        """
        try:
            dados = fetch_json(
                "https://dados.gov.br/api/3/action/package_show",
                headers={"Accept": "application/json"},
                params={"id": id},
                not_found_message="Conjunto de dados não encontrado.",
                not_found_error_code="DADOS_ID_NOT_FOUND",
            )
        except (InvalidJSON, ErrorUpstream, ConnectionErrorUpstream) as e:
            logger.warning("[FAIFApi] Falha ao detalhar pacote CKAN id=%s: %s", id, e)
            raise ErrorNotFound("Conjunto de dados não encontrado.", error_code="DADOS_ID_NOT_FOUND")

        if isinstance(dados, dict) and isinstance(dados.get("result"), dict):
            return jsonify(dados["result"])
        return jsonify(dados)

    # ------------------------ Teste Portal Transparência ------------------------
    @bp.route("/teste-portal")
    def teste_portal():
        """
        Rota de teste para verificar se a API do Portal da Transparência está funcionando.
        """
        url = "https://api.portaldatransparencia.gov.br/api-de-dados/emendas"
        headers = {
            "Accept": "application/json",
            "chave-api-dados": current_app.config["TOKEN_PORTAL"],
            "User-Agent": "FAIFApi/1.0",
        }
        params = {"pagina": "1"}
        
        logger.info("[FAIFApi] Teste Portal - Token: %s", current_app.config["TOKEN_PORTAL"][:10] + "...")
        
        try:
            dados = fetch_json(
                url,
                headers=headers,
                params=params,
                not_found_message="Teste falhou.",
                not_found_error_code="TESTE_FAILED",
            )
            logger.info("[FAIFApi] Teste Portal - Resposta: %s", dados)
            return jsonify({
                "status": "sucesso",
                "token_usado": current_app.config["TOKEN_PORTAL"][:10] + "...",
                "resposta_api": dados,
                "tamanho_resposta": len(dados) if isinstance(dados, list) else "N/A"
            })
        except Exception as e:
            logger.error("[FAIFApi] Teste Portal - Erro: %s", e)
            return jsonify({
                "status": "erro",
                "erro": str(e),
                "token_usado": current_app.config["TOKEN_PORTAL"][:10] + "..."
            }), 500

    # ------------------------ Histórico utilitário ------------------------
    @bp.route("/historico")
    def consultar_historico():
        """
        Retorna últimas entradas do histórico salvo no banco.

        Uso:
            /faif/historico[?limit=50]

        Parâmetros:
            limit (query, opcional) - número máximo de registros a retornar.

        Retorno:
            Lista JSON com registros do histórico (id, endpoint, parametros, ip_cliente, data_hora)
        """
        limite = request.args.get("limit", 50, type=int)
        rows = listar_historico(limit=limite)
        return jsonify(rows)

    return bp


# -----------------------------------------------------------------------------
# Error handlers
# -----------------------------------------------------------------------------
def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(err)
    def handle_faif_error(exc: err):
        logger.warning("[FAIFApi] %s", exc)
        return error_response_from_exception(exc)

    @app.errorhandler(HTTPNotFound)
    def handle_404_error(exc: HTTPNotFound):
        not_found = ErrorNotFound(
            "Rota não encontrada.",
            error_code="ROUTE_NOT_FOUND",
            details=str(exc),
        )
        return error_response_from_exception(not_found)

    @app.errorhandler(Exception)
    def handle_unexpected_error(exc: Exception):
        logger.exception("[FAIFApi] Erro inesperado: %s", exc)
        fallback = err("Erro interno do servidor.")
        return error_response_from_exception(fallback)


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    app = create_app()
    # Ajuste via env FLASK_RUN_PORT/FLASK_RUN_HOST se preferir
    app.run(debug=True, host="0.0.0.0", port=5000)
