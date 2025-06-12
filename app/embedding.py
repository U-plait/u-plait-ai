from sentence_transformers import SentenceTransformer
import numpy as np

embedding_model = SentenceTransformer('jhgan/ko-sroberta-multitask')

def get_embedding(text: str) -> np.ndarray:
    return embedding_model.encode(text)
