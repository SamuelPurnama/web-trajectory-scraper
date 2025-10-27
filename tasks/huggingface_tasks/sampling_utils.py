import os
import ell
import random
from typing import Literal
from pydantic import BaseModel, Field
from huggingface_hub import list_models, list_datasets

from tasks.huggingface_tasks.constants import *
from tasks.instruction_utils import get_instruction

from huggingface_hub import login
login(os.getenv("HUGGINGFACE_TOKEN"))


def get_huggingface_search_query_generator():
    class HFQuery(BaseModel):
        query: str = Field(description="Search query for Hugging Face Hub")

    @ell.complex(model="gpt-4o", response_format=HFQuery)
    def lmp(persona: str):
        return [
            ell.system(f"You are {persona}"),
            ell.user(
                "Generate a query you would use to search for datasets or models on the Hugging Face Hub. "
                "Examples: 'text-to-image model with stable diffusion', 'climate change dataset', 'translation model for French'."
            ),
        ]

    def get_queries(persona: str) -> str:
        return lmp(persona).parsed.query  # type: ignore

    return get_queries


def get_random_hf_model(min_downloads: int = 1000):
    models = list_models(sort="downloads", direction=-1, limit=10000)
    filtered = [m for m in models if m.downloads and m.downloads > min_downloads]
    return random.choice(filtered).modelId if filtered else None


def get_random_hf_dataset(min_downloads: int = 1000):
    datasets = list_datasets(sort="downloads", direction=-1, limit=10000)
    filtered = [d for d in datasets if d.downloads and d.downloads > min_downloads]
    return random.choice(filtered).id if filtered else None


def create_huggingface_search_task(query: str):
    return [dict(
        task_type="huggingface_search",
        query=query,
        steps=[
            "If you are not already on the Hugging Face Hub, go to url https://huggingface.co",
            "Click on the search bar.",
            f"Search for '{query}'"
        ],
    )]


def create_huggingface_docs_task():
    doc_page = random.choice(HF_DOCS)

    return [dict(
        task_type="huggingface_docs",
        doc_page=doc_page,
        steps=[
            "If you are not already on the Hugging Face Hub, go to url https://huggingface.co",
            "Click on 'Docs'",
            f"Scroll down until you find {doc_page}.",
            f"Click on the docs for {doc_page}.",
            "Scroll down the documentation page and read the content.",
            "Summarize the documentation."
        ],
    )]


def create_huggingface_community_task():
    steps = [
        "If you are not already on the Hugging Face Hub, go to url https://huggingface.co",
        "Click on 'Community'",        
    ]
    category = random.choices(HF_COMMUNITY, weights=[0.9, 0.05, 0.05])[0]
    steps.append(f"Choose {category}.")
    if category == 'Blog Articles':
        topic = random.choice(HF_BLOG)
        steps.append(f"Click on '{topic}'.")
    elif category == 'Social Posts':
        steps.extend([
            "Click on 'Sort: Trending",
            "Click 'Newest'.",
            "Click on the top post.",
            "Send the user a summary of the post."
        ])
    elif category == 'Daily Papers':
        steps.extend([
            "Filter by 'Monthly' papers.",
            "Click on the a paper with at least 10 upvotes. You may have to scroll to find this."
        ])

    return [dict(
        task_type="huggingface_community",
        category=category,
        steps=steps
    )]


def create_huggingface_model_lookup_code_task(model_id: str):
    return [dict(
        task_type="huggingface_model_lookup_code",
        model_id=model_id,
        steps=[
            "If you are not already on the Hugging Face Hub, go to url https://huggingface.co",
            "Click on the search bar.",
            f"Search for the model '{model_id}' in the search bar.",
            f"Open the model page for '{model_id}'.",
            "Click on 'Use this model'.",
            "Then, if available, click on 'Transformers'. If there is not a button for this, tell the user this is not available.",
            "Click on 'Copy'.",
            "Send the user the copied code."
        ],
    )]


