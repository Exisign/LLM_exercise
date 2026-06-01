# 1. 모듈 가져오기
from langgraph.graph import StateGraph, END
# 공유 메모리의 형태를 규정할 때 활용
from typing import TypedDict

# 2. 상태 정의
# LangGraph에서 State는 모든 노드가 공유하는 "공유 메모리" 역할을 한다.
#
# 일반 함수 호출에서는 보통 인자와 반환값만 넘기지만,
# LangGraph에서는 여러 노드가 같은 상태 구조를 기준으로 값을 읽고 갱신한다.
#
# 실전에서는 아래처럼 더 많은 값을 상태에 넣는다.
#
# class AgentState(TypedDict):
#     question: str        # 사용자 질문
#     documents: list      # RAG 검색 결과
#     answer: str          # LLM 최종 답변
#     retry_count: int     # 재시도 횟수
#     need_search: bool    # 검색 필요 여부
#     tool_result: dict    # 도구 실행 결과
#
# 이 예제에서는 구조를 단순화해서 msg 하나만 사용한다.
'''
[
    {"msg" : "......"},
    {"msg" : "......"},
    {"msg" : "......"},
]
'''
class CustomState(TypedDict):
    msg:str

# 3. 노드 정의
# LangGraph에서 노드는 "하나의 작업 단위"다.
#
# 실전에서는 노드 하나가 아래와 같은 역할을 맡을 수 있다.
#
# - 질문 분류 노드
# - RAG 검색 노드
# - LLM 답변 생성 노드
# - 답변 검증 노드
# - 도구 호출 노드
# - 실패 시 재시도 판단 노드
# - 사람 승인 대기 노드
#
# 이 예제의 add_prefix는 단순히 문자열 앞에 값을 붙이지만,
# 구조적으로는 "첫 번째 처리 작업"을 의미한다.
def add_prefix(state:CustomState):
    '''
    기존 상태 값에 특정 내용을 앞에 추가
    parameters : 
        - state : 공유 메모리, 전역 상태, 랭그래프에서 관리되는 상태
    '''
    return { 'msg' : "헬로 " + state['msg']}

# 두 번째 노드
# 앞 노드에서 갱신된 상태를 이어받아 다음 처리를 수행한다.
#
# 이 흐름은 단순히 보면:
#   T1 -> T2
#
# 실전에서는:
#   RAG 검색 -> LLM 답변 생성
#   LLM 답변 생성 -> 답변 검증
#   답변 검증 -> 재검색 or 종료
#
# 같은 식으로 확장된다.
def add_surfix( state:CustomState):
    # 기존 상태 값에 특정 내용을 뒤에 추가
    return { 'msg' : state['msg'] + " !!"}

# 4. 그래프 구성
# StateGraph는 여러 작업 노드를 연결해서 실행 흐름을 정의하는 구조다.
#
# 단순 체인은 보통:
#   A -> B -> C
#
# LangGraph는 조건 분기를 통해:
#   A -> 조건에 따라 B / C / D
#
# 같은 구조를 만들 수 있다.
#
# 예:
#   질문이 DB 관련이면      -> SQL 생성 노드
#   질문이 문서 검색이면    -> RAG 검색 노드
#   질문이 일정 관련이면    -> Calendar Tool 노드
#
# 이 예제는 가장 단순한 선형 흐름만 사용한다.
# 4-1. 그래프를 연결할 타겟 (기본 구성, 구조적 틀)
workflow = StateGraph( CustomState ) # CustomState의 형태, 이를 기반한 공유 메모리를 활용하여 상태 그래프 구성
# 4-2. shem(task, tool, agent) 등을 추가 -> 서클 형태 -> 시작, 끝 모름 (설정 전까지)
workflow.add_node("T1", add_prefix)
workflow.add_node("T2", add_surfix)
# 4-3. 시작점 설정
workflow.set_entry_point("T1") # 그래프 호출 진행되면 설정 노드가 호출됨, 상태값 전달하여.
# 4-4. 작업 순서를 지정(방향성)
# T1이 끝나면 T2로 이동한다.
#
# 현재 예제:
#   START -> T1 -> T2 -> END
#
# 실전 예:
#   START
#     -> 질문 분류
#     -> 조건 분기
#        ├─ RAG 검색
#        ├─ 일반 답변
#        └─ 도구 호출
#     -> 답변 생성
#     -> 답변 검증
#     -> END
workflow.add_edge('T1', 'T2') # T1 -> T2 규칙 지정(방향성
# 4-5. 끝점 설정
workflow.add_edge("T2", END) # T2가 끝나면 종료
# 4-6. 컴파일 수행 => Make => 수행 가능한 형태로 완성
app = workflow.compile()

# 5. 데이터 주입(사용자의 질의 등 ...) -> 그래프 호출 -> 그래프를 순환하면서 요청에 대한 처리 수행
#   데이터 형태 => 공유 메모리를 참조하여 구성
#   데이터 => 노드(1) => 노드(2) => END(응답)
res = app.invoke({"msg" : "랭그래프"})
print( res )