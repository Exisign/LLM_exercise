# 1. 모듈 가져오기
from langgraph.graph import StateGraph, END
# 공유 메모리의 형태를 규정할 때 활용
from typing import TypedDict

# 2. 상태 정의, 데이터 저장할 그릇, 공유 메모리, 모든 노드에서 사용 가능.
'''
[
    {"msg" : "......"},
    {"msg" : "......"},
    {"msg" : "......"},
]
'''
class CustomState(TypedDict):
    msg:str

# 3. 특정 목적의 노드 준비, 작은 단위 task -> tool (rag, mcp, ..)
#   단순한 함수로 구성
def add_prefix(state:CustomState):
    '''
    기존 상태 값에 특정 내용을 앞에 추가
    parameters : 
        - state : 공유 메모리, 전역 상태, 랭그래프에서 관리되는 상태
    '''
    return { 'msg' : "헬로" + state['msg']}

def add_surfix( state:CustomState):
    # 기존 상태 값에 특정 내용을 뒤에 추가
    return { 'msg' : "헬로" + state['msg'] + " !!"}

# 4. 그래프 연결(구성)
# 4-1. 그래프를 연결할 타겟 (기본 구성, 구조적 틀)
workflow = StateGraph( CustomState ) # CustomState의 형태, 이를 기반한 공유 메모리를 활용하여 상태 그래프 구성
# 4-2. shem(task, tool, agent) 등을 추가 -> 서클 형태 -> 시작, 끝 모름 (설정 전까지)
workflow.add_node("T1", add_prefix)
workflow.add_node("T2", add_surfix)
# 4-3. 시작점 설정
workflow.set_entry_point("T1") # 그래프 호출 진행되면 설정 노드가 호출됨, 상태값 전달하여.
# 4-4. 작업 순서를 지정(방향성)
workflow.add_edge('T1', 'T2') # T1 -> T2 규칙 지정(방향성
# 4-5. 끝점 설정
workflow.add_edge("T2", END) # T2가 끝나면 종료