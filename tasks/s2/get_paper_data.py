import json
import os
import time

import fire
from tqdm import tqdm

from tasks.s2.s2_api import fetch_s2_papers_by_keyword


def get_s2_search_results(
    keywords_json: str, outdir: str, filename: str = "s2_papers.json"
):
    with open(keywords_json, "r") as f:
        field2keywords = json.load(f)

    field_and_keywords = []
    for field, keywords in field2keywords.items():
        field_and_keywords.extend([(field, keyword) for keyword in keywords])

    s2_search_results: list[dict] = []
    with tqdm(total=len(field_and_keywords)) as pbar:
        for field, keyword in field_and_keywords:
            pbar.set_description(field)
            s2_search_results.append(
                dict(
                    field=field,
                    keyword=keyword,
                    results=fetch_s2_papers_by_keyword(keyword),
                )
            )

            pbar.update(1)

    with open(os.path.join(outdir, filename), "w") as outfile:
        json.dump(s2_search_results, outfile, indent=2)


if __name__ == "__main__":
    fire.Fire(get_s2_search_results)
