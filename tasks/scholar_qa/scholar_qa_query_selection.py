import csv
import json
import random

import fire
from langdetect import DetectorFactory, detect


def read_csv_file(file_path: str) -> list[tuple]:
    data = []
    with open(file_path, mode="r") as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            data.append(row)
    return data


def read_queries(
    file_path: str,
    num_samples: int = 10000,
    seed: int = 42,
    max_query_len: int = 200,
):

    def is_english(text):
        DetectorFactory.seed = 0
        try:
            # Ensure the text has enough meaningful content
            if not text.strip():  # Check for empty or whitespace-only strings
                return False
            return detect(text) == "en"
        except:
            # Handle cases where language detection fails
            return False

    data = [
        sample
        for sample in read_csv_file(file_path)
        if 0 < len(sample[1]) <= max_query_len
    ]
    random.seed(seed)
    sampled_data = random.sample(data, min(num_samples, len(data)))
    return [
        {"query": query, "label": label}
        for timestamp, query, label in sampled_data
        if len(query) <= max_query_len and is_english(query)
    ]


def select_scholar_qa_queries(scholar_qa_queries_csv: str, outpath: str):
    data = read_queries(scholar_qa_queries_csv)
    with open(outpath, mode="w") as json_file:
        json.dump(data, json_file, indent=2)


if __name__ == "__main__":
    fire.Fire(select_scholar_qa_queries)
    """
    python -m tasks.scholar_qa.scholar_qa_query_selection --scholar_qa_queries_csv /root/weka/oe-training-default/webolmo/tanmayg/webolmo-synthetic/scholar_qa_queries.csv --outpath /root/weka/oe-training-default/webolmo/tanmayg/webolmo-synthetic/scholar_qa_selected_queries.json
    """
