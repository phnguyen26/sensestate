import json
import os
from typing import Any
from openai import OpenAI
from qdrant_client.http import models

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


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
        price_cond = parsed.get("price_condition") or "approx"
        condition.append(CONDITION_MAP[price_cond]("price", price))
    if area is not None:
        area_cond = parsed.get("area_condition") or "approx"
        condition.append(CONDITION_MAP[area_cond]("area", area))
    if address is not None:
        condition.append(
            models.FieldCondition(key="address", match=models.MatchText(text=address))
        )
    if price_unit is not None:
        condition.append(
            models.FieldCondition(
                key="price_unit", match=models.MatchText(text=price_unit)
            )
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
        "price_condition": "export the price unit from the input, such as eq (for equal), gt (for greater than), approx (for approximate) and something like that, can be None, but can't none when the price existed",
        "address": "export the address from the input, it should explicitly be city, district, street, if the address is 'thành phố hồ chí minh', just return 'hồ chí minh', return string type, can be None ",
        "area": "export the area from the input, return float type, can be None",
        "area_condition": "export the area unit from the input, such as eq (for equal), gt (for greater than) and something like that, can be None, but can't none when the area existed",
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