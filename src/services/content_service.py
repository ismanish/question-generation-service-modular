"""
Content retrieval service using OpenSearch
"""
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
from typing import Optional

from src.core.config import settings
from src.core.logging import LoggerMixin


class IndexMappingService(LoggerMixin):
    """Service for managing OpenSearch index mappings"""
    
    def __init__(self):
        self.index_map = {
            "An Invitation to Health": "chunk_357973585",
            "Steps to writing well": "chunk_1337899796"
        }
    
    def get_index_for_title(self, title: str) -> str:
        """Get the OpenSearch index name for a given book title"""
        if title in self.index_map:
            return self.index_map[title]
        else:
            available_titles = list(self.index_map.keys())
            raise ValueError(f"Title '{title}' not found. Available titles: {available_titles}")
    
    def get_available_titles(self) -> list:
        """Get all available book titles"""
        return list(self.index_map.keys())


class OpenSearchClient(LoggerMixin):
    """OpenSearch client wrapper"""
    
    def __init__(self):
        self._client = None
    
    @property
    def client(self) -> OpenSearch:
        """Get OpenSearch client"""
        if self._client is None:
            session = boto3.Session(profile_name=settings.AWS_PROFILE_NAME)
            credentials = session.get_credentials()
            
            auth = AWSV4SignerAuth(credentials, settings.OPENSEARCH_REGION, 'aoss')
            self._client = OpenSearch(
                hosts=[{'host': settings.OPENSEARCH_HOST.replace('https://', ''), 'port': 443}],
                http_auth=auth,
                use_ssl=True,
                verify_certs=True,
                connection_class=RequestsHttpConnection,
                pool_maxsize=20
            )
        return self._client


class ContentRetrievalService(LoggerMixin):
    """Service for retrieving content from OpenSearch"""
    
    def __init__(self):
        self.opensearch_client = OpenSearchClient()
        self.index_mapping = IndexMappingService()
    
    def _determine_chapter_key(self, content_id: str) -> str:
        """Determine which metadata field contains chapter information"""
        current_index = self.index_mapping.get_index_for_title(content_id)
        
        # Check toc_level_2_title first
        level_2_chapters = self._find_chapter_names(current_index, 'toc_level_2_title')
        
        if level_2_chapters and 'chapter' in "".join([val['key'].lower() for val in level_2_chapters]):
            return 'toc_level_2_title'
        else:
            return 'toc_level_1_title'
    
    def _find_chapter_names(self, index: str, chapter_key: str) -> list:
        """Find available chapter names using the specified chapter key"""
        query = {
            "size": 0,
            "aggs": {
                "chapter_names": {
                    "terms": {
                        "field": f"metadata.source.metadata.{chapter_key}.keyword",
                        "size": 200
                    }
                }
            }
        }
        
        try:
            response = self.opensearch_client.client.search(index=index, body=query)
            return response.get('aggregations', {}).get('chapter_names', {}).get('buckets', [])
        except Exception as e:
            self.logger.error(f"Error finding chapter names in index {index}: {e}")
            return []
    
    def retrieve_chapter_content(
        self,
        chapter_name: str,
        content_id: str,
        max_chunks: int = None,
        max_chars: int = None
    ) -> str:
        """Retrieve chapter content from OpenSearch"""
        if not chapter_name:
            raise ValueError("Chapter name must be provided")
        if not content_id:
            raise ValueError("Content ID must be provided")
        
        max_chunks = max_chunks or settings.MAX_CHUNKS
        max_chars = max_chars or settings.MAX_CHARS
        
        self.logger.info(f"Retrieving content for chapter: {chapter_name} from {content_id}")
        
        try:
            current_index = self.index_mapping.get_index_for_title(content_id)
            self.logger.info(f"Using OpenSearch index: {current_index}")
        except ValueError as e:
            raise ValueError(f"Unsupported book title: {e}")
        
        # Determine the correct chapter key
        chapter_key = self._determine_chapter_key(content_id)
        self.logger.debug(f"Using chapter key: {chapter_key}")
        
        # Create query for chapter content
        query_body = {
            "query": {
                "term": {
                    f"metadata.source.metadata.{chapter_key}.keyword": chapter_name
                }
            },
            "sort": [
                {"metadata.source.metadata.pdf_page_number": "asc"},
                {"metadata.source.metadata.page_sequence": "asc"}
            ],
            "_source": {
                "excludes": ["embedding"]
            },
            "size": max_chunks
        }
        
        try:
            response = self.opensearch_client.client.search(index=current_index, body=query_body)
        except Exception as e:
            raise Exception(f"Search error in index {current_index}: {e}")
        
        hits = response['hits']['hits']
        total_hits = response['hits']['total']['value']
        
        if total_hits == 0:
            self.logger.warning(f"No content found for chapter '{chapter_name}' in '{content_id}'")
            return ""
        
        self.logger.info(f"Found {total_hits} content chunks")
        
        # Combine content from all hits
        chapter_text = ""
        for hit in hits:
            chapter_text += hit['_source']['value']
        
        # Limit content if it exceeds max_chars
        if len(chapter_text) > max_chars:
            self.logger.info(f"Truncating content from {len(chapter_text)} to {max_chars} characters")
            chapter_text = chapter_text[:max_chars]
        
        self.logger.info(f"Retrieved content length: {len(chapter_text)} characters")
        return chapter_text


def get_content_service() -> ContentRetrievalService:
    """Get content retrieval service instance"""
    return ContentRetrievalService()
