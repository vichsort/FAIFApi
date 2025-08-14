from typing import Any, Dict, List, Optional

def normalize_deputados_list(raw: Any) -> List[Dict[str, Any]]:
    """
    Normaliza a resposta da API da Câmara para a forma esperada pelo app:
    lista de objetos com: nome, email, id, siglaPartido, siglaUf, urlFoto
    Aceita tanto {'dados': [...]} quanto lista direta.
    """
    lista = []
    if isinstance(raw, dict):
        lista = raw.get("dados", []) or []
    elif isinstance(raw, list):
        lista = raw
    else:
        return []

    normalizado: List[Dict[str, Any]] = []
    for d in lista:
        if not isinstance(d, dict):
            continue
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
    return normalizado


def map_cnpj_data(dados: Optional[Dict[str, Any]], digits: str = "") -> Dict[str, Any]:
    """
    Mapeia a resposta da BrasilAPI (CNPJ) para um objeto com campos relevantes,
    similar ao que o app espera. Se `dados` for None ou inválido, retorna
    valores vazios/strings.
    """
    if not isinstance(dados, dict):
        dados = {}

    # principal atividade
    principal_code = dados.get("cnae_fiscal")
    principal_desc = dados.get("cnae_fiscal_descricao") or ""
    atividades_principal: List[Dict[str, str]] = []
    if principal_code or principal_desc:
        atividades_principal.append(
            {
                "code": str(principal_code) if principal_code is not None else "",
                "text": principal_desc or "",
            }
        )

    # secundarias
    atividades_secundarias = []
    for item in dados.get("cnaes_secundarios", []) or []:
        if isinstance(item, dict):
            atividades_secundarias.append(
                {
                    "code": str(item.get("codigo") or ""),
                    "text": item.get("descricao") or "",
                }
            )

    # qsa (sócios)
    qsa = []
    for s in dados.get("qsa", []) or []:
        if not isinstance(s, dict):
            continue
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

    return mapped


def normalize_ckan_list(dados_ckan: Any) -> List[Dict[str, str]]:
    """
    Normaliza a resposta do CKAN (dados.gov.br package_search) para uma lista de items:
    cada item com id, titulo, descricao.
    """
    pkgs = []
    if isinstance(dados_ckan, dict):
        result_obj = dados_ckan.get("result")
        if isinstance(result_obj, dict):
            pkgs = result_obj.get("results") or []
    itens: List[Dict[str, str]] = []
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


def normalize_public_list(dados_pub: Any) -> List[Dict[str, str]]:
    """
    Normaliza endpoints públicos alternativos (lista de conjuntos de dados)
    para lista com id, titulo, descricao.
    """
    raw_items = []
    if isinstance(dados_pub, list):
        raw_items = dados_pub
    elif isinstance(dados_pub, dict):
        for key in ("results", "itens", "items", "dados", "data"):
            value = dados_pub.get(key)
            if isinstance(value, list):
                raw_items = value
                break

    itens: List[Dict[str, str]] = []
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
