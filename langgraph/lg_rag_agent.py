'''
식사 추천
    - RAG 활용 -> 툴로 차용하여 활용 : @tool => rag 활용 (백터 디비 활용)
        - 환각 형상 방지(할루시네이션)
            - 존재하지 않는 것을 있는 것 처럼 창작하여 답변
        - 내부 데이터 접근 불가
            - LLM 관점에서 private한 데이터는 모름
            - 보안 이슈
        - 최신 정보 부재 (LLM이 모르는 정보)
    - 전체 의사결정 구조
        - 랭그래프 활용
    - 필요 시 부분적으로 랭체인 고려
        - 프럼프트 => LLM 추론 : 랭체인으로 묶어서 하나의 단위(노드)로 구성 가능함.
    - 프럼프트
        - fewshot 활용 
'''

# 1. 모듈 가져오기
from langgraph.graph import StateGraph, END
from typing import TypedDict, List                  # 커스텀 공유메모리(그래프상 노드가 공유하는)[{}, {}, {}, ...]
from langchain_core.tools import tool               # 툴 정의할 때 사용 데코레이터용
from langchain_core.messages import HumanMessage, BaseMessage    # 사용자의 메세지 형태 편하게 구성
from langchain_core.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate
from langchain_aws import ChatBedrock, ChatBedrockConverse # AWS bedrock llm 호출시 사용
from langgraph.prebuilt import ToolNode, tools_condition    # 툴 -> 노드로 변환, 조건부 툴 적용
from dotenv import load_dotenv
import os
import boto3

# rag 추가
from tools import rag_search                        # rag 도구를 외부에 구성, 커스텀
print(rag_search)