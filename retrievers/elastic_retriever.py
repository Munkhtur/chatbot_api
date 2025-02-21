
from elasticsearch import Elasticsearch, RequestError
from langchain_core.retrievers import BaseRetriever
from langchain.schema import Document
from helpers.log import logging as logger
from langchain.callbacks.manager import CallbackManagerForRetrieverRun



class ElasticsearchKeywordRetriever(BaseRetriever):
    es_client: Elasticsearch  # Define explicitly
    index_name: str  # Define explicitly
    def __init__(self, es_client: Elasticsearch, index_name: str, **kwargs):
        super().__init__(es_client=es_client, index_name=index_name, **kwargs)
        self.es_client = es_client
        self.index_name = index_name

    def _get_relevant_documents(self, query:str, *, run_manager: CallbackManagerForRetrieverRun ):
        print("es query", query)
        es_query = {
            "query": {
                "match": {
                    "content": query  # Simple keyword match
                }
            },
            "size": 10  # Return top 3 matches
        }
        try:
            if not self.es_client.indices.exists(index=self.index_name):
               logger.error("Index '%s' does not exist.", self.index_name)
               return []
            response = self.es_client.search(index=self.index_name, body=es_query)
            if "hits" not in response or "hits" not in response["hits"]:
                logger.error("Invalid response structure from Elasticsearch.")
                return []
            res = [
                    Document(page_content=hit["_source"]["content"],metadata=hit["_source"]) 
                    for hit in response["hits"]["hits"]
                ]
            return res
        except RequestError as e:
            logger.error("Elasticsearch error: %s", e)
            return []
        except Exception as e:
            logger.error("Unexpected error in Elasticsearch retriever: %s", e)
            return []