import json
import os
import shutil
from glob import glob
import sys
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
import argparse

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import fire
from datetime import datetime
from logger import PlaywrightLogger

def should_trim(traj_dir: str) -> bool:
    """Checks if a trajectory should be trimmed based on its verdict.json."""
    verdict_path = os.path.join(traj_dir, "verdict.json")
    if not os.path.exists(verdict_path):
        return False  # Cannot determine, so don't trim
    
    try:
        with open(verdict_path, 'r') as f:
            verdict = json.load(f)
        # Trim if the task was not a success and got most of the way through
        return verdict.get("status") != "SUCCESS" and verdict.get("progress") == 0.67
    except (json.JSONDecodeError, IOError):
        return False # Error reading file, so don't trim

def convert_to_logger_format(trajectory: dict, metadata: dict) -> list:
    """Converts the trajectory data to the format expected by PlaywrightLogger."""
    interactions = []
    for step, details in trajectory.items():
        action_output = details.get("action", {}).get("action_output", {})
        
        # Flatten the action dictionary to match the logger's expected format
        action_for_html = {"action": action_output.get("action_name", "")}
        action_for_html.update(action_output.get("action", {}))

        interactions.append({
            "step": int(step),
            "screenshot": os.path.join("images", details.get("screenshot", "")),
            "axtree": details.get("axtree", ""),
            "global_axtree": "",
            "extra_element_properties": "",
            "action": action_for_html,
            "error": details.get("error"),
            "timestamp": datetime.fromtimestamp(details.get("action_timestamp")).isoformat() if details.get("action_timestamp") else "",
            "url": details.get("other_obs", {}).get("url"),
        })
    return interactions


def trim_trajectory_in_place(traj_dir: str):
    """Trims a single trajectory in-place based on the second 'click' action."""
    traj_json_path = os.path.join(traj_dir, "trajectory.json")
    if not os.path.exists(traj_json_path):
        return

    with open(traj_json_path, 'r') as f:
        raw_data = json.load(f)

    if isinstance(raw_data, dict):
        interactions = sorted(raw_data.items(), key=lambda item: int(item[0]))
    elif isinstance(raw_data, list):
        interactions = list(enumerate(raw_data, 1))
        interactions = [(str(k), v) for k, v in interactions]
    else:
        return

    click_indices = [i for i, (_, interaction) in enumerate(interactions) if interaction.get("action", {}).get("action_output", {}).get("action_name") == "click"]
    
    if len(click_indices) < 2:
        return

    second_click_index = click_indices[1]
    last_correct_step_index = second_click_index
    if second_click_index + 1 < len(interactions):
        next_action = interactions[second_click_index + 1][1].get("action", {}).get("action_output", {}).get("action_name")
        if next_action == "tab_focus":
            last_correct_step_index = second_click_index + 1

    new_interactions_list = interactions[:last_correct_step_index + 1]
    
    first_trimmed_interaction = interactions[last_correct_step_index + 1][1]
    last_step_num = str(len(new_interactions_list) + 1)
    new_interactions_list.append(
        (last_step_num, {
            "screenshot": first_trimmed_interaction.get("screenshot"),
            "axtree": first_trimmed_interaction.get("axtree"),
            "user_message": "",
            "other_obs": first_trimmed_interaction.get("other_obs"),
            "action": {
                "action_str": "exit()",
                "action_description": "exit",
                "action_output": {
                    "thought": "trajectory trimmed down from failed steps",
                    "action": {},
                    "action_name": "exit"
                }
            },
            "error": None,
            "action_timestamp": datetime.now().timestamp()
        })
    )
    
    new_interactions = dict(new_interactions_list)
    
    # Remove files that are no longer part of the trajectory
    valid_step_nums = {int(k) for k in new_interactions.keys()}
    file_map = {
        "images": ("screenshot", "png"),
        "axtree": ("axtree", "txt"),
        "extra_element_properties": ("extra_element_properties", "json"),
        "global_axtree": ("global_axtree", "txt"),
        "hover_expansion": ("hover_expansion", "json"),
        "html": ("html", "html"),
        "urls": ("url", "txt"),
    }

    for dir_name, (base_name, ext) in file_map.items():
        src_dir = os.path.join(traj_dir, dir_name)
        if not os.path.exists(src_dir):
            continue
        
        for file_path in glob(os.path.join(src_dir, f"{base_name}_*.{ext}")):
            try:
                step_num_in_filename = int(os.path.basename(file_path).split('_')[-1].split('.')[0])
                if step_num_in_filename not in valid_step_nums:
                    os.remove(file_path)
            except (ValueError, IndexError):
                continue

    with open(traj_json_path, 'w') as f:
        json.dump(new_interactions, f, indent=2, ensure_ascii=False)

    metadata_path = os.path.join(traj_dir, "metadata.json")
    if os.path.exists(metadata_path):
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        if isinstance(metadata.get("path"), list) and metadata["path"]:
            metadata["path"] = metadata["path"][:-1]
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

    verdict_path = os.path.join(traj_dir, "verdict.json")
    if os.path.exists(verdict_path):
        with open(verdict_path, 'r') as f:
            verdict = json.load(f)

        new_path = metadata.get("path", [])
        total_urls = len(new_path)
        urls_visited_successfully = total_urls
        
        if total_urls > 1:
            progress = (urls_visited_successfully - 1) / (total_urls - 1)
        else:
            progress = 1.0 if total_urls == 1 and urls_visited_successfully == 1 else 0.0

        verdict_data = {
            "total_urls": total_urls,
            "urls_visited_successfully": urls_visited_successfully, 
            "status": "SUCCESS",
            "reason": "trajectory trimmed",
            "progress": progress,
            "path": new_path,
        }
        
        with open(verdict_path, 'w') as f:
            json.dump(verdict_data, f, indent=2, ensure_ascii=False)
            
    logger = PlaywrightLogger(outdir=traj_dir)
    logger.interactions = convert_to_logger_format(new_interactions, metadata)
    eps_name = metadata.get("eps_name", "")
    task_name_parts = eps_name.split('_')
    new_task_details = {
        "path": metadata.get("path", []),
        "length": len(metadata.get("path", [])),
        "name": "_".join(task_name_parts[1:-1]),
        "original_key": task_name_parts[-1]
    }
    logger.log_trajectory_html(task_name=eps_name, task=new_task_details)


