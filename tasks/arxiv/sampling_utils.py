import json
import random
import re
from typing import Literal

import ell
from pydantic import BaseModel, Field
from scipy.sparse import find

from tasks.arxiv.category_codes import sample_category_code
from tasks.instruction_utils import get_instruction


def remove_version_suffix(url: str) -> str:
    return re.sub(r"v\d+$", "", url)


def find_paper_on_arxiv_by_title_via_search_engine(title: str, id: str):
    search_engine = random.choice(["google", "bing"])
    id_wo_version = remove_version_suffix(id)
    steps = [
        f"Go to https://{search_engine}.com unless already on it with the search box visible.",
        f"Search '{title} site:arxiv.org' using the search box.",
        f"The paper with title '{title}' should be visible in the first few search results. If not, scroll down the list of search results (usually in the top few) until you see the arxiv link corresponding to the title '{title}' and click it. Note that you want to go for the abstract link (e.g. https://arxiv.org/abs/2211.11559) instead of the pdf (e.g. https://arxiv.org/pdf/2211.11559) or html (e.g. https://arxiv.org/html/2211.11559).",
    ]

    return [
        dict(
            task_type="find_paper_on_arxiv_by_title_via_search_engine",
            title=title,
            id=id,
            steps=steps,
        )
    ]


def find_paper_on_arxiv_by_title(title: str, id: str):
    id_wo_version = remove_version_suffix(id)
    steps = [
        "Go to https://arxiv.org unless already on it with the search box visible.",
        f"Search '{title}' using the search box.",
        f"The search should have returned a list of papers. The paper with title '{title}' should be visible in one of the top results, but if not scroll down until you see it. Once found, click on the arxiv link for the paper.",
    ]

    return [
        dict(
            task_type="find_paper_on_arxiv_by_title",
            title=title,
            id=id,
            steps=steps,
        )
    ]


def find_paper_on_arxiv_by_title_and_open_pdf(title: str, id: str):
    id_wo_version = remove_version_suffix(id)
    steps = [
        "Go to https://arxiv.org unless already on it with the search box visible.",
        f"Search '{title}' using the search box",
        f"The search should have returned a list of papers. The paper with title '{title}' should be visible in one of the top results, but if not scroll down until you see it. Once found click on the pdf link for the paper.",
    ]

    return [
        dict(
            task_type="find_paper_on_arxiv_by_title_and_open_pdf",
            title=title,
            id=id,
            steps=steps,
        )
    ]


def find_paper_on_arxiv_by_title_and_open_html(title: str, id: str):
    id_wo_version = remove_version_suffix(id)
    task = find_paper_on_arxiv_by_title(title, id)[0]
    task["steps"].append(  # pyright: ignore
        f"If you are on the paper's arxiv page which shows the abstract, sometimes you might be able to see a link to the html version of the paper that might read 'HTML (Experimental)' or similar in the 'Access Paper' section. If you see it, click it to open the html version. If you don't see it, the html version might not be available so let the user know it doesn't exist for this paper."
    )
    task["task_type"] = "find_paper_on_arxiv_by_title_and_open_html"
    return [task]


def find_authors_of_paper_on_arxiv(title: str, id: str, authors: list[str]):
    task = find_paper_on_arxiv_by_title(title, id)[0]
    task["authors"] = authors
    author_str = ", ".join(authors)
    task["steps"].append(  # pyright: ignore
        f"Once on the abstract page for the article, identity the names of the author from the same page and convey it to the user. Otherwise, let the user know you could not find the paper."
    )
    task["task_type"] = "find_authors_of_paper_on_arxiv"
    return [task]


def find_versions_of_paper_on_arxiv(title: str, id: str):
    task = find_paper_on_arxiv_by_title(title, id)[0]
    task["steps"].append(  # pyright: ignore
        f"Once on the abstract page for the article, identify the number of versions of the paper from the same page (the versions are typically marked as v1, v2 etc in the Submission History section) and convey it to the user. Otherwise, let the user know you could not find the paper."
    )
    task["task_type"] = "find_versions_of_paper_on_arxiv"
    return [task]


def find_category_codes_of_paper_on_arxiv(title: str, id: str):
    task = find_paper_on_arxiv_by_title(title, id)[0]
    task["steps"].append(  # pyright: ignore
        f"Once on the abstract page for the article, see what subjects or listings the paper belongs to (e.g. cs.CV, cs.LG etc) and convey it to the user. Otherwise, let the user know you could not find the paper."
    )
    task["task_type"] = "find_category_codes_of_paper_on_arxiv"
    return [task]


