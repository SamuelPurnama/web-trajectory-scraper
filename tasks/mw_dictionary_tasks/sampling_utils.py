import random
from typing import Literal, Optional

import ell
from pydantic import BaseModel, Field

# import apis.wikipedia_api as wikipedia_api
from tasks.instruction_utils import get_instruction
from tasks.persona_utils import read_personas


def get_merriam_webster_keyword_generator():
    class SearchWords(BaseModel):
        words: list[str] = Field(description="The list of search words")

    @ell.complex(model="gpt-4o", response_format=SearchWords)
    def lmp(persona: str, num_words: int):
        return [
            ell.system(f"You are {persona}"),
            ell.user(
                f"Generate {num_words} words that you might look up in a dictionary like Merriam-Webster based on your interests or profession. Choose words that are likely to have interesting definitions, etymologies, or word histories."
            ),
        ]

    def get_merriam_webster_words_from_llm(
        persona: str, num_words: int
    ) -> list[str]:
        return lmp(persona, num_words).parsed.words  # type: ignore

    return get_merriam_webster_words_from_llm


def create_merriam_webster_basic_search_task(word):
    steps = [
        "Unless already on Merriam-Webster with the search bar visible, go to https://www.merriam-webster.com/",
        f"Search for '{word}' using the search input box",
        f"After the search results appear, inform the user about the definition of '{word}' and any pronunciation guides provided.",
    ]

    return [
        dict(
            task_type="merriam_webster_basic_search",
            word=word,
            steps=steps,
        )
    ]


def create_merriam_webster_goto_section_task(word: str, num_tasks: int):
    tasks = []
    possible_sections = [ #manually curated
        "Example Sentences",
        "Related Articles",
        "Word History",
        "Kids Definition",
        "Entries Near"
    ]

    num_to_generate = min(num_tasks, len(possible_sections))
    selected_sections = random.sample(possible_sections, num_to_generate)

    for section_name in selected_sections:
        steps = [
            "Unless already on Merriam-Webster with the search bar visible, go to https://www.merriam-webster.com/",
            f"Search for '{word}' using the search input box.",
            f"Once on the page for '{word}', navigate to the section titled or related to '{section_name}'.",
            f"Confirm you have found the '{section_name}' section.",
        ]

        tasks.append(
            dict(
                task_type="merriam_webster_goto_section",
                word=word,
                section=section_name,
                steps=steps,
            )
        )
    return tasks



def generate_merriam_webster_task(
    persona: str,
    task_type: Literal[
        "merriam_webster_basic_search", "merriam_webster_goto_section"
    ],
    num_words: int,
    tasks_per_word: int = 1,
    words: Optional[list[str]] = None,
):
    if task_type == "merriam_webster_basic_search":
        assert (
            tasks_per_word == 1
        ), f"merriam_webster_basic_search only supports tasks_per_word==1 but got {tasks_per_word}"

    if words is None:
        words = get_merriam_webster_keyword_generator()(
            persona=persona, num_words=num_words
        )

    tasks = []
    for word in words:
        if task_type == "merriam_webster_basic_search":
            tasks.extend(create_merriam_webster_basic_search_task(word))
        elif task_type == "merriam_webster_goto_section":
            tasks.extend(
                create_merriam_webster_goto_section_task(word, tasks_per_word)
            )

    for task in tasks:
        task["instruction"] = get_instruction(
            "dictionary", task["steps"]
        ).model_dump()
    return dict(tasks=tasks, words=words)


MERRIAM_WEBSTER_TASK_TYPES = [
    "merriam_webster_basic_search",
    "merriam_webster_goto_section",
]
