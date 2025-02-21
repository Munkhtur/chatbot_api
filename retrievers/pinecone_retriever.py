import time
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
import os


pc = Pinecone()




def create_pinecone_retriever(index_name, embeddings):
    existing_indexes = [idx["name"] for idx in pc.list_indexes()]
    if index_name not in existing_indexes:
        pc.create_index(name=index_name, dimension=384, metric="cosine", spec=ServerlessSpec(cloud="aws", region="us-east-1"))
    while not pc.describe_index(index_name).status["ready"]:
        time.sleep(1)
    index = pc.Index(index_name)
    db_pinecone = PineconeVectorStore(index=index, embedding=embeddings)
    return db_pinecone.as_retriever(search_type="similarity", search_kwargs={"k": 10})