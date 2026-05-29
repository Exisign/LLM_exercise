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

# 3. 파일에 저장한 뒤 아래와 같이 불러오는 것도 방법이지
# ./data/*.txt
import glob
files = glob.glob('./rag/data/*.txt')
raw_docs = [ TextLoader(file, encoding='utf-8').load()[0] for file in files]
print(len(raw_docs), type(raw_docs[0]))

# 4. 텍스트 분할(특정 크기 단위(청크 단위)) => 성능 고려하여 여러 차례 시도 =>
splitter = RecursiveCharacterTextSplitter( chunk_size = 512, #원 텍스트에서 자르는 단위 (512토큰이면 자르기)
                               chunk_overlap = 100#문맥 유지를 위해겹치는 구간
                               )

splitis = splitter.split_documents(raw_docs)
print(f"총 청크수 : {len(splitis)}")
print(f"내용 : {splitis[0]}")
print(f"내용 : {splitis[1]}")