import json
import random
import re
from typing import Literal

import ell
from pydantic import BaseModel, Field
from scipy.sparse import find
from tasks.instruction_utils import get_instruction


### PAPER TASKS ###
def find_paper_on_pwc_by_title(title: str):
    steps = [
        f"Go to https://paperswithcode.com/ unless already on it with the search box visible.",
        f"Search '{title}' using the search box.",
        f"The paper that best matches '{title}' should be visible. If not, scroll down until you see it",
        "If you still don't see it, let the user know that the paper is not available on Papers with Code, and what the closest match is.",
        "Once you have identified the paper, click on it to open the paper page.",
    ]
    return [
        dict(
            task_type="find_paper_on_pwc_by_title",
            title=title,
            steps=steps,
        )
    ]

def find_paper_on_pwc_by_title_and_open_pdf(title: str):
    task = find_paper_on_pwc_by_title(title)[0]
    task["steps"].append(  # pyright: ignore
        "Once the page for the paper is open, click on the PDF link to open the PDF."
    )
    task["task_type"] = "find_paper_on_pwc_by_title_and_open_pdf"
    task["title"] = title
    return [task]


def find_paper_on_pwc_by_title_and_open_abstract(title: str):
    task = find_paper_on_pwc_by_title(title)[0]
    task["steps"].append(  # pyright: ignore
        "Once the page for the paper is open, click on the abstract link to open the abstract page."
    )
    task["task_type"] = "find_paper_on_pwc_by_title_and_open_abstract"
    task["title"] = title
    return [task]


def find_authors_of_paper_on_pwc(title: str):
    task = find_paper_on_pwc_by_title(title)[0]
    task["steps"].append(  # pyright: ignore
        "Once the page for the paper is open, find the authors of the paper."
    )
    task["task_type"] = "find_authors_of_paper_on_pwc"
    task["title"] = title
    return [task]


def go_to_code_repository_of_paper_on_pwc(title: str):
    task = find_paper_on_pwc_by_title(title)[0]
    task["steps"] +=  [ # pyright: ignore
        "Once the page for the paper is open, find the official code repository of the paper. If there is none, find the code repository with the most stars. Scroll down the page if necessary to find the code repository.",
        "Once you identify the code repository, click on it to open the repository page."
    ]
    task["task_type"] = "go_to_code_repository_of_paper_on_pwc"
    task["title"] = title
    return [task]


def find_number_of_code_repositories_of_paper_on_pwc(title: str):
    task = find_paper_on_pwc_by_title(title)[0]
    task["steps"].append(  # pyright: ignore
        "Once the page for the paper is open, find the number of available code repositories of the paper."
    )
    task["task_type"] = "find_number_of_code_repositories_of_paper_on_pwc"
    task["title"] = title
    return [task]


def go_to_first_dataset_of_paper_on_pwd(title: str):
    task = find_paper_on_pwc_by_title(title)[0]
    task["steps"] += [ # pyright: ignore
        "Once the page for the paper is open, go to the datasets section if there is one.",
        "Click on the first dataset link to open the dataset page."
    ]
    task["task_type"] = "find_first_dataset_of_paper_on_pwd"
    task["title"] = title
    return [task]


def find_tasks_of_paper_on_pwc(title: str):
    task = find_paper_on_pwc_by_title(title)[0]
    task["steps"] += [ # pyright: ignore
        "Once the page for the paper is open, go to the tasks section if there is one.",
        "Find the tasks listed in the tasks section, and report them to the user."
    ]
    task["task_type"] = "find_tasks_of_paper_on_pwc"
    task["title"] = title
    return [task]


def go_to_first_task_of_paper_on_pwc(title: str):
    task = find_paper_on_pwc_by_title(title)[0]
    task["steps"] +=  [ # pyright: ignore
        "Once the page for the paper is open, go to the tasks section if there is one.",
        "Click on the first task link to open the task page."
    ]
    task["task_type"] = "go_to_first_task_of_paper_on_pwc"
    task["title"] = title
    return [task]


def find_first_n_lines_of_abstract_of_paper_on_pwc(title: str, max_lines: int = 5):
    task = find_paper_on_pwc_by_title(title)[0]
    n = random.choice(range(1, max_lines + 1))
    task["steps"].append(  # pyright: ignore
        f"Once the page for the paper is open, relay the first {n} {'line' if n == 1 else 'lines'} from the abstract to the user."
    )
    task["title"] = title
    task["task_type"] = "find_first_n_lines_of_abstract_of_paper_on_pwc"
    return [task]


