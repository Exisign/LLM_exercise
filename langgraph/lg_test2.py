'''
    TOOL 사용, LLM 적용
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

# 2. 환경변수 로드
load_dotenv()

# 3. LLM 추론용 객체 생성(전역 변수)
#   모델별로 ChatBedrock or ChatBedrockConverse 교체 적용
# 아래는 GPT? (왜 인지 모르겠지만, 클로드도 됨.)
llm = ChatBedrock(
    model=os.getenv('MODEL_ID'),
    client=boto3.client('bedrock-runtime', region_name=os.getenv('AWS_REGION'))
    )

# ChatBedrockConverse => us.anthropic.claude-haiku-4-5-20251001-v1:0
# 아래는, 클로드용?
# llm = ChatBedrockConverse(model  = os.getenv('MODEL_ID'), 
#                   client = boto3.client( 'bedrock-runtime', region_name=os.getenv('AWS_REGION') ) 
#                 )


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

'''
# 사이클 구성
- openai (bedrock) 경우
    - 질의 -> chatbot -> llm 호출 -> 응답 -> end
- 클로드 (bedrock) 경우    
    - 질의 -> chatbot -> llm 호출 -> 응답 -> 부족하면 생각 -> 도구 사용 필요성
    -> 툴 -> 툴 사용 -> 결과 -> chatbot -> llm 호출 -> 응답 -> end
'''

# 그래프 실행 가능하게 구성
app = workflow.compile()


# 테스트
if __name__ == '__main__':
    while True:
        # 1. 질의 획득
        user_input = input('\n유저: ').lower()
        # 2. 탈출 코드
        if user_input == 'q':
            break
        # 3. 프럼프트 구성
        prompt = { "messages" : [ HumanMessage(content=user_input)]}
        print(prompt)
        # 4. 그래프 작동 (invoke : 동기식, stream : 비동기식)
        for evt in app.stream(prompt, stream_mode = 'values'):
            msg = evt['messages'][-1] # 마지막에 추가된 응답 내용
            print("Agent", msg.content) # 출력


'''
openai.gpt-oss-120b-1:0 : LLM에서 직접 추론하여 응답. 도구 사용 x
us.anthropic.claude-haiku-4-5-20251001-v1:0 : 도구 사용 했음. LLM 2회 추론 행위 있었음
- 현재는 프럼프트 입력 => 새 채팅창 컨셉 => 단기 기억 x => 이전 대화 내용을 기억해서 프럼프트에 전달 x (이전 컨셉)
- 메모리 적용 -> 같은 내용에 대해서 반복 작업 x
'''

'''
# Claude    --> 추론 > Tool 적용 

유저: 4곱 3
{'messages': [HumanMessage(content='4곱 3', additional_kwargs={}, response_metadata={})]}
Agent 4곱 3
[chatbot_node 호출전 상태값] {'messages': [HumanMessage(content='4곱 3', additional_kwargs={}, response_metadata={}, id='fc8d85cf-acd4-4b89-a1be-6669c0d97de7')]}
[chatbot_node 호출 후 상태값] {'messages': [AIMessage(content='4와 3을 곱하겠습니다.', additional_kwargs={'usage': {'prompt_tokens': 603, 'completion_tokens': 85, 'cache_read_input_tokens': 0, 'cache_write_input_tokens': 0, 'total_tokens': 688}, 'stop_reason': 'tool_use', 'model_id': 'us.anthropic.claude-haiku-4-5-20251001-v1:0'}, response_metadata={'usage': {'prompt_tokens': 603, 'completion_tokens': 85, 'cache_read_input_tokens': 0, 'cache_write_input_tokens': 0, 'total_tokens': 688}, 'stop_reason': 'tool_use', 'model_id': 'us.anthropic.claude-haiku-4-5-20251001-v1:0', 'model_provider': 'bedrock', 'model_name': 'us.anthropic.claude-haiku-4-5-20251001-v1:0'}, id='lc_run--019e80fc-da06-7be0-ad1b-2100d9230307-0', tool_calls=[{'name': 'multiply', 'args': {'a': 4, 'b': 3}, 'id': 'toolu_bdrk_01BGxCe9dBpPLjPFaC7zx3Yk', 'type': 'tool_call'}], invalid_tool_calls=[], usage_metadata={'input_tokens': 603, 'output_tokens': 85, 'total_tokens': 688, 'input_token_details': {'cache_creation': 0, 'cache_read': 0}})]}
Agent 4와 3을 곱하겠습니다.
    [TOOL 실행] 4x3 계산중 ..
