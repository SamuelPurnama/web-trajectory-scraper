import json
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

import fire
from tqdm import tqdm

from tasks.persona_utils import read_personas
from tasks.booking.sampling_utils import BOOKING_TASK_TYPES, generate_booking_task

# BOOKING_SAMPLING_CONFIG = {
#     "booking_search_stays": 500,
#     "booking_change_language": 100,
#     "booking_change_currency": 100,
#     "booking_list_trending_destinations": 200,
#     "booking_search_flights": 300,
#     "booking_search_car_rentals": 200,
#     "booking_search_attractions": 200,
#     "booking_search_cruise": 50,
# }

BOOKING_SAMPLING_CONFIG = {
    "booking_search_stays": 1,
    "booking_change_language": 1,
    "booking_change_currency": 1,
    "booking_list_trending_destinations": 1,
    "booking_search_flights": 1,
    "booking_search_car_rentals": 1,
    "booking_search_attractions": 1,
    "booking_search_cruise": 1,
}


def main(
    filepath: str,
    persona_path: str,
    num_workers: int = 10,
    timeout: int = 60,
    seed: int = 42,
    indent: int = 2,
):
    personas = read_personas(persona_path)
    random.seed(seed)
    random.shuffle(personas)

    futures = []
    future2type = {}
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        for i, (task_type, count) in enumerate(BOOKING_SAMPLING_CONFIG.items()):
            assert task_type in BOOKING_TASK_TYPES, f"{task_type} not valid"
            for j in range(count):
                persona = personas[(i + j) % len(personas)]
                f = executor.submit(generate_booking_task, persona, task_type)
                futures.append(f)
                future2type[f] = task_type

        all_tasks = []
        for f in tqdm(as_completed(futures), total=len(futures)):
            try:
                all_tasks.append(f.result(timeout=timeout))
            except Exception as e:
                tt = future2type[f]
                print(f"Error in {tt}: {e}")
            finally:
                if not f.done():
                    f.cancel()

    with open(filepath, "w") as out:
        json.dump(all_tasks, out, indent=indent)


if __name__ == "__main__":
    fire.Fire(main)
