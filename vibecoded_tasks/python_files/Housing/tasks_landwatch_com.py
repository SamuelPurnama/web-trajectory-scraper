import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

LANDWATCH_TASK_TYPES = Literal[
    "lw_search_by_state",
    "lw_search_by_county",
    "lw_search_by_land_type",
    "lw_filter_price_range",
    "lw_filter_acreage_range",
    "lw_filter_property_features",
    "lw_sort_results",
    "lw_view_property_details",
    "lw_save_property_to_favorites",
    "lw_request_info_form",
    "lw_browse_land_by_map",
    "lw_search_by_keyword",
    "lw_filter_recently_added",
    "lw_browse_land_by_agent",
]

LANDWATCH_SAMPLING_CONFIG: Dict[LANDWATCH_TASK_TYPES, int] = {
    "lw_search_by_state": 10,
    "lw_search_by_county": 10,
    "lw_search_by_land_type": 10,
    "lw_filter_price_range": 10,
    "lw_filter_acreage_range": 10,
    "lw_filter_property_features": 10,
    "lw_sort_results": 10,
    "lw_view_property_details": 10,
    "lw_save_property_to_favorites": 10,
    "lw_request_info_form": 10,
    "lw_browse_land_by_map": 10,
    "lw_search_by_keyword": 10,
    "lw_filter_recently_added": 10,
    "lw_browse_land_by_agent": 10,
}

STATES = [
    "Texas", "California", "Florida", "Georgia", "North Carolina", "Tennessee", "Missouri", "Oklahoma", "Colorado", "Arizona",
    "Arkansas", "Alabama", "Michigan", "Kentucky", "South Carolina", "Mississippi", "Montana", "New Mexico", "Virginia", "Oregon",
    "Idaho", "Minnesota", "Wisconsin", "Iowa", "Kansas", "Nebraska", "South Dakota", "North Dakota", "Wyoming", "Louisiana"
]

COUNTIES = [
    "Los Angeles County, CA", "Harris County, TX", "Maricopa County, AZ", "Cook County, IL", "San Diego County, CA",
    "Orange County, CA", "Broward County, FL", "Miami-Dade County, FL", "Dallas County, TX", "Tarrant County, TX",
    "Riverside County, CA", "Clark County, NV", "King County, WA", "Bexar County, TX", "Wayne County, MI",
    "Santa Clara County, CA", "Palm Beach County, FL", "Alameda County, CA", "Hillsborough County, FL", "Franklin County, OH",
    "Travis County, TX", "Pima County, AZ", "Mecklenburg County, NC", "Fulton County, GA", "Suffolk County, NY"
]

LAND_TYPES = [
    "Farms", "Ranches", "Hunting Land", "Timberland", "Recreational Property", "Residential Property", "Commercial Property",
    "Undeveloped Land", "Horse Property", "Waterfront", "Lakefront", "Riverfront", "Mountain Land", "Pasture", "Vineyard",
    "Orchard", "Golf Property", "Cabin", "Resort", "Fishing Property", "Cattle Ranch", "Equestrian Property", "Organic Farm",
    "Off-Grid Land", "Desert Land"
]

PRICE_RANGES = [
    "$5,000-$10,000", "$10,000-$25,000", "$25,000-$50,000", "$50,000-$75,000", "$75,000-$100,000", "$100,000-$150,000",
    "$150,000-$200,000", "$200,000-$250,000", "$250,000-$300,000", "$300,000-$400,000", "$400,000-$500,000", "$500,000-$600,000",
    "$600,000-$750,000", "$750,000-$1,000,000", "$1,000,000-$1,500,000", "$1,500,000-$2,000,000", "$2,000,000-$3,000,000",
    "$3,000,000-$5,000,000", "$5,000,000-$10,000,000", "$10,000,000+"
]

