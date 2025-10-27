import random
from typing import Literal, Optional

import ell
from pydantic import BaseModel, Field

from tasks.instruction_utils import get_instruction
from tasks.persona_utils import read_personas


def get_all_recipe_keyword_generator():
    class SearchWords(BaseModel):
        recipes: list[str] = Field(description="The list of search recipes")

    @ell.complex(model="gpt-4o", response_format=SearchWords)
    def lmp(persona: str, num_recipes: int):
        return [
            ell.system(f"You are {persona}"),
            ell.user(
                f"Generate {num_recipes} real recipe names currently found on AllRecipes.com. The recipes should represent a variety of countries or regional cuisines. Only provide the exact recipe titles as they appear on AllRecipes."
            ),
        ]

    def get_all_recipes_titles_from_llm(
        persona: str, num_recipes: int
    ) -> list[str]:
        return lmp(persona, num_recipes).parsed.recipes  # type: ignore

    return get_all_recipes_titles_from_llm

def get_all_ingredient_keyword_generator():
    class IngredientNames(BaseModel):
        ingredients: list[str] = Field(description="The list of ingredient names")

    @ell.complex(model="gpt-4o", response_format=IngredientNames)
    def lmp(persona: str, num_ingredients: int):
        return [
            ell.system(f"You are {persona}"),
            ell.user(
                f"Generate {num_ingredients} unique and real ingredient names currently found on AllRecipes.com. The ingredients should represent a variety of cuisines and ingredient types."
            ),
        ]

    def get_all_ingredient_names_from_llm(
            persona: str, num_ingredients: int
    ) -> list[str]:
        return lmp(persona, num_ingredients).parsed.ingredients 

    return get_all_ingredient_names_from_llm


def create_all_recipes_basic_search_task(recipe):
    steps = [
        "Unless already on Allrecipes with the search bar visible, go to https://www.allrecipes.com/",
        f"Search for '{recipe}' using the search input box.",
        f"From the search results, select any one recipe that matches words in '{recipe}' in the title.",
        "Inform the user of the name of the recipe and a list of its ingredients."
    ]   

    return [
        dict(
            task_type="all_recipes_basic_search",
            recipe=recipe,
            steps=steps,
        )
    ]


def create_all_recipes_basic_ingredient_search_task(ingredient: str):
    steps = [
        "Unless already on Allrecipes with the search bar visible, go to https://www.allrecipes.com/",
        f"Search for '{ingredient}' using the search input box.",
        f"From the search results, select any one recipe that contains '{ingredient}' in the title or ingredients.",
        "Inform the user of the name of the recipe and a list of its ingredients.",
    ]

    return [
        dict(
            task_type="all_recipes_basic_ingredient_search",
            ingredient=ingredient,
            steps=steps,
        )
    ]


def create_all_recipes_search_directions_task(recipe: str):
    steps = [
        "Unless already on Allrecipes with the search bar visible, go to https://www.allrecipes.com/",
        f"Search for '{recipe}' using the search input box.",
        f"From the search results, select any one recipe that matches words in '{recipe}' in the title.",
        "Navigate to the 'Directions' section of the recipe.",
        "Extract and summarize the cooking directions for this recipe."
    ]

    return [
        dict(
            task_type="all_recipes_search_directions",
            recipe=recipe,
            steps=steps,
        )
    ]


def create_all_recipes_search_nutrition_facts_task(recipe: str):
    steps = [
        "Unless already on Allrecipes with the search bar visible, go to https://www.allrecipes.com/",
        f"Search for '{recipe}' using the search input box.",
        f"From the search results, select any one recipe that matches words in '{recipe}' in the title.",
        "Navigate to the 'Nutrition Facts' section of the recipe.",
        "Extract and list the nutrition facts provided for this recipe."
    ]

    return [
        dict(
            task_type="all_recipes_search_nutrition_facts",
            recipe=recipe,
            steps=steps,
        )
    ]


