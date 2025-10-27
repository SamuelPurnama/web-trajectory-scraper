DISTANCE_TEMPLATES = [
    "How far is the nearest {query} from {origin}?",
    "Where is the closest place for {query} near {origin}?",
    "Find the closest {query} from {origin} and tell me how far it is."
]

QA_QUESTION_TEMPLATES = {
    "formatted_address": "What is the address of {name}?",
    "formatted_phone_number": "What is the phone number of {name}?",
    "opening_hours": "What are the opening hours of {name}?",
    "rating": "What is the average rating for {name}?",
    "user_ratings_total": "How many people have reviewed {name}?",
    "wheelchair_accessible_entrance": "Is {name} wheelchair accessible?",
}

QA_FIELDS = list(QA_QUESTION_TEMPLATES.keys())