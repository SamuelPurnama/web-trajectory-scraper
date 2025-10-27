import json
import os
import random

import feedparser
import fire

from tasks.arxiv.category_codes import CATEGORY_CODES


def get_papers(category_code: str, max_results: int):
    num_papers_per_year = max_results // 5
    papers = []
    for year in [2020, 2021, 2022, 2023, 2024]:
        month = str(random.choice(range(1, 13))).zfill(2)
        feed = feedparser.parse(
            f"https://export.arxiv.org/api/query?search_query=cat:{category_code}+AND+submittedDate:[{year}{month}01+TO+{year}{month}28]&start=0&max_results={num_papers_per_year}"
        )
        for entry in feed.entries:
            papers.append(
                dict(
                    id=entry.id,
                    published=entry.published,
                    title=entry.title,
                    authors=entry.authors,
                    summary=entry.summary,
                )
            )

    return papers


def main(output_dir: str):
    papers = []
    for field in CATEGORY_CODES:
        for subfield, code in CATEGORY_CODES[field].items():
            print(f"{field}--{subfield}")
            subfield_papers = get_papers(code, 100)
            for paper in subfield_papers:
                paper["field"] = field
                paper["subfield"] = subfield
                paper["code"] = code
            papers.extend(subfield_papers)

    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "arxiv_papers.jsonl")
    with open(output_file, "w") as f:
        for paper in papers:
            f.write(json.dumps(paper) + "\n")


if __name__ == "__main__":
    fire.Fire(main)
