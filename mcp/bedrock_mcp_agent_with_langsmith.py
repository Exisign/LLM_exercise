"""
Bedrock + LangGraph + MCP + LangSmith 통합 에이전트
LangSmith로 모든 데이터 흐름을 추적
"""

import asyncio
import json
import sys
import os
import time
from pathlib import Path
from typing import Any, Dict
from datetime import datetime

#  환경 변수 로드 (LangSmith 포함)
from dotenv import load_dotenv

env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)

#  LangSmith 활성화 (환경 변수 자동 감지)
# LANGCHAIN_API_KEY, LANGCHAIN_PROJECT 필요
from langsmith import Client
from langchain_core.tracers.context import tracing_v2_enabled

# 환경 변수 확인
bedrock_model = os.getenv("MODEL_ID")
aws_region = os.getenv("AWS_REGION", "us-east-1")
langsmith_api_key = os.getenv("LANGCHAIN_API_KEY")
langsmith_project = os.getenv("LANGCHAIN_PROJECT", "agent-mcp-llm")

print(f" Bedrock: {bedrock_model}", file=sys.stderr)
print(f" AWS Region: {aws_region}", file=sys.stderr)
print(f" LangSmith: {' 활성화' if langsmith_api_key else '  비활성화'}", file=sys.stderr)
if langsmith_api_key:
    print(f" Project: {langsmith_project}", file=sys.stderr)

# LangChain/LangGraph 임포트
from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, MessagesState, END
from langgraph.prebuilt import ToolNode

# MCP
from mcp_tools_adapter import MCPToolAdapter


