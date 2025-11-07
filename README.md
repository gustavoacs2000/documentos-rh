Com certeza. Foi um prazer construir este projeto com você. Foi uma sessão de desenvolvimento muito produtiva e com ótimas ideias.

Aqui está um arquivo `README.md` extremamente detalhado, que documenta toda a nossa jornada, desde a concepção até a lógica de validação.

-----

# Portal de RH com OCR e Validação Automática

Este projeto é um sistema de back-end robusto, construído em Django e Docker, projetado para gerenciar e validar automaticamente documentos de funcionários. O sistema utiliza OCR (Tesseract) para extrair texto de Imagens e PDFs e, em seguida, compara esse texto com um conjunto de regras de validação dinâmicas definidas pelo RH.

## Stack de Tecnologia

  * **Backend:** Python 3.11 com Django
  * **Banco de Dados:** PostgreSQL
  * **Armazenamento de Arquivos:** Cloudflare R2 (usando a API S3 da `django-storages` e `boto3`)
  * **Tarefas Assíncronas (OCR):** Celery com Redis como broker
  * **Motor de OCR:** Tesseract (com `pytesseract`)
  * **Processamento de PDF:** `poppler-utils` (com `pdf2image`)
  * **Ambiente de Desenvolvimento:** Docker e Docker Compose

## Funcionalidades Principais

  * **Painel de Admin (RH):** Uma interface de administração (`/admin`) robusta onde o RH pode:
      * Cadastrar diferentes "Tipos de Documento" (ex: RG, CPF, Contrato).
      * Criar "Regras de Validação" dinâmicas para cada tipo de documento (ex: "RG deve conter o texto 'Carteira de Identidade'").
      * Revisar, aprovar ou rejeitar documentos enviados.
      * Ver o texto extraído pelo OCR e o feedback da validação automática.
  * **Portal do Funcionário (MVP):**
      * Um portal frontal (`/dashboard`) para o funcionário comum.
      * Sistema de login e logout (`/accounts/login/`).
      * Um dashboard que lista todos os documentos necessários e seus status (Pendente, Em Revisão, Aprovado, Rejeitado).
      * Páginas de upload dedicadas para cada tipo de documento.
  * **Sistema de OCR Assíncrono (Celery):**
      * Uploads de arquivos são instantâneos. O processamento de OCR é enviado para uma fila.
      * Um "worker" do Celery, rodando em um contêiner separado, pega a tarefa.
      * Suporta OCR de **Imagens (JPG, PNG)** e **PDFs (incluindo múltiplas páginas)**.
  * **Motor de Validação Automática:**
      * Após o OCR, o sistema busca as regras cadastradas para aquele documento.
      * Se o documento falha nas regras, seu status é automaticamente mudado para "Rejeitado" e as falhas são salvas no campo "Feedback do RH".
      * Se o documento passa, seu status muda para "Aguardando Revisão".
  * **Níveis de Permissão:**
      * **Admin (Superusuário):** Acesso total.
      * **RH (Staff):** Acesso ao `/admin`, mas *apenas* para gerenciar documentos (não pode criar usuários).
      * **Funcionário (Usuário Comum):** *Sem acesso* ao `/admin`. Usa apenas o portal frontal.

## Estrutura Final do Projeto

```
/documentos-rh/
│
├── .env                  # (Secreto) Guarda senhas e chaves de API
├── .env.example          # Molde para as variáveis de ambiente
├── .gitignore            # Ignora o .env e arquivos de cache
├── docker-compose.yml    # Orquestra todos os serviços
├── Dockerfile            # Receita para construir a imagem Python/Tesseract/Poppler
├── README.md             # (Este arquivo)
├── requirements.txt      # Lista de bibliotecas Python
│
├── src/                  # Todo o código-fonte do Django
│   ├── documents/        # O nosso app principal
│   │   ├── migrations/   # Arquivos de migração do banco
│   │   ├── __init__.py
│   │   ├── admin.py      # Configuração do painel admin (com Inlines)
│   │   ├── apps.py
│   │   ├── forms.py      # O DocumentUploadForm (ModelForm)
│   │   ├── models.py     # O cérebro: DocumentType, EmployeeDocument, ValidationRule
│   │   ├── tasks.py      # A lógica do OCR e Validação (Celery)
│   │   ├── tests.py
│   │   ├── urls.py       # Rotas do portal do funcionário (dashboard, upload)
│   │   └── views.py      # Lógica do portal do funcionário
│   │
│   ├── portal/           # O projeto principal do Django
│   │   ├── __init__.py   # Modificado para carregar o Celery
│   │   ├── asgi.py
│   │   ├── celery.py     # Arquivo de configuração do Celery
│   │   ├── settings.py   # Arquivo principal de configuração
│   │   ├── urls.py       # Arquivo principal de rotas (admin, auth, app)
│   │   └── wsgi.py
│   │
│   └── manage.py         # Utilitário de linha de comando do Django
│
└── templates/              # Pasta de templates HTML
    ├── base.html           # Molde principal (com nav bar)
    ├── dashboard.html      # Tabela de status de documentos
    ├── upload_document.html  # Formulário de upload
    │
    └── registration/
        └── login.html      # Página de login personalizada
```

