import json
import os
from typing import List

EVAL_DATA_PATH = "app/evaluation/eval_data.json"

def save_eval_sample(question: str, answer: str, contexts: List[str]): 
    new_data = {
        "question": question,
        "answer": answer,
        "ground_truth": "",
        "contexts": contexts
    }

    if os.path.exists(EVAL_DATA_PATH):
        with open(EVAL_DATA_PATH, "r", encoding="utf-8") as f:
            try:
                existing = json.load(f)
            except json.JSONDecodeError:
                existing = []
    else:
        existing = []

    existing.append(new_data)

    with open(EVAL_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)