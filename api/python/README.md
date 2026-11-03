# API Python da Clyvo

API FastAPI do chatbot Clyvo, com ferramentas de recomendação de planos,
busca de clínicas, geração de ficha para suporte e persistência no MongoDB.

## Requisitos

- Python 3.14+
- `uv`
- `GEMINI_API_KEY`
- `MONGODB_URI` para gerar e salvar fichas

## Executar localmente

Na raiz do repositório:

```bash
cd api/python
uv sync --locked
cp .env.example .env
uv run uvicorn chatbot:app --reload --host 0.0.0.0 --port 8000
```

Variáveis:

```env
GEMINI_API_KEY=sua_chave
GEMINI_MODEL=gemini-3.7-flash
MONGODB_URI=mongodb+srv://usuario:senha@cluster.mongodb.net/
MONGODB_DATABASE=clyvo
```

Endpoints principais:

- `GET /docs` — Swagger
- `GET /openapi.json` — contrato OpenAPI
- `POST /chat` — conversa com o chatbot

Exemplo:

```bash
curl -X POST http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"mensagem":"Quero conhecer os planos para meu cachorro"}'
```

## Verificações

```bash
python3 -m compileall -q .
uv lock --check
```

## Docker

O Dockerfile fica em `azure/Dockerfile` e deve ser executado a partir da
raiz, pois copia `api/python/pyproject.toml` e `api/python/uv.lock`:

```bash
docker build --platform linux/amd64 -f azure/Dockerfile -t disruptive-clyvo-api:local .
docker run --rm -p 8000:8000 \
  --env-file api/python/.env \
  disruptive-clyvo-api:local
```

## Deploy no Azure

Consulte o README da raiz para o fluxo completo de ACR + Azure Container
Instances.
