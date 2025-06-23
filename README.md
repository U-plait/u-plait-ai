![header](https://capsule-render.vercel.app/api?type=venom&color=gradient&height=300&section=header&text=Uplait&fontSize=90&fontColor=ffffff)

# U-Plait 프로젝트 소개

**U-Plait**는 LG U+ 고객의 통신성향에 맞는 요금제 및 결합 상품을 추천해주는 서비스입니다.  
LLM 기반 챗봇과의 대화를 통해 사용자는 자신에게 알맞는 요금제를 비교, 추천 받을 수 있습니다.


### [U-plait : 프론트엔드 레포지토리 바로가기](https://github.com/U-plait/u-plait-fe)
### [U-plait : 백엔드 레포지토리 바로가기](https://github.com/U-plait/u-plait-be)
<br><br />
# 1. 프로젝트의 목적
1. LLM 기반 챗봇을 활용해 사용자에게 맞춤형 통신 요금제를 추천함으로써,
통신 상품 탐색 과정을 보다 효율적이고 편리하게 만들어 사용자 경험을 향상시키고자 합니다.

2. 챗봇을 통해 고객센터로 연결되는 반복적이고 단순한 상담 업무 부담을 줄임으로써,
유플러스의 AICC 영역에서 실제 적용 가능한 상담 자동화 솔루션을 제공합니다.
<br><br />

# 3. 팀원 소개

<table>
  <tr>
    <td align="center"><b>조장</b></td>
    <td align="center"><b>Backend</b></td>
    <td align="center"><b>Backend</b></td>
    <td align="center"><b>Backend</b></td>
    <td align="center"><b>Backend</b></td>
    <td align="center"><b>Backend</b></td>
    <td align="center"><b>Backend</b></td>
  </tr>
  <tr>
    <td align="center">
      <a href="https://github.com/dev-kim">
        <img src="https://avatars.githubusercontent.com/dev-kim" width="100px;" alt="dev-kim"/><br />
        <sub><b>임동준</b></sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/hayong39">
        <img src="https://avatars.githubusercontent.com/hayong39" width="100px;" alt="hayong39"/><br />
        <sub><b>변하영</b></sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/Yyang-YE">
        <img src="https://avatars.githubusercontent.com/Yyang-YE" width="100px;" alt="Yyang-YE"/><br />
        <sub><b>양여은</b></sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/songhyeongyu">
        <img src="https://avatars.githubusercontent.com/songhyeongyu" width="100px;" alt="songhyeongyu"/><br />
        <sub><b>송현규</b></sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/etoile0626">
        <img src="https://avatars.githubusercontent.com/etoile0626" width="100px;" alt="etoile0626"/><br />
        <sub><b>최윤제</b></sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/Heoooo">
        <img src="https://avatars.githubusercontent.com/Heoooo" width="100px;" alt="Heoooo"/><br />
        <sub><b>허진혁</b></sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/Suhun0331">
        <img src="https://avatars.githubusercontent.com/Suhun0331" width="100px;" alt="Suhun0331"/><br />
        <sub><b>김수훈</b></sub>
      </a>
    </td>
  </tr>
  <tr>
    <td align="center">기획 및 발표 총괄</td>
    <td align="center">챗봇 개발, 배포</td>
    <td align="center">챗봇 개발, 디자인</td>
    <td align="center">Spring 서버 개발</td>
    <td align="center">Spring 서버 개발</td>
    <td align="center">Spring 서버 개발</td>
    <td align="center">기획 및 문서작업</td>
  </tr>
</table>

<br><br />
# 4. 기술 스택 (Tech Stack)
### 4.3 AI

| 구분          | 기술 |
|---------------|------|
| 백엔드 연동   | ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white) |
| AI 플랫폼     | ![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=flat&logo=openai&logoColor=white)<br>![Hugging Face](https://img.shields.io/badge/Hugging%20Face-FFD21F?style=flat&logo=huggingface&logoColor=black) |
| LLM 프레임워크 | ![LangChain](https://img.shields.io/badge/LangChain-000000?style=flat&logo=python&logoColor=white) |
| AI 평가 도구  | ![RAGAS](https://img.shields.io/badge/RAGAS-0056D2?style=flat&logo=python&logoColor=white) |

<br><br />

# 5. 기능 소개

### 1. 요금제 추천 
<img width="400" height="550" alt="image" src="https://github.com/user-attachments/assets/a3de4b35-87ce-4a3f-b6bf-29b9509221f4" />

👉 **사용자의 질문에서 맥락을 파악하여 이에 알맞은 요금제를 추천합니다.**

<br><br />

### 2. 선호 태그 기반 요금제 추천
<img width="400" height="550" alt="image" src="https://github.com/user-attachments/assets/32e01253-90c8-49d1-8cb5-12e69687d0a7" />

👉 **사용자의 정보와 사용자의 선호태그에 기반한 요금제를 추천합니다.**

<br><br />

### 3. 대화 로그 기반 질의(멀티턴)
<tr>
    <td align="center">
      <img width="400" height="550" alt="image" src="https://github.com/user-attachments/assets/64dc572f-ad54-4a5b-86d9-77044e75022b" />
    </td>
    <td align="center">
      <img width="400" height="550" alt="image" src="https://github.com/user-attachments/assets/251e2d24-93af-4bc1-958e-34aa6b36c453" />
    </td>
  </tr>

👉 **이전 질문 "시니어 요금제 추천"을 반영한 답변을 합니다.**

<br><br />

# 6. RAG 기반 요금제 추천 챗봇 데이터 흐름도
<img width="500" alt="image" src="https://github.com/user-attachments/assets/52efac97-57d9-4633-b176-655f6ed95e4a" />

- 사용자 정보와 사용자 선호태그를 이용하여 사용자 맞춤 요금제를 추천할 수 있습니다.
- 채팅을 통해서 사용자 선호태그를 갱신합니다.

# 7. 임베딩 모델별 응답 품질 벤치마크

## 7-1. 비교 모델 목록

### 1. [intfloat/multilingual-e5-small · Hugging Face](https://huggingface.co/intfloat/multilingual-e5-small)
- 임베딩 벡터 차원수 : 384 (제일 작음)
- 특징 : 다국어 지원

### 2. [jhgan/ko-sroberta-multitask · Hugging Face](https://huggingface.co/jhgan/ko-sroberta-multitask)
- 임베딩 벡터 차원수 : 768
- 특징 : 한국어 특화 다목적 태스크 특화 모델

### 3. [text-embedding-3-small · OpenAI](https://platform.openai.com/docs/models/text-embedding-3-small)
- 임베딩 벡터 차원수 : 1536
- 특징 : 최신 고성능 임베딩, 비용 효율

### 4. [text-embedding-3-small · OpenAI](https://platform.openai.com/docs/models/text-embedding-3-large)
- 임베딩 벡터 차원수 : 3072
- 특징 : OpenAI 최상위 임베딩, 고비용 & 고성능

---

- 사용자의 질문에 대한 정확성, 맥락 반영, 신뢰도 측면에서 주요 임베딩 모델들을 비교 분석하였습니다.
- 질문-답변 쌍을 직접 평가하여, 실사용 기반에서의 응답 품질을 수치화하였습니다.
- 최종적으로 "jhgan/ko-sroberta-multitask" 모델을 선택했습니다.

👉 전체 벤치마크 결과 보기:
https://diagnostic-sandwich-f3d.notion.site/Uplait-217a970704a280528a56cca41a956cab?source=copy_link
