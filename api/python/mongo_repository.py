import os
import logging
from datetime import datetime, timezone

from bson import ObjectId
from pymongo import MongoClient

logger = logging.getLogger(__name__)


def salvar_contratacao(ficha: dict) -> str:
    uri = os.getenv("MONGODB_URI")
    database_name = os.getenv("MONGODB_DATABASE", "clyvo")
    if not uri:
        raise RuntimeError(
            "MONGODB_URI não configurada. Defina a conexão do MongoDB no ambiente."
        )

    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    try:
        client.admin.command("ping")
        colecao = client[database_name]["contratacoes"]
        resultado = colecao.insert_one(
            {
                **ficha,
                "status": "aguardando_suporte",
                "criada_em": datetime.now(timezone.utc),
            }
        )
        contratacao_id = str(resultado.inserted_id)
        logger.info(
            "Ficha salva no MongoDB: database=%s collection=contratacoes id=%s",
            database_name,
            contratacao_id,
        )
        return contratacao_id
    finally:
        client.close()


def serializar_id(documento: dict) -> dict:
    if isinstance(documento.get("_id"), ObjectId):
        documento["_id"] = str(documento["_id"])
    return documento
