import random
from typing import Literal

USER_AGENTS = dict(
    linux=[
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.140 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.5938.132 Safari/537.36",
    ],
    mac=[
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
    ],
)
VIEWPORTS = [
    dict(width=1920, height=947),
    dict(width=1366, height=657),
    dict(width=1440, height=812),
    dict(width=1536, height=754),
    dict(width=1280, height=657),
]
GEOLOCATIONS = dict(
    seattle=dict(longitude=-122.3321, latitude=47.6062),
    los_angeles=dict(longitude=-118.2437, latitude=34.0522),
    new_york=dict(longitude=-74.0060, latitude=40.7128),
)

PROXIES = dict(
    seattle=dict(
        server="",
        username="",
        password="",
    ),
    los_angeles=dict(
        server="",
        username="",
        password="",
    ),
    new_york=dict(
        server="",
        username="",
        password="",
    ),
)

TIMEZONES = dict(
    seattle="America/Los_Angeles",
    los_angeles="America/Los_Angeles",
    new_york="America/New_York",
)


def sample_browser_context(os_type: Literal["linux", "mac"] = "linux"):
    loc = random.choice(list(GEOLOCATIONS.keys()))
    return dict(
        locale="en-US",
        timezone_id=TIMEZONES[loc],
        proxy=PROXIES[loc],
        geolocation=GEOLOCATIONS[loc],
        user_agent=random.choice(USER_AGENTS[os_type]),
        viewport=random.choice(VIEWPORTS),
        permissions=["geolocation"],
        color_scheme="light",
    )


# import ipdb

# ipdb.set_trace()
