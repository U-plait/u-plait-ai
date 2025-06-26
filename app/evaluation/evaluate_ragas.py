from ragas.metrics import (
    answer_relevancy,
    context_recall,
    context_precision,
    faithfulness,
    answer_correctness,
)
from ragas import evaluate
from datasets import Dataset
import json
import pandas as pd

from dotenv import load_dotenv
load_dotenv()

pd.set_option("display.max_colwidth", 100)
pd.set_option("display.max_columns", None)
pd.set_option("display.width", None)

with open("app/evaluation/eval_data.json", "r", encoding="utf-8") as f:
    raw_data = json.load(f)

dataset = Dataset.from_list(raw_data)

metrics = [
    answer_relevancy,
    context_recall,
    context_precision,
    faithfulness,
    answer_correctness,
]

result = evaluate(dataset, metrics=metrics)

df = result.to_pandas()
df.to_csv("ragas_result.csv", index=False)