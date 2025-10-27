import json
import os
import random
import fire

from tasks.github.constants import *
from github import Github, Auth

def get_repos_by_keyword(keyword: str, max_results_per_keyword: int):
    auth = Auth.Token(os.getenv("GITHUB_TOKEN"))
    g = Github(auth=auth)
    repos = []
    repositories = g.search_repositories(query=f'{keyword}') # , sort='stars', order='desc', language:python
    for i, repo in enumerate(repositories):
        if i >= max_results_per_keyword: 
            break
        try:
            readme = repo.get_readme().decoded_content.decode()
        except Exception as e:
            print(f"Error fetching readme for {repo.name}: {e}")
            readme = None
        repo_info = {
            "name": repo.name, 
            "description": repo.description, 
            "url": repo.html_url, 
            "stars": repo.stargazers_count, 
            "forks": repo.forks_count,
            "language": repo.language,
            "readme": readme,
        }
        repos.append(repo_info)
    return repos


def main(output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "gitbub_repos.jsonl")
    wf = open(output_file, "w")
    for field in FIELD_TO_KEYWORDS:
        keywords = FIELD_TO_KEYWORDS[field]
        for kw in keywords:
            repos = get_repos_by_keyword(kw, 50)
            for repo in repos:
                repo["field"] = field
                repo["keyword"] = kw
                if repo["readme"] is not None:
                    wf.write(json.dumps(repo) + "\n")
                    wf.flush()
    wf.close()


if __name__ == "__main__":
    fire.Fire(main)
