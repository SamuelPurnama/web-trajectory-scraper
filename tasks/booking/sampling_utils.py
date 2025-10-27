import os
import ell
import random
from typing import Literal, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from openai import OpenAI
from tasks.booking.constants import *
from tasks.instruction_utils import get_instruction

openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

BOOKING_TASK_TYPES = [
    "booking_change_language",
    "booking_change_currency",
    "booking_list_trending_destinations",
    "booking_search_flights",
    "booking_search_car_rentals",
    "booking_search_attractions",
    "booking_search_stays",
    "booking_search_cruise"
]


def get_booking_location_generator():
    class Location(BaseModel):
        location: str = Field(
            description="Name of a city, region, or destination for Booking.com searches.")

    @ell.complex(model="gpt-4o", response_format=Location)
    def lmp(persona: str):
        return [
            ell.system(f"You are {persona} exploring travel ideas."),
            ell.user(
                "Generate a realistic and specific travel destination that you would search for on Booking.com, such as 'Barcelona' or 'Yellowstone National Park'."
            ),
        ]

    def get_location_from_llm(persona: str) -> str:
        return lmp(persona).parsed.location  # type: ignore

    return get_location_from_llm


def random_date_range():
    today = datetime.today()
    start = today + timedelta(days=random.randint(7, 60))
    end = start + timedelta(days=random.randint(2, 14))
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


def create_booking_search_stays_task(location: str) -> list[dict]:
    start_date, end_date = random_date_range()
    num_adults = random.randint(1, 6)
    num_children = random.randint(0, 6)
    num_rooms = random.randint(1, 4)

    return [
        {
            "task_type": "booking_search_stays",
            "steps": [
                "Go to https://www.booking.com",
                "Click on the search bar labeled 'Where are you going?'",
                f"Type in {location}.",
                "Click on the calendar to select dates.",
                f"Click on start date {start_date}.",
                f"Click on end date {end_date}.",
                "Click on the person icon.",
                f"Choose {num_adults} adults.",
                f"Choose {num_children} children.",
                f"Choose {num_rooms} rooms.",
                "Click the search button."
            ],
        }
    ]


def create_booking_attractions_task(location: str):
    date_0, date_1 = random_date_range()
    return [{
        "task_type": "booking_search_attractions",
        "steps": [
            "Go to https://www.booking.com",
            "Click on the 'Attractions' button",
            "Click on 'Where are you going' search bar",
            f"Type '{location}' into the search box.",
            f"Once '{location}' has popped up in the dropdown beneath the search bar, click on it",
            "Click 'Select your dates' button",
            f"If the pop up of the rental period is already displayed matching {date_0}, select {date_0}"
            f" - ELSE: Click on the '>' / 'Next month' button to see the next month, repeat until {date_0} is available, then select {date_0}",
            f"If the pop up of the rental period is already displayed matching {date_1}, select {date_1}"
            f" - ELSE: Click on the '>' / 'Next month' button to see the next month, repeat until {date_1} is available, then select {date_1}",
            "Click the 'Search' button",
            "Click on the first result of the page",
            "Exit and return the name of the attraction to the user"
        ]
    }]


def create_booking_flights_task(location_A: str, location_B: str):
    start_date, end_date = random_date_range()
    num_adults = random.randint(1, 6)
    trip_type = random.choice(["round-trip", "one-way"])
    return [{
        "task_type": "booking_search_flights",
        "steps": [
            "Go to https://www.booking.com",
            f"Click on '{trip_type}' option",
            "Click on search bar 'Where from'",
            f"Type in {location_A}",
            "Click on search bar 'Where to'",
            f"Type in {location_B}",
            "Click on calendar",
            f"Click on start date {start_date}",
            f"Click on end date {end_date}",
            "Click on person icon",
            f"Choose {num_adults} adults",
            "Click search button"
        ]
    }]


def create_booking_car_rentals_task(location: str):
    date_A, date_B = random_date_range()
    return [{
        "task_type": "booking_search_car_rentals",
        "steps": [
            "Go to https://www.booking.com",
            "Click on search bar 'Pick-up location'",
            f"Type in {location}",
            "Click on calendar labeled 'Pick-up date'",
            f"Choose pick up date {date_A}",
            "Click on calendar labeled 'Drop-off date'",
            f"Choose drop off date {date_B}",
            "Click search",
            "Wait for the results to load",
            "Tell the user the price of the first result"
        ]
    }]


