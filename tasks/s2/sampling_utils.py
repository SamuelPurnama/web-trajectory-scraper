import random
from typing import Literal

from tasks.instruction_utils import get_instruction


def basic_s2_search(paper: dict):
    keyword = paper["keyword"]
    return dict(
        task_type="basic_s2_search",
        keyword=keyword,
        steps=[
            "Go to url 'https://www.semanticscholar.org' unless already on it with the search box visible.",
            "If you see the 'ACCEPT & CONTINUE' button, click it.",
            f"Search '{keyword}' using the search box.",
        ],
    )


def basic_s2_search_and_filter_by_field(paper: dict):
    task = basic_s2_search(paper)
    task["task_type"] = "basic_s2_search_and_filter_by_field"
    field = task["field"] = paper["field"]
    task["steps"].append(  # pyright: ignore
        f"Filter by field '{field}' by clicking on 'Field of Study' and selecting '{field}' or similar."
    )
    return task


def basic_s2_search_and_filter_by_has_pdf(paper: dict):
    task = basic_s2_search(paper)
    task["task_type"] = "basic_s2_search_and_filter_by_has_pdf"
    field = task["field"] = paper["field"]
    task["steps"].append(  # pyright: ignore
        random.choice(
            [
                "Filter for results that have a pdf by clicking on 'Has PDF'.",
                "Filter out results that don't have a pdf by clicking on 'Has PDF'.",
                "Show only those results that have a pdf by clicking on 'Has PDF'.",
            ]
        )
    )
    return task


def s2_search_paper_by_title(paper: dict):
    title = paper["title"]
    return dict(
        task_type="s2_search_paper_by_title",
        title=title,
        steps=[
            "Go to 'https://www.semanticscholar.org' unless already on it with the search box visible.",
            "If you see the 'ACCEPT & CONTINUE' button, click it.",
            f"Search '{title}' using the search box.",
            f"Click on the search result link that best matches the title '{title}'. Usually its the top result. If you don't see it, scroll down to find it.",
        ],
    )


def s2_find_authors_of_paper(paper: dict):
    task = s2_search_paper_by_title(paper)
    task["task_type"] = "s2_find_authors_of_paper"
    task["steps"].append(  # pyright: ignore
        "Once on the paper's page that shows the title and TLDR, you should see the authors listed below the title. In some cases, you might see a '+X authors' link where X is a number. This indicates that there are more authors than visible. In such cases you should click on this link to reveal the entire author list. Finally, let the user know who the authors of this paper are."
    )
    return task


def s2_find_citations_of_paper(paper: dict):
    task = s2_search_paper_by_title(paper)
    task["task_type"] = "s2_find_citations_of_paper"
    task["steps"].append(  # pyright: ignore
        "Once on the paper's page that shows the title and TLDR, you should be able to see citation counts displayed as 'X Citations' where X is the number of citations of the paper (or scroll down until you see it). Let the user know this citation count. Note that citation count refers to papers that cited this paper."
    )
    return task


def s2_find_references_of_paper(paper: dict):
    task = s2_search_paper_by_title(paper)
    task["task_type"] = "s2_find_references_of_paper"
    task["steps"].append(  # pyright: ignore
        "Once on the paper's page that shows the title and TLDR, you should be able to see reference counts displayed as 'X References' where X is the number of references of the paper (or scroll down until you see it). Let the user know this reference count. Note that references are the papers that were cited in this paper."
    )
    return task


def s2_show_citations_of_paper(paper: dict):
    task = s2_search_paper_by_title(paper)
    task["task_type"] = "s2_show_citations_of_paper"
    task["steps"].append(  # pyright: ignore
        "Once on the paper's page that shows the title and TLDR, you should be able to see a link that reads 'X Citations' where X is the number of citations of the paper (or scroll down until you see it). Click on this link to go to the section that shows all citations of this paper i.e papers that have cited this paper."
    )
    return task


def s2_show_references_of_paper(paper: dict):
    task = s2_search_paper_by_title(paper)
    task["task_type"] = "s2_show_references_of_paper"
    task["steps"].append(  # pyright: ignore
        "Once on the paper's page that shows the title and TLDR, you should be able to see a link that reads 'X References' where X is the number of references of the paper (or scroll down until you see it). Click on this link to go to the section that shows all references of this paper i.e papers that have been cited in this paper."
    )
    return task


def s2_show_related_papers(paper: dict):
    task = s2_search_paper_by_title(paper)
    task["task_type"] = "s2_show_related_papers"
    task["steps"].append(  # pyright: ignore
        "Once on the paper's page that shows the title and TLDR, you should be able to see a link that reads 'Related Papers' (or scroll down until you see it). Click on this link to go to the section that shows all papers related to this paper."
    )
    return task


def s2_get_citation_blurb(paper: dict):
    task = s2_search_paper_by_title(paper)
    task["task_type"] = "s2_get_citation_blurb"
    citation_style = random.choice(["BibTeX", "MLA", "APA", "Chicago"])
    task["steps"].extend(  # pyright: ignore
        [
            "Once on the paper's page that shows the title and TLDR, you should be able to see a button that reads 'Cite'. Click on this button.",
            f"You should now see a modal with the heading 'Cite Paper'. In this modal, click on the button that reads '{citation_style}' and let the user know the exact citation blurb which usually contains the authors names, paper title, publication venue, year etc.",
        ]
    )
    return task


