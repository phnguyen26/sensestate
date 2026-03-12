from fastapi import FastAPI, HTTPException, Query
from fastapi import APIRouter
from typing import Annotated
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.http import models
from config.qdrant_config import QDRANT_COLLECTION_NAME, get_qdrant_client
import os
import json
import time

router = APIRouter()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
qdrant_client = get_qdrant_client()

CONDITION_MAP = {
    "eq": lambda key, value: models.FieldCondition(
        key=key, range=models.Range(gte=value, lte=value)
    ),
    "gt": lambda key, value: models.FieldCondition(
        key=key, range=models.Range(gt=value)
    ),
    "gte": lambda key, value: models.FieldCondition(
        key=key, range=models.Range(gte=value)
    ),
    "lt": lambda key, value: models.FieldCondition(
        key=key, range=models.Range(lt=value)
    ),
    "lte": lambda key, value: models.FieldCondition(
        key=key, range=models.Range(lte=value)
    ),
    "lte": lambda key, value: models.FieldCondition(
        key=key, range=models.Range(lte=value)
    ),
    "approx": lambda key, value: models.FieldCondition(
        key=key, range=models.Range(lte=value * 1.1, gte=value * 0.9)
    ),
}


def build_filter(parsed: dict) -> models.Filter | None:
    condition = []
    price = parsed.get("price")
    area = parsed.get("area")
    address = parsed.get("address")
    price_unit = parsed.get("price_unit")
    if price is not None:
        price_cond = parsed.get("price_condition") or "eq"
        condition.append(CONDITION_MAP[price_cond]("price", price))
    if area is not None:
        area_cond = parsed.get("area_condition") or "eq"
        condition.append(CONDITION_MAP[area_cond]("area", area))
    if address is not None:
        condition.append(
            models.FieldCondition(key="address", match=models.MatchText(text=address))
        )
    if price_unit is not None:
        condition.append(
            models.FieldCondition(
                key="price_unit", match=models.MatchTextAny(text_any=price_unit)
            )
        )
    if not condition:
        return None
    return models.Filter(must=condition)


def create_prompt(s: str):
    prompt = f"""
    Parse the user's input into json format(just json, nothing else):
    {{
        "price": "export the price from the input, return float type, just the number, no trailing zeros, can be None",
        "price_unit": "export the price unit from the input, such as 'tỷ', 'triệu/tháng', 'Thỏa thuận', return string type, can be None",
        "price_condition": "export the price unit from the input, such as eq (for equal), gt (for greater than), approx (for approximate) and something like that, can be None, but can't none when the price existed",
        "address": "export the address from the input, it should explicitly be city, district, street, if the address is 'thành phố hồ chí minh', just return 'hồ chí minh', return string type, can be None ",
        "area": "export the area from the input, return float type, can be None",
        "area_condition": "export the area unit from the input, such as eq (for equal), gt (for greater than) and something like that, can be None, but can't none when the area existed",
        "main_content": "export the main content from the input, without including the price, area, must not be None, can be an empty string"
    }}
    User input: {s}
    """
    return prompt


@router.get("/api/properties")
async def search(
    s: Annotated[str, Query(title="search", max_length=100)],
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=9, ge=1, le=50),
):
    start_time = time.time()
    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {
                "role": "user",
                "content": create_prompt(s),
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