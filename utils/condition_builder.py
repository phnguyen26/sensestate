import json
import os
from typing import Any
from openai import OpenAI
from qdrant_client.http import models

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


CONDITION_MAP = {
    "range": lambda key, range_from, range_to: models.FieldCondition(
        key=key, range=models.Range(gte=range_from, lte=range_to)
    ),
    "keyword": lambda key, value: models.FieldCondition(
        key=key, match=models.MatchValue(value=value)
    ),
    "text": lambda key, value: models.FieldCondition(
        key=key, match=models.MatchText(text=value)
    )
}


def build_filter(parsed: dict) -> models.Filter | None:
    condition = []
    address = parsed.get("address")
    price_unit = parsed.get("price_unit")
    property_type = parsed.get("type")
    
    price_from = parsed.get("price_from")
    price_to = parsed.get("price_to")
    condition.append(CONDITION_MAP["range"]("price", price_from, price_to))
    
    area_from = parsed.get("area_from", None)
    area_to = parsed.get("area_to", None)
    condition.append(CONDITION_MAP["range"]("area", area_from, area_to))

    if address is not None:
        condition.append(
            CONDITION_MAP["text"]("address", address)
        )

    if price_unit is not None:
        condition.append(
            CONDITION_MAP["text"]("price_unit", price_unit)
        )

    if property_type is not None:
        condition.append(
            CONDITION_MAP["keyword"]("type", property_type)
        )

    if not condition:
        return None
    return models.Filter(must=condition)


def create_parsing_prompt(s: str):
    prompt = f"""
    Parse the user's input into json format(just json, nothing else):
    {{
        "price": "export the price from the input, return float type, just the number, no trailing zeros, can be None",
        "price_unit": "export the price unit from the input, such as 'tỷ', 'triệu/tháng', 'Thỏa thuận', return string type, can be None",
        "price_from": "export the minimum price from the input, return float type, can be None",
        "price_to": "export the maximum price from the input, return float type, can be None",
        "address": "export the address from the input, it should explicitly be city, district, street, if the address is 'thành phố hồ chí minh', just return 'hồ chí minh', return string type, can be None ",
        "area": "export the area from the input, return float type, can be None",
        "area_from": "export the minimum area from the input, return float type, can be None",
        "area_to": "export the maximum area from the input, return float type, can be None",
        "main_content": "export the main content from the input, without including the price, area, must not be None, can be an empty string"
    }}
    User input: {s}
    """
    return prompt

def parse_query(s: str) -> dict[str, Any]:
    response = openai_client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {"role": "user", "content": create_parsing_prompt(s)}
        ]
    )
    return json.loads(response.choices[0].message.content)

if __name__ == "__main__":
    pass