Agent 12
[chatbot_node 호출전 상태값] {'messages': [HumanMessage(content='4곱 3', additional_kwargs={}, response_metadata={}, id='fc8d85cf-acd4-4b89-a1be-6669c0d97de7'), AIMessage(content='4와 3을 곱하겠습니다.', additional_kwargs={'usage': {'prompt_tokens': 603, 'completion_tokens': 85, 'cache_read_input_tokens': 0, 'cache_write_input_tokens': 0, 'total_tokens': 688}, 'stop_reason': 'tool_use', 'model_id': 'us.anthropic.claude-haiku-4-5-20251001-v1:0'}, response_metadata={'usage': {'prompt_tokens': 603, 'completion_tokens': 85, 'cache_read_input_tokens': 0, 'cache_write_input_tokens': 0, 'total_tokens': 688}, 'stop_reason': 'tool_use', 'model_id': 'us.anthropic.claude-haiku-4-5-20251001-v1:0', 'model_provider': 'bedrock', 'model_name': 'us.anthropic.claude-haiku-4-5-20251001-v1:0'}, id='lc_run--019e80fc-da06-7be0-ad1b-2100d9230307-0', tool_calls=[{'name': 'multiply', 'args': {'a': 4, 'b': 3}, 'id': 'toolu_bdrk_01BGxCe9dBpPLjPFaC7zx3Yk', 'type': 'tool_call'}], invalid_tool_calls=[], usage_metadata={'input_tokens': 603, 'output_tokens': 85, 'total_tokens': 688, 'input_token_details': {'cache_creation': 0, 'cache_read': 0}}), ToolMessage(content='12', name='multiply', id='7a0170f4-a9ac-4ab8-9ae1-1a39a7f22e5c', tool_call_id='toolu_bdrk_01BGxCe9dBpPLjPFaC7zx3Yk')]}
[chatbot_node 호출 후 상태값] {'messages': [AIMessage(content='4 × 3 = **12** 입니다.', additional_kwargs={'usage': {'prompt_tokens': 701, 'completion_tokens': 18, 'cache_read_input_tokens': 0, 'cache_write_input_tokens': 0, 'total_tokens': 719}, 'stop_reason': 'end_turn', 'model_id': 'us.anthropic.claude-haiku-4-5-20251001-v1:0'}, response_metadata={'usage': {'prompt_tokens': 701, 'completion_tokens': 18, 'cache_read_input_tokens': 0, 'cache_write_input_tokens': 0, 'total_tokens': 719}, 'stop_reason': 'end_turn', 'model_id': 'us.anthropic.claude-haiku-4-5-20251001-v1:0', 'model_provider': 'bedrock', 'model_name': 'us.anthropic.claude-haiku-4-5-20251001-v1:0'}, id='lc_run--019e80fc-e544-7f81-86bd-1aabb0bab0b0-0', tool_calls=[], invalid_tool_calls=[], usage_metadata={'input_tokens': 701, 'output_tokens': 18, 'total_tokens': 719, 'input_token_details': {'cache_creation': 0, 'cache_read': 0}})]}
Agent 4 × 3 = **12** 입니다.

'''

'''
OpenAI GPT --> 추론 1번

유저: 4곱 3
{'messages': [HumanMessage(content='4곱 3', additional_kwargs={}, response_metadata={})]}
Agent 4곱 3
[chatbot_node 호출전 상태값] {'messages': [HumanMessage(content='4곱 3', additional_kwargs={}, response_metadata={}, id='f3f45fd8-84d8-4e8f-a5d3-95c6d92df0b9')]}
[chatbot_node 호출 후 상태값] {'messages': [AIMessage(content='<reasoning>The user input: "4곱 3". Likely Korean: "곱" means multiplication. So they might be asking "4 곱 3" i.e., 4 times 3. So answer is 12. Provide answer. Maybe ask if they need anything else. Provide result.</reasoning>4\u202f×\u202f3\u202f=\u202f12.', additional_kwargs={'usage': {'prompt_tokens': 72, 'completion_tokens': 83, 'cache_read_input_tokens': 0, 'cache_write_input_tokens': 0, 'total_tokens': 155}, 'stop_reason': None, 'thinking': {}, 'model_id': 'openai.gpt-oss-120b-1:0'}, response_metadata={'usage': {'prompt_tokens': 72, 'completion_tokens': 83, 'cache_read_input_tokens': 0, 'cache_write_input_tokens': 0, 'total_tokens': 155}, 'stop_reason': None, 'thinking': {}, 'model_id': 'openai.gpt-oss-120b-1:0', 'model_provider': 'bedrock', 'model_name': 'openai.gpt-oss-120b-1:0'}, id='lc_run--019e8102-e3c8-7211-b44b-b3f417e03e7d-0', tool_calls=[], invalid_tool_calls=[], usage_metadata={'input_tokens': 72, 'output_tokens': 83, 'total_tokens': 155, 'input_token_details': {'cache_creation': 0, 'cache_read': 0}})]}
Agent <reasoning>The user input: "4곱 3". Likely Korean: "곱" means multiplication. So they might be asking "4 곱 3" i.e., 4 times 3. So answer is 12. Provide answer. Maybe ask if they need anything else. Provide result.</reasoning>4 × 3 = 12.
'''