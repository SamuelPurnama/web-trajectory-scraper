import os
import json
import sys
import glob
import re
from PIL import Image
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
import argparse

# Add the project's root directory to the Python path to allow importing the logger
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from deterministic_agent.logger import PlaywrightLogger

VIEWPORT_MAP = {
    (1920, 1080): "Standard Full HD (Desktop)",
    (1366, 768): "Widescreen Laptop",
    (1536, 864): "High-Resolution Laptop",
    (1280, 720): "Small Desktop Monitor",
    (1024, 768): "Minimum Supported Desktop Viewport",
}

def get_viewport_from_image(image_path):
    """Reads an image and returns a viewport dictionary based on its dimensions."""
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            name = VIEWPORT_MAP.get((width, height), "Unknown Resolution")
            return {"width": width, "height": height, "name": name}
    except FileNotFoundError:
        # This can happen if file renaming hasn't occurred yet.
        # We can try the 0-indexed path as a fallback.
        if '_001.' in image_path:
            try:
                return get_viewport_from_image(image_path.replace('_001.', '_000.'))
            except FileNotFoundError:
                 print(f"Warning: Screenshot not found at {image_path} or fallback, cannot determine viewport.")
        else:
            print(f"Warning: Screenshot not found at {image_path}, cannot determine viewport.")
    except Exception as e:
        print(f"Warning: Could not read image {image_path}. Error: {e}")
    return None

def fix_metadata(dir_path, verbose=True):
    """
    Fixes a legacy metadata.json file by restructuring it and adding viewport
    information derived from the first screenshot.
    """
    metadata_path = os.path.join(dir_path, "metadata.json")
    if not os.path.exists(metadata_path):
        return

    with open(metadata_path, 'r') as f:
        try:
            metadata = json.load(f)
        except json.JSONDecodeError:
            if verbose: print(f"Warning: Could not decode JSON from {metadata_path}, skipping.")
            return

    is_legacy = "goal" not in metadata or "eps_name" not in metadata
    viewport_missing = "viewport" not in metadata or not metadata.get("viewport")

    if not is_legacy and not viewport_missing:
        return

    if verbose: print(f"Processing metadata for {dir_path}...")

    if is_legacy:
        if verbose: print(f"  - Converting legacy structure...")
        eps_name = os.path.basename(os.path.normpath(dir_path))
        metadata = {
            "goal": "", "eps_name": eps_name,
            "task": {
                "task_type": "", "keyword": "", "steps": [],
                "instruction": {"high_level": "", "mid_level": "", "low_level": ""}
            },
            "path": metadata.get("path", []),
            "viewport": metadata.get("viewport", {})
        }

    if viewport_missing:
        if verbose: print(f"  - Adding missing viewport info...")
        image_full_path = os.path.join(dir_path, "images", "screenshot_001.png")
        viewport = get_viewport_from_image(image_full_path)
        if viewport:
            metadata["viewport"] = viewport
        elif verbose:
            print("  - Warning: Could not determine viewport from screenshot.")

    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

def rename_data_files_to_1_based(dir_path, verbose=True):
    """
    Finds 0-indexed data files and renames them to be 1-indexed.
    It renames in reverse order to avoid overwriting existing files.
    """
    if not os.path.exists(os.path.join(dir_path, "images", "screenshot_000.png")):
        return # No 0-indexed files found, nothing to do.

    if verbose: print(f"  - Renaming data files from 0-index to 1-index in {dir_path}...")

    FILE_PATTERNS = {
        "images": "screenshot_*.png", "urls": "url_*.txt", "html": "html_*.html",
        "axtree": "axtree_*.txt", "global_axtree": "global_axtree_*.txt",
        "extra_element_properties": "extra_element_properties_*.json",
    }
    
    files_to_rename = []
    for subdir, pattern_glob in FILE_PATTERNS.items():
        search_path = os.path.join(dir_path, subdir, pattern_glob)
        files_to_rename.extend(glob.glob(search_path))

    def get_index(f):
        match = re.search(r'_(\d{3,})\.', os.path.basename(f))
        return int(match.group(1)) if match else -1

    files_to_rename.sort(key=get_index, reverse=True)

    for old_path in files_to_rename:
        index = get_index(old_path)
        if index == -1: continue

        new_index = index + 1
        base = os.path.basename(old_path)
        zfilled_new = str(new_index).zfill(len(re.search(r'_(\d{3,})\.', base).group(1)))
        new_base = re.sub(r'_(\d{3,})\.', f'_{zfilled_new}.', base, 1)
        new_path = os.path.join(os.path.dirname(old_path), new_base)
        os.rename(old_path, new_path)

def fix_trajectory(dir_path, verbose=True):
    """
    Fixes a legacy trajectory.json file by renaming data files and then
    re-generating the JSON to be 1-indexed.
    """
    trajectory_path = os.path.join(dir_path, "trajectory.json")
    if not os.path.exists(trajectory_path): return False

    with open(trajectory_path, 'r') as f:
        try: data = json.load(f)
        except json.JSONDecodeError:
            if verbose: print(f"Warning: Could not decode JSON from {trajectory_path}, skipping.")
            return False

    if isinstance(data, dict): return False

    if verbose: print(f"Fixing legacy trajectory.json in {dir_path}...")
    rename_data_files_to_1_based(dir_path, verbose)

    for interaction in data:
        if 'step' not in interaction: continue
        original_step = interaction['step']
        new_step = original_step + 1
        interaction['step'] = new_step

        zfilled_original = str(original_step).zfill(3)
        zfilled_new = str(new_step).zfill(3)
        for key in ['screenshot', 'axtree', 'global_axtree', 'extra_element_properties']:
            if key in interaction and isinstance(interaction.get(key), str):
                interaction[key] = interaction[key].replace(f'_{zfilled_original}.', f'_{zfilled_new}.')

    logger = PlaywrightLogger(outdir=dir_path)
    logger.interactions = data
    logger.log_trajectory_json()
    return True

def process_directory(dir_path):
    """
    Worker function to process a single trajectory directory.
    Calls fix_trajectory and fix_metadata.
    Returns a tuple of (dir_path, was_fixed, error_message).
    """
    try:
        # Verbose is set to False to avoid garbled output from parallel processes.
        # Progress is tracked by the main process.
        was_fixed = fix_trajectory(dir_path, verbose=False)
        fix_metadata(dir_path, verbose=False)
        return (dir_path, was_fixed, None)
    except Exception as e:
        return (dir_path, False, str(e))

def main():
    """
    Main function to find and process trajectory directories in parallel.
    """
    parser = argparse.ArgumentParser(
        description="Finds and fixes legacy trajectory data in specified directories. "
                    "It can scan parent directories for trajectory subdirectories and "
                    "process them in parallel.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('paths', nargs='+', 
                        help="One or more paths to process.\n"
                             "Can be:\n"
                             "- An individual trajectory directory (containing trajectory.json).\n"
                             "- A parent directory containing trajectory subdirectories.\n"
                             "- A glob pattern (e.g., 'data/task_*').")
    parser.add_argument('--num-workers', type=int, default=multiprocessing.cpu_count(),
                        help=f"Number of worker processes to use. Defaults to the number of CPU cores ({multiprocessing.cpu_count()}).")

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
            # glob might return files, we only care about directories
            continue

        if os.path.exists(os.path.join(path, "trajectory.json")):
            trajectory_dirs_to_process.add(os.path.abspath(path))
            continue

        subdirectories = [d.path for d in os.scandir(path) if d.is_dir()]
        for subdir in subdirectories:
            if os.path.exists(os.path.join(subdir, "trajectory.json")):
                trajectory_dirs_to_process.add(os.path.abspath(subdir))

    if not trajectory_dirs_to_process:
        print("\nNo valid trajectory directories found to process.")
        return

    sorted_dirs = sorted(list(trajectory_dirs_to_process))
    print(f"\nFound {len(sorted_dirs)} trajectory directories. Processing with {args.num_workers} workers...")

    # Process directories in parallel
    fixed_count = 0
    failed_count = 0
    already_correct_count = 0
    failed_dirs = []

    with ProcessPoolExecutor(max_workers=args.num_workers) as executor:
        future_to_dir = {executor.submit(process_directory, dir_path): dir_path for dir_path in sorted_dirs}
        
        progress = tqdm(as_completed(future_to_dir), total=len(sorted_dirs), desc="Fixing trajectories", unit="dir")
        for future in progress:
            dir_path, was_fixed, error = future.result()
            if error:
                failed_count += 1
                failed_dirs.append((dir_path, error))
            elif was_fixed:
                fixed_count += 1
            else:
                already_correct_count += 1
    
    # Print summary
    print("\n--- Fix Legacy Trajectories Summary ---")
    print(f"Total directories processed: {len(sorted_dirs)}")
    print(f"  - Trajectories fixed: {fixed_count}")
    print(f"  - Already in correct format: {already_correct_count}")
    print(f"  - Directories failed: {failed_count}")

    if failed_dirs:
        print("\nFailed directories:")
        for dir_path, error in failed_dirs:
            print(f"  - {os.path.basename(dir_path)}: {error}")

if __name__ == "__main__":
    main()
