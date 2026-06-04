'''
MCP Client
mCP Server 와 통신

-- server를 VS Code 터미널로 하나 띄우고,
-- client로 또 새로운 터미널에서 python .{현재경로}/client.py 등으로 실행.
'''

# 1. 모듈 가져오기
import asyncio
import json
import sys
from mcp import ClientSession, StdioServerParameters # 커넥션 담당
from mcp.client.stdio import stdio_client

# 2. MCP Client 클래스 구성
class MCPClient:
    '''MCP Server와 통신하는 클래스(역할:클라이언트)'''
    # 생성자
    def __init__(self, server_script: str = 'server.py'):
        '''
        Args:
            server_script: 실행할 Server측 스크립트 경로
        '''
        self.server_script = server_script
        self.tools = [] # MCP 서버에게 툴 목록 가져와서 저장
        pass
    
    # 실제 일을 수행하는 함수
    async def run(self):
        print(f'MCP Server 접속중...')
        server_params = StdioServerParameters(
            command= sys.executable,
            args = [self.server_script],
            env = None
        )
        print(f'sys.executable {sys.executable} server_script {self.server_script}')
        # 접속 -> I/O -> 예외상황 발생될 수 있음
        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    print(f'MCP 서버 연결 성공 : 서버측으로부터 입력, 출력에 대한 객체 획득')
                    # 1. 세션 초기화
                    await session.initialize()  # await --> 비동기 처리, 순서 정립 --> 응답이 오지 않으면 다음 step 전환 X
                    # 2. 사용 가능한 모든 도구 조회
                    print(f'MCP 서버측에 도구 목록 요청')
                    res = await session.list_tools()
                    self.tools = res.tools
                    print(f'{len(self.tools)}개의 도구 확인 됨.')#, self.tools[0])
                    for i, tool in enumerate(self.tools, 1):
                        print(f'    {i}.    {tool.name}')
                        print(f'    설명.    {tool.description}')
                        # 파라미터(매개변수) 정보 추출 => 스키마 => 매개변수명, 타입
                        if hasattr(tool, "inputSchema") and tool.inputSchema: #해당 맴버가 있는가? -> 값은 있는가?
                            props = tool.inputSchema.get('properties', {}) # d키 -> 값 추출(인덱싱), 비워있는 경우 대비, 
                            if props:
                                print(f'    입력: {",".join(props.keys())}') # a,b
                        print('-' * 30 + '\n')
                    print('\n' + '-' * 30)
                    print('도구 호출 테스트')
                    print('-' * 30 + '\n')
                    await self.call_tool( session, "add", {"a":100, "b":5})
                    await self.call_tool( session, "get_time", {})
                    await self.call_tool( session, "save_note", {"note_id":"de-001", "note_content":"mcp 1"})
                    await self.call_tool( session, "save_note", {"note_id":"de-002", "note_content":"mcp 2"})
                    await self.call_tool( session, "list_note", {})
                    await self.call_tool( session, "delete_note", {"note_id":"de-001"})
                    await self.call_tool( session, "list_note", {})
                    print('\n' + '-' * 30)
                    print('도구 호출 테스트 완료')
                    print('-' * 30 + '\n')
        except Exception as e:
            print(f'MCP Server 접속 오류 : {e}')
        pass

    # MCP 서버에 존재하는 도구를 호출하는 함수
    async def call_tool(self, session, tool_name: str, arguments: dict):
        try:
            result = await session.call_tool(tool_name, arguments)
            # 결과 출력
            print(f'결과출력 : {result}')
            if hasattr(result, 'content') and result.content:
                for content in result.content:
                    if hasattr(content, 'text'):
                        print(f"결과 : \n{content.text}\n")
                    else:
                        print(f"결과 : \n{content}\n")
            else:
                print(f"결과 : \n{result}\n")        
        except Exception as e:
            print(f'에러 발생 {e}')
        pass

# 3. 비동기 main 함수 구성
async def main():
    
    '''비동기식 메인 함수'''
    # MCPClient 객체 생성
    client = MCPClient()
    # 가동
    await client.run()

# 4. 비동기 함수 호출 -> MCP 서버 연동
if __name__ == '__main__':
    # 비동기로 함수를 호출
    asyncio.run( main() )