class LangSmithMetrics:
    """LangSmith 메트릭 추적 헬퍼"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.metrics = {}
    
    def start(self):
        """추적 시작"""
        self.start_time = time.time()
        self.metrics = {
            "start_time": datetime.now().isoformat(),
            "steps": []
        }
    
    def log_step(self, step_name: str, duration: float, data: Dict = None):
        """각 단계 기록"""
        step_info = {
            "name": step_name,
            "duration_ms": duration * 1000,
            "timestamp": datetime.now().isoformat()
        }
        if data:
            step_info["data"] = data
        
        self.metrics["steps"].append(step_info)
    
    def end(self):
        """추적 종료"""
        self.end_time = time.time()
        total_duration = self.end_time - self.start_time
        self.metrics["end_time"] = datetime.now().isoformat()
        self.metrics["total_duration_ms"] = total_duration * 1000
        return self.metrics


class BedrockMCPAgentWithLangSmith:
    """LangSmith 통합 Bedrock + MCP 에이전트"""
    
    def __init__(self, server_script: str = "server.py"):
        self.server_script = server_script
        self.mcp_adapter = None
        self.llm = None
        self.tools = []
        self.graph = None
        self.langsmith_client = None
        self.metrics = LangSmithMetrics()
        
        # LangSmith 클라이언트 초기화
        if langsmith_api_key:
            self.langsmith_client = Client()
            print(f" LangSmith 클라이언트 준비 완료", file=sys.stderr)
    
    async def initialize(self):
        """에이전트 초기화"""
        print("\n" + "=" * 70)
        print(" Bedrock + LangGraph + MCP + LangSmith 에이전트")
        print("=" * 70 + "\n")
        
        # 1. MCP Tool 로드
        print("1️  MCP Server와 연결 중...") 
        step_start = time.time()
        
        self.mcp_adapter = MCPToolAdapter(self.server_script)
        await self.mcp_adapter.initialize()
        self.tools = self.mcp_adapter.create_langchain_tools()
        
        step_duration = time.time() - step_start
        print(f"    {len(self.tools)}개의 Tool 로드 완료 ({step_duration:.2f}초)\n")
        
        # 2. Bedrock LLM 초기화
        print("2  Bedrock LLM 초기화 중...")
        step_start = time.time()
        
        self.llm = ChatBedrock(
            model_id=bedrock_model,
            region_name=aws_region,
            model_kwargs={
                "temperature": 0.7,
                "max_tokens": 2000,
            }
        )
        
        step_duration = time.time() - step_start
        print(f"    Bedrock LLM 초기화 완료 ({step_duration:.2f}초)\n")
        
        # 3. LangGraph 에이전트 구성
        print("3️  LangGraph 에이전트 구성 중...")
        step_start = time.time()
        
        self._setup_graph()
        
        step_duration = time.time() - step_start
        print(f"    에이전트 구성 완료 ({step_duration:.2f}초)\n")
        
        print("=" * 70)
        print(" 초기화 완료! 프롬프트를 입력하세요")
        if self.langsmith_client:
            print(f" LangSmith Project: {langsmith_project}")
            print(f" Dashboard: https://smith.langchain.com")
        print("=" * 70 + "\n")
        
        return self
    
    def _setup_graph(self):
        """LangGraph 상태 그래프 구성"""
        
        llm_with_tools = self.llm.bind_tools(self.tools)
        
        workflow = StateGraph(MessagesState)
        
        def call_model(state: MessagesState) -> dict:
            """LLM 호출"""
            messages = state["messages"]
            
            #  LangSmith: LLM 호출 기록
            if self.langsmith_client:
                print(f" [LLM] 입력: {messages[-1].content[:50]}...", file=sys.stderr)
            
            step_start = time.time()
            response = llm_with_tools.invoke(messages)
            step_duration = time.time() - step_start
            
            #  LangSmith: 메트릭 기록
            self.metrics.log_step(
                "llm_call",
                step_duration,
                {
                    "input_length": len(str(messages)),
                    "output_length": len(response.content) if hasattr(response, 'content') else 0,
                    "has_tool_calls": bool(getattr(response, 'tool_calls', []))
                }
            )
            
            if self.langsmith_client:
                print(f" [LLM] 응답: {response.content[:50] if hasattr(response, 'content') else 'Tool 호출'}...", file=sys.stderr)
                print(f"  [LLM] 처리시간: {step_duration*1000:.0f}ms", file=sys.stderr)
            
            return {"messages": [response]}
        
        # Tool 실행
        tool_node = ToolNode(self.tools)
        
        def should_continue(state: MessagesState) -> str:
            """Tool 호출 여부 판단"""
            messages = state["messages"]
            last_message = messages[-1]
            
            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                tool_names = [tc.get('name') for tc in last_message.tool_calls]
                if self.langsmith_client:
                    print(f" [Tools] 호출: {', '.join(tool_names)}", file=sys.stderr)
                return "tools"
            else:
                return "end"
        
        # 그래프 구성
        workflow.add_node("agent", call_model)
        workflow.add_node("tools", tool_node)
        
        workflow.add_edge("tools", "agent")
        
        workflow.add_conditional_edges(
            "agent",
            should_continue,
            {
                "tools": "tools",
                "end": END
            }
        )
        
        workflow.set_entry_point("agent")
        
        self.graph = workflow.compile()
    
    async def process_query(self, user_input: str) -> str:
        """사용자 쿼리 처리 (LangSmith 추적)"""
        print(f"\n 사용자: {user_input}\n")
        
        #  LangSmith: Run 시작
        self.metrics.start()
        
        messages = [HumanMessage(content=user_input)]
        
        try:
            # LangSmith 컨텍스트에서 실행
            if self.langsmith_client:
                print(f"\n LangSmith Tracing 활성화", file=sys.stderr)
                with tracing_v2_enabled(project_name=langsmith_project):
                    result = self.graph.invoke({"messages": messages})
            else:
                result = self.graph.invoke({"messages": messages})
            
            # 최종 응답 추출
            final_message = result["messages"][-1]
            
            if hasattr(final_message, 'content'):
                response = final_message.content
            else:
                response = str(final_message)
            
            #  LangSmith: 메트릭 종료
            metrics = self.metrics.end()
            
            print(f" 에이전트: {response}\n")
            
            # 처리 통계 출력
            print(" 처리 통계:")
            print(f"  ├─ 총 처리시간: {metrics['total_duration_ms']:.0f}ms")
            print(f"  ├─ 단계 수: {len(metrics['steps'])}")
            for i, step in enumerate(metrics['steps'], 1):
                print(f"  ├─ [{i}] {step['name']}: {step['duration_ms']:.0f}ms")
            print(f"  └─ LangSmith: {' 기록됨' if self.langsmith_client else '  비활성화'}\n")
            
            return response
        
        except Exception as e:
            error_msg = f" 처리 중 에러 발생: {str(e)}"
            print(error_msg)
            
            #  LangSmith: 에러 기록
            metrics = self.metrics.end()
            metrics["error"] = str(e)
            
            import traceback
            traceback.print_exc()
            return error_msg
    
    async def interactive_mode(self):
        """대화형 모드"""
        print("\n" + "=" * 70)
        print(" 대화형 모드 (LangSmith 추적 활성화)")
        print("=" * 70)
        if self.langsmith_client:
            print(f" 모든 대화가 LangSmith에 기록됩니다")
            print(f" 대시보드: https://smith.langchain.com")
        print("=" * 70 + "\n")
        
        while True:
            try:
                user_input = input(" 프롬프트: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['exit', 'quit', '종료']:
                    print("\n 종료합니다.")
                    break
                
                await self.process_query(user_input)
            
            except KeyboardInterrupt:
                print("\n\n 종료합니다.")
                break
            except Exception as e:
                print(f" 에러: {e}")
    
    async def run_demo(self):
        """데모 실행"""
        demo_queries = [
            "10과 5를 더해줘",
            "현재 시간은?",
            "메모 저장해줘. ID는 'demo_001', 내용은 'LangSmith 통합 성공!'",
            "저장된 메모들을 보여줘",
            "20과 30을 곱해줘"
        ]
        
        print("\n" + "=" * 70)
        print(" 데모 실행 (LangSmith 추적 활성화)")
        print("=" * 70)
        if self.langsmith_client:
            print(f" 모든 실행이 LangSmith에 기록됩니다")
        print("=" * 70 + "\n")
        
        for query in demo_queries:
            await self.process_query(query)
            await asyncio.sleep(0.5)
    
    async def cleanup(self):
        """정리"""
        if self.mcp_adapter:
            await self.mcp_adapter.cleanup()


async def main():
    """메인 함수"""
    
    agent = BedrockMCPAgentWithLangSmith("server.py")
    
    try:
        await agent.initialize()
        
        print("\n선택하세요:")
        print("  [1] 데모 실행 (LangSmith 추적)")
        print("  [2] 대화형 모드 (LangSmith 추적)")
        print("  [3] 단일 쿼리 실행 (LangSmith 추적)")
        
        choice = input("\n입력 (1/2/3): ").strip()
        
        if choice == "1":
            await agent.run_demo()
        elif choice == "2":
            await agent.interactive_mode()
        elif choice == "3":
            query = input("프롬프트 입력: ").strip()
            if query:
                await agent.process_query(query)
        else:
            print("잘못된 선택입니다.")
    
    except Exception as e:
        print(f" 에러: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await agent.cleanup()


if __name__ == "__main__":
    asyncio.run(main())