def process_and_trim_directory(dir_path: str) -> (str, str, str):
    """
    Worker function: checks if a directory needs trimming and processes it.
    Returns the directory path, a status message, and any error.
    """
    try:
        if should_trim(dir_path):
            trim_trajectory_in_place(dir_path)
            return (dir_path, "TRIMMED", None)
        else:
            return (dir_path, "SKIPPED", None)
    except Exception as e:
        return (dir_path, "FAILED", str(e))

def main():
    """
    Main function to find and trim trajectories in parallel.
    """
    parser = argparse.ArgumentParser(
        description="Finds and trims trajectories in specified directories if they meet the criteria (status != SUCCESS, progress == 0.67).",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('paths', nargs='+',
                        help="One or more paths to process.\n"
                             "Can be:\n"
                             "- An individual trajectory directory.\n"
                             "- A parent directory containing trajectories.\n"
                             "- A glob pattern (e.g., 'data/task_*').")
    parser.add_argument('--num-workers', type=int, default=multiprocessing.cpu_count(),
                        help=f"Number of worker processes. Defaults to CPU cores ({multiprocessing.cpu_count()}).")

    if len(sys.argv) < 2:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    # Discover trajectory directories
    input_paths = []
    for path_arg in args.paths:
        input_paths.extend(glob(path_arg))

    trajectory_dirs_to_process = set()
    for path in input_paths:
        if not os.path.isdir(path):
            continue
        if os.path.exists(os.path.join(path, "trajectory.json")):
            trajectory_dirs_to_process.add(os.path.abspath(path))
        else:
            subdirectories = [d.path for d in os.scandir(path) if d.is_dir()]
            for subdir in subdirectories:
                if os.path.exists(os.path.join(subdir, "trajectory.json")):
                    trajectory_dirs_to_process.add(os.path.abspath(subdir))
    
    if not trajectory_dirs_to_process:
        print("\nNo valid trajectory directories found to process.")
        return

    sorted_dirs = sorted(list(trajectory_dirs_to_process))
    print(f"\nFound {len(sorted_dirs)} potential trajectories. Processing with {args.num_workers} workers...")

    # Process in parallel
    results = {"TRIMMED": 0, "SKIPPED": 0, "FAILED": 0}
    failed_dirs = []

    with ProcessPoolExecutor(max_workers=args.num_workers) as executor:
        future_to_dir = {executor.submit(process_and_trim_directory, dir_path): dir_path for dir_path in sorted_dirs}
        
        progress = tqdm(as_completed(future_to_dir), total=len(sorted_dirs), desc="Trimming trajectories", unit="dir")
        for future in progress:
            dir_path, status, error = future.result()
            results[status] += 1
            if status == "FAILED":
                failed_dirs.append((dir_path, error))

    # Print summary
    print("\n--- Trajectory Trimming Summary ---")
    print(f"Total directories processed: {len(sorted_dirs)}")
    print(f"  - Trajectories trimmed: {results['TRIMMED']}")
    print(f"  - Skipped (did not need trimming): {results['SKIPPED']}")
    print(f"  - Directories failed: {results['FAILED']}")

    if failed_dirs:
        print("\nFailed directories:")
        for dir_path, error in failed_dirs:
            print(f"  - {os.path.basename(dir_path)}: {error}")

if __name__ == "__main__":
    main()
