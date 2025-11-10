import os
import random
from pathlib import Path
from typing import Literal, Optional

# Load environment variables from .env file BEFORE importing ell
# Try multiple possible .env file locations
possible_env_files = [
    Path(__file__).parent.parent / ".env",  # Root .env
    Path(__file__).parent.parent / "vibecoded_tasks" / ".env",  # vibecoded_tasks/.env
]

env_file = None
for env_path in possible_env_files:
    if env_path.exists():
        env_file = env_path
        break

if env_file:
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

# Verify API key is available
if not os.getenv("OPENAI_API_KEY"):
    # Also check if it's available from system environment (might be set externally)
    if not os.environ.get("OPENAI_API_KEY"):
        print("WARNING: OPENAI_API_KEY not found. Make sure .env file contains OPENAI_API_KEY=your_key")

import ell
# Explicitly configure ell with OpenAI client if API key is available
if os.getenv("OPENAI_API_KEY"):
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        # ell should automatically use OPENAI_API_KEY from environment
        # The warning is just informational - it checks at definition time
    except Exception:
        pass  # ell will use default behavior
from pydantic import BaseModel, Field


class Instructions(BaseModel):
    high_level: str = Field(
        description="Instruction to a super smart web browsing assistant with minimal details"
    )
    mid_level: str = Field(
        description="Instruction to a slightly less smart web browsing assistant with a few details"
    )
    low_level: str = Field(
        description="Instruction to an average web browsing assistant with full details but avoiding itemized list of steps."
    )


def get_instruction(website: str, steps: list[str]) -> Instructions:
    @ell.complex(model="gpt-4o", response_format=Instructions)
    def lmp(website: str, steps: list[str]):
        return f"""You are converting detailed task steps into comprehensive, highly specific instructions for web browsing assistants.

YOUR JOB:
1. PRESERVE all specific details from the steps (dates, locations, values, filters, etc.)
2. ENHANCE the instructions by:
   - Making implicit information explicit (e.g., if it says "filter by price", specify the exact price range mentioned)
   - Adding context where helpful (e.g., "using the search box", "from the dropdown menu")
   - Clarifying actions (e.g., "click on the filter button and select" instead of just "filter")
   - Including all specific parameters mentioned anywhere in the steps
   - Making it clear what the user should see/verify after each action

CRITICAL REQUIREMENTS:
- Include ALL specific details: dates (YYYY-MM-DD), times, locations, cities, airport codes, exact filter values, categories, search terms, names, prices, ratings, quantities, features, amenities
- Make every instruction actionable and specific - never generic
- If steps mention specific values, dates, or filters, they MUST appear in the instructions
- Enhance clarity without adding information not in the steps
- Tasks should involve MORE than just navigating to a page/feature - they MUST PERFORM VARIOUS ACTIONS/TASKS WITHIN THAT PAGE/FEATURE. Instructions should clearly reflect the actual actions performed (searching, filtering, sorting, selecting, viewing details, etc.), not just page navigation.

Examples:

BAD (too generic, loses details):
"Review available first-class flights on Booking.com"

GOOD (preserves AND enhances all details):
"Navigate to Booking.com flights page, search for first-class flights from Seattle-Tacoma International Airport (SEA) to Paris Charles de Gaulle Airport (CDG) with departure date 2024-12-15 and return date 2024-12-22. After the search results appear, apply a price filter to show only flights priced between $3,000 and $5,000, then sort the filtered results by flight duration to find the shortest options."

BAD (missing specifics):
"Filter hotels by amenities"

GOOD (preserves AND enhances with specifics):
"Go to Booking.com and search for hotels in New York City, New York. Set check-in date to 2024-11-20 and check-out date to 2024-11-25 (5 nights). Once results appear, open the amenities filter section and enable both 'Swimming Pool' and 'Free WiFi' filters. Verify that the displayed hotels now only show properties with both amenities. Then sort the filtered results by guest rating to see the highest-rated options first."

Below are the detailed steps for a task on {website}. Generate three levels of instructions that:
1. Include ALL specific details from the steps
2. Enhance with clarity and context
3. Make actions explicit and verifiable

# Task Steps

{chr(10).join(steps)}

Output Levels:
- High level: Concise and straightforward - just the core action with key specifics. One sentence. Example: "Navigate to the Amazon Jobs website and search for jobs in Warehouse" or "Search for first-class flights from Seattle to Paris departing on 2024-12-15 on Booking.com"
- Mid level: Include most specifics (dates, locations, filters, search terms, verification steps) with moderate detail and context. You do not need to elaborate on the validation steps.
- Low level: Include EVERY specific detail (dates, times, exact locations/airports, filter values, UI elements, verification criteria) as a flowing, detailed instruction with full context"""

    return lmp(website, steps).parsed  # type: ignore
