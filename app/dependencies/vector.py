"""
VectorStore 초기화. EMBEDDING_SOURCE 값에 따라 embedding function 선택:
  - openai      : OpenAIEmbeddings (실 API)
  - huggingface : HuggingFaceEmbeddings (로컬 모델)
  - mock        : DeterministicFakeEmbedding (로컬 시연/부하 — 재현 가능)
"""

import os

from langchain_community.vectorstores.pgvector import PGVector
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.embeddings import DeterministicFakeEmbedding

vectorstore = None


def init_vectorstore():
    global vectorstore

    embedding_source = (os.getenv("EMBEDDING_SOURCE") or "").lower()

    if embedding_source == "huggingface":
        embedding_function = HuggingFaceEmbeddings(
            model_name=os.getenv("HF_MODEL_NAME"),
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
    elif embedding_source == "openai":
        embedding_function = OpenAIEmbeddings(
            model=os.getenv("OPENAI_MODEL_NAME"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
        )
    elif embedding_source == "mock":
        print("[VectorStore] EMBEDDING_SOURCE=mock → DeterministicFakeEmbedding 사용")
        size = int(os.getenv("MOCK_EMBEDDING_DIM", "384"))
        embedding_function = DeterministicFakeEmbedding(size=size)
    else:
        raise ValueError(
            "Unsupported EMBEDDING_SOURCE — 'openai' | 'huggingface' | 'mock' 중 하나를 지정하세요."
        )

    vectorstore = PGVector(
        collection_name=os.getenv("COLLECTION_NAME", "uplait_plans"),
        connection_string=os.getenv("DATABASE_URL"),
        embedding_function=embedding_function,
    )


def get_vectorstore():
    if vectorstore is None:
        raise ValueError("VectorStore not initialized")
    return vectorstore
