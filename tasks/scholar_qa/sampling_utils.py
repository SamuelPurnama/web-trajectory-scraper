from typing import Literal

from tasks.instruction_utils import get_instruction


def common_steps(query: str):
    return [
        "Go to url 'https://scholarqa.allen.ai' unless already on it with the search box visible.",
        f"Search '{query}' using the search box. The Scholar QA website will take some time to process the query while displaying each processing step. You must wait until you see the final result (indicated by the appearance of a 'Download Report' button).",
    ]


def basic_scholar_qa_search(query: str):
    return dict(
        task_type="basic_scholar_qa_search",
        query=query,
        steps=[
            *common_steps(query),
            "When the final result is diplayed, let the user know that the result of their query is ready to view.",
        ],
    )


def scholar_qa_search_with_stats(query: str):
    return dict(
        task_type="scholar_qa_search_with_stats",
        query=query,
        steps=[
            *common_steps(query),
            "While Scholar QA is processing your request, make note of the number of highly relevant passages retrieved, number of papers retrieved from semantic scholar abstracts, number of highly relevant papers after re-ranking and aggregation, and the number of sections in the answer outline. Make note of the information as soon as it appears on the page.",
            "When the final result is diplayed, let the user know that the result of their query is ready to view and provide a summary of the information you made a note of.",
        ],
    )


def scholar_qa_search_with_titles(query: str):
    return dict(
        task_type="scholar_qa_search_with_titles",
        query=query,
        steps=[
            *common_steps(query),
            "While Scholar QA is processing your request, make note of the section titles generated as the answer outline.",
            "When the final result is diplayed, let the user know that the result of their query is ready to view and provide a list of the section titles you made a note of.",
        ],
    )


def scholar_qa_cited_papers(query: str):
    return dict(
        task_type="scholar_qa_cited_papers",
        query=query,
        steps=[
            *common_steps(query),
            "Once the final result is diplayed, scroll down to the bottom of the page where the number of papers cited in the answer is displayed and click it.",
            "Let the user know the citation count and that you have opened the citations.",
        ],
    )


def scholar_qa_search_most_relevant(query: str):
    return dict(
        task_type="scholar_qa_search_most_relevant",
        query=query,
        steps=[
            *common_steps(query),
            "While Scholar QA is processing your request, make note of the section titles generated as the answer outline.",
            "When the final result is diplayed, scroll down until you find the one section most relevant to the original query.",
            "Click on that section to reveal more details. Scroll down to ensure the section's title is near the top of the page.",
            f"Let the user know the section you just opened and why you think its the most relevant to the user's query '{query}'.",
        ],
    )


SCHOLAR_QA_TASK_TYPES = Literal[
    "basic_scholar_qa_search",
    "scholar_qa_search_with_stats",
    "scholar_qa_search_with_titles",
    "scholar_qa_cited_papers",
    "scholar_qa_search_most_relevant",
]


def generate_scholar_qa_task(
    task_type: SCHOLAR_QA_TASK_TYPES,
    query: str,
):
    task_generator = globals()[task_type]
    task = task_generator(query)
    task["instruction"] = get_instruction(
        "Scholar QA", task["steps"]
    ).model_dump()
    return task


if __name__ == "__main__":
    task_types: list[SCHOLAR_QA_TASK_TYPES] = [
        "basic_scholar_qa_search",
        "scholar_qa_search_with_stats",
        "scholar_qa_search_with_titles",
        "scholar_qa_cited_papers",
        "scholar_qa_search_most_relevant",
    ]
    for task_type in task_types:
        task = generate_scholar_qa_task(task_type, "History of coding agents")
        print(task)