def create_huggingface_dataset_lookup_code_task(dataset_id: str):
    return [dict(
        task_type="huggingface_dataset_lookup_code",
        dataset_id=dataset_id,
        steps=[
            "If you are not already on the Hugging Face Hub, go to url https://huggingface.co",
            "Click on the search bar.",
            f"Search for the dataset '{dataset_id}' in the search bar.",
            f"Open the dataset page for '{dataset_id}'.",
            "Click on 'Use this dataset'. If there is not a button for this, tell the user this is not available.",
            "Then, if available, click on 'Datasets'.",
            "Click on 'Copy'.",
            "Send the user the copied code."
        ],
    )]


def create_huggingface_dataset_qa_task(dataset_id: str):
    dataset_info = next((d for d in list_datasets(search=dataset_id, limit=1) if d.id == dataset_id), None)
    if not dataset_info:
        return []

    QA_TEMPLATES = {
        "downloads": "How many downloads does the dataset '{name}' have?",
        "cardData.tasks": "What task(s) is the dataset '{name}' used for?",
        "cardData.language": "What language(s) is the dataset '{name}' available in?",
        "cardData.license": "What is the license of the dataset '{name}'?",
        "createdAt": "When was the dataset '{name}' created?",
    }

    available_fields = []
    for key in QA_TEMPLATES:
        try:
            parts = key.split(".")
            value = dataset_info
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    value = getattr(value, part, None)
            if value:
                available_fields.append((key, QA_TEMPLATES[key], value))
        except Exception:
            continue

    return [
        dict(
            task_type="huggingface_dataset_qa",
            dataset_id=dataset_id,
            key=key,
            question=template.format(name=dataset_id),
            answer=value,
            steps=[
                "Go to url https://huggingface.co",
                f"Search for '{dataset_id}' in the search bar.",
                "Open the dataset page.",
                f"Answer the question: {template.format(name=dataset_id)}",
            ],
        )
        for key, template, value in available_fields
    ]


def create_huggingface_model_qa_task(model_id: str):
    model_info = next((m for m in list_models(search=model_id, limit=1) if m.modelId == model_id), None)
    if not model_info:
        return []

    QA_TEMPLATES = {
        "downloads": "How many downloads does the model '{name}' have?",
        "cardData.license": "What is the license of the model '{name}'?",
        "cardData.tags": "What tags are associated with the model '{name}'?",
        "cardData.model_size": "What is the size of the model '{name}'?",
        "likes": "How many likes does the model '{name}' have?",
        "createdAt": "When was the model '{name}' created?",
    }

    available_fields = []
    for key in QA_TEMPLATES:
        try:
            parts = key.split(".")
            value = model_info
            for part in parts:
                value = getattr(value, part, None) if hasattr(value, part) else value.get(part)
            if value:
                available_fields.append((key, QA_TEMPLATES[key], value))
        except Exception:
            continue

    return [
        dict(
            task_type="huggingface_model_qa",
            model_id=model_id,
            key=key,
            question=template.format(name=model_id),
            answer=value,
            steps=[
                "Go to https://huggingface.co",
                f"Search for '{model_id}' in the search bar.",
                "Open the model page.",
                f"Answer the question: {template.format(name=model_id)}",
            ],
        )
        for key, template, value in available_fields
    ]


def create_huggingface_dataset_filter_task():
    steps=[
        "Go to url https://huggingface.co",
        "Click on 'Datasets'",
    ]

    filter = random.choice(['language', 'modality', 'task'])
    if filter == 'language':
        num_languages = random.randint(1, 3)
        languages = random.sample(HF_LANGUAGES, num_languages)
        steps.extend([
            "Click on the 'Languages' filter.",
            f"Click on each of these languages: {languages}. You may need to scroll down to find all of them.",
        ])
    elif filter == 'modality':
        modality = random.choice(HF_MODALITIES)
        steps.extend(["Click on the 'Main' filter.", f"Choose the {modality} modality."])
    elif filter == 'task':
        ai_task = random.choice(HF_TASKS)
        steps.extend([
            "Click on the 'Tasks' filter.",
            f"Scroll down until you see the {ai_task} task.",
            f"Click on {ai_task}."
        ])
    steps.append("If there are any matching results, view the results.")

    return [dict(
        task_type="huggingface_dataset_filter",
        steps=steps
    )]


