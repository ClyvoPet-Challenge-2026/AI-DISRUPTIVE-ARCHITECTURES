import os
import re
import logging
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

load_dotenv(Path(__file__).with_name(".env"))

from clyvo_tools import FERRAMENTAS, FUNCOES_AUTORIZADAS
from contratacao import ContratacaoPlanoClyvo, gerar_ficha_pydantic
from mongo_repository import salvar_contratacao

app = FastAPI()
logger = logging.getLogger(__name__)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(
    api_key=api_key,
    http_options=types.HttpOptions(
        timeout=60000,
        retry_options=types.HttpRetryOptions(attempts=1),
    ),
)

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.7-flash")
SYSTEM_PROMPT = """
# CONTEXTO E PERSONA
Você é o assistente virtual oficial da **Clyvo**, uma plataforma de e-commerce e planos de saúde pet.
Seu objetivo é orientar tutores na escolha do melhor plano de saúde para o pet deles e localizar clínicas parceiras credenciadas.

# GUARDRAIL DE ESCOPO (RIGOROSO)
Você é um robô de atendimento EXCLUSIVO da Clyvo.
Se o cliente fizer QUALQUER pergunta ou pedido fora do contexto de planos de saúde pet ou clínicas credenciadas (ex: ensinar programação Python, falar sobre tempo, curiosidades, piadas, futebol):
1. Recuse imediatamente e de forma cortês.
2. Informe que você foi programado APENAS para ajudar com planos de saúde e serviços da Clyvo.
3. Traga o foco de volta perguntando sobre as necessidades de saúde do pet dele.

# FLUXO DE ATENDIMENTO E FERRAMENTAS
1. Para recomendar o plano ideal, colete de forma natural:
   - Identifique primeiro qual pet está sendo tratado usando o contexto cadastral.
   - Se houver mais de um pet e o tutor não deixar claro qual é, pergunte o nome do pet.
   - Idade do pet
   - Se possui doença crônica ou tratamento contínuo (True/False)
   - Orçamento mensal máximo do tutor (R$)
   - Nível de tolerância a risco / cobertura desejada (baixo, medio, medio-alto, alto)
   Em seguida, chame a ferramenta `recomendar_plano`.
   - Se o pet já possuir uma contratação ativa no contexto, informe isso e não trate
     uma nova contratação como existente sem a solicitação explícita do tutor.

2. Caso o cliente informe o nome de uma clínica ou hospital, chame a ferramenta `buscar_clinicas_proximas` usando o nome informado.
3. Caso o cliente solicite clínicas próximas sem informar um nome, use a latitude e longitude fornecidas no contexto técnico da mensagem e chame a ferramenta `buscar_clinicas_proximas`. Nunca peça a localização novamente.

# REGRA DE CONFIRMAÇÃO E FICHA FINAL
O chatbot nunca conclui, ativa ou confirma o fechamento de um plano.
Ao definir o plano com o tutor:
1. Apresente o resumo completo (Nome do tutor, Nome do pet, Plano escolhido e Valor mensal).
2. Pergunte EXPLICITAMENTE: "Todos os dados estão corretos? Posso gerar a ficha para encaminhamento ao suporte?"
3. Apenas após a confirmação dos dados, gere a ficha e informe que o atendimento do suporte é necessário para finalizar a contratação.
"""


class PetContext(BaseModel):
    id: int
    nome: str
    especie: str | None = None
    raca: str | None = None
    data_nascimento: str | None = None


class PlanContext(BaseModel):
    id: int
    nome: str
    valor_mensal: float


class ContractContext(BaseModel):
    id: int
    pet_id: int
    plano_id: int
    plano_nome: str
    status: str
    valor_mensal: float


class ChatRequest(BaseModel):
    mensagem: str
    previous_interaction_id: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    pets: list[PetContext] = Field(default_factory=list)
    planos: list[PlanContext] = Field(default_factory=list)
    contratacoes: list[ContractContext] = Field(default_factory=list)


class ChatResponse(BaseModel):
    resposta: str
    interaction_id: str
    contratacao_id: str | None = None
    contratacao: ContratacaoPlanoClyvo | None = None


def mensagem_confirma_ficha(mensagem: str) -> bool:
    texto = re.sub(r"[^\w\s]", " ", mensagem.casefold())
    if re.search(r"\b(não|nao|cancelar|cancele|desist[io])\b", texto):
        return False
    return bool(
        re.search(
            r"\b(sim|confirmo|confirmar|pode confirmar|pode fechar|pode contratar)\b",
            texto,
        )
    )


