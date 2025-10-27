import random
from typing import Literal, Optional

import ell
from pydantic import BaseModel, Field

# import apis.wikipedia_api as wikipedia_api
from tasks.instruction_utils import get_instruction
from tasks.persona_utils import read_personas


def get_recipe_generator():
    class SearchWords(BaseModel):
        words: list[str] = Field(description="The list of search words")

    @ell.complex(model="gpt-4o", response_format=SearchWords)
    def lmp(persona: str, num_words: int):
        return [
            ell.system(f"You are {persona}"),
            ell.user(
                f"Generate {num_words} common, real-world recipes that you might look up on Allrecipes.com. "
                f"Examples: 'chicken parmesan', 'chocolate chip cookies', 'beef stew', 'caesar salad'. "
                f"Make sure to include a variety of recipes including appetizers, main courses, and desserts. "
                f"Use simple, clear recipe names that people would actually search for."
            ),
        ]

    def get_recipe_from_llm(
        persona: str, num_words: int
    ) -> list[str]:
        return lmp(persona, num_words).parsed.words  # type: ignore

    return get_recipe_from_llm


def create_recipe_search_task(recipe_name: str):
    steps = [
        "Unless already on AllRecipes with the search bar visible, go to https://www.allrecipes.com/",
        f"Search for '{recipe_name}' using the search input box",
        "Click on the first recipe result",
        "After the recipe page loads, inform the user of:",
        "1. The recipe title",
        "2. Total cooking time",
        "3. Number of servings",
        "4. A brief description of the recipe",
    ]

    return [
        dict(
            task_type="allrecipes_recipe_search",
            recipe=recipe_name,
            steps=steps,
        )
    ]


def create_ingredient_search_task(ingredient: str):
    steps = [
        "Unless already on AllRecipes, go to https://www.allrecipes.com/",
        f"In the search bar titled 'Find a recipe or ingredient' type '{ingredient}'",
        "Click on the first recipe result",
        "After the recipe page loads, inform the user of:",
        "1. The recipe title",
        "2. Total cooking time",
        "3. The main ingredients needed",
        "4. A brief description of how the recipe uses the searched ingredient",
    ]

    return [
        dict(
            task_type="allrecipes_ingredient_search",
            ingredient=ingredient,
            steps=steps,
        )
    ]


def generate_allrecipes_task(
    persona: str,
    task_type: Literal["allrecipes_recipe_search", "allrecipes_ingredient_search"],
    num_tasks: int,
):
    if task_type == "allrecipes_recipe_search":
        recipes = get_recipe_generator()(persona=persona, num_words=num_tasks)
        tasks = []
        for recipe in recipes:
            tasks.extend(create_recipe_search_task(recipe))
    else:  # ingredient search
        ingredients = get_recipe_generator()(persona=persona, num_words=num_tasks)
        tasks = []
        for ingredient in ingredients:
            tasks.extend(create_ingredient_search_task(ingredient))

    for task in tasks:
        task["instruction"] = get_instruction(
            "allrecipes", task["steps"]
        ).model_dump()
    return dict(tasks=tasks)


ALLRECIPES_TASK_TYPES = [
    "allrecipes_recipe_search",
    "allrecipes_ingredient_search",
]