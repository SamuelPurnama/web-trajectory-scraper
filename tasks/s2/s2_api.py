import json
import os
import time

import requests


def fetch_s2_papers_by_keyword(
    keyword: str,
    fields: str = "title,url,authors,abstract,venue",
    publication_types: str = "JournalArticle,Conference",
    year: str = "2021-",
    limit: int = 10,
    api_key: str | None = os.getenv("S2_API_KEY", None),
) -> list[dict]:

    # Define the query parameters
    query_params = {
        "query": keyword,
        "fields": fields,
        "publicationTypes": publication_types,
        "year": year,
        "limit": limit,
    }

    # Define headers with API key
    headers = {"x-api-key": api_key} if api_key else {}

    status_code = None
    response: requests.Response | None = None
    while status_code is None or status_code == 429:
        if status_code == 429:
            time.sleep(0.1)
            print("Retrying ...")
        # Send the API request
        response = requests.get(
            "http://api.semanticscholar.org/graph/v1/paper/search",
            params=query_params,
            headers=headers,
        )
        status_code = response.status_code

    assert response is not None
    if response.status_code != 200:
        print(
            f"s2 paper search by keyword {keyword} failed with status code {response.status_code}: {response.text}"
        )
        return []
    content = response.json()
    return content["data"] if "data" in content else []