def summarize_results_of_paper_on_pwc(title: str):
    task = find_paper_on_pwc_by_title(title)[0]
    task["steps"] += [ # pyright: ignore
        "Once the page for the paper is open, go to the results section if there is one.",
        "Summarize the results listed in the results section, and report your summary to the user."
    ]
    task["task_type"] = "summarize_results_of_paper_on_pwc"
    task["title"] = title
    return [task]


def find_methods_of_paper_on_pwc(title: str):
    task = find_paper_on_pwc_by_title(title)[0]
    task["steps"] += [ # pyright: ignore
        "Once the page for the paper is open, go to the methods section if there is one.",
        "Find the methods listed in the methods section, and report them to the user."
    ]
    task["task_type"] = "find_methods_of_paper_on_pwc"
    task["title"] = title
    return [task]


def generate_pwc_qa(title: str, abstract: str, artifact: str = "paper"):
    class QuestionAnswer(BaseModel):
        question: str = Field(
            description="Factual question that can be answered based on the provided context."
        )
        answer: str = Field(
            description="Answer to the question typically containing 1-5 words or at most 20 words."
        )

    @ell.complex(model="gpt-4o", response_format=QuestionAnswer)
    def lmp():
        return [
            ell.system(f"You are a researcher."),
            ell.user(
                f"Generate a factual question answer pair that is of scientific relevance based on the following title and abstract of a {artifact}:\n\nTitle: {title}\n\nAbstract: {abstract}\n\n## Guidelines\n\nQuestion should be such that the answer typically contains 1-5 words or at most 20 words. Make sure your question is well-defined and can be answered purely based on the Abstract without requiring any other world knowledge."
            ),
        ]

    qa: QuestionAnswer = lmp().parsed  # pyright: ignore
    return qa.question, qa.answer


def pwc_qa(title: str, abstract: str):
    task = find_paper_on_pwc_by_title(title)[0]
    question, answer = generate_pwc_qa(title, abstract)
    task["question"] = question
    task["answer"] = answer
    task["steps"].append(  # pyright: ignore
        f"Once the page for the paper is open and you're at the Abstract section, answer the following question based on the Abstract - '{question}'"
    )
    task["abstract"] = abstract
    task["task_type"] = "pwc_qa"
    return [task]


### DATASET TASKS ###
def find_dataset_by_name(name: str):
    steps = [
        f"Go to https://paperswithcode.com/ unless already on it with the search box visible.",
        f"Go to Datasets page.",
        f"Once you're on the Datasets page, locate the search box 'Search for datasets' on the page.",
        f"Search '{name}' using the search box.",
        f"The dataset that best matches '{name}' should be visible. If not, scroll down until you see it",
        "Once you have identified the dataset, click on it to open the dataset page.",
    ]
    return [
        dict(
            task_type="find_dataset_by_name",
            name=name,
            steps=steps,
        )
    ]


def go_to_paper_of_dataset(name: str):
    task = find_dataset_by_name(name)[0]
    task["steps"] += [ # pyright: ignore
        "Once the page for the dataset is open, find the paper that introduced the dataset."
        "Click on the paper link to open the paper page."
    ]
    task["task_type"] = "go_to_paper_of_dataset"
    task["name"] = name
    return [task]


def go_to_most_starred_dataloader_of_dataset(name: str):
    task = find_dataset_by_name(name)[0]
    task["steps"] += [ # pyright: ignore
        "Once the page for the dataset is open, go to the dataloaders section if there is one.",
        "Click on the dataloader with the most stars. Scroll down the page if necessary to find the dataloader.",
        "Once you identify the dataloader, click on it to open the dataloader page."
    ]
    task["task_type"] = "go_to_most_starred_dataloader_of_dataset"
    task["name"] = name
    return [task]


def summarize_usage_of_dataset(name: str):
    task = find_dataset_by_name(name)[0]
    task["steps"] += [ # pyright: ignore
        "Once the page for the dataset is open, go to the Usage section if there is one.",
        "Summarize the usage of the dataset listed in the Usage section, and report your summary to the user.",
        "If there is no Usage section, let the user know that the dataset does not have a Usage section."
    ]
    task["task_type"] = "summarize_usage_of_dataset"
    task["name"] = name
    return [task]


def find_similar_datasets_of_dataset(name: str):
    task = find_dataset_by_name(name)[0]
    task["steps"] += [ # pyright: ignore
        "Once the page for the dataset is open, go to the Similar Datasets section if there is one.",
        "Find the similar datasets listed in the Similar Datasets section, and report them to the user.",
        "If there is no Similar Datasets section, let the user know that the dataset does not have a Similar Datasets section."
    ]
    task["task_type"] = "find_similar_datasets_of_dataset"
    task["name"] = name
    return [task]


