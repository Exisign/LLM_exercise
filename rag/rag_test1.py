'''
벡터 디비 데이터 구축

- 대량의 말뭉치를 vectordb에 세팅, 구성
- 말충치 => 특정 크기 단위로 분할해서 처리 -> 단위:청크(어느 정도 덩어리/크기를 잡을지 관건 -> 성능영향 미침)-> 토큰 제한
'''

# RAG, 백터 디비에 자연어 -> 토큰화 -> 저장, 검색(유사도기발)
# 1. 모듈 가져오기
from langchain_community.vectorstores import FAISS
# FAISS --> meta 개발, 고차원 벡터 유사도 검색 및 클러스터링을 위한 오픈소스 라이브러리
from langchain_aws import BedrockEmbeddings # 토크나이저
import boto3
from dotenv import load_dotenv
import os
# 대량의 문서 처리 기능 제공
from langchain_community.document_loaders import TextLoader #텍스트로부터 로드
from langchain_text_splitters import RecursiveCharacterTextSplitter # 청크 단위 스플리터?

# 2. 환경 변수 로드
load_dotenv()

# 3. 데이터 임시 편성(LLM 모르는/학습하지 않은 최신데이터 or 사내데이터 가정)
data = [
    "맥도널드 대표 제품은 빅맥이다.",
    "버거키의 대표 제품은 와퍼이다.",
    "맘스터치의 대표 제품은 휠렛버거이다.",
    "롯데리아의 대표 제품은 새우 버거이다."
]

# 4. 임베딩 (임베딩 모델 사용 => 학습 종료 된 것임. 학습 시 사용 된 다국어의 양 표현의 양으로 이해)
# 자연어 -> 토큰화(분절->백터화->패딩)
tokenizer = BedrockEmbeddings(model_id="amazon.titan-embed-text-v2:0",#"amazon.titan-embed-text-v1"
                  region_name = os.getenv('AWS_REGION')
                  )

# 5. 백터 디비에 토큰화 된 내용 입력
vector_db = FAISS.from_texts(data, tokenizer) # a메모리 기반, 디비를 메모리에 로드

# 6. 검색 => 유사도 활용 
docs = vector_db.similarity_search("버거킹의 대표 버거는?")

# 7. 결과 확인 -> 유사도가 가장 높은 데이터 추출(디비에 저장된)
print(docs[0].page_content)
# docs -> 유사도 순으로 나열 된 데이터