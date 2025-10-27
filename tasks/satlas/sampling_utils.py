import ell
import random
from typing import Literal
from pydantic import BaseModel, Field

from tasks.instruction_utils import get_instruction

SATLAS_LAYERS = {
    "Marine Infrastructure": [
        "How many wind turbines are shown?"
    ],
    "Renewable Energy": [
        "How many wind turbines are shown?",
        "How many square km of solar farms are there?"
    ],
    "Tree Cover": [
        "How many square km have Full tree coverage?",
        "How many square km have High tree coverage?",
        "How many square km have Medium tree coverage?"
    ]
}
SATLAS_DATES = [
    "2016-01", "2017-01", "2018-01", "2019-01", "2020-01",
    "2021-01", "2022-01", "2023-01", "2023-12"
]


def get_location_generator():
    class PlaceQuery(BaseModel):
        location: str = Field(
            description="Location that could be searchable on google maps such as 'Seattle' or 'Egypt' or 'Tasmania' or 'South America'"
        )

    @ell.complex(model="gpt-4o", response_format=PlaceQuery)
    def lmp(persona: str):
        return [
            ell.system(f"You are {persona}."),
            ell.user(
                f"Generate a location that could be searchable on google maps such as 'Seattle' or 'Egypt' or 'Tasmania' or 'South America'"
                f"Choose a place based on your lifestyle or interests."
            ),
        ]

    def get_location_from_llm(
        persona: str
    ) -> str:
        return lmp(persona).parsed.location  # type: ignore

    return get_location_from_llm


def create_satlas_map_qa_task(location: str, layer: str, question: str) -> list[dict]:
    date = random.choice(SATLAS_DATES)

    use_satellite = random.random() < 0.5
    use_heatmap = random.random() < 0.5
    access_map_options = random.random() < 0.5

    steps = [
        "Go to url https://satlas.allen.ai",
    ]

    if access_map_options == 0:
        steps.append("Click on 'Explore Map'.")
    else:
        steps.append("Click on'Map'.")

    steps.extend([
        "Click on the 'Search...' bar.",
        f"Type in the location {location}.",
        "Press enter to search for that location."
    ])

    steps.extend([
        f"Click on the '{layer}' bubble to activate that data layer.",
        f"Click on the date {date}.",
    ])

    if use_satellite:
        steps.append("Toggle the satellite view to on if it's not on already.")
    if use_heatmap:
        steps.append("Toggle the heatmap view to on if it's not on already..")

    steps.append(f"Answer the question: {question}")

    return [{
        "task_type": "satlas_map_qa",
        "steps": steps
    }]



def generate_satlas_task(
    persona: str,
    task_type: Literal[
        "satlas_map_qa_task",
    ]
):
    tasks = []
    if task_type == "satlas_map_qa_task":
         location = get_location_generator()(persona)
         for layer in SATLAS_LAYERS:
             for question in SATLAS_LAYERS[layer]:
                print("locaiton, layer, question:",location, layer, question )
                tasks.extend(create_satlas_map_qa_task(location, layer, question))

    for t,task in enumerate(tasks):
        print("Processing task ", t, " out of ", len(tasks), " for task type ", task_type)
        try:
            task["goal"] = "\n".join(task["steps"])
            task["instruction"] = get_instruction(
                "satlas", task["steps"]
            ).model_dump()
        except Exception as e:
            print("[ERROR] Skipping task due to instruction generation failure:", e)
            continue
    return dict(tasks=tasks)


SATLAS_TASK_TYPES = [
    "satlas_map_qa_task",  # use the satlas map to answer various questions about treecover and infrastructure
]
