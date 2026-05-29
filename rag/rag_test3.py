'''
- 저장된 백터 디비 로드
- llm을 이용 추론 -> 프롬프트에 rag를 이용한 검색 증강용 데이터 추가하여 추론 진행 
    - 프롬프트 (질의 + rag 검색 결가)
- 랭체인의 체인 구성
'''

# 1. 모듈 가져오기
from langchain_community.vectorstores import FAISS
from langchain_aws import BedrockEmbeddings
import boto3
from dotenv import load_dotenv
import os
from langchain_aws import ChatBedrock
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough    # 질문 검색과 사용자 질문 세팅 등 동시 작업
from langchain_core.output_parsers import StrOutputParser   # llm응답 파싱 => 문자열만 추출


# 2. 환경변수 로드
load_dotenv()

# 3. 임베딩 모델 로드
tokenizer = BedrockEmbeddings(model_id="amazon.titan-embed-text-v2:0",#"amazon.titan-embed-text-v1"
                  region_name = os.getenv('AWS_REGION')
                  )

# 4. 저장 된 디비 파일(rag_test_2 참고)을 기반으로 로드
vector_db = FAISS.load_local('hp-story', tokenizer, allow_dangerous_deserialization=True)

# 5. LLM 클라이언트 생성
bedrock_client = boto3.client(
    service_name = 'bedrock-runtime',
    region_name = os.getenv('AWS_REGION')
)

# 6. LLM 생성
llm = ChatBedrock(
      client   = bedrock_client,
      model = 'openai.gpt-oss-120b-1:0',
      model_kwargs = {
        "max_tokens" : 500,
        "temperature": 0.7
      }
)

# 7. prompt 구성
prompt = ChatPromptTemplate.from_template('''
    다음의 제공된 context(문액, 참고)를 사용하여 질문에 답변해주세요.
    만약, 문맥에서 답을 찾을 수 없다면, "잘모르겠음" 이라고 대답하세요.
                                          
    <context>
    {context}
    <context>

    질문 : {user_input}
''')

# 8. 체인구성
retriever = vector_db.as_retriever(search_kwargs={"k" : 3}) #유사도가 높은 문서(청크)의 상위 3개를 참조
# 문서 결합 함수 (커스텀 기능 구성)
def format_docs(docs):
    # 3개의 청크를 => 1개의 말뭉치 합치기
    '''
        청크1 -> 유사도 1등

        청크2 -> 유사도 2등

        청크3 -> 유사도 3등
    '''
    return "\n\n".join(doc.page_content for doc in docs)
# 각종 기능을 결합 -> 랭체인 파이프라인 구성하는 LCEL 문법 -> | 사용 후 열거
rag_chain = (
    {"context":retriever | format_docs, "user_input" : RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# 실행
query = '해리포터의 가장 친한 친구 2명은?'
res = rag_chain.invoke(query)
print('== AI 답변 ==')
print(res)