ACREAGE_RANGES = [
    "0.25-0.5 Acres", "0.5-1 Acres", "1-2 Acres", "2-5 Acres", "5-10 Acres", "10-20 Acres", "20-40 Acres", "40-80 Acres",
    "80-160 Acres", "160-320 Acres", "320-640 Acres", "640-1,280 Acres", "1,280-2,560 Acres", "2,560-5,000 Acres",
    "5,000-10,000 Acres", "10,000+ Acres", "Under 1 Acre", "1-5 Acres", "5-20 Acres", "20+ Acres"
]

PROPERTY_FEATURES = [
    "Electricity", "Water", "Septic", "Paved Road", "Well", "Fenced", "Barn", "Creek", "Pond", "Mountain View",
    "Gated Entrance", "Mobile Home Allowed", "No Restrictions", "Owner Financing", "Mineral Rights", "HOA", "Crops", "Pasture",
    "Timber", "Irrigation", "RV Allowed", "Solar", "Dock", "Boat Ramp", "Public Land Access"
]

SORT_OPTIONS = [
    "Newest Listings", "Lowest Price", "Highest Price", "Smallest Acreage", "Largest Acreage", "Recently Reduced",
    "Most Viewed", "Best Match", "Oldest Listings", "Closest to Me", "Most Photos", "Least Photos", "Most Popular",
    "Featured", "Auction Ending Soon", "Just Sold", "Recently Added", "Alphabetical A-Z", "Alphabetical Z-A", "Random"
]

KEYWORDS = [
    "hunting", "fishing", "cabin", "timber", "investment", "off-grid", "mountain", "lake", "river", "farm", "ranch",
    "recreational", "vacant", "waterfront", "pasture", "orchard", "vineyard", "equestrian", "resort", "golf", "organic",
    "solar", "desert", "retreat", "subdivision"
]

AGENTS = [
    "Whitetail Properties", "Mossy Oak Properties", "United Country Real Estate", "Land Century", "LandLeader",
    "National Land Realty", "Hayden Outdoors", "Sotheby's International Realty", "RE/MAX", "Coldwell Banker",
    "Keller Williams", "Century 21", "Land And Farm", "LandHub", "LandFlip", "Ranch Marketers", "Hall and Hall",
    "Farm & Ranch Realty", "Premier Land Company", "LandGuys", "Fay Ranches", "Texas Ranch Sales", "California Outdoor Properties",
    "Peoples Company", "LandMart.com"
]

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss any popups or banners (e.g., cookie consent, newsletter signup, etc).",
        "Do not submit any payment or personal information.",
    ]

def _instr(steps: list[str]) -> dict:
    return get_instruction("LandWatch", steps).model_dump()

def lw_search_by_state(_: dict) -> dict:
    state = random.choice(STATES)
    steps = [
        "Go to url 'https://www.landwatch.com/'.",
        *_ui_hygiene(),
        f"Locate and click on the 'Land for Sale' menu.",
        f"Select '{state}' from the state list.",
        f"Verify that the search results page shows listings for land in '{state}'.",
        "Assert that at least one property card is visible and the page heading includes the state name.",
    ]
    return {"task_type": "lw_search_by_state", "state": state, "steps": steps}

def lw_search_by_county(_: dict) -> dict:
    county = random.choice(COUNTIES)
    steps = [
        "Go to url 'https://www.landwatch.com/'.",
        *_ui_hygiene(),
        "Click on the 'Land for Sale' menu.",
        "Select 'Browse by County'.",
        f"Choose '{county}' from the list.",
        f"Verify search results are filtered to '{county}'.",
        "Assert that the results heading or breadcrumb includes the county name.",
    ]
    return {"task_type": "lw_search_by_county", "county": county, "steps": steps}

def lw_search_by_land_type(_: dict) -> dict:
    land_type = random.choice(LAND_TYPES)
    steps = [
        "Go to url 'https://www.landwatch.com/'.",
        *_ui_hygiene(),
        "Click on the 'Land Types' or 'Land for Sale' menu.",
        f"Select '{land_type}' from the available land types.",
        f"Verify that the results page lists properties of type '{land_type}'.",
        "Assert that the page heading or filter chips include the selected land type.",
    ]
    return {"task_type": "lw_search_by_land_type", "land_type": land_type, "steps": steps}

