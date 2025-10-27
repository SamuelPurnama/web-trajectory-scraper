import os
import json
import sys
import glob
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
import argparse

def process_trajectory(dir_path, verbose=True):
    """
    Remaps 'switch_tab' actions to 'tab_focus' actions in a trajectory.json file,
    incrementing the page index for each tab switch.
    """
    trajectory_path = os.path.join(dir_path, "trajectory.json")
    if not os.path.exists(trajectory_path):
        return False

    try:
        with open(trajectory_path, 'r', encoding='utf-8') as f:
            trajectory_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, IOError):
        return False

    if not isinstance(trajectory_data, dict):
        return False

    modified = False
    current_page_index = 0
    
    sorted_step_keys = sorted(trajectory_data.keys(), key=int)

    for step_key in sorted_step_keys:
        step_data = trajectory_data[step_key]
        
        action_output = step_data.get("action", {}).get("action_output", {})
        action_name = action_output.get("action_name")

        if action_name == 'switch_tab':
            modified = True
            new_page_index = current_page_index + 1

            action_output["action_name"] = "tab_focus"
            
            action = action_output.get("action", {})
            action["tab_id"] = new_page_index
            action["page_index"] = new_page_index
            action_output["action"] = action

            step_data["action"]["action_str"] = f"tab_focus(tab_id={new_page_index}, page_index={new_page_index})"
            step_data["action"]["action_description"] = f"focus tab {new_page_index}"
            
            current_page_index = new_page_index
    
    if modified:
        try:
            with open(trajectory_path, 'w', encoding='utf-8') as f:
                json.dump(trajectory_data, f, indent=2, ensure_ascii=False)
            if verbose: print(f"Updated trajectory in: {dir_path}")
        except IOError as e:
            if verbose: print(f"Error writing to {dir_path}: {e}")
            return False
        return True
    return False

def remap_worker(dir_path: str) -> (str, str, str):
    """
    Worker function that calls process_trajectory and returns status.
    """
    try:
        was_remapped = process_trajectory(dir_path, verbose=False)
        if was_remapped:
            return (dir_path, "REMAPPED", None)
        else:
            return (dir_path, "SKIPPED", None)
    except Exception as e:
        return (dir_path, "FAILED", str(e))

def main():
    """
    Finds and processes trajectory directories in parallel to remap tab switching actions.
    """
    parser = argparse.ArgumentParser(
        description="Remaps 'switch_tab' to 'tab_focus' in trajectory files within specified directories.",
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
        input_paths.extend(glob.glob(path_arg))

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
    results = {"REMAPPED": 0, "SKIPPED": 0, "FAILED": 0}
    failed_dirs = []

    with ProcessPoolExecutor(max_workers=args.num_workers) as executor:
        future_to_dir = {executor.submit(remap_worker, dir_path): dir_path for dir_path in sorted_dirs}
        
        progress = tqdm(as_completed(future_to_dir), total=len(sorted_dirs), desc="Remapping tabs", unit="dir")
        for future in progress:
            dir_path, status, error = future.result()
            results[status] += 1
            if status == "FAILED":
                failed_dirs.append((dir_path, error))

    # Print summary
    print("\n--- Tab Remapping Summary ---")
    print(f"Total directories processed: {len(sorted_dirs)}")
    print(f"  - Trajectories remapped: {results['REMAPPED']}")
    print(f"  - Skipped (no switch_tab found): {results['SKIPPED']}")
    print(f"  - Directories failed: {results['FAILED']}")

    if failed_dirs:
        print("\nFailed directories:")
        for dir_path, error in failed_dirs:
            print(f"  - {os.path.basename(dir_path)}: {error}")

if __name__ == "__main__":
    main()