def create_booking_search_cruise_task() -> list[dict]:
    port_type = random.choice(['us', 'international'])
    if port_type == 'us':
        departure_port = random.choice(BOOKING_US_CRUISE_PORTS)
    elif port_type == 'international':
        departure_port = random.choice(BOOKING_INT_CRUISE_PORTS)

    return [
        {
            "task_type": "booking_search_cruise",
            "steps": [
                "Go to https://www.booking.com",
                "Click on the 'Cruises' button",
                "Click on 'Departure Port' button",
                f"Click on '{departure_port}'",
                "Click on the 'Close the departure port filter menu' button that is represented with a blue circle with a white X in it.",
                "Click 'View Cruises' button",
                "Click on 'Sort Results' Drop down",
                "Click on 'Price (Low to High)'",
                "Click 'Apply'",
                "Click on the first result in the page",
                "Exit and return the name of the cruise to the user"
            ]
        }
    ]


def create_booking_change_language_task() -> list[dict]:
    language = random.choice(BOOKING_LANGUAGES)
    return [
        {
            "task_type": "booking_change_language",
            "steps": [
                "Go to https://www.booking.com",
                "Click on 'Select your language' button, that is represented with a national flag in a circle.",
                f"Click on '{language}'."
            ]
        }
    ]


def create_booking_change_currency_task() -> list[dict]:
    currency = random.choice(BOOKING_CURRENCIES)
    return [
        {
            "task_type": "booking_change_currency",
            "steps": [
                "Go to https://www.booking.com",
                "Click on 'Select your currency',"
                " that is represented by an acronym for the currently used currency (e.g. USD for United States Dollar).",
                f"Click on '{currency}'."
            ]
        }
    ]


def create_booking_list_trending_task() -> list[dict]:
    return [
        {
            "task_type": "booking_list_trending_destinations",
            "steps": [
                "Go to https://www.booking.com",
                "Scroll down to the 'Trending destinations' section.",
                "Tell the user the top 2 destinations."
            ]
        }
    ]


def generate_booking_task(
    persona: str,
    task_type: Literal[
        "booking_search_stays",
        "booking_change_language",
        "booking_change_currency",
        "booking_list_trending_destinations",
        "booking_search_flights",
        "booking_search_car_rentals",
        "booking_search_attractions",
        "booking_search_cruise",
    ],
) -> dict:
    if task_type == "booking_search_stays":
        location = get_booking_location_generator()(persona)
        task = create_booking_search_stays_task(location)[0]
    elif task_type == "booking_change_language":
        task = create_booking_change_language_task()[0]
    elif task_type == "booking_change_currency":
        task = create_booking_change_currency_task()[0]
    elif task_type == "booking_list_trending_destinations":
        task = create_booking_list_trending_task()[0]
    elif task_type == "booking_search_flights":
        locA = get_booking_location_generator()(persona)
        locB = get_booking_location_generator()(persona)
        task = create_booking_flights_task(locA, locB)[0]
    elif task_type == "booking_search_car_rentals":
        location = get_booking_location_generator()(persona)
        task = create_booking_car_rentals_task(location)[0]
    elif task_type == "booking_search_attractions":
        location = get_booking_location_generator()(persona)
        task = create_booking_attractions_task(location)[0]
    elif task_type == "booking_search_cruise":
        task = create_booking_search_cruise_task()[0]
    else:
        raise NotImplementedError(f"Unknown task_type: {task_type}")

    task["goal"] = "\n".join(task["steps"])
    task["instruction"] = get_instruction(
        "booking.com", task["steps"]).model_dump()
    return task


if __name__ == "__main__":
    persona = "A seasoned traveler who loves exploring new destinations"
    for task_type in BOOKING_TASK_TYPES:
        task = generate_booking_task(persona, task_type)
        print(f"{task_type}: {task}")
    import ipdb; ipdb.set_trace()
