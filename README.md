# Clyvo — API e deploy Azure

Backend FastAPI do chatbot Clyvo. A API usa Gemini, oferece duas tools
(`recomendar_plano` e `buscar_clinicas_proximas`), gera fichas de contratação
para encaminhamento ao suporte e salva essas fichas no MongoDB com status
`aguardando_suporte`.

## Estrutura

```text
api/python/
  chatbot.py             # aplicação FastAPI e endpoint /chat
  clyvo_tools.py         # ferramentas da IA
  contratacao.py         # extração estruturada da ficha
  mongo_repository.py    # persistência MongoDB
  pyproject.toml
  uv.lock
azure/
  Dockerfile             # imagem de produção
  deploy_azure.sh        # ACR + Azure Container Instances
```

## Pré-requisitos

Para executar localmente:

- Python 3.14+
- `uv`
- `GEMINI_API_KEY`
- `MONGODB_URI`

Para publicar no Azure:

- Azure CLI (`az`)
- Docker, ou `USE_ACR_BUILD=1`
- `az login`
- assinatura Azure com permissões para Resource Group, ACR e ACI

O script de dependências do Microsoft Foundry também exige `azd`; ele é
necessário apenas para fluxos Foundry/azd, não para o script ACR + ACI deste
projeto.

## Configuração local

Crie `api/python/.env`:

```env
GEMINI_API_KEY=sua_chave
GEMINI_MODEL=gemini-3.7-flash
MONGODB_URI=mongodb+srv://usuario:senha@cluster.mongodb.net/
MONGODB_DATABASE=clyvo
```

O `.env`, `.venv`, bytecode Python e caches não devem ser versionados.

## Comandos locais

```bash
cd /home/roque/Documents/AI-DISRUPTIVE-ARCHITECTURES
cd api/python
uv sync --locked
uv run uvicorn chatbot:app --reload --host 0.0.0.0 --port 8000
```

Em outro terminal:

```bash
curl http://localhost:8000/openapi.json
curl -X POST http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"mensagem":"Quais planos vocês oferecem?"}'
```

## Validação

```bash
cd /home/roque/Documents/AI-DISRUPTIVE-ARCHITECTURES
python3 -m compileall -q api/python
cd api/python && uv lock --check
bash -n ../../azure/deploy_azure.sh
```

Validação opcional da imagem:

```bash
cd /home/roque/Documents/AI-DISRUPTIVE-ARCHITECTURES
docker build --platform linux/amd64 -f azure/Dockerfile -t disruptive-clyvo-api:local .
```

## Deploy Azure — ACR + ACI

O script cria ou usa os recursos abaixo:

- Resource Group: `rg-disruptive-api`
- Azure Container Registry: `acrdisruptive565592`
- Azure Container Instance: `aci-disruptive-api`
- Região padrão: `mexicocentral`

Antes do deploy:

```bash
cd /home/roque/Documents/AI-DISRUPTIVE-ARCHITECTURES
az login
az account set --subscription "<SUBSCRIPTION_ID_OU_NOME>"
export GEMINI_API_KEY="sua_chave"
export MONGODB_URI="mongodb+srv://usuario:senha@cluster.mongodb.net/"
export MONGODB_DATABASE="clyvo"
export GEMINI_MODEL="gemini-3.7-flash"
```

Com Docker local:

```bash
bash azure/deploy_azure.sh
```

Sem Docker local, usando ACR Tasks:

```bash
USE_ACR_BUILD=1 bash azure/deploy_azure.sh
```

O script imprime a URL pública ao final. Para consultar manualmente:

```bash
az container show -g rg-disruptive-api -n aci-disruptive-api \
  --query ipAddress.fqdn -o tsv
az container logs -g rg-disruptive-api -n aci-disruptive-api
curl http://<FQDN>:8000/openapi.json
```

Para remover todo o resource group:

```bash
bash azure/deploy_azure.sh destroy
```

> O comando `destroy` remove permanentemente todos os recursos dentro de
> `rg-disruptive-api`. Confirme o resource group antes de executá-lo.

## Contrato do chatbot

O endpoint aceita:

```json
{
  "mensagem": "Quais clínicas existem perto de mim?",
  "previous_interaction_id": null,
  "latitude": -23.55,
  "longitude": -46.63,
  "pets": [],
  "planos": [],
  "contratacoes": []
}
```

O chatbot não finaliza contratos. Depois da confirmação do tutor, ele gera a
ficha, salva no MongoDB e retorna o `contratacao_id` para o suporte concluir a
operação.
