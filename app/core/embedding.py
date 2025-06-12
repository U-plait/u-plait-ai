# LangChain 관련 작업
from langchain_community.embeddings import HuggingFaceEmbeddings

embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def get_embedding(text: str) -> list[float]:
    return embedding_model.embed_query(text)