import json
import os
import re
import time
from typing import Any, Iterator

from openai import OpenAI
from qdrant_client.http import models
from utils.condition_builder import build_filter, create_parsing_prompt, parse_query
from config.qdrant_config import QDRANT_CHUNKS_NAME,QDRANT_COLLECTION_NAME,get_qdrant_client



openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
qdrant_client = get_qdrant_client()




def _safe_json_load(raw: str) -> dict[str, Any]:
    text = (raw or "").strip()
    if not text:
        return {}

    # Handle accidental markdown wrappers.
    text = text.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            return {}
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return {}


def _resolve_parent_ids(
    metadata_filter: models.Filter | None,
    max_ids: int = 5000,
) -> tuple[list[int], bool]:
    if metadata_filter is None:
        return [], False

    parent_ids: list[int] = []
    offset = None
    truncated = False

    while True:
        records, offset = qdrant_client.scroll(
            collection_name=QDRANT_COLLECTION_NAME,
            scroll_filter=metadata_filter,
            with_payload=False,
            with_vectors=False,
            offset=offset,
        )

        for record in records:
                parent_ids.append(record.id)

        if offset is None:
            break
    return parent_ids


def _build_chunk_filter(parsed: dict[str, Any]) -> models.Filter | None:
    metadata_filter = build_filter(parsed)
    if metadata_filter is None:
        return None

    parent_ids = _resolve_parent_ids(metadata_filter)
    if not parent_ids:
        return None


    return  models.Filter(
            must=[
                models.FieldCondition(
                    key="parent_id",
                    match=models.MatchAny(any=parent_ids),
                )
            ])



def retrieve_chunks(parsed: dict[str, Any]) -> list[dict[str, Any]]:
    query_text = parsed.get("main_content").strip()
    # if not query_text:
    #     query_text = "real estate"

    chunk_filter = _build_chunk_filter(parsed)
    query_vector = openai_client.embeddings.create(
        input=query_text,
        model="text-embedding-3-small",).data[0].embedding

    hybrid_result = qdrant_client.query_points(
        collection_name=QDRANT_CHUNKS_NAME,
        prefetch=[
            models.Prefetch(
                query=query_vector,
                using="dense",
                filter=chunk_filter,
                limit= 5
            ),
            models.Prefetch(
                query=models.Document(text=query_text, model="Qdrant/bm25"),
                using="sparse",
                filter=chunk_filter,
                limit=5
            ),
        ],
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        limit=5,
        with_payload=True,
        with_vectors=False,
    )
    points = hybrid_result.points
        

    parent_ids = []
    for point in points:
        parent_id = point.payload.get("parent_id")
        parent_ids.append(parent_id)

    unique_parent_ids = list(dict.fromkeys(parent_ids))
    parent_map: dict[int, dict[str, Any]] = {}

    if unique_parent_ids:
        parent_records = qdrant_client.retrieve(
            collection_name=QDRANT_COLLECTION_NAME,
            ids=unique_parent_ids,
            with_payload=True,
            with_vectors=False,
        )
        parent_map = {
            record.id: record.payload for record in parent_records
        }

    contexts = []
    parent_ids_set = set()
    for point in points:
        payload = point.payload
        parent_id = payload.get("parent_id")
        parent_payload = parent_map.get(parent_id)
        if parent_id in parent_ids_set: continue
        parent_ids_set.add(parent_id)
        contexts.append(
            {
                "score": point.score,
                "chunk": payload.get("chunk"),
                "parent_id": parent_id,
                "content": {
                    "title": parent_payload.get("title"),
                    "address": parent_payload.get("address"),
                    "price": parent_payload.get("price"),
                    "price_unit": parent_payload.get("price_unit"),
                    "area": parent_payload.get("area"),
                    # "description": parent_payload.get("description"),
                    "direction": parent_payload.get("direction", ""),
                    # "type": parent_payload.get("type")
                }
            }
        )

    return contexts


def generate_answer(user_query: str, contexts: list[dict[str, Any]]) -> str:


    system_prompt = (
        "You are a real-estate assistant. "
        "Answer only from the provided retrieval contexts. "
        "If context is insufficient, say you do not have enough information. "
        "Always include brief source references using url when possible. The url should be https://sensestate.vercel.app/property-single.html?id= followed by the parent_id from the retrieval context. "
        "Answer everything in Vietnamese"
    )

    user_prompt = (
        f"User query: {user_query}\n\n"
        f"Retrieved contexts (JSON): {json.dumps(contexts, ensure_ascii=True)}"
    )

    completion = openai_client.chat.completions.create(
        model="gpt-4.1-nano",
        # temperature=0.2,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    return (completion.choices[0].message.content or "").strip()


def generate_answer_stream(
    user_query: str,
    contexts: list[dict[str, Any]],
) -> Iterator[str]:
    system_prompt = (
        "You are a real-estate assistant. "
        "Answer only from the provided retrieval contexts. "
        "If context is insufficient, say you do not have enough information. "
        "Always include brief source references using url when possible. The url should be http://127.0.0.1:8000/property-single.html?id= followed by the parent_id from the retrieval context. "
        "Answer everything in Vietnamese"
    )

    user_prompt = (
        f"User query: {user_query}\n\n"
        f"Retrieved contexts (JSON): {json.dumps(contexts, ensure_ascii=True)}"
    )

    stream = openai_client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        stream=True,
    )

    for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        content = getattr(delta, "content", None)
        if content:
            yield content


def run_rag(user_query: str) -> dict[str, Any]:
    start_time = time.time()
    parsed = parse_query(user_query)
    contexts = retrieve_chunks(parsed=parsed)
    answer = generate_answer(user_query=user_query, contexts=contexts)
    query_time = time.time() - start_time
    return {
        "query": user_query,
        "parsed_input": parsed,
        "results": contexts,
        "answer": answer,
        "query_time": query_time,
    }


def run_rag_stream(user_query: str) -> dict[str, Any]:
    start_time = time.time()
    parsed = parse_query(user_query)
    contexts = retrieve_chunks(parsed=parsed)
    query_time = time.time() - start_time

    return {
        "query": user_query,
        "parsed_input": parsed,
        "results": contexts,
        "query_time": query_time,
        "answer_stream": generate_answer_stream(user_query=user_query, contexts=contexts),
    }
