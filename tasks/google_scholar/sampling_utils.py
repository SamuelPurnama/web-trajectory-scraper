import random
from typing import Literal

from tasks.instruction_utils import get_instruction


def basic_gscholar_search(paper: dict):
    keyword = paper["keyword"]
    return dict(
        task_type="basic_gscholar_search",
        keyword=keyword,
        steps=[
            "Go to url 'https://scholar.google.com' unless already on it with the search box visible.",
            f"Search '{keyword}' using the search box.",
        ],
    )


def basic_gscholar_author_search(paper: dict):
    author = random.choice(paper["authors"])["name"]
    return dict(
        task_type="basic_gscholar_author_search",
        author=author,
        steps=[
            "Go to url 'https://scholar.google.com' unless already on it with the search box visible.",
            f"Search '{author}' using the search box.",
            f"Matching user profiles for '{author}' should now be displayed. Click on the author link who has the most citations.",
        ],
    )


def basic_gscholar_title_search(paper: dict):
    title = paper["title"]
    return dict(
        task_type="basic_gscholar_title_search",
        title=title,
        steps=[
            "Go to url 'https://scholar.google.com' unless already on it with the search box visible.",
            f"Search '{title}' using the search box.",
            f"Matching papers for '{title}' should now be displayed. Usually the first search result is the most relevant. In rare cases, if the top few results are not a good match, you might need to scroll down until you find the most relevant match.",
        ],
    )


def gscholar_open_paper_page(paper: dict):
    task = basic_gscholar_title_search(paper)
    task["task_type"] = "gscholar_open_paper_page"
    task["steps"].append(  # pyright: ignore
        "Once you have located the paper in the search results, click on the paper title link to open the paper's page."
    )
    return task


def gscholar_paper_citation_count(paper: dict):
    task = basic_gscholar_title_search(paper)
    task["task_type"] = "gscholar_paper_citation_count"
    task["steps"].append(  # pyright: ignore
        "Once you have located the paper in the search results, let the user know its citation counts. It should be a link that reads 'Cited by X' where X is the citation count. If no such link exists then the paper has not been cited in which case the citation count is 0."
    )
    return task


def gscholar_paper_citation_blurb(paper: dict):
    task = basic_gscholar_title_search(paper)
    citation_type = random.choice(
        ["MLA", "APA", "Chicago", "Harvard", "Vancouver"]
    )
    task["task_type"] = "gscholar_paper_citation_blurb"
    task["citation_type"] = citation_type
    task["steps"].append(  # pyright: ignore
        f"Once you have located the paper in the search results, click on the link that reads 'Cite' to open the citation popup. Let the user know the citation for the paper in {citation_type} format"
    )
    return task


def gscholar_paper_related_articles(paper: dict):
    task = basic_gscholar_title_search(paper)
    task["task_type"] = "gscholar_paper_related_articles"
    task["steps"].append(  # pyright: ignore
        "Once you have located the paper in the search results, click on the link that reads 'Related articles'."
    )
    return task


def gscholar_author_info(paper: dict):
    info_type = random.choice(
        [
            "designation",
            "homepage link (if it exists)",
            "areas of interest (these are mentioned in the links below the author designation and home page info)",
        ]
    )
    task = basic_gscholar_author_search(paper)
    task["task_type"] = "gscholar_author_info"
    task["info_type"] = info_type
    task["steps"].append(  # pyright: ignore
        f"Once you are on the author's page, let the user know the author's {info_type}."
    )
    return task


def gscholar_author_citation_info(paper: dict):
    year = random.choice([2021, 2022, 2023, 2024, 2025])
    info_type = random.choice(
        [
            "citation count (All)",
            "citation count since 2020",
            "h-index (All)",
            "h-index since 2020",
            "i10-index (All)",
            "i10-index since 2020",
        ]
    )
    task = basic_gscholar_author_search(paper)
    task["task_type"] = "gscholar_author_citation_info"
    task["info_type"] = info_type
    task["steps"].append(  # pyright: ignore
        f"Once you are on the author's page, let the user know the author's {info_type}."
    )
    return task


def gscholar_authors_most_cited_papers(paper: dict):
    n = random.choice(range(1, 6))
    task = basic_gscholar_author_search(paper)
    task["task_type"] = "gscholar_authors_most_cited_papers"
    task["steps"].append(  # pyright: ignore
        f"Once you are on the author's page, let the user know the author's {n} most cited papers (title, authors, venue, citation count, and publication year). Since the papers are already shown in order of decreasing citation counts, you should return the top {n} papers in the table of results."
    )
    return task


def gscholar_sort_by_year(paper: dict):
    task = basic_gscholar_author_search(paper)
    task["task_type"] = "gscholar_sort_by_year"
    task["steps"].append(  # pyright: ignore
        f"Once on the author's page, click on the link that reads 'Year' to sort the author's work by publication date."
    )
    return task


def gscholar_most_recent_papers(paper: dict):
    task = gscholar_sort_by_year(paper)
    n = random.choice(range(1, 6))
    task["task_type"] = "gscholar_most_recent_papers"
    task["steps"].append(  # pyright: ignore
        f"Once the author's work is sorted by publication date, let the user know the {n} most recent papers. For each paper provide the title, authors, venue, citation count and year published."
    )
    return task


GSCHOLAR_TASK_TYPES = Literal[
    "basic_gscholar_search",
    "basic_gscholar_author_search",
    "basic_gscholar_title_search",
    "gscholar_open_paper_page",
    "gscholar_paper_citation_count",
    "gscholar_paper_citation_blurb",
    "gscholar_paper_related_articles",
    "gscholar_author_info",
    "gscholar_author_citation_info",
    "gscholar_authors_most_cited_papers",
    "gscholar_sort_by_year",
    "gscholar_most_recent_papers",
]


def generate_gscholar_task(
    task_type: GSCHOLAR_TASK_TYPES,
    paper: dict,
):
    task_generator = globals()[task_type]
    task = task_generator(paper)
    task["instruction"] = get_instruction(
        "Google Scholar", task["steps"]
    ).model_dump()
    return task


if __name__ == "__main__":
    sample_paper = {
        "keyword": "machine learning",
        "field": "Computer Science",
        "title": "A Comprehensive Guide to Machine Learning",
        "authors": [{"name": "Tanmay Gupta"}],
    }

    task_types: list[GSCHOLAR_TASK_TYPES] = [
        "basic_gscholar_search",
        "basic_gscholar_author_search",
        "basic_gscholar_title_search",
        "gscholar_open_paper_page",
        "gscholar_paper_citation_count",
        "gscholar_paper_citation_blurb",
        "gscholar_paper_related_articles",
        "gscholar_author_info",
        "gscholar_author_citation_info",
        "gscholar_authors_most_cited_papers",
        "gscholar_sort_by_year",
        "gscholar_most_recent_papers",
    ]

    for task_type in task_types:
        task = generate_gscholar_task(task_type, sample_paper)
        print(f"Task type: {task_type}")
        print(task)
