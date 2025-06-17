# from sentence_transformers import SentenceTransformer
# import numpy as np

# embedding_model = SentenceTransformer('jhgan/ko-sroberta-multitask')

# def get_embedding(text: str) -> np.ndarray:
#     return embedding_model.encode(text)

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_embedding(text: str) -> list[float]:
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"  # 또는 text-embedding-ada-002
    )
    return response.data[0].embedding