def create_huggingface_model_filter_task():
    steps=[
        "Go to url https://huggingface.co",
        "Click on 'Models'",
    ]

    filter = random.choice(['language', 'modality', 'task'])
    if filter == 'language':
        num_languages = random.randint(1, 3)
        languages = random.sample(HF_LANGUAGES, num_languages)
        steps.extend([
            "Click on the 'Languages' filter.",
            f"Click on each of these languages: {languages}. You may need to scroll down to find all of them.",
        ])
    elif filter == 'modality':
        modality = random.choice(HF_MODALITIES)
        steps.extend(["Click on the 'Main' filter.", f"Choose the {modality} modality. You may need to scroll down to find it."])
    elif filter == 'task':
        ai_task = random.choice(HF_TASKS)
        steps.extend([
            "Click on the 'Tasks' filter.",
            f"Scroll down until you see the {ai_task} task.",
            f"Click on {ai_task}."
        ])
    steps.append("If there are any matching results, view the results.")

    return [dict(
        task_type="huggingface_model_filter",
        steps=steps,
    )]


def generate_huggingface_task(
    persona: str,
    task_type: Literal[
        "huggingface_search",
        "huggingface_community",
        "huggingface_docs",
        "huggingface_model_lookup_code",
        "huggingface_dataset_lookup_code",
        "huggingface_dataset_filter",
        "huggingface_dataset_qa",
        "huggingface_model_qa",
        "huggingface_model_filter",
    ],
):
    tasks = []

    if task_type == "huggingface_search":
        query = get_huggingface_search_query_generator()(persona)
        tasks.extend(create_huggingface_search_task(query))

    elif task_type == "huggingface_community":
        tasks.extend(create_huggingface_community_task())

    elif task_type == "huggingface_docs":
        tasks.extend(create_huggingface_docs_task())

    elif task_type == "huggingface_model_lookup_code":
        model_id = get_random_hf_model()
        if model_id:
            tasks.extend(create_huggingface_model_lookup_code_task(model_id))

    elif task_type == "huggingface_dataset_lookup_code":
        dataset_id = get_random_hf_dataset()
        if dataset_id:
            tasks.extend(create_huggingface_dataset_lookup_code_task(dataset_id))

    elif task_type == "huggingface_dataset_qa":
        dataset_id = get_random_hf_dataset()
        if dataset_id:
            tasks.extend(create_huggingface_dataset_qa_task(dataset_id))

    elif task_type == "huggingface_model_qa":
        model_id = get_random_hf_model()
        if model_id:
            tasks.extend(create_huggingface_model_qa_task(model_id))

    elif task_type == "huggingface_dataset_filter":
        tasks.extend(create_huggingface_dataset_filter_task())

    elif task_type == "huggingface_model_filter":
        tasks.extend(create_huggingface_model_filter_task())

    else:
        raise ValueError(f"Unsupported task type: {task_type}")

    for task in tasks:
        task["instruction"] = get_instruction("huggingface", task["steps"]).model_dump()

    return dict(tasks=tasks)


HUGGINGFACE_TASK_TYPES = [
    "huggingface_search",
    "huggingface_community",
    "huggingface_docs",
    "huggingface_model_lookup_code",
    "huggingface_dataset_lookup_code",
    "huggingface_dataset_filter",
    "huggingface_dataset_qa",
    "huggingface_model_qa",
    "huggingface_model_filter"
]
