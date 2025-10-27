import json
import os

import ell
import fire
from pydantic import BaseModel, Field
from tqdm import tqdm

FIELDS_OF_STUDY = [
    "Computer Science",
    "Medicine",
    # "Chemistry",
    "Biology",
    "Materials Science",
    "Physics",
    # "Geology",
    # "Psychology",
    # "Art",
    # "History",
    # "Geography",
    # "Sociology",
    "Business",
    # "Political Science",
    # "Economics",
    # "Philosophy",
    "Mathematics",
    "Engineering",
    "Environmental Science",
    # "Agricultural and Food Sciences",
    "Education",
    # "Law",
    # "Linguistics",
]


def generate_keyword(field_of_study: str, num_keywords: int) -> list[str]:
    class Keywords(BaseModel):
        keywords: list[str] = Field(description="The list of search keywords")

    @ell.complex(model="gpt-4o", response_format=Keywords)
    def lmp():
        return [
            ell.system(
                f"You are a top researcher in the field of {field_of_study}."
            ),
            ell.user(
                f"Generate {num_keywords} technical search keywords related to {field_of_study} that a PhD researcher like yourself might use on a paper search engine like google scholar, arxiv etc."
            ),
        ]

    return lmp().parsed.keywords  # pyright: ignore


def generate_keywords_for_all_fields(
    outdir: str,
    filename: str = "s2_keywords.json",
):
    keywords = dict()
    for field_of_study in tqdm(FIELDS_OF_STUDY):
        keywords[field_of_study] = generate_keyword(
            field_of_study=field_of_study, num_keywords=10
        )

    with open(os.path.join(outdir, filename), "w") as f:
        json.dump(keywords, f, indent=4)


if __name__ == "__main__":
    fire.Fire(generate_keywords_for_all_fields)

    # python -m tasks.s2.generate_keywords --outdir /root/weka/oe-training-default/webolmo/tanmayg/webolmo-synthetic
