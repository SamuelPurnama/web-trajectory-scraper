import random
from typing import Literal, Optional

import ell
from pydantic import BaseModel, Field

from tasks.instruction_utils import get_instruction
from tasks.persona_utils import read_personas


def get_bbc_keyword_generator():
    class SearchWords(BaseModel):
        topics: list[str] = Field(description="The list of search news keywords")

    @ell.complex(model="gpt-4o", response_format=SearchWords)
    def lmp(persona: str, num_topics: int):
        return [
            ell.system(f"You are {persona}"),
            ell.user(
                f"Generate {num_topics} news topics that you might find on BBC news based on general news topics which have more then 5 article results relating to them at any given time. Limit news topic to 1 word but you can expand to 2 words if absolutely necessary for topics like 'climate change' or 'election results'. Topics too specific like 'volcanic eruptions' should not be used since they are rare, but the more general topic 'natural disasters' can. Each news topic must be unique to the others."
            ),
        ]

    def get_bbc_titles_from_llm(
        persona: str, num_topics: int
    ) -> list[str]:
        return lmp(persona, num_topics).parsed.topics

    return get_bbc_titles_from_llm


# Predefined BBC navigation categories
BBC_CATEGORIES = ["Home", "News", "Sport", "Business", "Innovation", "Culture", "Arts", "Travel", "Earth"]


def create_bbc_basic_search_task(news_topic):
    steps = [
        "Unless already on BBC News, go to https://www.bbc.com/news.",
        "Click on the magnifying glass icon to open the search and navigation bar.",
        f"Search for '{news_topic}' using the search bar.",
        "From the results, select the most recent article.",
        "Display the headline and the publication date back to the user."
    ]   

    return [
        dict(
            task_type="bbc_basic_search",
            news_type=news_topic,
            steps=steps,
        )
    ]


def create_bbc_topic_nav_task(news_topic):
    steps = [
        "Unless already on BBCNews, go to https://www.bbc.com/.",
        f"Find and click on the button labeled '{news_topic}'.",
        "Find the first news article title and inform the user.",
    ]
    return [
        dict(
            task_type="bbc_topic_nav",
            news_topic=news_topic,
            steps=steps,
        )
    ]


def create_bbc_live_nav_task(news_topic):
    steps = [
        "Unless already on BBC News, go to https://www.bbc.com/news.",
        "Find the 'Live' button and click on it.",
        "Find the titles underneath the 'Live now' section and then find each title which relate to {news_topic} and have a 'Live' tag and which is above the 'recently live' section.",
        "Inform the user of all the titles which satisfy the conditions above.",
    ]
    return [
        dict(
            task_type="bbc_live_nav",
            news_topic=news_topic,
            steps=steps,
        )
    ]


def create_bbc_recent_articles_task(news_topic, num_articles):
    steps = [
        f"Unless already on BBCNews with the {news_topic} section in the navigation bar underlined, go to https://www.bbc.com/.",
        f"Find the {num_articles} most recent article titles to the user.",
        f"Among the {num_articles} chosen, visit a random article.",
        "Find the title of that article and inform the user.",
    ]
    return [
        dict(
            task_type="bbc_recent_article",
            news_topic=news_topic,
            steps=steps,
        )
    ]
    
    
def create_bbc_summarize_articles_task(news_topic, num_articles):
    steps = [
        f"Unless already on BBCNews with the {news_topic} section in the navigation bar underlined, go to https://www.bbc.com/.",
        f"Find the {num_articles} most recent article titles to the user.",
        "Summarize the article and inform the user.",
    ]
    return [
        dict(
            task_type="bbc_summarize_articles",
            news_topic=news_topic,
            steps=steps,
        )
    ]
    
    
def create_bbc_find_authors_task(news_topic, num_articles):
    steps = [
        f"Unless already on BBCNews with the {news_topic} section in the navigation bar underlined, go to https://www.bbc.com/.",
        f"Find the {num_articles} most recent article titles to the user.",
        "Find the author for each article and inform the user.",
    ]
    return [
        dict(
            task_type="bbc_find_authors",
            news_topic=news_topic,
            steps=steps,
        )
    ]
    
    
def generate_bbc_task(
    persona: str,
    task_type: Literal[
        "bbc_basic_search",
        "bbc_topic_nav",
        "bbc_live_nav",
        "bbc_recent_articles",
        "bbc_summarize_articles",
        "bbc_find_authors"
    ],
    num_words: int = 1,
    tasks_per_word: int = 1,
    topics: Optional[list[str]] = None,
):

    if task_type == "bbc_topic_nav":
        if topics is None:
            num_categories = min(num_words, len(BBC_CATEGORIES))
            topics = random.sample(BBC_CATEGORIES, num_categories)
    elif topics is None:
        topics = get_bbc_keyword_generator()(
            persona=persona, num_topics=num_words
        )

    tasks = []
    for topic in topics:
        if task_type == "bbc_basic_search":
            tasks.extend(create_bbc_basic_search_task(topic))
        elif task_type == "bbc_topic_nav":
            tasks.extend(create_bbc_topic_nav_task(topic))
        elif task_type == "bbc_live_nav":
            tasks.extend(create_bbc_live_nav_task(topic))
        elif task_type == "bbc_recent_articles":
            tasks.extend(create_bbc_recent_articles_task(topic, tasks_per_word))
        elif task_type == "bbc_summarize_articles":
            tasks.extend(create_bbc_summarize_articles_task(topic, tasks_per_word))
        elif task_type == "bbc_find_authors":
            tasks.extend(create_bbc_find_authors_task(topic, tasks_per_word))
        else:
            raise ValueError(f"Unsupported task_type: {task_type}")

    for task in tasks:
        task["instruction"] = get_instruction(
            "dictionary", task["steps"]
        ).model_dump()

    return dict(tasks=tasks, topics=topics)


BBC_TASK_TYPES = [
    "bbc_basic_search",
    "bbc_topic_nav",
    "bbc_live_nav",
    "bbc_recent_articles",
    "bbc_summarize_articles",
    "bbc_find_authors"
]