def s2_find_author_page(paper: dict):
    author = random.choice(paper["authors"])["name"]
    # field = paper["field"]
    return dict(
        task_type="s2_find_author_page",
        author=author,
        # field=field,
        steps=[
            "Go to 'https://www.semanticscholar.org' unless already on it with the search box visible.",
            "If you see the 'ACCEPT & CONTINUE' button, click it.",
            f"Search '{author}' using the search box.",
            f"The search results might show matching author profiles with links that read '{author}' or similar at the top of search results. If multiple matching author profiles are shown, pick the one with the most citations. If no matching author profiles are shown, see if there are links matching the author name below paper titles. If you do find such a link, then click on the link to go to that authors page.",
        ],
    )


def s2_find_author_stats(paper: dict):
    task = s2_find_author_page(paper)
    stat_type = random.choice(
        [
            "publication count",
            "h-index",
            "citation count",
            "highly influential citation count",
        ]
    )
    task["task_type"] = "s2_find_author_stats"
    task["stat_type"] = stat_type
    task["steps"].append(  # pyright: ignore
        f"Once on the author page, let the user know the author's {stat_type}"
    )
    return task


AUTHOR_DETAILS = Literal[
    "Publications", "Citing Authors", "Referenced Authors", "Co-Authors"
]


def s2_show_author_details(paper: dict, detail: AUTHOR_DETAILS | None = None):
    task = s2_find_author_page(paper)
    if detail is None:
        detail = random.choice(
            [
                "Publications",
                "Citing Authors",
                "Referenced Authors",
                "Co-Authors",
            ]
        )
    detail_to_desc = {
        "Publications": "publications by this author",
        "Citing Authors": "authors who have cited this author",
        "Referenced Authors": "authors who have been cited by this author",
        "Co-Authors": "authors who have co-authored papers with this author",
    }
    desc = detail_to_desc[detail]
    task["task_type"] = "s2_show_author_details"
    task["detail"] = detail
    task["steps"].append(  # pyright: ignore
        f"Once on the author's page, click on the navigation link that reads '{detail}' to show all {desc}."
    )
    return task


def s2_authors_most(paper: dict):
    task = s2_show_author_details(paper)
    author = task["author"]
    detail: AUTHOR_DETAILS = task["detail"]  # pyright: ignore
    n = random.choice(range(1, 6))
    detail_to_question = {
        "Publications": f"what are the {n} most influential publications by the author (titles, venue it was published, and citation counts).",
        "Citing Authors": f"who are the {n} authors who have cited this author the most and how many times they have cited this author.",
        "Referenced Authors": f"who are the {n} authors whose work this author has referenced the most (names and reference counts).",
        "Co-Authors": f"who are the {n} authors with whom this authors has co-authored the most papers (names and number of publications they have together).",
    }
    question = detail_to_question[detail]
    task["task_type"] = "s2_authors_most"
    task["question"] = question
    task["steps"].append(  # pyright: ignore
        f"You should now see the list of {author}'s top {detail.lower()} sorted in decrease order of influence/importance. Based on this list, let the user know {question}."
    )
    return task


S2_TASK_TYPES = Literal[
    "basic_s2_search",
    "basic_s2_search_and_filter_by_field",
    "basic_s2_search_and_filter_by_has_pdf",
    "s2_search_paper_by_title",
    "s2_find_authors_of_paper",
    "s2_find_citations_of_paper",
    "s2_find_references_of_paper",
    "s2_show_citations_of_paper",
    "s2_show_references_of_paper",
    "s2_show_related_papers",
    "s2_get_citation_blurb",
    "s2_find_author_page",
    "s2_find_author_stats",
    "s2_show_author_details",
    "s2_authors_most",
]


def generate_s2_task(
    task_type: S2_TASK_TYPES,
    paper: dict,
):
    task_generator = globals()[task_type]
    task = task_generator(paper)
    task["instruction"] = get_instruction(
        "Semantic Scholar", task["steps"]
    ).model_dump()
    return task


if __name__ == "__main__":
    task_types: list[S2_TASK_TYPES] = [
        "basic_s2_search",
        "basic_s2_search_and_filter_by_field",
        "basic_s2_search_and_filter_by_has_pdf",
        "s2_search_paper_by_title",
        "s2_find_authors_of_paper",
        "s2_find_citations_of_paper",
        "s2_find_references_of_paper",
        "s2_show_citations_of_paper",
        "s2_show_references_of_paper",
        "s2_show_related_papers",
        "s2_get_citation_blurb",
        "s2_find_author_page",
        "s2_find_author_stats",
        "s2_show_author_details",
        "s2_authors_most",
    ]

    sample_paper = {
        "keyword": "machine learning",
        "field": "Computer Science",
        "title": "A Comprehensive Guide to Machine Learning",
        "authors": [{"name": "Tanmay Gupta"}],
    }

    for task_type in task_types:
        task = generate_s2_task(task_type=task_type, paper=sample_paper)
        print(f"Generated task for {task_type}:")
        print(task)