-----

## Configuração do Ambiente (Passo a Passo)

Esta seção detalha como configurar o ambiente de desenvolvimento do zero, incluindo as armadilhas que encontramos.

### Pré-requisitos

  * **Docker** e **Docker Compose** instalados.
  * **Docker Desktop** (ou o motor Docker) deve estar em execução.

### 1\. Preparação Inicial

1.  Clone o repositório (ou crie os arquivos).
2.  **MUITO IMPORTANTE:** Crie a pasta `src/` vazia na raiz do projeto. O `Dockerfile` precisa copiá-la durante o build inicial.
    ```bash
    mkdir src
    ```

### 2\. Variáveis de Ambiente (.env)

1.  Copie o `.env.example` para um novo arquivo `.env`:
    ```bash
    cp .env.example .env
    ```
2.  **Edite o `.env`** e preencha suas chaves.

#### Como Obter as Chaves do Cloudflare R2:

1.  Vá ao seu painel Cloudflare \> **R2**.
2.  Clique em **"Manage R2 API Tokens"** (Gerenciar Tokens).
3.  Clique em **"Create API Token"**.
4.  Dê um nome e escolha a permissão **"Object Read & Write"**.
5.  Copie o **Access Key ID** (`AWS_ACCESS_KEY_ID`) e o **Secret Access Key** (`AWS_SECRET_ACCESS_KEY`). **A chave secreta só é mostrada uma vez.**
6.  Volte para seu bucket R2, clique nele. O **S3 API Endpoint** estará na página de visão geral. É ele que você usará para `AWS_S3_ENDPOINT_URL`.

**Errado:** `.../nome-do-bucket`
**Correto:** `https://<account-id>.r2.cloudflarestorage.com`

### 3\. O Truque do "Ovo e a Galinha" (Primeira Subida)

Tivemos um problema em que o serviço `web` precisava do `manage.py` para rodar, mas o `manage.py` ainda não existia. A solução é subir o contêiner no modo "sleep".

1.  **Edite `docker-compose.yml`** (Temporariamente):

    ```yaml
    services:
      web:
        build: .
        # Comente o comando original
        # command: python manage.py runserver 0.0.0.0:8000
        # Adicione este comando para manter o contêiner "vivo"
        command: sleep infinity 
        volumes:
          - ./src:/app
        # ... resto do serviço web ...
    ```

2.  **Construa e suba os contêineres pela primeira vez:**

    ```bash
    docker-compose up -d --build
    ```

    (Isso irá instalar o Tesseract, Poppler e todas as bibliotecas Python).

### 4\. Inicialização do Django

Com os contêineres rodando (e o `web` dormindo), podemos "entrar" nele para criar os arquivos do Django.

1.  **Criar o Projeto:**

    ```bash
    docker-compose exec web django-admin startproject portal .
    ```

    *(O `.` no final é crucial para criar o projeto na pasta `src/`)*

2.  **Criar o App:**

    ```bash
    docker-compose exec web python manage.py startapp documents
    ```

### 5\. Configuração Final do Ambiente

1.  **Configure o Django:** Este é o momento de editar todos os arquivos em `src/` (como `settings.py`, `portal/celery.py`, `portal/__init__.py`), conforme detalhado na "Estrutura do Projeto".
2.  **Reverta o `docker-compose.yml`:** Agora que o `src/manage.py` existe, reverta o `docker-compose.yml` para seu estado final (remova o `sleep infinity` e descomente o `command: python manage.py runserver...`).
3.  **Reinicie os serviços com o comando final:**
    ```bash
    docker-compose up -d --build
    ```

### 6\. Finalização do Banco de Dados

1.  **Crie as tabelas do Django:**

    ```bash
    docker-compose exec web python manage.py migrate
    ```

2.  **Crie seu superusuário (Admin):**

    ```bash
    docker-compose exec web python manage.py createsuperuser
    ```

### 7\. Migrações dos Modelos (Fase 3)

Após definir os modelos em `models.py`, o processo de migração foi:

```bash
# 1. Criar o arquivo de migração
docker-compose exec web python manage.py makemigrations documents
# 2. Aplicar a migração (criar as tabelas)
docker-compose exec web python manage.py migrate
```

-----

