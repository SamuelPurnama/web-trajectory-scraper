import json
import random
import re
from typing import Literal

import ell
from pydantic import BaseModel, Field
from scipy.sparse import find

from tasks.arxiv.category_codes import sample_category_code
from tasks.github.constants import *
from tasks.instruction_utils import get_instruction


def sample_keyword():
    topic = random.choice(list(FIELD_TO_KEYWORDS.keys()))
    keywords = FIELD_TO_KEYWORDS[topic]
    keyword = random.choice(keywords)
    return keyword

def sample_language():
    return random.choice(LANGUAGES)

def sample_repo_sort_criteria():
    return random.choice(REPO_SORT_CRITERIA)


def find_repos_on_github_by_keyword(keyword: str):
    steps = [
        f"Go to https://github.com unless already on it with the search box visible.",
        f"Search '{keyword}' using the search box.",
        f"The repositories related to '{keyword}' should be visible. If not, scroll down until you see them",
    ]

    return [
        dict(
            task_type="find_repos_on_github_by_keyword",
            keyword=keyword,
            steps=steps,
        )
    ]


def find_repos_on_github_by_keyword_and_language(keyword: str, language: str):
    steps = [
        f"Go to https://github.com unless already on it with the search box visible.",
        f"Search '{keyword} language:{language}' using the search box.",
        f"The repositories related to '{keyword}' in {language} should be visible. If not, scroll down until you see them.",
    ]

    return [
        dict(
            task_type="find_repos_on_github_by_keyword_and_language",
            keyword=keyword,
            language=language,
            steps=steps,
        )
    ]


def find_top_repo_on_github_by_keyword_and_sort_criteria(keyword: str, sort_criteria: str):
    task = find_repos_on_github_by_keyword(keyword)[0]
    task["steps"] += [
        f"Sort the repositories by '{sort_criteria}' and identify the top repository from the list.",
        f"Once you have identified the repository, click on it to open the repository page.",
    ]
    task["task_type"] = "find_top_repo_on_github_by_keyword_and_sort_criteria"
    task["sort_criteria"] = sort_criteria
    task["keyword"] = keyword
    return [task]

def find_repo_on_github_by_name(repo_name: str):
    steps = [
        f"Go to https://github.com unless already on it with the search box visible.",
        f"Search '{repo_name}' using the search box.",
        f"The repository that best matches '{repo_name}' should be visible. If not, scroll down until you see it",
        f"Once you have identified the repository, click on it to open the repository page.",
    ]
    return [
        dict(
            task_type="find_repo_on_github_by_name",
            repo_name=repo_name,
            steps=steps,
        )
    ]

# def find_user_on_github_by_username(username: str):
#     steps = [
#         f"Go to https://github.com unless already on it with the search box visible.",
#         f"Search '{username}' using the search box.",
#         f"Filter by 'Users' to only look at the user results.",
#         f"The user related to '{username}' should be visible. If not, scroll down until you see it",
#     ]
#     return [
#         dict(
#             task_type="find_user_on_github_by_username",
#             username=username,
#             steps=steps,
#         )
#     ]

# def find_repo_count_of_user(username: str, repo_count: str):
#     task = find_user_on_github_by_username(username)[0]
#     task["steps"].append(  # pyright: ignore
#         f"Once the page for the user is open, find the repository count of the user."
#     )
#     task["task_type"] = "find_repo_count_of_user_on_github_by_username"
#     task["repo_count"] = repo_count
#     return [task]


# def find_followers_count_of_user(username: str, followers_count: str):
#     task = find_user_on_github_by_username(username)[0]
#     task["steps"].append(  # pyright: ignore
#         f"Once the page for the user is open, find the followers count of the user."
#     )
#     task["task_type"] = "find_followers_count_of_user_on_github_by_username"
#     task["followers_count"] = followers_count
#     return [task]


# def find_top_repo_of_user_by_criteria(username: str, repo_name: str, sort_criteria: str = ['stars', 'last updated', 'name'],):
#     task = find_user_on_github_by_username(username)[0]
#     task["steps"].append(  # pyright: ignore
#         f"Once the page for the user is open, go to the repositories section.",
#         f"Then, sort the repositories by '{sort_criteria}' and identify the top repository from the list.",
#     )
#     task["task_type"] = "find_top_repo_of_user_by_criteria"
#     task["sort_criteria"] = sort_criteria
#     task["repo_name"] = repo_name
#     task["username"] = username
#     return [task]


def go_to_github_repo_readme(repo_name: str):
    task = find_repo_on_github_by_name(repo_name)[0]
    task["steps"].append(  # pyright: ignore
        f"Once the page for the repository is open, navigate to the README section."
    )
    task["task_type"] = "go_to_github_repo_readme"
    task["repo_name"] = repo_name
    return [task]


