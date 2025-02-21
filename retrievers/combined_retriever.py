from langchain_core.retrievers import BaseRetriever
from langchain_cohere import CohereRerank
from langchain_core.vectorstores import VectorStoreRetriever
from retrievers.elastic_retriever import ElasticsearchKeywordRetriever
from retrievers.pinecone_retriever import create_pinecone_retriever
from elasticsearch import Elasticsearch
from langchain.callbacks.manager import CallbackManagerForRetrieverRun
from langchain_huggingface import HuggingFaceEmbeddings
from helpers.log import logging as logger
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_google_genai import ChatGoogleGenerativeAI
from helpers.prompt_templates import qa_prompt, contextualize_q_prompt
from models.models import Organization
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

class CombinedRetriever(BaseRetriever):
    pinecone_retriever: VectorStoreRetriever
    es_retriever: ElasticsearchKeywordRetriever

    def _get_relevant_documents(self, query,*, run_manager: CallbackManagerForRetrieverRun):
        pinecone_results = self.pinecone_retriever.invoke(query)
        es_results = self.es_retriever.invoke(query)

        # Initialize both models
        cohere_default = CohereRerank(model="rerank-multilingual-v3.0", top_n=5)
        # Retrieve results
        combined_results = pinecone_results + es_results

        try:
            # Attempt to rerank the combined results using Cohere API
            reranked_default = cohere_default.compress_documents(combined_results, query)
            logger.info("Successfully reranked the documents using Cohere.")
            return reranked_default
        except Exception as e:
            logger.error("Unexpected error while reranking: %s", e)
            logger.info("Returning pinecone results without reranking.")
            return pinecone_results
retrievers = {}
def get_org_chain(org_id, db:Session):
    
    try:
        org = db.query(Organization).filter(Organization.id == org_id).one()
    except NoResultFound:
        raise ValueError(f"Organization with ID {org_id} not found")

    if org_id in retrievers:
        print("incache")
        return retrievers[org_id]

    embeddings = HuggingFaceEmbeddings(model_name=org.embedding_model)

    es = Elasticsearch("http://localhost:9200")
    index_name_es = org.es_index

    pinecone_retriever = create_pinecone_retriever(org.pine_index, embeddings)
    es_retriever = ElasticsearchKeywordRetriever(es, index_name_es)

    retriever = CombinedRetriever(pinecone_retriever=pinecone_retriever, es_retriever=es_retriever)
    history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_q_prompt)
    qa_chain = create_stuff_documents_chain(llm, qa_prompt)
    rag_chain = create_retrieval_chain(history_aware_retriever, qa_chain)

    retrievers[org_id] = rag_chain
    return rag_chain
