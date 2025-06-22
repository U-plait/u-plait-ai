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

# 판다스 출력 옵션 설정
pd.set_option("display.max_colwidth", 100)
pd.set_option("display.max_columns", None)
pd.set_option("display.width", None)

# 평가용 데이터 로드
with open("app/evaluation/eval_data.json", "r", encoding="utf-8") as f:
    raw_data = json.load(f)

# Dataset 변환
dataset = Dataset.from_list(raw_data)

# 평가 지표 구성
metrics = [
    answer_relevancy,
    context_recall,
    context_precision,
    faithfulness,
    answer_correctness,
]

# 평가 실행
result = evaluate(dataset, metrics=metrics)

# 평가 결과 출력
df = result.to_pandas()
df.to_csv("ragas_result.csv", index=False)     # CSV