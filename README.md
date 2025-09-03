# FAIF - Facilitador de Acesso à Informação Federal
![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0-black.svg)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-orange.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

**FAIF** é um middleware unificado para diversas APIs de dados abertos do governo brasileiro. O objetivo é simplificar o acesso à informação, oferecendo endpoints consistentes e respostas padronizadas para serem consumidas por aplicações externas.

## ✨ Sobre o Projeto

Este projeto atua como uma camada de abstração sobre várias APIs governamentais, cada uma com suas particularidades. Ao oferecer uma única interface com rotas bem definidas e um padrão de resposta consistente, o FAIF acelera o desenvolvimento de aplicações que consomem dados públicos.

## 🚀 Tecnologias Utilizadas

* **Backend:** Flask
* **Banco de Dados:** PostgreSQL
* **ORM:** Flask-SQLAlchemy
* **Migrations:** Flask-Migrate (Alembic)
* **Driver do Banco:** psycopg (v3)
* **Cliente HTTP:** Requests

## 🏁 Como Começar

Siga os passos abaixo para configurar e executar o projeto localmente.

### Pré-requisitos

* Python 3.10+
* Pip
* Um servidor PostgreSQL instalado e rodando.

### Instalação e Configuração

1.  **Clone o repositório:**
```bash
git clone https://github.com/vichsort/FAIFApi.git
cd FAIFApi
```

2.  **Crie e ative um ambiente virtual:**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate
```

3.  **Instale as dependências:**
```bash
pip install -r requirements.txt
```

4.  **Configure as variáveis de ambiente:**
    * Crie uma cópia do arquivo `.env.example` e renomeie para `.env`.
    * Abra o arquivo `.env` e preencha as variáveis com suas informações.

    **`.env.example`:**
```env
# String de conexão do seu banco de dados PostgreSQL
DATABASE_URL="postgresql+psycopg://usuario:senha@host:porta/nome_do_banco"

# Chave da API do Portal da Transparência (se necessário)
TOKEN_PORTAL="sua_chave_aqui"
```

5.  **Configure o Banco de Dados:**
    * Primeiro, defina a variável de ambiente `FLASK_APP`:
        ```bash
          # Windows (PowerShell)
          $env:FLASK_APP = "app"
          # Linux / macOS
          export FLASK_APP=app
        ```
    * Agora, rode o comando de "upgrade" do Flask-Migrate. Isso criará todas as tabelas no seu banco de dados PostgreSQL com base nos modelos definidos em `models.py`.
        ```bash
        flask db upgrade
        ```

### Rodando a Aplicação

Com tudo configurado, inicie o servidor Flask:

```bash
python run.py
````

A API estará disponível em `http://localhost:5000`.

## 📖 Padrão da API

Todas as respostas seguem uma estrutura JSON padronizada para garantir previsibilidade.

### Resposta de Sucesso (`200 OK`)

```json
{
  "ok": true,
  "data": { ... }
}
```

### Resposta de Erro (`4xx` ou `5xx`)

```json
{
  "ok": false,
  "error": {
    "code": "CODIGO_DO_ERRO",
    "message": "Mensagem clara sobre o que aconteceu.",
    "details": { ... } 
  }
}
```

## 🔗 Endpoints da API

-----

### Busca de Deputados por Nome

`GET /faif/deputados?nome=<nome>`

Busca deputados por nome e retorna uma lista simplificada.

  * **Exemplo:** `curl "http://localhost:5000/faif/deputados?nome=tiririca"`
  * **Sucesso:** Retorna `{"ok": true, "data": [{"id": 123, "nome": "...", ...}]}`
  * **Erro Comum:** `400 Bad Request` se o parâmetro `nome` não for fornecido.

### Detalhes de um Deputado por ID

`GET /faif/deputados/<id>`

Retorna os dados detalhados de um deputado específico.

  * **Exemplo:** `curl "http://localhost:5000/faif/deputados/160976"`
  * **Sucesso:** Retorna `{"ok": true, "data": {"id": 160976, "nomeCivil": "...", ...}}`
  * **Erro Comum:** `404 Not Found` se o ID não existir.


## 🏛️ Arquitetura

O design da API é construído sobre alguns pilares para garantir robustez e manutenibilidade:

1.  **Estrutura de Pacote:** A aplicação é organizada como um pacote Python (`app/`) com uma "Application Factory" (`create_app`), o que evita importações circulares e facilita a testabilidade.
2.  **ORM com SQLAlchemy:** A comunicação com o banco de dados é abstraída, permitindo queries seguras e Pythonicas.
3.  **Migrations com Alembic:** As alterações no schema do banco de dados são versionadas e gerenciadas via `Flask-Migrate`.
4.  **Camada de Serviços:** A lógica de negócio e normalização dos dados é separada dos blueprints, mantendo as rotas limpas e focadas.
