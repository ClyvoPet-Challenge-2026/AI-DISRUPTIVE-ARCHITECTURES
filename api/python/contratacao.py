import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, field_validator

load_dotenv(Path(__file__).with_name(".env"))


class ContratacaoPlanoClyvo(BaseModel):
    nome_tutor: str
    nome_pet: str
    especie: Literal["cao", "gato"]
    idade_pet: int
    tem_doenca_cronica: bool
    plano_escolhido: str
    valor_mensal: float

    @field_validator("especie", mode="before")
    @classmethod
    def normalizar_especie(cls, valor: object) -> object:
        if not isinstance(valor, str):
            return valor
        especie = valor.casefold().strip()
        if especie in {"cachorro", "cão", "cao", "dog", "canino"}:
            return "cao"
        if especie in {"gato", "gata", "cat", "felino", "felina"}:
            return "gato"
        return especie


def gerar_ficha_pydantic(historico_conversa: str) -> ContratacaoPlanoClyvo:
    client = genai.Client(
        api_key=os.getenv("GEMINI_API_KEY"),
        http_options=types.HttpOptions(
            timeout=60000,
            retry_options=types.HttpRetryOptions(attempts=1),
        ),
    )
    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-3.7-flash"),
        contents=f"""
Você é um extrator de dados da Clyvo.
Extraia somente os dados da ficha aprovada pelo tutor no histórico abaixo.
Não invente valores. Se algum dado obrigatório não estiver presente,
retorne uma resposta inválida para que a aplicação informe o problema.

HISTÓRICO:
{historico_conversa}
""",
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ContratacaoPlanoClyvo,
        ),
    )
    return ContratacaoPlanoClyvo.model_validate_json(response.text)
