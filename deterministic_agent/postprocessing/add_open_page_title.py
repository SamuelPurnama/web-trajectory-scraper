import os
import json
import sys
import glob
import re
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
import argparse

def extract_title_from_html(html_path):
    try:
        with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            match = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
            return match.group(1).strip() if match else ""
    except (FileNotFoundError, IOError):
        return ""

def process_trajectory(dir_path, verbose=True):
    trajectory_path = os.path.join(dir_path, "trajectory.json")
    if not os.path.exists(trajectory_path):
        return False

    try:
        with open(trajectory_path, 'r', encoding='utf-8') as f:
            trajectory_data = json.load(f)
    except (json.JSONDecodeError, IOError):
        return False

    modified = False
    open_pages = []
    page_index = 0
    
    sorted_step_keys = sorted(trajectory_data.keys(), key=int)

    for i, step_key in enumerate(sorted_step_keys):
        step_data = trajectory_data[step_key]
        step_data.setdefault("other_obs", {})

        if i == 0:
            page_index = step_data.get("other_obs", {}).get("page_index", 0)
        
        while len(open_pages) <= page_index:
            open_pages.append({"title": "", "url": ""})

        html_path = os.path.join(dir_path, "html", f"html_{step_key.zfill(3)}.html")
        title = extract_title_from_html(html_path)
        url = step_data.get("other_obs", {}).get("url", "")
        
        open_pages[page_index]["title"] = title
        open_pages[page_index]["url"] = url

        current_titles = [page["title"] for page in open_pages]
        current_urls = [page["url"] for page in open_pages]
        
        if step_data["other_obs"].get("open_pages_titles") != current_titles:
            step_data["other_obs"]["open_pages_titles"] = current_titles
            modified = True
            
        if step_data["other_obs"].get("open_pages_urls") != current_urls:
            step_data["other_obs"]["open_pages_urls"] = current_urls
            modified = True
        
        if step_data["other_obs"].get("page_index") != page_index:
            step_data["other_obs"]["page_index"] = page_index
            modified = True

        action_output = step_data.get("action", {}).get("action_output", {})
        if action_output.get("action_name") == "tab_focus":
            page_index = action_output.get("action", {}).get("page_index", page_index)
    
    if modified:
        try:
            with open(trajectory_path, 'w', encoding='utf-8') as f:
                json.dump(trajectory_data, f, indent=2, ensure_ascii=False)
            return True
        except IOError:
            return False
    return False

def title_worker(dir_path: str) -> (str, str, str):
    """
    Worker function that calls process_trajectory for adding page titles.
    """
    try:
        was_modified = process_trajectory(dir_path, verbose=False)
        if was_modified:
            return (dir_path, "MODIFIED", None)
        else:
            return (dir_path, "SKIPPED", None)
    except Exception as e:
        return (dir_path, "FAILED", str(e))

def main():
    """
    Finds and processes trajectory directories in parallel to add open page titles.
    """
    parser = argparse.ArgumentParser(
        description="Adds 'open_pages_titles' and 'open_pages_urls' to trajectory files based on HTML content.",
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
    results = {"MODIFIED": 0, "SKIPPED": 0, "FAILED": 0}
    failed_dirs = []

    with ProcessPoolExecutor(max_workers=args.num_workers) as executor:
        future_to_dir = {executor.submit(title_worker, dir_path): dir_path for dir_path in sorted_dirs}
        
        progress = tqdm(as_completed(future_to_dir), total=len(sorted_dirs), desc="Adding page titles", unit="dir")
        for future in progress:
            dir_path, status, error = future.result()
            results[status] += 1
            if status == "FAILED":
                failed_dirs.append((dir_path, error))

    # Print summary
    print("\n--- Add Page Titles Summary ---")
    print(f"Total directories processed: {len(sorted_dirs)}")
    print(f"  - Trajectories modified: {results['MODIFIED']}")
    print(f"  - Skipped (no changes needed): {results['SKIPPED']}")
    print(f"  - Directories failed: {results['FAILED']}")

    if failed_dirs:
        print("\nFailed directories:")
        for dir_path, error in failed_dirs:
            print(f"  - {os.path.basename(dir_path)}: {error}")

if __name__ == "__main__":
    main()
