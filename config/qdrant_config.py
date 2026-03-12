import os

from qdrant_client import QdrantClient
from qdrant_client.http import models
import logging

QDRANT_URL = os.getenv('QDRANT_URL')
QDRANT_API_KEY = os.getenv('QDRANT_API_KEY')
QDRANT_COLLECTION_NAME = "sensetate"
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
def get_qdrant_client():
    return QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
def load_and_create_collection(collection_name: str):
    client = get_qdrant_client()
    if not client.collection_exists(collection_name):
        logger.info(f'Creating {collection_name} collection')
        client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE),
        )
        
        client.create_payload_index(
            collection_name=collection_name,
            field_name="address",
            field_schema=models.TextIndexParams(
                type="text",
                tokenizer=models.TokenizerType.WORD,
                lowercase=True
            )
        )
        
        client.create_payload_index(
            collection_name=collection_name,
            field_name="price",
            field_schema=models.PayloadSchemaType.FLOAT
        )
        
        
        client.create_payload_index(
            collection_name=collection_name,
            field_name="area",
            field_schema=models.PayloadSchemaType.FLOAT
        )
        
        
        client.create_payload_index(
            collection_name=collection_name,
            field_name="price_unit",
            field_schema=models.TextIndexParams(
                type="text",
                tokenizer=models.TokenizerType.WORD,
                lowercase=True
            )
        )
        
        client.create_payload_index(
            collection_name=collection_name,
            field_name="url",
            field_schema=models.PayloadSchemaType.KEYWORD
        )
        
    
    
    