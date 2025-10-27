import os
import json
import sys
import glob
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
import argparse


def compute_delta_y(metadata_path: str) -> int:
    """
    Reads viewport height from metadata.json and returns 90% of it as an integer.
    """
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    viewport = metadata.get("viewport", {})
    height = viewport.get("height")
    if not isinstance(height, (int, float)):
        raise ValueError("viewport.height missing or invalid in metadata.json")
    return int(height * 0.9)


def process_trajectory(dir_path: str, verbose: bool = True) -> bool:
    """
    For a single trajectory directory, update all scroll actions so that:
      action_output.action = {"delta_x": 0, "delta_y": int(0.9 * viewport_height)}
    Does not modify any other fields.

    Returns True if any modification was made; otherwise False.
    """
    trajectory_path = os.path.join(dir_path, "trajectory.json")
    metadata_path = os.path.join(dir_path, "metadata.json")

    if not (os.path.exists(trajectory_path) and os.path.exists(metadata_path)):
        return False

    try:
        delta_y = compute_delta_y(metadata_path)
    except Exception:
        return False

    try:
        with open(trajectory_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, IOError):
        return False

    modified = False

    def update_step(step_obj: dict) -> bool:
        action_output = step_obj.get("action", {}).get("action_output", {})
        action_name = action_output.get("action_name")
        if action_name != "scroll":
            return False
        # Only modify if different from desired structure
        current_action = action_output.get("action", {})
        desired_action = {"delta_x": 0, "delta_y": delta_y}
        if isinstance(current_action, dict) and current_action == desired_action:
            return False
        action_output["action"] = desired_action
        return True

    if isinstance(data, dict):
        for step_key in sorted(data.keys(), key=lambda k: int(k) if str(k).isdigit() else k):
            step_data = data.get(step_key, {})
            if isinstance(step_data, dict) and update_step(step_data):
                modified = True
    elif isinstance(data, list):
        for step_data in data:
            if isinstance(step_data, dict) and update_step(step_data):
                modified = True
    else:
        return False

    if modified:
        try:
            with open(trajectory_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            if verbose:
                print(f"Updated trajectory in: {dir_path}")
        except IOError:
            return False
        return True

    return False


def worker(dir_path: str) -> (str, str, str):
    """
    Worker wrapper for parallel execution.
    Returns (dir_path, STATUS, error_or_none)
    """
    try:
        changed = process_trajectory(dir_path, verbose=False)
        return (dir_path, "UPDATED" if changed else "SKIPPED", None)
    except Exception as e:
        return (dir_path, "FAILED", str(e))


def main():
    """
    Scans provided paths for trajectory directories and updates scroll actions in parallel.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Update scroll actions in trajectory files to use delta_x=0 and delta_y=0.9*viewport.height.\n"
            "Only the nested action object inside action_output is modified."
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        'paths',
        nargs='+',
        help=(
            "One or more paths to process. Can be:\n"
            "- An individual trajectory directory.\n"
            "- A parent directory containing trajectories.\n"
            "- A glob pattern (e.g., '/root/.../successful_trajectories_postprocessed/*')."
        ),
    )
    parser.add_argument(
        '--num-workers',
        type=int,
        default=255,
        help="Number of worker processes. Default: 255.",
    )

    if len(sys.argv) < 2:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    # Resolve input paths and discover trajectory directories
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
            subdirs = [d.path for d in os.scandir(path) if d.is_dir()]
            for subdir in subdirs:
                if os.path.exists(os.path.join(subdir, "trajectory.json")):
                    trajectory_dirs_to_process.add(os.path.abspath(subdir))

    if not trajectory_dirs_to_process:
        print("\nNo valid trajectory directories found to process.")
        return

    sorted_dirs = sorted(list(trajectory_dirs_to_process))
    print(f"\nFound {len(sorted_dirs)} potential trajectories. Processing with {args.num_workers} workers...")

    results = {"UPDATED": 0, "SKIPPED": 0, "FAILED": 0}
    failed = []

    with ProcessPoolExecutor(max_workers=args.num_workers) as executor:
        futures = {executor.submit(worker, dir_path): dir_path for dir_path in sorted_dirs}
        progress = tqdm(as_completed(futures), total=len(sorted_dirs), desc="Updating scroll actions", unit="dir")
        for future in progress:
            dir_path, status, error = future.result()
            results[status] += 1
            if status == "FAILED":
                failed.append((dir_path, error))

    print("\n--- Scroll Action Update Summary ---")
    print(f"Total directories processed: {len(sorted_dirs)}")
    print(f"  - Updated: {results['UPDATED']}")
    print(f"  - Skipped: {results['SKIPPED']}")
    print(f"  - Failed: {results['FAILED']}")

    if failed:
        print("\nFailed directories:")
        for dir_path, error in failed:
            print(f"  - {os.path.basename(dir_path)}: {error}")


if __name__ == "__main__":
    main()


