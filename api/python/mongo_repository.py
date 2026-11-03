import os
from datetime import datetime, timezone

from bson import ObjectId
from pymongo import MongoClient


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
        resultado = client[database_name]["contratacoes"].insert_one(
            {
                **ficha,
                "status": "aguardando_suporte",
                "criada_em": datetime.now(timezone.utc),
            }
        )
        return str(resultado.inserted_id)
    finally:
        client.close()


def serializar_id(documento: dict) -> dict:
    if isinstance(documento.get("_id"), ObjectId):
        documento["_id"] = str(documento["_id"])
    return documento