def find_benchmark_count_of_dataset(name: str):
    task = find_dataset_by_name(name)[0]
    task["steps"] += [ # pyright: ignore
        "Once the page for the dataset is open, go to the Benchmarks section if there is one.",
        "Find the total number of benchmarks, and report it to the user.",
        "If there is no Benchmarks section, let the user know that the dataset does not have a Benchmarks section."
    ]
    task["task_type"] = "find_benchmark_count_of_dataset"
    task["name"] = name
    return [task]


def find_paper_count_of_dataset(name: str):
    task = find_dataset_by_name(name)[0]
    task["steps"] += [ # pyright: ignore
        "Once the page for the dataset is open, go to the Papers section if there is one.",
        "Find the total number of papers, and report it to the user.",
        "If there is no Papers section, let the user know that the dataset does not have a Papers section."
    ]
    task["task_type"] = "find_paper_count_of_dataset"
    task["name"] = name
    return [task]


def go_to_first_benchmark_of_dataset(name: str):
    task = find_dataset_by_name(name)[0]
    task["steps"] += [ # pyright: ignore
        "Once the page for the dataset is open, go to the Benchmarks section if there is one.",
        "Click on the first benchmark link to open the benchmark page."
    ]
    task["task_type"] = "go_to_first_benchmark_of_dataset"
    task["name"] = name
    return [task]


def pwc_dataset_qa(name: str, abstract: str):
    task = find_dataset_by_name(name)[0]
    question, answer = generate_pwc_qa(name, abstract, artifact="dataset")
    task["question"] = question
    task["answer"] = answer
    task["steps"].append(  # pyright: ignore
        f"Once the page for the dataset is open, answer the following question based on the dataset - '{question}'"
    )
    task["abstract"] = abstract
    task["task_type"] = "pwc_dataset_qa"
    return [task]


# def go_to_area_page_via_browse_sota(area: str):
#     steps = [
#         f"Go to https://paperswithcode.com/ unless already on it with the search box visible.",
#         f"Go to Browse State-of-the-art page.",
#         f"Once you're on the Browse State-of-the-art page, go to the section for {area} if there is one.",
#         f"Click on the {area} link to open the {area} page."
#     ]
#     return [
#         dict(
#             task_type="go_to_area_page_via_browse_sota",
#             area=area,
#             steps=steps,
#         )
#     ]


# def find_benchmark_count_of_area(area: str):
#     task = go_to_area_page_via_browse_sota(area)[0]
#     task["steps"].append(  # pyright: ignore
#         "Once the page for the area is open, find the total number of benchmarks, and report it to the user.",
#     )
#     task["task_type"] = "find_benchmark_count_of_area"
#     task["area"] = area
#     return [task]


# def find_dataset_count_of_area(area: str):
#     task = go_to_area_page_via_browse_sota(area)[0]
#     task["steps"].append(  # pyright: ignore
#         "Once the page for the area is open, find the total number of datasets, and report it to the user.",
#     )
#     task["task_type"] = "find_dataset_count_of_area"
#     task["area"] = area
#     return [task]


# def find_paper_count_of_area(area: str):
#     task = go_to_area_page_via_browse_sota(area)[0]
#     task["steps"].append(  # pyright: ignore
#         "Once the page for the area is open, find the total number of papers, and report it to the user.",
#     )
#     task["task_type"] = "find_paper_count_of_area"
#     task["area"] = area
#     return [task]


