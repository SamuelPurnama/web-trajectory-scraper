import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

FLIGHTAWARE_TASK_TYPES = Literal[
    "fa_search_flight",
    "fa_explore_airports",
    "fa_live_flight_map",
    "fa_airport_delays",
    "fa_airline_insights",
    "fa_flight_cancellations",
    "fa_adsb_coverage_check",
    "fa_product_services",
    "fa_discussions",
    "fa_flight_tracking",
]

FLIGHTAWARE_SAMPLING_CONFIG: Dict[FLIGHTAWARE_TASK_TYPES, int] = {
    "fa_search_flight": 10,
    "fa_explore_airports": 10,
    "fa_live_flight_map": 10,
    "fa_airport_delays": 10,
    "fa_airline_insights": 10,
    "fa_flight_cancellations": 10,
    "fa_adsb_coverage_check": 10,
    "fa_product_services": 10,
    "fa_discussions": 10,
    "fa_flight_tracking": 10,
}

DEPARTURE_AIRPORTS = ["SEA", "SFO", "LAX", "JFK", "EWR", "ATL"]
DESTINATION_AIRPORTS = ["ORD", "DFW", "DEN", "LAS", "MCO"]
AIRLINES = ["Delta", "United", "American", "Southwest", "JetBlue"]

# FlightAware Products and Services
FLIGHTAWARE_PRODUCTS = [
    "AeroAPI",
    "FlightAware Firehose", 
    "FlightAware Foresight",
    "Rapid Reports",
    "Custom Reports",
    "FlightAware Aviator",
    "Premium Subscriptions",
    "FlightAware Global",
    "FlightAware FBO Toolbox",
    "FlightAware TV℠",
    "GlobalBeacon"
]

# Information types to research
INFO_TYPES = [
    "pricing and cost information",
    "availability and access requirements", 
    "features and capabilities",
    "integration requirements",
    "support and documentation",
    "trial or demo options",
    "subscription plans",
    "API access and limits",
    "data coverage and accuracy",
    "use cases and applications"
]

# Discussion board options
DISCUSSION_FILTERS = ["latest", "top"]
DISCUSSION_TIME_PERIODS = ["all time", "year", "quarter", "month", "week"]
DISCUSSION_SORT_OPTIONS = ["replies", "views", "activity"]
DISCUSSION_REPORT_TYPES = ["count", "open"]

# Flight tracking options
AIRPORT_CODES = ["SEA", "SFO", "LAX", "JFK", "EWR", "ATL", "ORD", "DFW", "DEN", "LAS", "MCO", "BOS", "MIA", "PHX", "IAH"]
CITY_NAMES = ["Seattle", "San Francisco", "Los Angeles", "New York", "Newark", "Atlanta", "Chicago", "Dallas", "Denver", "Las Vegas", "Orlando", "Boston", "Miami", "Phoenix", "Houston"]
FLIGHT_STATUSES = ["en route", "scheduled", "departed", "arrived"]
TIME_WINDOWS = ["next 2 hours", "next 4 hours", "next 6 hours", "next 8 hours", "next 12 hours"]
ARRIVAL_PERIODS = ["today", "tomorrow", "yesterday"]


def _rand_date(start_days=1, end_days=10) -> str:
    d0 = dt.date.today() + dt.timedelta(days=random.randint(start_days, end_days))
    return d0.strftime("%Y-%m-%d")

def _get_instruction(steps: list[str]) -> dict:
    return get_instruction("FlightAware", steps).model_dump()

def fa_search_flight(_: dict) -> dict:
    departure = random.choice(DEPARTURE_AIRPORTS)
    destination = random.choice(DESTINATION_AIRPORTS)
    date = _rand_date()
    steps = [
        "Go to url 'https://www.flightaware.com/live/findflight/'.",
        f"Search for flights from {departure} to {destination}.",
        f"Set the departure date to {date}.",
        "Click 'Search' to view the results.",
        "Verify that the results page shows flights from {departure} to {destination} on {date}.",
    ]
    return {"task_type": "fa_search_flight", "from": departure, "to": destination, "date": date, "steps": steps}

def fa_explore_airports(_: dict) -> dict:
    airport_code = random.choice(DEPARTURE_AIRPORTS + DESTINATION_AIRPORTS)
    steps = [
        "Go to url 'https://www.flightaware.com/resources/airport/browse/'.",
        f"Search for information on airport {airport_code}.",
        "Verify the airport's details page opens.",
        "Ensure details like runway information, services, and activity statistics are available."
    ]
    return {"task_type": "fa_explore_airports", "airport": airport_code, "steps": steps}

def fa_live_flight_map(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.flightaware.com/live/'.",
        "Interact with the live map to view current flight paths.",
        "Zoom in to display a specific region.",
        "Verify that the map updates to show more flight details in that region."
    ]
    return {"task_type": "fa_live_flight_map", "steps": steps}

def fa_airport_delays(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.flightaware.com/live/airport/delays'.",
        "Review the list of current airport delays.",
        "Select an airport to view detailed delay information.",
        "Verify that the details are consistent with current known conditions (e.g., weather, traffic)."
    ]
    return {"task_type": "fa_airport_delays", "steps": steps}

def fa_airline_insights(_: dict) -> dict:
    airline = random.choice(AIRLINES)
    steps = [
        "Go to url 'https://www.flightaware.com/industry/airlines/'.",
        f"Search for airline information for '{airline}'.",
        "Verify details about on-time performance and operational insights are displayed."
    ]
    return {"task_type": "fa_airline_insights", "airline": airline, "steps": steps}

