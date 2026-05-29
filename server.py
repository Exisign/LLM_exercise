'''
백엔드 프로그램
기능
    - ~/chat URL 제공
    - 클라이언트 채팅 입력 => ~/chat 요청 => 프럼프트 구성 => bedrock 호출 => 응답 => 처리 => 프런트
'''

# 1. 모듈 갖져오기
from fastapi import FastAPI

# 2. fastapi 객체 생성
app = FastAPI(title='식사 메뉴 추천 AI')

# 3. API 구성
@app.post('/chat')
async def chat():
    return "채팅 응답"

