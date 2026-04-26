import asyncio

from fastapi import FastAPI, HTTPException, Query
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from typing import Annotated
from pydantic import BaseModel, Field
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.http import models
from config.qdrant_config import QDRANT_COLLECTION_NAME, get_qdrant_client, load_and_create_collection
from rag import run_rag, run_rag_stream
from utils.condition_builder import build_filter, create_parsing_prompt
import os
import json
import time

router = APIRouter()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
qdrant_client = get_qdrant_client()
load_and_create_collection()




class RagRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)




@router.get("/api/properties")
async def search(
    s: Annotated[str, Query(title="search", max_length=100)],
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=9, ge=1, le=50),
):
    start_time = time.time()
    response = client.chat.completions.create(
        model="gpt-5-nano",
        messages=[
            {
                "role": "user",
                "content": create_parsing_prompt(s),
            }
        ],
    )
    end_time = time.time()
    parsed = json.loads(response.choices[0].message.content)

    content = parsed.get("main_content")
    embedding_response = client.embeddings.create(
        model="text-embedding-3-small", input=content
    )
    query_vector = embedding_response.data[0].embedding
    try:
        result = qdrant_client.query_points(
            collection_name=QDRANT_COLLECTION_NAME,
            query=query_vector,
            query_filter=build_filter(parsed),
            limit=limit+1,
            offset=(page - 1) * limit,
            with_payload=True,
            with_vectors=False,
        )
        points = result.points
        has_more = len(points) > limit
        if has_more:
            points = points[:limit]
        return {
            "query_time": end_time - start_time,
            "parsed_input": parsed,
            "page": page,
            "limit": limit,
            "has_more": has_more,
            "results": [
                {
                    "id": point.id,
                    "score": point.score,
                    "payload": point.payload,
                }
                for point in points
            ],
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": f"{type(e).__name__}: {str(e)}", "parsed_input": parsed},
        )


@router.get(path="/api/data")
def home(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=9, ge=1, le=50),
):
    result = qdrant_client.query_points(
        collection_name=QDRANT_COLLECTION_NAME,
        limit=limit + 1,
        offset=(page - 1) * limit,
        with_payload=True,
        with_vectors=False,
    )
    points = result.points
    has_more = len(points) > limit
    if has_more:
        points = points[:limit]
    return {
        "page": page,
        "limit": limit,
        "has_more": has_more,
        "results": [{"id": p.id, "payload": p.payload} for p in points],
    }

@router.get("/api/properties/{property_id}")
def get_property(property_id: int):
    result = qdrant_client.retrieve(
        collection_name=QDRANT_COLLECTION_NAME,
        ids=[property_id], 
        with_payload=True
    )
    if not result:
        raise HTTPException(status_code=404, detail="Property not found")
    return result[0].payload


@router.post("/api/rag")
def rag_search(request: RagRequest):
    try:
        return run_rag(user_query=request.query)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": f"{type(e).__name__}: {str(e)}"},
        )


@router.post("/api/rag/stream")
def rag_search_stream(request: RagRequest):
    try:
        payload = run_rag_stream(user_query=request.query)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": f"{type(e).__name__}: {str(e)}"},
        )

    def event_stream():
        answer_parts: list[str] = []
        
        for token in payload["answer_stream"]:
            answer_parts.append(token)
            yield json.dumps({"type": "token", "content": token}, ensure_ascii=False) + "\n"


        yield json.dumps(
            {"type": "done", "answer": "".join(answer_parts)},
            ensure_ascii=False,
        ) + "\n"

    return StreamingResponse(
        event_stream(),
        media_type="application/x-ndjson", #newline delimited 
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )