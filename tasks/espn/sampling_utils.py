import random
from typing import Literal, Optional

import ell
from pydantic import BaseModel, Field

from tasks.instruction_utils import get_instruction
from tasks.persona_utils import read_personas

import json
import os

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(script_dir, "teams.json")) as f:
    teams_data = json.load(f)

def create_team_news_nav_task():
    league = random.choice(list(teams_data.keys()))
    team = random.choice(teams_data[league])
    article_num = random.choice(["first", "second", "third"])

    steps = [
        "If not there yet, navigate to https://www.espn.com/.",
        f"In the top navigation bar, hover over '{league}'.",
        f"From the teams list that appears below, select '{team}' to go to their page.",
        f"Once on the team page, display the title of the {article_num} post from the top."
    ]

    return [
        dict(
            task_type="team_news_nav",
            league=league,
            team=team,
            article_choice=article_num,
            steps=steps
        )
    ]

def create_team_search_task():
    league = random.choice(list(teams_data.keys()))
    team = random.choice(teams_data[league])
    action = random.choice(["clip", "article", "on_demand"])
    steps = [
        "Go to https://www.espn.com/.",
        "Click the search icon at the top right.",
        f"Search for '{team}'."
    ]

    if action == "clip":
        n = random.randint(1, 4)
        ordinal = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th"}[n]
        steps.append(f"Click on the {ordinal} video clip from the results.")
        steps.append("Report what the clip is about based on the title.")
    elif action == "article":
        n = random.randint(1, 4)
        ordinal = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th"}[n]
        steps.append(f"Click on the {ordinal} article from the results.")
        steps.append("Summarize the article headline and date.")
    else:
        steps.append('Click on a random available "On Demand" video.')
        steps.append("Describe the video title to the user.")

    return [
        dict(
            task_type="team_search",
            league=league,
            team=team,
            action=action,
            steps=steps
        )
    ]


section_reports = {
  "Home": [
    "Give a summary of the landing page.",
    "Highlight the top headline featured on the page.",
    "List any featured video titles or spotlight stories."
  ],
  "Stats": [
    "Return the top player stats.",
    "List the top 3 scorers.",
    "Provide the team’s season‑average points per game (or goals/runs)."
  ],
  "Schedule": [
    "Show upcoming schedule details.",
    "Report the date, opponent, and location of the next game.",
    "List the next three home games on the calendar."
  ],
  "Roster": [
    "Summarize the current roster.",
    "List the projected starting lineup and key substitutes.",
    "Identify the team captain(s) or most senior players."
  ],
  "Depth": [
    "Summarize depth chart structure.",
    "Highlight any recent changes to the starting lineup.",
    "Note notable backups who may get increased playing time."
  ],
  "Depth Chart": [
    "Summarize depth chart structure.",
    "Identify first‑, second‑, and third‑string players at key positions.",
    "Point out positional battles or newly promoted players."
  ],
  "Splits": [
    "Describe seasonal performance splits.",
    "Compare the team’s home vs. away record.",
    "Show monthly win–loss (or points) splits for the current season."
  ],
  "Injuries": [
    "Highlight recent injury updates.",
    "List players on injured reserve or day‑to‑day status.",
    "Report estimated return timelines for major injuries."
  ],
  "Transactions": [
    "Summarize recent team transactions.",
    "List the most recent signings or contract extensions.",
    "Note any trades, waivers, or releases in the past month."
  ],
  "Fantasy Men's Basketball": [
    "Report fantasy projections.",
    "Identify players trending up or down in fantasy value.",
    "Highlight injury or lineup changes affecting fantasy outlook."
  ],
  "Fantasy Women's Basketball: Sign Up": [
    "Report fantasy projections.",
    "Suggest top waiver‑wire pickups for the current week.",
    "Highlight players with high fantasy point averages."
  ],
  "Fill Out Brackets!": [
    "Explain how the bracket is structured.",
    "Describe available bracket challenges or contests.",
    "Provide tips for choosing upset picks in the bracket."
  ],
  "Tickets": [
    "Give information about upcoming ticketed events.",
    "Show current price ranges for the next home game.",
    "Report on any special ticket promotions or discounts."
  ],
  "Fixtures": [
    "List upcoming fixtures.",
    "Provide venue and kickoff times for the next three matches.",
    "Highlight any fixture congestion or back‑to‑back games."
  ],
  "Results": [
    "Summarize most recent match result.",
    "Give the scores of the last three games played.",
    "Highlight notable performances from the latest result."
  ],
  "Squad": [
    "List the full team squad.",
    "Break down the squad by position groups.",
    "Give average age or years of experience for the squad."
  ],
  "Table": [
    "Report the team’s current standing or position in league.",
    "Show total points (or wins) and goal/point differential.",
    "Identify how far the team is from the playoff cut‑off or top spot."
  ]
}


league_sections = {
    "NFL": ["Home", "Stats", "Schedule", "Roster", "Injuries"],
    "NBA": ["Home", "Stats", "Schedule", "Roster", "Depth", "Injuries", "Transactions", "Fantasy Men's Basketball", "Tickets", "Fill Out Brackets!"],
    "NHL": ["Home", "Stats", "Schedule", "Roster", "Injuries", "Transactions", "Tickets", "Fill Out Brackets!"],
    "MLB": ["Home", "Stats", "Schedule", "Roster", "Depth Chart", "Splits", "Injuries", "Transactions", "Tickets"],
    "WNBA": ["Home", "Stats", "Schedule", "Roster", "Injuries", "Fantasy Women's Basketball: Sign Up", "Tickets"],
    "Soccer": ["Home", "Fixtures", "Results", "Squad", "Stats", "Table"]
}

def create_team_page_deep_nav_task(league):
    team = random.choice(teams_data[league])
    section = random.choice(league_sections[league])
    report = random.choice(section_reports.get(section, ["Report something from this section."]))

    steps = [
        "Go to https://www.espn.com/.",
        f"In the top navigation bar, hover over or click on '{league}'.",
        "Click 'Teams' in the dropdown.",
        f"Click on the team '{team}'.",
        f"Navigate to the '{section}' section of the team page.",
        report
    ]

    return [
        dict(
            task_type="team_page_deep_nav",
            league=league,
            team=team,
            section=section,
            steps=steps
        )
    ]

# League-specific wrappers

def create_nfl_team_page_deep_nav(): return create_team_page_deep_nav_task("NFL")
def create_nba_team_page_deep_nav(): return create_team_page_deep_nav_task("NBA")
def create_nhl_team_page_deep_nav(): return create_team_page_deep_nav_task("NHL")
def create_mlb_team_page_deep_nav(): return create_team_page_deep_nav_task("MLB")
def create_wnba_team_page_deep_nav(): return create_team_page_deep_nav_task("WNBA")
def create_soccer_team_page_deep_nav(): return create_team_page_deep_nav_task("Soccer")


with open(os.path.join(script_dir, "basic_nav.json")) as f:
    nav = json.load(f)

# Build a flat list of possible sections to visit
top_sections = ["NFL", "NBA", "NHL", "MLB", "WNBA", "Tennis", "Soccer"]
more_subsections = nav["More Sports"]
all_targets = top_sections + more_subsections  # eg. ["NFL", ..., "Boxing", ...]

report_variants = [
    "Capture the article title.",
    "Capture the article author (if shown).",
    "Capture the article publication date.",
    "Capture the article title, author (if shown), and publication date."
]

def create_top_headlines_task():
    target = random.choice(all_targets)
    ordinals = ["first", "second", "third", "fourth", "fifth", "sixth", "seventh"]
    ordinal = random.choice(ordinals)
    report_step = random.choice(report_variants) 

    # Determine navigation path in the ESPN top bar
    if target in top_sections:
        nav_path = target
    else:
        nav_path = f"More Sports → {target}"

    steps = [
        "Go to https://www.espn.com/.",
        f"In the top navigation bar, click on \"{nav_path}\".",
        "On the landing page, locate the \"Top Headlines\" module.",
        f"If the module exists, click on the {ordinal} headline in the list, counting from the top.",
        report_step,
        "Display that information to the user.",
        "If the \"Top Headlines\" module is not present, end the task and return \"No headlines available.\""
    ]

    return [
        dict(
            task_type="section_top_headlines",
            target_section=target,
            headline_index=ordinal,
            steps=steps
        )
    ]


# def get_espn_keyword_generator():
#     """
#     Generate a function that returns exactly one 1–3-word sports topic for ESPN search.
#     """
#     class SearchWord(BaseModel):
#         topic: str = Field(
#             description="A single sports keyword (1–3 words) appropriate for an ESPN search."
#         )

#     @ell.complex(model="gpt-4o", response_format=SearchWord)
#     def lmp(persona: str):
#         return [
#             ell.system(f"You are {persona}."),
#             ell.user(
#                 (
#                     "Generate exactly 1 sports search term (1–3 words, distinct) "
#                     "suitable for ESPN.  Ensure it’s broad enough to yield multiple results "
#                     "but not overly generic.  Examples: 'Premier League', 'March Madness', 'zone defense'."
#                 )
#             ),
#         ]

#     def get_espn_search_term(persona: str) -> str:
#         """Return exactly one 1–3-word sports topic for ESPN search."""
#         return lmp(persona).parsed.topic

#     return get_espn_search_term


# def create_keyword_search_task(persona: str):
#     get_search_term = get_espn_keyword_generator()
#     query_word = get_search_term(persona)

#     article_idx = random.randint(1, 4)
#     idx_ordinal = {1: "first", 2: "second", 3: "third", 4: "fourth"}[article_idx]

#     report_variants = [
#         "Capture the article title.",
#         "Capture the article author (if shown).",
#         "Capture the article publication date.",
#         "Capture the article title, author (if shown), and publication date."
#     ]
#     report_step = random.choice(report_variants)

#     steps = [
#         f"Use the keyword **{query_word}** supplied by the persona.",
#         "Go to https://www.espn.com/.",
#         "Click the search icon at the top right to open the search bar.",
#         f"Type **{query_word}** into the search bar and press Enter.",
#         (
#             f"Click on the {idx_ordinal} article in the list if available; "
#             "if that position does not exist, click the next available article "
#             "up to the fourth result."
#         ),
#         report_step,
#         "Display that information to the user.",
#         "If no article results are found, end the task and return \"No articles available.\""
#     ]

#     return [
#         dict(
#             task_type="keyword_article_search",
#             persona=persona,
#             keyword=query_word,
#             article_index=article_idx,
#             steps=steps
#         )
#     ]




def generate_espn_task(
    persona: str,
    task_type: Literal[
        "team_news_nav",
        "team_search",
        "team_page_deep_nav",
        "section_top_headlines",
        # "keyword_article_search",
        "create_nfl_team_page_deep_nav",
        "create_nba_team_page_deep_nav",
        "create_nhl_team_page_deep_nav",
        "create_mlb_team_page_deep_nav",
        "create_wnba_team_page_deep_nav",
        "create_soccer_team_page_deep_nav"
    ],
    num_words: int = 1,
    tasks_per_word: int = 1,
    topics: Optional[list[str]] = None,
):
    if task_type == "team_page_deep_nav":
        if topics is None:
            num_leagues = min(num_words, len(teams_data))
            topics = random.sample(list(teams_data.keys()), num_leagues)
    elif task_type == "keyword_article_search":
        if topics is None:
            topics = [None]
    else:
        topics = [None]

    tasks = []
    for topic in topics:
        if task_type == "team_news_nav":
            tasks.extend(create_team_news_nav_task())
        elif task_type == "team_search":
            tasks.extend(create_team_search_task())
        elif task_type == "team_page_deep_nav":
            tasks.extend(create_team_page_deep_nav_task(topic))
        elif task_type == "section_top_headlines":
            tasks.extend(create_top_headlines_task())
        elif task_type == "keyword_article_search":
            tasks.extend(create_keyword_search_task(persona))
        elif task_type == "create_nfl_team_page_deep_nav":
            tasks.extend(create_nfl_team_page_deep_nav())
        elif task_type == "create_nba_team_page_deep_nav":
            tasks.extend(create_nba_team_page_deep_nav())
        elif task_type == "create_nhl_team_page_deep_nav":
            tasks.extend(create_nhl_team_page_deep_nav())
        elif task_type == "create_mlb_team_page_deep_nav":
            tasks.extend(create_mlb_team_page_deep_nav())
        elif task_type == "create_wnba_team_page_deep_nav":
            tasks.extend(create_wnba_team_page_deep_nav())
        elif task_type == "create_soccer_team_page_deep_nav":
            tasks.extend(create_soccer_team_page_deep_nav())
        else:
            raise ValueError(f"Unsupported task_type: {task_type}")

    for task in tasks:
        task["instruction"] = get_instruction("dictionary", task["steps"]).model_dump()

    return {"tasks": tasks, "topics": topics}


ESPN_TASK_TYPES = [
    "team_news_nav",
    "team_search",
    # "team_page_deep_nav",
    "section_top_headlines",
    # "keyword_article_search",
    "create_nfl_team_page_deep_nav",
    "create_nba_team_page_deep_nav",
    "create_nhl_team_page_deep_nav",
    "create_mlb_team_page_deep_nav",
    "create_wnba_team_page_deep_nav",
    "create_soccer_team_page_deep_nav",
]

