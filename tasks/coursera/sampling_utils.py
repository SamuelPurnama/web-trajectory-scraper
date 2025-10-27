import os
import ell
import random
from openai import OpenAI
from typing import Literal, Optional
from pydantic import BaseModel, Field

from tasks.instruction_utils import get_instruction
from tasks.coursera.constants import *


def get_coursera_query_generator():
    class LocationPair(BaseModel):
        query: str = Field(
            description="Query that one would search on coursera.org"
        )

    @ell.complex(model="gpt-4o", response_format=LocationPair)
    def lmp(persona: str):
        return [
            ell.system(f"You are {persona}."),
            ell.user(
                "Generate a realistic and specific query that you could search on coursera.org."
            ),
        ]
    
    def get_coursera_query_from_llm(
        persona: str
    ) -> str:
        return lmp(persona).parsed.query  # type: ignore

    return get_coursera_query_from_llm


def create_coursera_search_task(query: str) -> list[dict]:
    task = [{
        "task_type": "coursera_search",
        "steps": [
                "If not already, go to url https://www.coursera.org/",
                "Click on the search bar labeled 'What do you want to learn?",
                f"Type in the search query {query}.",
                "Press enter",
                "Summarize the top results."
            ]
    }]
    return task


def create_coursera_filter_degrees_task() -> list[dict]:
    tasks = []
    for program in COURSERA_DEGREE_SUBJECT_FILTERS:
        for _ in range(0,500):
            num_subjects = random.randint(0,11)
            subjects = random.sample(COURSERA_DEGREE_SUBJECT_FILTERS, num_subjects)
            task = {
                "task_type": "coursera_filter_degrees",
                "steps": [
                        "If not already, go to url https://www.coursera.org/",
                        "Click on 'Online Degrees'",
                        "Click on 'Program Level'",
                        f"Filter by program {program}",
                        "Click on 'Apply'",
                        "Click on 'Subject'", 
                        f"Choose the followings subjects: {subjects}",
                        "Click on 'Apply'",
                        "If any results are returned, tell the user how many results there are."
                    ]
            }
            tasks.append(task)
    return tasks


def create_coursera_explore_categories_task() -> list[dict]:
    tasks = []
    for category in COURSERA_CATEGORIES:
        steps = [
                "If not already, go to url https://www.coursera.org/",
                "Click on 'Explore'.",
                f"Click on {category} underneath 'Explore Categories'",
            ]
        
        for qa in COURSERA_CATEGORY_QAs:
            steps.append(qa)
            task = {
                "task_type": "coursera_explore_category",
                "steps": steps
            }
            tasks.append(task)      
    return tasks


def create_coursera_explore_roles_task() -> list[dict]:
    tasks = []
    for role_type in COURSERA_ROLES.keys():
        for role in COURSERA_ROLES[role_type]:
            steps = [
                    "If not already, go to url https://www.coursera.org/",
                    "Click on 'Explore'",
                    "Click on 'View All' underneath 'Explore Roles'",
                    f"Filter roles by clicking on {role_type}",
                    f"Once the results have loaded, click on {role}",
                ]
            
            for qa in COURSERA_ROLE_QAs:
                steps.append(qa)
                task = {
                    "task_type": "coursera_explore_role",
                    "steps": steps
                }
                tasks.append(task)
    return tasks


def generate_coursera_task(
    persona: str,
    task_type: Literal[
        "coursera_explore_roles", "coursera_explore_categories", "coursera_filter_degrees", "coursera_search"
    ]
):
    tasks = []
    if task_type == "coursera_explore_roles":
        tasks.extend(create_coursera_explore_roles_task())
    elif task_type == "coursera_explore_categories":
        tasks.extend(create_coursera_explore_categories_task())
    elif task_type == "coursera_filter_degrees":
        tasks.extend(create_coursera_filter_degrees_task())
    elif task_type == "coursera_search":
        query = get_coursera_query_generator()(persona)
        tasks.extend(create_coursera_search_task(query))

    for t,task in enumerate(tasks):
        print("Processing task ", t, " out of ", len(tasks), " for task type ", task_type)
        try:
            task["goal"] = "\n".join(task["steps"])
            task["instruction"] = get_instruction(
                "coursera", task["steps"]
            ).model_dump()
        except Exception as e:
            print("[ERROR] Skipping task due to instruction generation failure:", e)
            continue
    return dict(tasks=tasks)


COURSERA_TASK_TYPES = [
    "coursera_explore_roles",
    "coursera_explore_categories",
    "coursera_filter_degrees",
    "coursera_search"
]