def create_all_recipes_goto_section_task(recipe: str, num_tasks: int):
    tasks = []
    possible_sections = [
        "Ingredients",
        "Directions",
        "Nutrition Facts",
        "Cook's Note",
        "Reviews"
    ]

    num_to_generate = min(num_tasks, len(possible_sections))
    selected_sections = random.sample(possible_sections, num_to_generate)

    for section_name in selected_sections:
        steps = [
            "Unless already on Allrecipes with the search bar visible, go to https://www.allrecipes.com/",
            f"Search for '{recipe}' using the search input box.",
            f"From the search results, select any one recipe that matches words in '{recipe}' in the title.",
            f"Once on the page, navigate to the section titled or related to '{section_name}'.",
            f"Confirm you have found the '{section_name}' section.",
        ]

        tasks.append(
            dict(
                task_type="all_recipes_goto_section",
                recipe=recipe,
                section=section_name,
                steps=steps,
            )
        )
    return tasks


def create_all_recipes_check_reviews_task(recipe: str):
    steps = [
        "Unless already on Allrecipes with the search bar visible, go to https://www.allrecipes.com/",
        f"Search for '{recipe}' using the search input box.",
        f"From the search results, select any one recipe that matches words in '{recipe}' in the title.",
        f"Scroll to the 'Reviews' section of the recipe.",
        "Check if there are any reviews available for this recipe.",
        f"Read and summarize the content of the 'Most helpful positive review' section",
        "If there are no reviews or 'Most helpful positive review' section, note explicitly."
    ]

    return [
        dict(
            task_type="all_recipes_check_reviews",
            recipe=recipe,
            steps=steps,
        )
    ]


def create_all_recipes_sort_reviews_task(recipe: str, num_tasks: int):
    tasks = []
    possible_sorts = [
        "Most Helpful",
        "Most Positive",
        "Least Positive",
        "Newest"
    ]

    num_to_generate = min(num_tasks, len(possible_sorts))
    selected_sorts = random.sample(possible_sorts, num_to_generate)

    for sort in selected_sorts:
        steps = [
            "Unless already on Allrecipes with the search bar visible, go to https://www.allrecipes.com/",
            f"Search for '{recipe}' using the search input box.",
            f"From the search results, select any one recipe that matches words in '{recipe}' in the title.",
            "Check whether the recipe has a rating.",
            "If no rating is found on the page, stop and report 'No rating available for this recipe.'",
            "Otherwise, scroll to the 'Reviews' section of the selected recipe.",
            f"Sort the reviews by '{sort}' using the available sort options.",
            f"Read the top review under '{sort}' and summarize its content.",
        ]

        tasks.append(
            dict(
                task_type="all_recipes_sort_reviews",
                recipe=recipe,
                sort=sort,
                steps=steps,
            )
        )
    return tasks


def create_all_recipes_compare_two_recipes_task(recipe: str):
    steps = [
         "Unless already on Allrecipes with the search bar visible, go to https://www.allrecipes.com/",
        f"Search for '{recipe}' using the search input box.",
        f"From the results, choose two different recipes that matches words in '{recipe}' in the title.",
        "Open both recipes in separate tabs or windows.",
        "Compare the two recipes in terms of ingredients, preparation time, and rating.",
        "Summarize the main differences and recommend which one to try and why."
    ]

    return [
        dict(
            task_type="all_recipes_compare_two_recipes",
            recipe=recipe,
            steps=steps,
        )
    ]


def create_all_recipes_top_n_recipes_task(recipe: str, n: int):
    steps = [
        "Unless already on Allrecipes with the search bar visible, go to https://www.allrecipes.com/",
        f"Search for '{recipe}' using the search input box.",
        f"From the search results, select the top {n} recipes that matches words in '{recipe}' in the title.",
        f"For each of the top {n} recipes, extract the recipe title and list it.",
        f"If fewer than {n} recipes are available, list the available recipes and note this back to the user.",
    ]

    return [
        dict(
            task_type="all_recipes_top_n_recipes",
            recipe=recipe,
            n=n,
            steps=steps,
        )
    ]


