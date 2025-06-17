# vector_store.py
import os
from dotenv import load_dotenv
from langchain_community.vectorstores.pgvector import PGVector
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")
EMBEDDING_SOURCE = os.getenv("EMBEDDING_SOURCE")
HF_MODEL_NAME = os.getenv("HF_MODEL_NAME")
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def get_vector_store() -> PGVector:
    if EMBEDDING_SOURCE == "huggingface":
        embedding_function = HuggingFaceEmbeddings(
            model_name=HF_MODEL_NAME,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True}
        )
    elif EMBEDDING_SOURCE == "openai":
        embedding_function = OpenAIEmbeddings(
            model=OPENAI_MODEL_NAME,
            openai_api_key=OPENAI_API_KEY
        )
    else:
        raise ValueError("Unsupported EMBEDDING_SOURCE")

    return PGVector(
        collection_name=COLLECTION_NAME,
        connection_string=DATABASE_URL,
        embedding_function=embedding_function
    )