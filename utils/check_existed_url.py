from qdrant_client import models

def check_if_url_existed(client, url, collection_name):
    if not client.collection_exists(collection_name):
        return False
    result = client.count(
        collection_name = collection_name,
        count_filter=models.Filter(
            must=[
                models.FieldCondition(key="url", match=models.MatchValue(value=url))
            ]
        ),
        exact=True,
    )
    return result.count > 0


if __name__ == '__main__':
    pass