def show_recent_arxiv_listing():
    subject, sub_category, category_code = sample_category_code()
    last_step = random.choice(
        [
            f"Click on the 'recent' link for the subject '{subject}'",
            f"Click on the link for the sub cateogry '{sub_category}'",
        ]
    )
    return [
        dict(
            task_type="show_recent_arxiv_listings",
            subject=subject,
            sub_category=sub_category,
            category_code=category_code,
            steps=[
                "Go to arxiv.org",
                f"Scroll down until you see the section for '{subject}'",
                last_step,
            ],
        )
    ]


def generate_arxiv_qa(title, summary):
    class QuestionAnswer(BaseModel):
        question: str = Field(
            description="Factual scientific question that can be answered based on the provided context."
        )
        answer: str = Field(
            description="Answer to the question typically containing 1-5 words or at most 20 words."
        )

    @ell.complex(model="gpt-4o", response_format=QuestionAnswer)
    def lmp():
        return [
            ell.system(f"You are a research scientist"),
            ell.user(
                f"Generate a factual question answer pair that is of scientific relevance based on the following title and summary of an arxiv paper:\n\nTitle: {title}\n\nSummary: {summary}\n\n## Guidelines\n\nQuestion should be such that the answer typically contains 1-5 words or at most 20 words. Make sure your question is scientific and can be answered purely based on the summary without requiring any other world knowledge."
            ),
        ]

    qa: QuestionAnswer = lmp().parsed  # pyright: ignore
    return qa.question, qa.answer


def arxiv_qa(title, id, summary):
    task = find_paper_on_arxiv_by_title(title, id)[0]
    question, answer = generate_arxiv_qa(title, summary)
    task["question"] = question
    task["answer"] = answer
    task["steps"].append(  # pyright: ignore
        f"Once the arxiv page for the paper is open, answer the following question based on the title and summary or abstract on the page - '{question}'"
    )
    task["summary"] = summary
    task["task_type"] = "arxiv_qa"
    return [task]


def arxiv_first_lines_of_abstract(title, id, summary, max_lines=3):
    task = find_paper_on_arxiv_by_title(title, id)[0]
    n = random.choice(range(1, max_lines + 1))
    task["steps"].append(  # pyright: ignore
        f"Once the arxiv page for the paper is open, relay the first {n} lines from the abstract to the user."
    )
    task["summary"] = summary
    task["task_type"] = "arxiv_first_lines_of_abstract"
    return [task]


def generate_arxiv_task(
    task_type: Literal[
        "find_paper_on_arxiv_by_title",
        "find_paper_on_arxiv_by_title_via_search_engine",
        "find_authors_of_paper_on_arxiv",
        "find_paper_on_arxiv_by_title_and_open_html",
        "find_paper_on_arxiv_by_title_and_open_pdf",
        "find_versions_of_paper_on_arxiv",
        "find_category_codes_of_paper_on_arxiv",
        "show_recent_arxiv_listing",
        "arxiv_qa",
        "arxiv_first_lines_of_abstract",
    ],
    paper_info: dict | None,
):
    if paper_info is not None:
        title = paper_info["title"]
        id = paper_info["id"]
        authors = [author["name"] for author in paper_info["authors"]]
        summary = paper_info["summary"]
    else:
        title = id = authors = summary = None

    task_function = globals()[task_type]
    if task_type == "find_authors_of_paper_on_arxiv":
        tasks = task_function(title, id, authors)
    elif task_type in ["arxiv_qa", "arxiv_first_lines_of_abstract"]:
        tasks = task_function(title, id, summary)
    elif task_type == "show_recent_arxiv_listing":
        tasks = task_function()
    else:
        tasks = task_function(title, id)

    for task in tasks:
        task["instruction"] = get_instruction(
            "arxiv", task["steps"]
        ).model_dump()

    return tasks


if __name__ == "__main__":
    title = "A multitype Fiksel interaction model for tumour immune microenvironments"
    id = "http://arxiv.org/abs/2307.05556v1"
    # print(find_paper_on_arxiv_by_title_via_search_engine(title, id))
    # print(find_paper_on_arxiv_by_title(title, id))
    # print(find_paper_on_arxiv_by_title_and_open_html(title, id))
    # print(find_paper_on_arxiv_by_title_and_open_pdf(title, id))
    # print(find_authors_of_paper_on_arxiv(title, id, ["Author1", "Author2"]))
    # for i in range(3):
    #     print(
    #         generate_arxiv_task(
    #             task_type="show_recent_arxiv_listing", paper_info=None
    #         )
    #     )
    print(
        generate_arxiv_task(
            task_type="arxiv_first_lines_of_abstract",
            paper_info=dict(
                title=title,
                id=id,
                summary="This model works 20% better than previous SOTA",
                authors=[{"name": "Tanmay"}],
            ),
        )
    )