def fa_flight_cancellations(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.flightaware.com/live/cancelled/'.",
        "Look up cancellations for a given day.",
        "Select a cancellation entry for more information.",
        "Verify that reasons for cancellation and affected flights are noted."
    ]
    return {"task_type": "fa_flight_cancellations", "steps": steps}

def fa_adsb_coverage_check(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.flightaware.com/adsb/coverage/'.",
        "Review the ADS-B coverage map.",
        "Zoom into a specific area to view detailed receiver coverage.",
        "Verify that receivers are listed for the selected area."
    ]
    return {"task_type": "fa_adsb_coverage_check", "steps": steps}

def fa_product_services(_: dict) -> dict:
    product = random.choice(FLIGHTAWARE_PRODUCTS)
    info_type = random.choice(INFO_TYPES)
    
    steps = [
        "Go to url 'https://www.flightaware.com/'.",
        f"Navigate to the commercial products section to find information about {product}.",
        f"Research {info_type} for {product}.",
        f"Look for specific details about {info_type} and note any requirements or limitations.",
        f"Verify that the information is current and comprehensive for {product}.",
        f"Document the key findings about {info_type} for {product}."
    ]
    
    return {
        "task_type": "fa_product_services", 
        "product": product, 
        "info_type": info_type,
        "steps": steps
    }

def fa_discussions(_: dict) -> dict:
    filter_type = random.choice(DISCUSSION_FILTERS)
    time_period = random.choice(DISCUSSION_TIME_PERIODS)
    sort_by = random.choice(DISCUSSION_SORT_OPTIONS)
    report_type = random.choice(DISCUSSION_REPORT_TYPES)
    
    steps = [
        "Go to url 'https://www.flightaware.com/'.",
        "Navigate to the discussion board or forums section.",
        f"Select the '{filter_type}' filter to view discussions.",
        f"Set the time period to '{time_period}' to filter discussions.",
        f"Sort the discussions by '{sort_by}' to organize the results.",
        f"Review the discussion list and note the {report_type} of discussions available.",
        f"Click on a discussion to view its details and verify the sorting by '{sort_by}' is working correctly.",
        f"Report the total {report_type} of discussions found for the selected time period."
    ]
    
    return {
        "task_type": "fa_discussions",
        "filter_type": filter_type,
        "time_period": time_period,
        "sort_by": sort_by,
        "report_type": report_type,
        "steps": steps
    }

def fa_flight_tracking(_: dict) -> dict:
    # Ensure origin and destination are different
    origin_code = random.choice(AIRPORT_CODES)
    destination_code = random.choice([code for code in AIRPORT_CODES if code != origin_code])
    
    # Randomly choose between airport codes or city names
    use_codes = random.choice([True, False])
    if use_codes:
        origin = origin_code
        destination = destination_code
    else:
        origin_idx = AIRPORT_CODES.index(origin_code)
        dest_idx = AIRPORT_CODES.index(destination_code)
        origin = CITY_NAMES[origin_idx]
        destination = CITY_NAMES[dest_idx]
    
    flight_status = random.choice(FLIGHT_STATUSES)
    time_window = random.choice(TIME_WINDOWS)
    arrival_period = random.choice(ARRIVAL_PERIODS)
    
    steps = [
        "Go to url 'https://www.flightaware.com/'.",
        "Navigate to Flight Tracking -> Flight Finder.",
        f"Enter '{origin}' as the origin airport (either code or city name).",
        f"Enter '{destination}' as the destination airport (either code or city name).",
        f"Verify that the origin and destination are different airports.",
        f"Set the search to find flights that are '{flight_status}'.",
        f"Set the time window to '{time_window}' for scheduled departures.",
        f"Set the arrival period to '{arrival_period}' for flight arrivals.",
        f"Click 'Search' to find flights matching the criteria.",
        f"Select a flight that is '{flight_status}' from the search results.",
        f"Verify the flight details show the correct origin '{origin}' and destination '{destination}'.",
        f"Confirm the flight status matches the search criteria '{flight_status}'."
    ]
    
    return {
        "task_type": "fa_flight_tracking",
        "origin": origin,
        "destination": destination,
        "flight_status": flight_status,
        "time_window": time_window,
        "arrival_period": arrival_period,
        "steps": steps
    }

_TASK_GENERATORS: Dict[FLIGHTAWARE_TASK_TYPES, Callable[[dict], dict]] = {
    "fa_search_flight": fa_search_flight,
    "fa_explore_airports": fa_explore_airports,
    "fa_live_flight_map": fa_live_flight_map,
    "fa_airport_delays": fa_airport_delays,
    "fa_airline_insights": fa_airline_insights,
    "fa_flight_cancellations": fa_flight_cancellations,
    "fa_adsb_coverage_check": fa_adsb_coverage_check,
    "fa_product_services": fa_product_services,
    "fa_discussions": fa_discussions,
    "fa_flight_tracking": fa_flight_tracking,
}

def generate_flightaware_task(task_type: FLIGHTAWARE_TASK_TYPES, payload: dict) -> dict:
    task = _TASK_GENERATORS[task_type](payload or {})
    task["instruction"] = _get_instruction(task["steps"])
    return task

def main(filepath: str, payloads_json: str = "", num_workers: int = 12, timeout: int = 60, seed: int = 42, indent: int = 2):
    payloads = []
    if payloads_json:
        with open(payloads_json) as f:
            payloads = json.load(f)
    if not isinstance(payloads, list): payloads = []
    random.seed(seed)
    futures, out = [], []
    items = list(FLIGHTAWARE_SAMPLING_CONFIG.items())
    
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_flightaware_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try: out.append(fut.result(timeout=timeout))
            except Exception: pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)