def obter_historico(interaction_id: str, limite: int = 20) -> str:
    interacoes = []
    atual_id = interaction_id
    while atual_id and len(interacoes) < limite:
        atual = client.interactions.get(atual_id, include_input=True)
        interacoes.append(atual)
        atual_id = getattr(atual, "previous_interaction_id", None)

    linhas = []
    for interacao in reversed(interacoes):
        entrada = getattr(interacao, "input", None)
        if entrada:
            linhas.append(f"Entrada: {entrada}")
        if getattr(interacao, "output_text", None):
            linhas.append(f"Clyvo: {interacao.output_text}")
    return "\n".join(linhas)


def processar_mensagem(
    mensagem: str,
    previous_interaction_id: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    pets: list[PetContext] | None = None,
    planos: list[PlanContext] | None = None,
    contratacoes: list[ContractContext] | None = None,
) -> ChatResponse:
    mensagem_com_contexto = mensagem
    if latitude is not None and longitude is not None:
        mensagem_com_contexto = (
            f"{mensagem}\n\n"
            "[CONTEXTO TÉCNICO — localização atual do tutor]\n"
            f"latitude: {latitude}\n"
            f"longitude: {longitude}\n"
            "Ao buscar clínicas próximas, use essas coordenadas automaticamente "
            "e não peça a localização novamente."
        )
    contexto_cadastro = (
        "\n\n[CONTEXTO CADASTRAL DO TUTOR — fonte de verdade]\n"
        f"pets: {[pet.model_dump() for pet in pets or []]}\n"
        f"planos disponíveis: {[plano.model_dump() for plano in planos or []]}\n"
        "contratações/planos dos pets: "
        f"{[contratacao.model_dump() for contratacao in contratacoes or []]}\n"
        "Use esse contexto para identificar o pet e os planos existentes. "
        "Se houver mais de um pet e a mensagem não identificar qual deles é o alvo, "
        "pergunte o nome do pet antes de recomendar, alterar ou gerar ficha. "
        "Não invente pets, planos ou contratações."
    )
    mensagem_com_contexto += contexto_cadastro

    argumentos = {
        "model": MODEL,
        "system_instruction": SYSTEM_PROMPT,
        "input": mensagem_com_contexto,
        "tools": FERRAMENTAS,
    }

    if previous_interaction_id:
        argumentos["previous_interaction_id"] = previous_interaction_id

    interaction = client.interactions.create(**argumentos)
    contratacao = None
    contratacao_id = None

    for _ in range(5):
        chamadas = [
            step
            for step in (interaction.steps or [])
            if getattr(step, "type", None) == "function_call"
        ]
        if not chamadas:
            break

        resultados = []
        for chamada in chamadas:
            funcao = FUNCOES_AUTORIZADAS.get(chamada.name)
            if funcao is None:
                raise RuntimeError(f"Tool não autorizada: {chamada.name}")

            try:
                resultado = funcao(**chamada.arguments)
            except (TypeError, ValueError, KeyError) as error:
                resultados.append(
                    {
                        "type": "function_result",
                        "call_id": chamada.id,
                        "name": chamada.name,
                        "is_error": True,
                        "result": {"erro": str(error)},
                    }
                )
            else:
                resultados.append(
                    {
                        "type": "function_result",
                        "call_id": chamada.id,
                        "name": chamada.name,
                        "result": resultado,
                    }
                )

        interaction = client.interactions.create(
            model=MODEL,
            system_instruction=SYSTEM_PROMPT,
            input=resultados,
            previous_interaction_id=interaction.id,
            tools=FERRAMENTAS,
        )
    else:
        raise RuntimeError("A IA excedeu o limite de chamadas encadeadas de tools.")

    if mensagem_confirma_ficha(mensagem):
        historico = obter_historico(interaction.id)
        contratacao = gerar_ficha_pydantic(historico)
        contratacao_id = salvar_contratacao(contratacao.model_dump())
        resposta = (
            "A ficha foi gerada e registrada para análise. "
            "O chatbot não finaliza a contratação do plano. "
            f"Informe o ID {contratacao_id} ao suporte da Clyvo para concluir a operação."
        )
    else:
        resposta = interaction.output_text

    return ChatResponse(
        resposta=resposta,
        interaction_id=interaction.id,
        contratacao_id=contratacao_id,
        contratacao=contratacao,
    )


@app.post("/chat", response_model=ChatResponse)
def conversar(request: ChatRequest) -> ChatResponse:
    try:
        return processar_mensagem(
            request.mensagem,
            request.previous_interaction_id,
            request.latitude,
            request.longitude,
            request.pets,
            request.planos,
            request.contratacoes,
        )
    except Exception as error:
        logger.exception("Falha ao processar mensagem do chatbot")
        raise HTTPException(
            status_code=503,
            detail="A assistente está temporariamente indisponível. Tente novamente em instantes.",
        ) from error