def github_repo_first_lines_of_readme(repo_name: str, readme: str, max_lines: int = 5):
    task = go_to_github_repo_readme(repo_name)[0]
    n = random.choice(range(1, max_lines + 1))
    task["steps"].append(  # pyright: ignore
        f"Once you are at the README section, relay the first {n} {'line' if n == 1 else 'lines'} from the README to the user."
    )
    task["repo_name"] = repo_name
    task["task_type"] = "github_repo_first_lines_of_readme"
    task["readme"] = readme
    return [task]


def find_star_count_of_repo(repo_name: str):
    task = find_repo_on_github_by_name(repo_name)[0]
    task["steps"].append(  # pyright: ignore
        f"Once the page for the repository is open, find the star count of the repository."
    )
    task["task_type"] = "find_star_count_of_repo_on_github_by_name"
    return [task]


def find_fork_count_of_repo(repo_name: str):
    task = find_repo_on_github_by_name(repo_name)[0]
    task["steps"].append(  # pyright: ignore
        f"Once the page for the repository is open, find the fork count of the repository."
    )
    task["task_type"] = "find_fork_count_of_repo_on_github_by_name"
    return [task]


def find_branch_count_of_repo(repo_name: str):
    task = find_repo_on_github_by_name(repo_name)[0]
    task["steps"] += [  # pyright: ignore
        f"Once the page for the repository is open, find the total number of branches for this repository, and report it to user.",
    ]
    task["task_type"] = "find_branch_count_of_repo_on_github_by_name"
    return [task]


def find_commit_count_of_repo(repo_name: str):
    task = find_repo_on_github_by_name(repo_name)[0]
    task["steps"] += [  # pyright: ignore
        f"Once the page for the repository is open, find the total number of commits for this repository, and report it to user.",
    ]
    task["task_type"] = "find_commit_count_of_repo_on_github_by_name"
    return [task]


def find_last_commit_time_of_repo(repo_name: str):
    task = find_repo_on_github_by_name(repo_name)[0]
    task["steps"] += [  # pyright: ignore
        f"Once the page for the repository is open, find the time of the last commit for this repository, and report it to user.",
    ]
    task["task_type"] = "find_last_commit_time_of_repo_on_github_by_name"
    return [task]


def find_license_info_of_repo(repo_name: str):
    task = find_repo_on_github_by_name(repo_name)[0]
    task["steps"] += [  # pyright: ignore
        f"Once the page for the repository is open, go to the About section or scroll down to find the license section if there is one.",
        f"Once you locate the license section, report the license information to the user.",
    ]
    task["task_type"] = "find_license_info_of_repo_on_github_by_name"
    return [task]


def find_release_count_of_repo(repo_name: str):
    task = find_repo_on_github_by_name(repo_name)[0]
    task["steps"] += [  # pyright: ignore
        f"Once the page for the repository is open, go to Releases.",
        f"Then find the release count of the repository, and report it to user.",
    ]
    task["task_type"] = "find_release_count_of_repo_on_github_by_name"
    return [task]


def find_last_release_version_of_repo(repo_name: str):
    task = find_repo_on_github_by_name(repo_name)[0]
    task["steps"] += [  # pyright: ignore
        f"Once the page for the repository is open, go to Releases.",
        f"Then find the last release version of the repository, and report it to user.",
    ]
    task["task_type"] = "find_last_release_version_of_repo_on_github_by_name"
    return [task]


def find_open_issue_count_of_repo(repo_name: str):
    task = find_repo_on_github_by_name(repo_name)[0]
    task["steps"] += [  # pyright: ignore
        f"Once the page for the repository is open, go to Issues.",
        f"Then find the open issue count of the repository, and report it to user.",
    ]
    task["task_type"] = "find_open_issue_count_of_repo_on_github_by_name"
    return [task]


def find_open_pr_count_of_repo(repo_name: str):
    task = find_repo_on_github_by_name(repo_name)[0]
    task["steps"] += [  # pyright: ignore
        f"Once the page for the repository is open, go to Pull requests.",
        f"Then find the open pull request count of the repository, and report it to user.",
    ]
    task["task_type"] = "find_open_pr_count_of_repo_on_github_by_name"
    return [task]


def find_top_k_contributors_of_repo(repo_name: str, max_k: int = 3):
    task = find_repo_on_github_by_name(repo_name)[0]
    k = random.choice(range(1, max_k + 1))
    task["steps"] += [  # pyright: ignore
        f"Once the page for the repository is open, go to Insights.",
        f"Then go to Contributors.",
        f"Then find the top {k} contributors of the repository that have contributed the most commits.",
    ]
    task["task_type"] = "find_top_k_contributors_of_repo_on_github_by_name"
    task["k"] = k
    return [task]


