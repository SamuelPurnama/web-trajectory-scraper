import random
from typing import Literal, Optional

import ell
from pydantic import BaseModel, Field

# import apis.wikipedia_api as wikipedia_api
from tasks.instruction_utils import get_instruction
from tasks.persona_utils import read_personas


def get_cambridge_dictionary_keyword_generator():
    class SearchWords(BaseModel):
        words: list[str] = Field(description="The list of search words")

    @ell.complex(model="gpt-4o", response_format=SearchWords)
    def lmp(persona: str, num_words: int):
        return [
            ell.system(f"You are {persona}"),
            ell.user(
                f"Generate {num_words} words that you might look up in the Cambridge Dictionary based on your interests or profession. Choose words that might have British English vs American English differences, multiple meanings, interesting usage examples, or phrasal verbs."
            ),
        ]

    def get_cambridge_dictionary_words_from_llm(
        persona: str, num_words: int
    ) -> list[str]:
        return lmp(persona, num_words).parsed.words  # type: ignore

    return get_cambridge_dictionary_words_from_llm


def create_cambridge_dictionary_basic_search_task(word):
    steps = [
        "Unless already on Cambridge Dictionary with the search bar visible, go to https://dictionary.cambridge.org/",
        f"Search for '{word}' using the search input box",
        f"After the search results appear, inform the user about the definition of '{word}'.",
    ]

    return [
        dict(
            task_type="cambridge_dictionary_basic_search",
            word=word,
            steps=steps,
        )
    ]


def create_cambridge_dictionary_goto_section_task(word: str, num_tasks: int):
    tasks = []
    possible_sections = [ #manually curated
        "Examples",
        # "UK Dictionary",
        # "US Dictionary",
        # "Grammar",
        # "Translations",
        # "Idioms", 
        # "Phrasal Verbs",
        "Related word",
        "Browse"
        # "More meanings"
    ]

    num_to_generate = min(num_tasks, len(possible_sections))
    selected_sections = random.sample(possible_sections, num_to_generate)

    for section_name in selected_sections:
        steps = [
            "Unless already on Cambridge Dictionary with the search bar visible, go to https://dictionary.cambridge.org/",
            f"Search for '{word}' using the search input box.",
            f"Once on the page for '{word}', navigate to the section titled or related to '{section_name}'.",
            f"Confirm you have found the '{section_name}' section.",
        ]

        tasks.append(
            dict(
                task_type="cambridge_dictionary_goto_section",
                word=word,
                section=section_name,
                steps=steps,
            )
        )
    return tasks



def create_cambridge_dictionary_translate_task(word: str, num_tasks: int):
    tasks = []
    possible_languages = [ #manually curated
        "Spanish",
        "French",
        "German",
        "Russian"
    ]

    num_to_generate = min(num_tasks, len(possible_languages))
    selected_languages = random.sample(possible_languages, num_to_generate)

    for selected_language in selected_languages:
        steps = [
            "Unless already on Cambridge Dictionary with the search bar visible, go to https://dictionary.cambridge.org/translate/",
            f"Type {word} into the search box titled 'Enter text here'."
            f"Set the translation language from Spanish to '{selected_language}'. Is it likely called languageTo; change the selecion to the target language",
            f"Press the 'Translate' button to translate the word.",
            f"Capture the translation of '{word}' in '{selected_language}'.",
        ]

        tasks.append(
            dict(
                task_type="cambridge_dictionary_translate_word",
                word=word,
                language=selected_language,
                steps=steps,
            )
        )
    return tasks

def create_cambridge_dictionary_smart_vocabulary_task(word):
    steps = [
        "Unless already on Cambridge Dictionary with the search bar visible, go to https://dictionary.cambridge.org/",
        f"Search for '{word}' using the search input box.",
        f"After the search results appear, click on the '+' next to 'SMART Vocabulary: related words and phrases'.",
        f"Randomly select and relay back to the user 10 of the words in the newly expanded section.",
    ]
    return [{
        "task_type": "cambridge_dictionary_smart_vocabulary",
        "word": word,
        "steps": steps
    }]

def create_cambridge_dictionary_thesaurus_synonyms_task(word: str):
    steps = [
        "Unless already on Cambridge Dictionary with the search bar visible, go to https://dictionary.cambridge.org/plus/",
        f"Find the ‘Thesaurus’ section and click on it.",
        f"Find the search bar labeled ‘search Thesaurus’ and search for ‘{word}’.",
        f"Find the 'Synonyms' section and inform the user of the first 5 words found."
    ]
    
    return [
        dict(
            task_type="cambridge_dictionary_thesaurus_synonyms",
            word=word,
            steps=steps,
        )
    ]

def create_cambridge_dictionary_sentence_search_task(word):
    steps = [
        "Unless already on Cambridge Dictionary with the search bar visible, go to https://dictionary.cambridge.org/",
        f"Search for '{word}' using the search input box",
        f"After the search results appear, give the user an example of the '{word}' in a sentence.",
    ]

    return [
        dict(
            task_type="cambridge_dictionary_sentence_search",
            word=word,
            steps=steps,
        )
    ]

def create_cambridge_dictionary_US_pronounce_search_task(word):
    steps = [
        "Unless already on Cambridge Dictionary with the search bar visible, go to https://dictionary.cambridge.org/",
        f"Search for '{word}' using the search input box",
        f"After the search results appear, provide the user the 'us dpron-i' element of the '{word}'.",
    ]

    return [
        dict(
            task_type="cambridge_dictionary_US_pronounce_search",
            word=word,
            steps=steps,
        )
    ]
