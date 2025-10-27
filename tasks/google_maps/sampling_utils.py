import os
import ell
import random
import requests
import googlemaps  # https://github.com/googlemaps/google-maps-services-python
from openai import OpenAI
from typing import Literal, Optional
from pydantic import BaseModel, Field

from tasks.instruction_utils import get_instruction
from tasks.google_maps.templates import DISTANCE_TEMPLATES, QA_FIELDS, QA_QUESTION_TEMPLATES


openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
gmaps = googlemaps.Client(key=os.environ["GOOGLE_MAPS_API_KEY"])


def get_google_maps_locations_generator():
    class LocationPair(BaseModel):
        keywords: str = Field(
            description="One string location pair in the form 'Start to Destination'"
        )

    @ell.complex(model="gpt-4o", response_format=LocationPair)
    def lmp(persona: str):
        return [
            ell.system(f"You are {persona}."),
            ell.user(
                "Generate a realistic and specific location pair for a person like you to search for directions on Google Maps. "
                "The location pair should be a string in the format 'Start to Destination', like 'Seattle to Portland' or 'Gas Works Park to Ballard' or 'Yellowstone National Park to Jackson, WY'. "
                "Both locations should be fully specified, rather than vague like 'Poetry Shop' or 'Technical Institute'."
                f"The location pair could be a mix of cities, neighborhoods, or specific landmarks that reflect your lifestyle or interests."
            ),
        ]
    
    def get_google_maps_locations_from_llm(
        persona: str
    ) -> str:
        return lmp(persona).parsed.keywords  # type: ignore

    return get_google_maps_locations_from_llm


def create_google_maps_directions_task(location_pair: str) -> list[dict]:
    # location_pair is expected to be "StartLocation to EndLocation"
    if " to " not in location_pair:
        return []
    
    start, end = location_pair.split(" to ", maxsplit=1)
    direction_mode = random.choice(["driving", "walking", "biking", "transit"])

    return [
        {
            "task_type": "google_maps_directions",
            "steps": [
                "If you are not already on Google Maps, go to https://www.google.com/maps",
                "Click on 'Directions'"
                f"Enter {start} as the starting point.",
                f"Enter {end} as the destination.",
                "Press enter.",
                f"If the starting point and destination are filled in, and possible routes are shown, switch to {direction_mode} mode.",
                "Select the recommended route. If a route does not exist, end the task.",
            ],
        }
    ]


def get_google_maps_place_in_location_generator():
    class PlaceQuery(BaseModel):
        keywords: str = Field(
            description="One string like 'PLACE in LOCATION', e.g., 'Gas Works Park in Seattle'"
        )

    @ell.complex(model="gpt-4o", response_format=PlaceQuery)
    def lmp(persona: str):
        return [
            ell.system(f"You are {persona}."),
            ell.user(
                f"Generate a realistic Google Maps place query that you might search for."
                f"The query should be a string in the format 'PLACE in LOCATION', like 'bagel shop in New York City' or 'mountain bike trailhead in Whistler'. "
                f"Choose a place based on your lifestyle or interests."
            ),
        ]

    def get_google_maps_places_from_llm(
        persona: str
    ) -> str:
        return lmp(persona).parsed.keywords  # type: ignore

    return get_google_maps_places_from_llm


def search_place_by_text(query: str):
    """Returns first result with place_id from a text search."""
    print(f"🔍 Searching for: {query}")
    results = gmaps.places(query=query)
    if not results.get("results"):
        print("❌ No results found")
        return None
    return results["results"][0]  # includes place_id, name, etc.


def get_place_details(place_id: str):
    """Fetch detailed metadata for a given place."""
    fields = [
        "name",
        "formatted_address",
        "formatted_phone_number",
        "opening_hours",
        "rating",
        "user_ratings_total",
        "wheelchair_accessible_entrance",
    ]
    details = gmaps.place(place_id=place_id, fields=fields)
    if details.get("status") != "OK":
        print(f"❌ Failed to get details: {details.get('status')}")
        return None
    return details.get("result")


def get_place_details_from_text(query: str):
    result = search_place_by_text(query)
    if result is None:
        return None
    return get_place_details(result["place_id"])