def generate_github_qa(repo_name: str, description: str, readme: str):
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
            ell.system(f"You are a developer"),
            ell.user(
                f"Generate a factual question answer pair that is of technical relevance based on the following name, description, and readme of a Github repository:\n\nName: {repo_name}\n\nDescription: {description}\n\nREADME: {readme}\n\n## Guidelines\n\nQuestion should be such that the answer typically contains 1-5 words or at most 20 words. Make sure your question is well-defined and can be answered purely based on the README without requiring any other world knowledge."
            ),
        ]

    qa: QuestionAnswer = lmp().parsed  # pyright: ignore
    return qa.question, qa.answer


def github_qa(repo_name: str, description: str, readme: str):
    task = find_repo_on_github_by_name(repo_name)[0]
    question, answer = generate_github_qa(repo_name, description, readme)
    task["question"] = question
    task["answer"] = answer
    task["steps"].append(  # pyright: ignore
        f"Once the page for the Github repository is open and you're at the README section, answer the following question based on the README content - '{question}'"
    )
    task["description"] = description
    task["readme"] = readme
    task["task_type"] = "arxiv_qa"
    return [task]



def generate_github_task(
        task_type: Literal[
            "find_repos_on_github_by_keyword",
            "find_repos_on_github_by_keyword_and_language",
            "find_top_repo_on_github_by_keyword_and_sort_criteria",
            "find_repo_on_github_by_name",
            "go_to_github_repo_readme",
            "github_repo_first_lines_of_readme",
            "find_star_count_of_repo",
            "find_fork_count_of_repo",
            "find_open_issue_count_of_repo",
            "find_open_pr_count_of_repo",
            "find_top_k_contributors_of_repo",
            "github_qa",
        ],
        repo_info: dict | None,
        keyword: str | None = None,
        language: str | None = None,
        sort_criteria: str | None = None,
    ):
    
    if repo_info is not None:
        repo_name = repo_info.get("name")
        description = repo_info.get("description")
        readme = repo_info.get("readme")
        # star_cnt = repo_info.get("stars")
        # fork_cnt = repo_info.get("forks")
    else:
        repo_name = description = readme = None

    random.seed(42)
    if keyword is None:
        keyword = sample_keyword()
    if language is None:
        language = sample_language()
    if sort_criteria is None:
        sort_criteria = sample_repo_sort_criteria()
    task_function = globals()[task_type]

    if task_type == "find_repos_on_github_by_keyword":
        tasks = task_function(keyword)
    elif task_type == "find_repos_on_github_by_keyword_and_language":
        tasks = task_function(keyword, language)
    elif task_type == "find_top_repo_on_github_by_keyword_and_sort_criteria":
        tasks = task_function(keyword, sort_criteria)
    elif task_type == "github_qa":
        tasks = task_function(repo_name, description, readme)
    elif task_type == "github_repo_first_lines_of_readme":
        tasks = task_function(repo_name, readme)
    else:
        tasks = task_function(repo_name)

    for task in tasks:
        task["instruction"] = get_instruction(
            "github", task["steps"]
        ).model_dump()

    return tasks



if __name__ == "__main__":
    keyword = "machine learning"
    sort_criteria = "most stars"
    with open("/weka/oe-training-default/zixianm/WebOlmo/webolmo-synthetic/tasks/github/gitbub_repos.jsonl", "r") as file:
        repos = [json.loads(line) for line in file]

    repo_info = repos[0]
    print(repo_info)
    for task_type in [
        # "find_repos_on_github_by_keyword",
        # "find_repos_on_github_by_keyword_and_language",
        # "find_top_repo_on_github_by_keyword_and_sort_criteria",
        # "find_repo_on_github_by_name",
        # "go_to_github_repo_readme",
        # "github_repo_first_lines_of_readme",
        # "find_star_count_of_repo",
        # "find_fork_count_of_repo",
        # "find_open_issue_count_of_repo",
        # "find_open_pr_count_of_repo",
        # "find_top_k_contributors_of_repo",
        # "github_qa",
        "find_branch_count_of_repo",
        "find_commit_count_of_repo",
        "find_last_commit_time_of_repo",
        "find_license_info_of_repo",
        "find_release_count_of_repo",
        "find_last_release_version_of_repo",
    ]:  
        print(f"\n========== Task type: {task_type} ============")
        res = generate_github_task(task_type=task_type, repo_info=repo_info)
        print(res)