def generate_pwc_task(
        task_type: Literal[
            # paper tasks
            "find_paper_on_pwc_by_title",
            "find_paper_on_pwc_by_title_and_open_pdf",
            "find_paper_on_pwc_by_title_and_open_abstract",
            "find_authors_of_paper_on_pwc",
            "find_number_of_code_repositories_of_paper_on_pwc",
            "find_tasks_of_paper_on_pwc",
            "find_first_n_lines_of_abstract_of_paper_on_pwc",
            "find_methods_of_paper_on_pwc",
            "go_to_code_repository_of_paper_on_pwc",
            "go_to_first_dataset_of_paper_on_pwd",
            "go_to_first_task_of_paper_on_pwc",
            "summarize_results_of_paper_on_pwc",
            "pwc_qa",
            # dataset tasks
            "find_dataset_by_name",
            "find_similar_datasets_of_dataset",
            "find_benchmark_count_of_dataset",
            "find_paper_count_of_dataset",
            "go_to_paper_of_dataset",
            "go_to_most_starred_dataloader_of_dataset",
            "go_to_first_benchmark_of_dataset",
            "summarize_usage_of_dataset",
            "pwc_dataset_qa",
            # area tasks
            # "go_to_area_page_via_browse_sota",
            # "find_benchmark_count_of_area",
            # "find_dataset_count_of_area",
            # "find_paper_count_of_area",
        ],
        paper_info: dict | None = None,
        dataset_info: dict | None = None,
    ):
    
    # ['paper_url', 'arxiv_id', 'title', 'abstract', 'url_abs', 'url_pdf', 'proceeding', 'authors', 'tasks', 'date', 'methods']
    if paper_info is not None:
        title = paper_info["title"]
        authors = paper_info["authors"]
        abstract = paper_info["abstract"]
    else:
        title = id = authors = abstract = None
    # ['url', 'name', 'full_name', 'homepage', 'description', 'paper', 'introduced_date', 'warning', 'modalities', 'tasks', 'languages', 'variants', 'num_papers', 'data_loaders']
    if dataset_info is not None:
        dataset_name = dataset_info["name"]
        dataset_abstract = dataset_info["description"]
    else:
        dataset_name = dataset_id = dataset_abstract = None

    task_function = globals()[task_type]

    if task_type in [
            "find_paper_on_pwc_by_title",
            "find_paper_on_pwc_by_title_and_open_pdf",
            "find_paper_on_pwc_by_title_and_open_abstract",
            "find_authors_of_paper_on_pwc",
            "find_number_of_code_repositories_of_paper_on_pwc",
            "find_tasks_of_paper_on_pwc",
            "find_first_n_lines_of_abstract_of_paper_on_pwc",
            "find_methods_of_paper_on_pwc",
            "go_to_code_repository_of_paper_on_pwc",
            "go_to_first_dataset_of_paper_on_pwd",
            "go_to_first_task_of_paper_on_pwc",
            "summarize_results_of_paper_on_pwc",
        ]:
        tasks = task_function(title)
    elif task_type in [
            "find_dataset_by_name",
            "find_similar_datasets_of_dataset",
            "find_benchmark_count_of_dataset",
            "find_paper_count_of_dataset",
            "go_to_paper_of_dataset",
            "go_to_most_starred_dataloader_of_dataset",
            "go_to_first_benchmark_of_dataset",
            "summarize_usage_of_dataset",
        ]:
        tasks = task_function(dataset_name)
    elif task_type == "pwc_qa":
        tasks = task_function(title, abstract)
    elif task_type == "pwc_dataset_qa":
        tasks = task_function(dataset_name, dataset_abstract)
    else:
        raise ValueError(f"Unknown task type: {task_type}")

    for task in tasks:
        task["instruction"] = get_instruction(
            "github", task["steps"]
        ).model_dump()

    return tasks


if __name__ == "__main__":
    papers_path = "/weka/oe-training-default/zixianm/WebOlmo/webolmo-synthetic/tasks/papers_with_code/papers-with-abstracts.json"
    datasets_path = "/weka/oe-training-default/zixianm/WebOlmo/webolmo-synthetic/tasks/papers_with_code/datasets.json"

    papers = json.load(open(papers_path, "r"))
    datasets = json.load(open(datasets_path, "r"))
    
    random.seed(42)
    paper_info = random.choice(papers)
    dataset_info = random.choice(datasets)
    print(paper_info)
    print(dataset_info)
    for task_type in [
        "find_paper_on_pwc_by_title",
        "find_paper_on_pwc_by_title_and_open_pdf",
        "find_paper_on_pwc_by_title_and_open_abstract",
        "find_authors_of_paper_on_pwc",
        "go_to_code_repository_of_paper_on_pwc",
        "find_number_of_code_repositories_of_paper_on_pwc",
        "go_to_first_dataset_of_paper_on_pwd",
        "find_tasks_of_paper_on_pwc",
        "go_to_first_task_of_paper_on_pwc",
        "find_first_n_lines_of_abstract_of_paper_on_pwc",
        "summarize_results_of_paper_on_pwc",
        "find_methods_of_paper_on_pwc",
        "pwc_qa",
        # dataset tasks
        "find_dataset_by_name",
        "find_similar_datasets_of_dataset",
        "find_benchmark_count_of_dataset",
        "find_paper_count_of_dataset",
        "go_to_paper_of_dataset",
        "go_to_most_starred_dataloader_of_dataset",
        "go_to_first_benchmark_of_dataset",
        "summarize_usage_of_dataset",
        # area tasks
    ]:  
        print(f"\n========== Task type: {task_type} ============")
        res = generate_pwc_task(task_type=task_type, paper_info=paper_info, dataset_info=dataset_info)
        print(res)
