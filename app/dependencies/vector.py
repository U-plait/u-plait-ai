from langchain_community.vectorstores.pgvector import PGVector
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
import os

vectorstore = None

def init_vectorstore():
    global vectorstore

    embedding_source = os.getenv("EMBEDDING_SOURCE")
    if embedding_source == "huggingface":
        embedding_function = HuggingFaceEmbeddings(
            model_name=os.getenv("HF_MODEL_NAME"),
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True}
        )
    elif embedding_source == "openai":
        embedding_function = OpenAIEmbeddings(
            model=os.getenv("OPENAI_MODEL_NAME"),
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
    else:
        raise ValueError("Unsupported EMBEDDING_SOURCE")

    vectorstore = PGVector(
        collection_name=os.getenv("COLLECTION_NAME"),
        connection_string=os.getenv("DATABASE_URL"),
        embedding_function=embedding_function
    )

def get_vectorstore():
    if vectorstore is None:
        raise ValueError("VectorStore not initialized")
    return vectorstore