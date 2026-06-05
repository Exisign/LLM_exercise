# tool 변환
- MCP 서버에서 구성한 도구의 이름, 인자(혹은 매개변수), 반환값 정보를 가져와서 파이썬(MCP Client) 코드로 변환
(인터페이스 구성)
- MCP Client 도구 호출 -> 파이썬 코드 작동 -> JSON 변환 -> JSON RPC 방식으로 MCP Server에 전달
- 타입 맞춤.

# tool 전달 형태
```
name='add' 
title=None 
description='\n    두 수를 더하는 계신기\n\n    Args:\n        a: 첫 번째 수치\n        b: 두 번째 수치\n    \n    Returns\n        계산 결과\n    ' 

inputSchema={
    'properties': {
        'a': {'title': 'A', 'type': 'number'}, 
        'b': {'title': 'B', 'type': 'number'}}, 
    'required': ['a', 'b'], 
    'title': 'addArguments', 
    'type': 'object'
} 

outputSchema={
    'properties': {
        'result': {'title': 'Result', 'type': 'string'}
    }, 
    'required': ['result'], 
    'title': 'addOutput', 
    'type': 'object'
} 

icons=None 
annotations=None 
meta=None 
execution=None
```

# 랭스미스 
- 랭체인|랭그래프 => 에이전트 개발 => MCP, RAG등 도구 연동 구축
- 관리
    - 데이터 흐름 (Flow)
        - 사용자 입력 => LLM => Tool => ... => 최종 응답
        - 각 단계별 기록 (자동)
        - 트레킹
    - 처리 시간 (latency)
        - 전체 처리 시간
        - LLM 응답 시간
        - TOOL 실행 시간 
        - 트레킹 -> 최적화등 작업
    - 성능 지표 (Metrics)
        - Token 사용량
        - API 호출 비용 산출
        - 성공률 
        - 품질 관리
- 랭스미스 도구를 이용하여 트레킹, 관리등 작업 진행
- AI 서비스(LLM, 랭체인|랭그래프, MCP,..)의 모든 기록
    - 추적
    - 매트릭
    - 대시보드
    - 분석

# 랭스미스 설치
## 가입
- https://smith.langchain.com/ 접속
- signup 후 login
- 본인 SNS 및 기타 계정 사용

## API KEY 생성
- 왼쪽 메뉴바 > settings > + API Key 클릭
- 설명, 개인용, 만료일 지정 > 생성 > key copy
```
    lsv2_pt_2d4189...
```

## .env 세팅(key)
LANGCHAIN_API_KEY=  "lsv2_pt_2d4189..."
LANGCHAIN_PROJECT=  "agent-mcp-llm"
LANGCHAIN_TRACING_V2=   "true"

# 랭스미스 환경 체크
'''
python check_langsmith.py
'''