def create_cambridge_dictionary_UK_ronounce_search_task(word):
    steps = [
        "Unless already on Cambridge Dictionary with the search bar visible, go to https://dictionary.cambridge.org/",
        f"Search for '{word}' using the search input box",
        f"After the search results appear, provide the user the 'uk dpron-i' element of the '{word}'.",
    ]

    return [
        dict(
            task_type="cambridge_dictionary_UK_pronounce_search",
            word=word,
            steps=steps,
        )
    ]

def create_cambridge_dictionary_word_type(word):
    steps = [
        "Unless already on Cambridge Dictionary with the search bar visible, go to https://dictionary.cambridge.org/",
        f"Search for '{word}' using the search input box",
        f"After the search results appear, provide the user the 'pos dpos' element(s) of the '{word}'.",
    ]

    return [
        dict(
            task_type="cambridge_dictionary_word_type_search",
            word=word,
            steps=steps,
        )
    ]

def create_cambridge_dictionary_thesaurus_browse(word):
    steps = [
         "Unless already on Cambridge Dictionary with the search bar visible, go to https://dictionary.cambridge.org/plus/",
        f"Find the ‘Thesaurus’ section and click on it.",
        f"Find the search bar labeled 'Search Thesaurus’ and search for ‘{word}’.",
        f"Find the 'Browse' section and inform the user of the first 5 words found."
        
    ]

    return [
        dict(
            task_type="cambridge_dictionary_thesaurus_browse",
            word=word,
            steps=steps,
        )
    ]

def create_cambridge_dictionary_grammar_search(word):
    steps = [
         "Unless already on Cambridge Dictionary with the search bar visible, go to https://dictionary.cambridge.org/plus/",
        f"Find the ‘Grammar’ section and click on it.",
        f"Find the search bar labeled ‘Search Grammar and search for ‘{word}’.",
        f"Find the 'Browse' section and inform the user of the first 5 words found."
        
    ]

    return [
        dict(
            task_type="cambridge_dictionary_thesaurus_browse",
            word=word,
            steps=steps,
        )
    ]

def create_cambridge_dictionary_word_example_search(word):
    steps = [
         "Unless already on Cambridge Dictionary with the search bar visible, go to https://dictionary.cambridge.org/plus/",
        f"Type {word} into the search box titled 'Enter text here'."
        f"Find the EXAMPLES section",
        f"Inform the user of an example from Cambridge English Corpus."
        
    ]

    return [
        dict(
            task_type="cambridge_dictionary_word_example_search",
            word=word,
            steps=steps,
        )
    ]




def generate_cambridge_dictionary_task(
    persona: str,
    task_type: Literal[
        "cambridge_dictionary_basic_search", "cambridge_dictionary_translate_word"
    ],
    num_words: int,
    tasks_per_word: int = 1,
    words: Optional[list[str]] = None,
):
    if task_type == "cambridge_dictionary_basic_search":
        assert (
            tasks_per_word == 1
        ), f"cambridge_dictionary_basic_search only supports tasks_per_word==1 but got {tasks_per_word}"

    if words is None:
        words = get_cambridge_dictionary_keyword_generator()(
            persona=persona, num_words=num_words
        )

    tasks = []
    for word in words:
        if task_type == "cambridge_dictionary_basic_search":
            tasks.extend(create_cambridge_dictionary_basic_search_task(word))
        elif task_type == "cambridge_dictionary_goto_section":
            tasks.extend(create_cambridge_dictionary_goto_section_task(word, tasks_per_word))
        elif task_type == "cambridge_dictionary_translate_word":
            tasks.extend(create_cambridge_dictionary_translate_task(word, tasks_per_word))
        elif task_type == "cambridge_dictionary_smart_vocabulary":
            tasks.extend(create_cambridge_dictionary_smart_vocabulary_task(word))
        elif task_type == "cambridge_dictionary_thesaurus_synonyms":
            tasks.extend(create_cambridge_dictionary_thesaurus_synonyms_task(word))
        elif task_type == "cambridge_dictionary_sentence_search":
            tasks.extend(create_cambridge_dictionary_sentence_search_task(word))
        elif task_type == "cambridge_dictionary_US_pronounce_search":
            tasks.extend(create_cambridge_dictionary_US_pronounce_search_task(word))
        elif task_type == "cambridge_dictionary_UK_pronounce_search":
            tasks.extend(create_cambridge_dictionary_UK_ronounce_search_task(word))
        elif task_type == "cambridge_dictionary_word_type_search":
            tasks.extend(create_cambridge_dictionary_word_type(word))
        elif task_type == "cambridge_dictionary_thesaurus_browse":
            tasks.extend(create_cambridge_dictionary_thesaurus_browse(word))
        elif task_type == "cambridge_dictionary_word_example_search":
            tasks.extend(create_cambridge_dictionary_word_example_search(word))
        elif task_type == "cambridge_dictionary_grammar_search":
            tasks.extend(create_cambridge_dictionary_grammar_search(word))

    for task in tasks:
        task["instruction"] = get_instruction(
            "dictionary", task["steps"]
        ).model_dump()
    return dict(tasks=tasks, words=words)




CAMBRIDGE_DICTIONARY_TASK_TYPES = [
    "cambridge_dictionary_basic_search",
    "cambridge_dictionary_goto_section",
    "cambridge_dictionary_translate_word",
    "cambridge_dictionary_thesaurus_synonyms",
    "cambridge_dictionary_sentence_search",
    "cambridge_dictionary_US_pronounce_search",
    "cambridge_dictionary_UK_pronounce_search",
    "cambridge_dictionary_word_type_search",
    "cambridge_dictionary_thesaurus_browse",
    "cambridge_dictionary_word_example_search",
    "cambridge_dictionary_grammar_search",
]