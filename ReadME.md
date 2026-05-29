# 목표 (기본형)
- llm 기반 서비스 구성
- 주요기능
    - bedrock 사용 -> llm 호출 담당
    - llm 모델
        - claude, openai, google등 사용
    - 웹 프런트 화면 
        - streamlit 사용 (프런트 담당)
        - 파이썬으로만 구성 (html, css, js x)
        - 채팅화면
    - 백엔드
        - fastapi 구성
        - 화면 x
        - api 담당 -> bedrock과 통신 역활
    - langchain
        - 프럼프트 엔지니어링 담당
        - 프럼프트 , llm 호출등 파이프라인 구축
- 서비스 주제
    - 식사 메뉴 해결사 (메뉴 추천)
# 목표 (확장형)
- RAG
- vectorDB
- MCP
- chain -> graph 파이프라인 마이그레이션
- Agent
- A2A

# 구조
/
L .env                  : 환경변수
L .gitignore            : 가상환경, .env 등 추가하여 사용
L requirements.txt      : 패키지
L app.py                : 프런트, streamlit
L server.py             : 백엔드, fastapi

# 세팅
- 가상환경 구축
    ```
        python -m venv llm_venv
    ```
- 활성화
    ```
        # 윈도우
        .\llm_venv\Scripts\activate

        # 위에서, 실행되지 않으면 아래 구문 적용
        Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\llm_venv\Scripts\Activate.ps1

        # 맥
        source llm_venv\bin\activate
    ```
- .gitignore 내용 세팅
    - 가상환경 배제
    ```  
        ...
        # 가상환경제외
        llm_venv
    ```
- 패키지 설치
    ```
        (llm_venv)> pip install -r requirements.txt
    ```
    ```
        # 백엔드 구성, bedrock 호출
        fastapi
        # fastapi 구동
        uvicorn
        # 프런트 구성
        streamlit
        # 프런트 -> 백엔드 요청
        requests
        # AWS SDK
        boto3
        # 랭체인 AWS 전용
        langchain-aws
        # 랭체인 코어 라이브러리
        langchain-core
        # 환경변수, .env 로드
        python-dotenv
    ```

# 환경변수
- .env
    ```
        AWS_REGION=us-east-1
        MODEL_ID=google.gemma-3-27b-it
        AWS_BEARER_TOKEN_BEDROCK=...
    ```

# 구동
- 백엔드 : server.py
    ```
        uvicorn server:app --reload --port 8000
    ```
    - 테스트 
        - http://127.0.0.1:8000/chat post 방식 요청
        
- 프런트