def lw_filter_price_range(_: dict) -> dict:
    price_range = random.choice(PRICE_RANGES)
    steps = [
        "Go to url 'https://www.landwatch.com/'.",
        *_ui_hygiene(),
        "Enter any state or county in the search bar and submit.",
        "Wait for the results page to load.",
        "Locate the price filter dropdown or slider.",
        f"Set the price filter to '{price_range}'.",
        "Apply the filter.",
        f"Verify that all visible listings have prices within '{price_range}'.",
        "Assert that at least one property card is shown after filtering.",
    ]
    return {"task_type": "lw_filter_price_range", "price_range": price_range, "steps": steps}

def lw_filter_acreage_range(_: dict) -> dict:
    acreage = random.choice(ACREAGE_RANGES)
    steps = [
        "Go to url 'https://www.landwatch.com/'.",
        *_ui_hygiene(),
        "Search for land in any state.",
        "Wait for the results page to load.",
        "Locate the acreage filter.",
        f"Set the acreage filter to '{acreage}'.",
        "Apply the filter.",
        f"Verify that all visible listings have acreage within '{acreage}'.",
        "Assert that at least one property card is shown after filtering.",
    ]
    return {"task_type": "lw_filter_acreage_range", "acreage_range": acreage, "steps": steps}

def lw_filter_property_features(_: dict) -> dict:
    features = random.sample(PROPERTY_FEATURES, 2)
    steps = [
        "Go to url 'https://www.landwatch.com/'.",
        *_ui_hygiene(),
        "Search for land in any state.",
        "Wait for the results page to load.",
        "Open the 'Property Features' filter panel.",
        f"Select the following features: {features[0]} and {features[1]}.",
        "Apply the filter.",
        f"Verify that all visible listings mention at least one of the selected features.",
        "Assert that at least one property card is shown after filtering.",
    ]
    return {"task_type": "lw_filter_property_features", "features": features, "steps": steps}

def lw_sort_results(_: dict) -> dict:
    sort_option = random.choice(SORT_OPTIONS)
    steps = [
        "Go to url 'https://www.landwatch.com/'.",
        *_ui_hygiene(),
        "Search for land in any state.",
        "Wait for the results page to load.",
        "Locate the sort dropdown or control.",
        f"Select '{sort_option}' as the sort option.",
        "Verify that the results are re-ordered according to the selected sort.",
        "Assert that the first property card reflects the chosen sort order.",
    ]
    return {"task_type": "lw_sort_results", "sort_option": sort_option, "steps": steps}

def lw_view_property_details(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.landwatch.com/'.",
        *_ui_hygiene(),
        "Search for land in any state.",
        "Wait for the results page to load.",
        "Click on the first property card to open its details page.",
        "Verify that the property details page loads and displays property description, price, and contact info.",
        "Assert that the property title and price are visible on the page.",
    ]
    return {"task_type": "lw_view_property_details", "steps": steps}

def lw_save_property_to_favorites(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.landwatch.com/'.",
        *_ui_hygiene(),
        "Search for land in any state.",
        "Wait for the results page to load.",
        "Locate the 'Save' or 'Favorite' button on the first property card.",
        "Click the 'Save' or 'Favorite' button.",
        "If prompted to sign in or create an account, cancel or close the prompt.",
        "Assert that the property is visually marked as saved (e.g., icon changes color, 'Saved' text appears).",
    ]
    return {"task_type": "lw_save_property_to_favorites", "steps": steps}

def lw_request_info_form(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.landwatch.com/'.",
        *_ui_hygiene(),
        "Search for land in any state.",
        "Wait for the results page to load.",
        "Click on the first property card to open its details page.",
        "Locate the 'Request Info' or 'Contact Agent' form.",
        "Attempt to submit the form with all fields empty.",
        "Verify that validation errors are shown for required fields (e.g., name, email, phone).",
        "Assert that the form is not submitted and error messages are visible.",
    ]
    return {"task_type": "lw_request_info_form", "steps": steps}