## Lógica Central: OCR e Validação

Esta é a parte mais "mágica" do projeto, detalhada no arquivo `src/documents/tasks.py`.

**Fluxo do `process_document_ocr`:**

1.  A tarefa é chamada por um *signal* do Django (`post_save`) sempre que um `EmployeeDocument` é criado.
2.  A tarefa lê o arquivo (`.file.read()`) do Cloudflare R2 para a memória.
3.  **Tenta** processar o arquivo como uma Imagem (`Image.open`).
4.  **Se falhar** (ex: é um PDF), ela entra no `except` e **tenta** processar como um PDF (`convert_from_bytes`).
5.  Se for um PDF, ela faz um loop em cada página, passa o Tesseract em cada uma, e junta o texto.
6.  Se falhar em ambas, ela marca o documento como "Rejeitado" com uma nota de erro.
7.  Se o OCR for bem-sucedido, ela chama a função auxiliar `run_validation`.

**Fluxo do `run_validation`:**

1.  Busca todas as `ValidationRule`s associadas àquele tipo de documento (ex: as 3 regras do "RG").
2.  Se não houver regras, marca como "Aguardando Revisão" (`REVIEW`) e sai.
3.  Faz um loop em cada regra e verifica (sem distinção de maiúsculas/minúsculas) se o `rule_value` (ex: "Carteira de Identidade") está `in` o texto extraído.
4.  Cria uma lista de `failed_rules`.
5.  Se a lista de falhas estiver vazia, marca como "Aguardando Revisão" (`REVIEW`) com uma nota de sucesso.
6.  Se houverem falhas, marca como "Rejeitado" (`REJECTED`) e usa a lista de falhas como `notes_hr` (Feedback do RH).

-----

## Registro de Erros (Troubleshooting)

Durante o desenvolvimento, encontramos e corrigimos vários problemas comuns:

  * **`service "web" is not running`:** Resolvido usando `command: sleep infinity` durante a criação inicial do projeto (problema do "ovo e a galinha").
  * **`No changes detected` (ao rodar `makemigrations`)**:
      * **Causa 1:** O arquivo `models.py` não foi salvo.
      * **Causa 2:** Um `ImportError` no `models.py` (especificamente `from .tasks import ...`) estava quebrando o Django antes que ele pudesse ler os modelos.
      * **Solução:** Mover a importação para *dentro* da função (`trigger_ocr_on_upload`) que a utiliza.
  * **`relation "documents_validationrule" does not exist`:**
      * **Causa:** O modelo (`ValidationRule`) foi criado no `models.py` e registrado no `admin.py`, mas o comando `docker-compose exec web python manage.py migrate` não foi executado.
      * **Solução:** Rodar `makemigrations` e `migrate`.
  * **`NoReverseMatch for 'dashboard'` (Erro de Template):**
      * **Causa:** O `base.html` usava `{% url 'dashboard' %}`, mas essa rota (URL com `name='dashboard'`) ainda não existia no `urls.py`.
      * **Solução:** Criar a `dashboard_view` e a rota correspondente.
  * **404 após o Login:**
      * **Causa:** O Django redireciona para `/accounts/profile/` por padrão.
      * **Solução:** Definir `LOGIN_REDIRECT_URL = 'dashboard'` no `settings.py`.
  * **"Tela em Branco" no Dashboard:**
      * **Causa:** O arquivo `templates/dashboard.html` estava vazio ou não foi salvo.
  * **Erro de Importação no `views.py`:**
      * **Causa:** Usamos `redirect` e `get_object_or_404` sem importá-los.
      * **Solução:** Adicioná-los ao `from django.shortcuts import ...`.
  * **Tarefa de OCR (PDF) não funcionava:**
      * **Causa:** O `celeryworker` estava rodando o código antigo, sem a lógica de PDF.
      * **Solução:** Rodar `docker-compose up -d --build` (e não apenas `restart`) para forçar a reconstrução da imagem com as novas dependências (`poppler-utils` e `pdf2image`).

## Próximos Passos (Melhorias Futuras)

O *backend* está sólido, mas o projeto pode evoluir:

1.  **Frontend Robusto:** Substituir os templates básicos do Django por um frontend moderno (React, Vue, HTMX) para uma experiência de usuário (UX) melhor no portal do funcionário.
2.  **Validação por Regex:** Implementar a lógica para a regra `REGEX_MATCH` no `tasks.py`, permitindo ao RH validar formatos de CPF, Datas, etc.
3.  **Visualização Segura:** Criar uma view que sirva os arquivos do R2 (que deve ser privado) usando URLs pré-assinadas (Presigned URLs), em vez de links diretos.
4.  **Testes:** Escrever testes unitários e de integração para os modelos e para a tarefa de OCR.