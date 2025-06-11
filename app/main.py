from fastapi import FastAPI

app = FastAPI()

# 메인 API 작성, 라우터 설정 등
@app.get("/query/")
def get_answer(query: str):
    return "MAIN API"