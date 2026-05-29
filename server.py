'''
백엔드 프로그램
기능
    - ~/chat URL 제공
    - 클라이언트 채팅 입력 => ~/chat 요청 => 프럼프트 구성 => bedrock 호출 => 응답 => 처리 => 프런트

실행
    - uvicorn server:app --reload --port 8000
'''

# 1. 모듈 갖져오기
from fastapi import FastAPI
# 입력폼 유효성 검사, 구조 정의
from pydantic import BaseModel
# LLM 모듈
from llm import chain

# 2. fastapi 객체 생성
app = FastAPI(title='식사 메뉴 추천 AI')

# 요청 데이터 구조 정의
class UserRequest(BaseModel):
    query:str

# 3. API 구성
@app.post('/chat')
async def chat(req:UserRequest):
     # LLM 호출
    try:
        print(req)
        response = chain.invoke( {"user_input":req.query} )
        return {"response":response.content}
    except Exception as e:
        return {"response":f"에러 {e}"}