def lw_browse_land_by_map(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.landwatch.com/'.",
        *_ui_hygiene(),
        "Locate and click the 'Map' view or 'Browse by Map' option.",
        "Wait for the interactive map to load.",
        "Pan or zoom to a specific region (e.g., Texas).",
        "Click on a cluster or marker to view property listings in that area.",
        "Assert that the listings update to reflect the selected map region.",
    ]
    return {"task_type": "lw_browse_land_by_map", "steps": steps}

def lw_search_by_keyword(_: dict) -> dict:
    keyword = random.choice(KEYWORDS)
    steps = [
        "Go to url 'https://www.landwatch.com/'.",
        *_ui_hygiene(),
        f"Enter '{keyword}' in the main search bar and submit.",
        "Wait for the results page to load.",
        f"Verify that at least some listings mention '{keyword}' in their title or description.",
        "Assert that the search results heading or filter chips include the keyword.",
    ]
    return {"task_type": "lw_search_by_keyword", "keyword": keyword, "steps": steps}

def lw_filter_recently_added(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.landwatch.com/'.",
        *_ui_hygiene(),
        "Search for land in any state.",
        "Wait for the results page to load.",
        "Locate the filter or sort option for 'Recently Added' or 'Newest Listings'.",
        "Apply the filter or sort.",
        "Verify that the first few listings have recent 'Added' or 'Listed' dates (within the past 30 days).",
        "Assert that the results are ordered by recency.",
    ]
    return {"task_type": "lw_filter_recently_added", "steps": steps}

def lw_browse_land_by_agent(_: dict) -> dict:
    agent = random.choice(AGENTS)
    steps = [
        "Go to url 'https://www.landwatch.com/'.",
        *_ui_hygiene(),
        "Locate and click on the 'Find an Agent' or 'Browse by Agent' link.",
        f"Search for or select '{agent}' from the agent list.",
        f"Verify that the agent's profile or listings page loads.",
        "Assert that at least one property card is visible and the agent's name appears on the page.",
    ]
    return {"task_type": "lw_browse_land_by_agent", "agent": agent, "steps": steps}

_TASK_GENERATORS: Dict[LANDWATCH_TASK_TYPES, Callable[[dict], dict]] = {
    "lw_search_by_state": lw_search_by_state,
    "lw_search_by_county": lw_search_by_county,
    "lw_search_by_land_type": lw_search_by_land_type,
    "lw_filter_price_range": lw_filter_price_range,
    "lw_filter_acreage_range": lw_filter_acreage_range,
    "lw_filter_property_features": lw_filter_property_features,
    "lw_sort_results": lw_sort_results,
    "lw_view_property_details": lw_view_property_details,
    "lw_save_property_to_favorites": lw_save_property_to_favorites,
    "lw_request_info_form": lw_request_info_form,
    "lw_browse_land_by_map": lw_browse_land_by_map,
    "lw_search_by_keyword": lw_search_by_keyword,
    "lw_filter_recently_added": lw_filter_recently_added,
    "lw_browse_land_by_agent": lw_browse_land_by_agent,
}

def generate_landwatch_task(task_type: LANDWATCH_TASK_TYPES, payload: dict) -> dict:
    task = _TASK_GENERATORS[task_type](payload or {})
    task["instruction"] = _instr(task["steps"])
    return task

def main(filepath: str, payloads_json: str = "", num_workers: int = 12, timeout: int = 60, seed: int = 42, indent: int = 2):
    payloads = []
    if payloads_json:
        with open(payloads_json) as f:
            payloads = json.load(f)
    if not isinstance(payloads, list): payloads = []
    random.seed(seed)
    futures, out = [], []
    items = list(LANDWATCH_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_landwatch_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try: out.append(fut.result(timeout=timeout))
            except Exception: pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)