import os

from qdrant_client import QdrantClient
from qdrant_client.http import models
import logging

QDRANT_URL = os.getenv('QDRANT_URL', 'http://localhost:6333')
QDRANT_API_KEY = os.getenv('QDRANT_API_KEY')
QDRANT_COLLECTION_NAME = "sensestate"
QDRANT_CHUNKS_NAME = "sensestate-chunks"
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
def get_qdrant_client():
    return QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
def load_and_create_collection():
    client = get_qdrant_client()
    if not client.collection_exists(QDRANT_COLLECTION_NAME):
        logger.info(f'Creating {QDRANT_COLLECTION_NAME} collection')
        client.create_collection(
                collection_name=QDRANT_COLLECTION_NAME,
                vectors_config={} #storing only metadata
        )
        
        client.create_payload_index(
            collection_name=QDRANT_COLLECTION_NAME,
            field_name="address",
            field_schema=models.TextIndexParams(
                type="text",
                tokenizer=models.TokenizerType.WORD,
                lowercase=True
            )
        )
        
        client.create_payload_index(
            collection_name=QDRANT_COLLECTION_NAME,
            field_name="price",
            field_schema=models.PayloadSchemaType.FLOAT
        )
        
        
        client.create_payload_index(
            collection_name=QDRANT_COLLECTION_NAME,
            field_name="area",
            field_schema=models.PayloadSchemaType.FLOAT
        )
        
        
        client.create_payload_index(
            collection_name=QDRANT_COLLECTION_NAME,
            field_name="price_unit",
            field_schema=models.TextIndexParams(
                type="text",
                tokenizer=models.TokenizerType.WORD,
                lowercase=True
            )
        )
        
        client.create_payload_index(
            collection_name=QDRANT_COLLECTION_NAME,
            field_name="url",
            field_schema=models.PayloadSchemaType.KEYWORD
        )
    if not client.collection_exists(QDRANT_CHUNKS_NAME):
        logger.info(f'Creating {QDRANT_CHUNKS_NAME} collection')
        client.create_collection(
                collection_name=QDRANT_CHUNKS_NAME,
                vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE),
        )
        
    
    
    