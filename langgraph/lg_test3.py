'''
랭그래프 - 단기기억을 위해 메모리 추가
'''
# 1. 모듈 가져오기
from langgraph.graph import StateGraph, END, MessagesState, START
from typing import TypedDict
from langchain_core.tools import tool               # 툴 정의할 때 사용 데코레이터용
from langchain_core.messages import HumanMessage    # 사용자의 메세지 혀앹 편하게 구성
from langchain_aws import ChatBedrock, ChatBedrockConverse # AWS bedrock llm 호출시 사용
from langgraph.prebuilt import ToolNode, tools_condition    # 툴 -> 노드로 변환, 조건부 툴 적용
from dotenv import load_dotenv
import os
import boto3

# 메모리 관련
from langgraph.checkpoint.memory import MemorySaver # 단기기억용, 프로그램 종료되면 삭제
# 2. 메모리 생성 -> 현재는 RAM에 저장함. 실제는 => 물리적 VectorDB
memory = MemorySaver() 


# 2. 환경변수 로드
load_dotenv()

# 3. LLM 추론용 객체 생성(전역 변수)
#   모델별로 ChatBedrock or ChatBedrockConverse 교체 적용
# 아래는 GPT? (왜 인지 모르겠지만, 클로드도 됨.)
# llm = ChatBedrock(
#     model=os.getenv('MODEL_ID'),
#     client=boto3.client('bedrock-runtime', region_name=os.getenv('AWS_REGION'))
#     )

# ChatBedrockConverse => us.anthropic.claude-haiku-4-5-20251001-v1:0
# 아래는, 클로드용?
llm = ChatBedrockConverse(model  = os.getenv('MODEL_ID'), 
                  client = boto3.client( 'bedrock-runtime', region_name=os.getenv('AWS_REGION') ) 
                )


# 4. 툴 준비
@tool # LLM이 알 수 있는 (이해할 수 있는) 형식으로 자동 변환됨
def multiply( a:int, b:int) -> int:
    ''' 두 수를 곱한 후 반환 '''
    print(f'    [TOOL 실행] {a}x{b} 계산중 ..')
    return a * b

# 프럼프트를 받고 LLM은 직접 추론할 것인지? 아니면 도구를 사하여 해결할 것인지 스스로 판단하여처리함.

# 5. 여러개의 툴(여기서는 1개만 있음)을 모아서 llm에 등록
tools = [ multiply ]
llm_with_tools = llm.bind_tools(tools) # llm에게 이런 툴도 사용할 수 있다라는 것을 등록 (알림)

# 6. 노드 구성 -> 사전에 필요한 것 -> 상태 메모리 필요 -> 랭그래프가 정의한 MessageState(라입러리에서 준비돼 있음)을 사용
def chatbot_node(state:MessagesState):
    print('[chatbot_node 호출전 상태값]', state)
    # 전달된 내용(사용자의 프럼프트를) LLM에게 전달 -> 추론 요청 -> LLM 판단 -> 직접 해결 or 도구 사용 해결 -> 수행 -> 응답
    res = llm_with_tools.invoke(state['messages']) # messages 키값은 MessageState에 정의 됨
    new_state = {"messages" : [res]} # MessagesState의 형식에 맞춰서 구성했음

    print('[chatbot_node 호출 후 상태값]', new_state)
    return new_state

# 7. 그래프 구성
# 그래프 생성
workflow = StateGraph(MessagesState)
# 노드 추가
workflow.add_node('chatbot', chatbot_node)  # 프럼프트/대화 내용 등 보고 생각 -> 판단 노드
workflow.add_node('tools', ToolNode(tools)) # 툴에 목적을 수행(여기서 곱하기)하는 -> 행동 노드 

# 시작점 (= set_entry_point())
workflow.add_edge(START, 'chatbot')         # 서비스 가동 -> 프럼프트 등 데이터 주입 -> 가장 먼저 작동
# 조건에 따라 행동을 다르게 수행 구성 => 조건부 규칙 부여
workflow.add_conditional_edges(
    'chatbot',              # 이전 노드가 텍스트 응답을 했다면 -> END 이동
    tools_condition         # 이전 노드가 도구가 필요하다로 응답 -> 도구 노드로 이동
)

# 도구 사용 -> 결과 획득 -> 챗봇으로 전달 -> ...
workflow.add_edge('tools', 'chatbot') # tools -> chatbot

# 그래프 실행 가능하게 구성
app = workflow.compile(checkpointer=memory)


# 테스트
if __name__ == '__main__':
    # TODO config 구성
    config = {"configurable":{"thread_id":"user-1"}} # 사용자별로 기억관리, "user-1" 고정
    while True:
        # 1. 질의 획득
        user_input = input('\n유저: ').lower()
        # 2. 탈출 코드
        if user_input == 'q': 
            break
        # 3. 프럼프트
        prompt = { "messages" : [ HumanMessage(content=user_input)]}
        print(prompt)
        # 4. 그래프 작동 (invoke : 동기식, stream : 비동기식)
        for evt in app.stream(prompt, stream_mode = 'values', config=config):
            msg = evt['messages'][-1] # 마지막에 추가된 응답 내용
            print("Agent", msg.content) # 출력