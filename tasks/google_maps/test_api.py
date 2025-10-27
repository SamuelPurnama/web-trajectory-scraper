import os
from pprint import pprint

from tasks.google_maps.sampling_utils import (
    get_google_maps_place_in_location_generator,
    create_google_maps_qa_task,
)

def test_google_maps_qa_task_pipeline():
    persona = "a tech-savvy remote worker who likes coffee, coworking spaces, and accessible public places"
    os.environ["GOOGLE_MAPS_API_KEY"] = "YOUR_REAL_API_KEY_HERE"

    print("🔍 Generating place queries using LLM...")
    generator = get_google_maps_place_in_location_generator()
    place_queries = generator(persona)
    pprint(place_queries)

    print("\n📍 Creating QA tasks from real place data...")
    tasks = create_google_maps_qa_task(place_queries)
    for i, task in enumerate(tasks, 1):
        print(f"\n=== Task {i} ===")
        pprint(task)

if __name__ == "__main__":
    test_google_maps_qa_task_pipeline()