def create_google_maps_qa_task(place_query: str, max_fields: int = 3) -> list[dict]:
    tasks = []

    print("🔍 Place query:", place_query)
    details = get_place_details_from_text(place_query)
    if not details:
        print("⚠️ No details found for:", place_query)
        return []

    name = details.get("name", "this place")

    # Find valid fields we can ask about
    available_fields = [f for f in QA_FIELDS if f in details]
    if not available_fields:
        print(f"⚠️ No valid QA fields found in details for {place_query}")
        return []

    # Randomly select up to max_fields
    selected_fields = random.sample(available_fields, min(len(available_fields), max_fields))

    for field in selected_fields:
        question = QA_QUESTION_TEMPLATES[field].format(name=name)
        answer = details[field]

        # Clean up complex values (e.g., list of hours)
        if isinstance(answer, dict):
            answer = str(answer)
        elif isinstance(answer, list):
            answer = "; ".join(answer)

        tasks.append({
            "task_type": "google_maps_qa",
            "steps": [
                "If you are not already on Google Maps, go to https://www.google.com/maps",
                f"Search for '{name}' on Google Maps.",
                question,
            ]
        })

    return tasks


def get_google_maps_origin_generator():
    class OriginLocation(BaseModel):
        origin: str = Field(
            description="A realistic location string such as a city, neighborhood, or specific address based on the user's persona."
        )

    @ell.complex(model="gpt-4o", response_format=OriginLocation)
    def lmp(persona: str):
        return [
            ell.system(f"You are {persona}."),
            ell.user(
                "Where are you currently located or starting from? Respond with a realistic location such as a city, neighborhood, or landmark that represents your likely origin for a Google Maps search."
            ),
        ]

    def get_origin_from_llm(persona: str) -> str:
        return lmp(persona).parsed.origin  # type: ignore

    return get_origin_from_llm



def get_google_maps_place_generator():
    class PlaceType(BaseModel):
        place: str = Field(
            description="A realistic general place such as a coffee shop, library, gas station, hospital, or grocery store, based on the user's persona."
        )

    @ell.complex(model="gpt-4o", response_format=PlaceType)
    def lmp(persona: str, origin: str):
        return [
            ell.system(f"You are {persona}."),
            ell.user(
                f"Generate a realistic, public-facing place of interest."
                "Good Examples: coffee shop, museum, library, gas station, hospital, university, trailhead, or grocery store."
                "Choose something that reflects your lifestyle or interests."
            ),
        ]

    def get_query_from_llm(persona: str, origin: str) -> str:
        return lmp(persona, origin).parsed.place  # type: ignore

    return get_query_from_llm


def create_google_maps_distance_task(
    persona: str
) -> list[dict]:
    get_place_from_llm= get_google_maps_place_generator()
    get_origin_from_llm = get_google_maps_origin_generator()

    origin = get_origin_from_llm(persona)
    place = get_place_from_llm(persona, origin)

    direction_mode = random.choice(["driving", "walking"])

    print(f"Persona: {persona}")
    print(f"🔍 Place: '{place}'")
    print(f"📍 Origin: '{origin}'")

    return [
        {
            "task_type": "google_maps_distance",
            "steps": [
                "If you are not already on Google Maps, go to https://www.google.com/maps",
                f"Search for '{origin}'.",
                "Click on 'Nearby'.",
                f"Search for '{place}'.",
                f"Filter places that are within 15 minutes away via {direction_mode}.",
                "Select a place with at least 3.0 stars user rating. If there are no places with at least 3.0 stars, choose the top result.",
                f"Report the distance and travel time for the selected {place}.",
            ]
        }
    ]



def generate_google_maps_task(
    persona: str,
    task_type: Literal[
        "google_maps_directions", "google_maps_qa", "google_maps_distance"
    ]
):
    tasks = []
    if task_type == "google_maps_directions":
         location_pair = get_google_maps_locations_generator()(persona)
         tasks.extend(create_google_maps_directions_task(location_pair))
    elif task_type == "google_maps_qa":
         place_query = get_google_maps_place_in_location_generator()(persona)
         tasks.extend(
             create_google_maps_qa_task(place_query)
         )
    if task_type == "google_maps_distance":
        tasks.extend(
            create_google_maps_distance_task(persona)
        )

    for task in tasks:
        task["goal"] = "\n".join(task["steps"])
        task["instruction"] = get_instruction(
            "google_maps", task["steps"]
        ).model_dump()
        print("task:", task)
    return dict(tasks=tasks)


GOOGLE_MAP_TASK_TYPES = [
    "google_maps_directions",  # route between two known places
    "google_maps_qa",  # questions about places (hours of operation, address, user ratings, etc.)
    "google_maps_distance"  # distance and travel time from original to relative place
]