def create_all_recipes_sample_n_recipes_task(recipe: str, n: int):
    steps = [
        "Unless already on Allrecipes with the search bar visible, go to https://www.allrecipes.com/",
        f"Search for '{recipe}' using the search input box.",
        f"From the search results, randomly select {n} recipes that matches words in '{recipe}' in the title.",
        "For each of the selected recipes, extract the recipe title and list it.",
        f"If fewer than {n} recipes are available, list the available recipes and note this back to the user.",
    ]

    return [
        dict(
            task_type="all_recipes_sample_n_recipes",
            recipe=recipe,
            n=n,
            steps=steps,
        )
    ]


def generate_all_recipes_task(
    persona: str,
    task_type: Literal[
       "all_recipes_basic_search",
        "all_recipes_search_directions",
        "all_recipes_search_nutrition_facts",
        "all_recipes_goto_section",
        "all_recipes_check_reviews",
        "all_recipes_sort_reviews",
        "all_recipes_compare_two_recipes",
        "all_recipes_top_n_recipes",
        "all_recipes_sample_n_recipes",
        "all_recipes_basic_ingredient_search"
    ],
    num_keywords: int,
    tasks_per_word: int = 1,
    summarize_n: int = 0,
    recipes: Optional[list[str]] = None,
    ingredients: Optional[list[str]] = None,
):
    if task_type in ["all_recipes_basic_search", "all_recipes_basic_ingredient_search"]:
        assert (
            tasks_per_word == 1
        ), f"{task_type} only supports tasks_per_word==1 but got {tasks_per_word}"

    if task_type in ["all_recipes_top_n_recipes", "all_recipes_sample_n_recipes"]:
        assert (
            summarize_n > 0
        ), f"{task_type} only supports summarize_n>0 but got {summarize_n}"

    if recipes is None:
        recipes = get_all_recipe_keyword_generator()(
            persona=persona, num_recipes=num_keywords
        )
    if ingredients is None:
        ingredients = get_all_ingredient_keyword_generator()(
            persona=persona, num_ingredients=num_keywords
        )

    tasks = []
    for recipe in recipes:
        if task_type == "all_recipes_basic_search":
            tasks.extend(create_all_recipes_basic_search_task(recipe))
        elif task_type == "all_recipes_search_directions":
            tasks.extend(create_all_recipes_search_directions_task(recipe))
        elif task_type == "all_recipes_search_nutrition_facts":
            tasks.extend(create_all_recipes_search_nutrition_facts_task(recipe))
        elif task_type == "all_recipes_goto_section":
            tasks.extend(create_all_recipes_goto_section_task(recipe, tasks_per_word))
        elif task_type == "all_recipes_check_reviews":
            tasks.extend(create_all_recipes_check_reviews_task(recipe))
        elif task_type == "all_recipes_sort_reviews":
            tasks.extend(create_all_recipes_sort_reviews_task(recipe, tasks_per_word))
        elif task_type == "all_recipes_compare_two_recipes":
            tasks.extend(create_all_recipes_compare_two_recipes_task(recipe))
        elif task_type == "all_recipes_top_n_recipes":
            tasks.extend(create_all_recipes_top_n_recipes_task(recipe, summarize_n))
        elif task_type == "all_recipes_sample_n_recipes":
            tasks.extend(create_all_recipes_sample_n_recipes_task(recipe, summarize_n))

    for ingredient in ingredients:
        if task_type == "all_recipes_basic_ingredient_search":
            tasks.extend(create_all_recipes_basic_ingredient_search_task(ingredient))
    
    for task in tasks:
        task["instruction"] = get_instruction(
            "dictionary", task["steps"]
        ).model_dump()
    return dict(tasks=tasks, ingredients=ingredients, recipes=recipes)

ALL_RECIPES_TASK_TYPES = [
    "all_recipes_basic_search",
    "all_recipes_search_directions",
    "all_recipes_search_nutrition_facts",
    "all_recipes_goto_section",
    "all_recipes_check_reviews",
    "all_recipes_sort_reviews",
    "all_recipes_compare_two_recipes",
    "all_recipes_top_n_recipes",
    "all_recipes_sample_n_recipes",
    "all_recipes_basic_ingredient_search"
]