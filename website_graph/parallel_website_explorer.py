#!/usr/bin/env python3
'''
For running parallel website exploration.

Empirically, the best number of workers is 64.

'''

import os
import json
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse
from webgraph_utils import get_filename_from_url


WEBSITES_FILE = "website_txts/retry.txt"
BASE_OUTPUT_DIR = "july_27_585_websites"
MAX_DEPTH = 3
DEPTH_MAX_ITEMS = "10,6,4"
WORKER_COUNTS = [82] # 64 works better than 32 but maybe 128 is even better.

def read_websites(websites_file):
    websites = []
    with open(websites_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and line.startswith('http'):
                websites.append(line)
    return websites

def process_website(website, output_dir):
    try:
        cmd = [
            "uv", "run", "--active", "-m", "website_explorer",
            website,
            "--max-depth", str(MAX_DEPTH),
            "--depth-max-items", DEPTH_MAX_ITEMS,
            "--output-dir", output_dir
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=6000) # 45 minute timeout per webstie
        if result.returncode != 0:
            print(f"Error for {website}: {result.stderr}")
        return website, result.returncode == 0
    except Exception as e:
        print(f"Exception for {website}: {str(e)}")
        print(f"Command was: {' '.join(cmd)}")
        return website, False

def run_parallel_exploration(websites, num_workers):
    output_dir = BASE_OUTPUT_DIR
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    print(f"Running with {num_workers} workers...")
    start_time = time.time()
    successful = 0
    
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        future_to_website = {
            executor.submit(process_website, website, output_dir): website 
            for website in websites
        }
        
        for future in as_completed(future_to_website):
            website, success = future.result()
            if success:
                successful += 1
                # print(f"✓ {website}")
            else:
                print(f"✗ {website}")
    
    wall_time = time.time() - start_time
    print(f"Workers: {num_workers}, Time: {wall_time:.2f}s, Success: {successful}/{len(websites)}")
    
    # Save timing results to txt file
    timing_file = os.path.join(BASE_OUTPUT_DIR, f"timing_workers_{num_workers}.txt")
    with open(timing_file, 'w') as f:
        f.write(f"Workers: {num_workers}\n")
        f.write(f"Wall Time: {wall_time:.2f} seconds\n")
        f.write(f"Total Websites: {len(websites)}\n")
        f.write(f"Successful: {successful}\n")
        f.write(f"Failed: {len(websites) - successful}\n")
        f.write(f"Success Rate: {successful/len(websites)*100:.1f}%\n")
    
    analyze_results(websites, output_dir)

    return wall_time, successful

def analyze_results(websites, output_dir):
    """
    Analyzes the results of the website exploration to find websites
    with 0 or 1 nodes or where the JSON file was not created.
    """
    problematic_count = 0
    problematic_websites = []

    for website in websites:
        website_base_name = get_filename_from_url(website)
        website_dir = os.path.join(output_dir, website_base_name)
        
        if not os.path.isdir(website_dir):
            problematic_count += 1
            problematic_websites.append(f"{website} (no output directory)")
            continue

        json_files = [f for f in os.listdir(website_dir) if f.startswith(website_base_name) and f.endswith('.json')]

        if not json_files:
            problematic_count += 1
            problematic_websites.append(f"{website} (no JSON file)")
            continue
        
        # In case of multiple runs, use the latest file
        json_files.sort()
        latest_json_file = os.path.join(website_dir, json_files[-1])

        try:
            with open(latest_json_file, 'r') as f:
                data = json.load(f)
            
            num_nodes = len(data.get('nodes', []))
            if num_nodes <= 1:
                problematic_count += 1
                problematic_websites.append(f"{website} ({num_nodes} nodes)")

        except (json.JSONDecodeError, KeyError) as e:
            problematic_count += 1
            problematic_websites.append(f"{website} (error reading JSON: {e})")

    analysis_file = os.path.join(BASE_OUTPUT_DIR, "website_analysis.txt")
    with open(analysis_file, 'w') as f:
        f.write(f"Total websites with 1 or 0 nodes, or with no JSON file: {problematic_count}\n")
        f.write("="*50 + "\n")
        for line in problematic_websites:
            f.write(f"{line}\n")

    print(f"Analysis complete. Found {problematic_count} websites with issues. See {analysis_file} for details.")

def main():
    websites = read_websites(WEBSITES_FILE)
    Path(BASE_OUTPUT_DIR).mkdir(exist_ok=True)
    
    for num_workers in WORKER_COUNTS:
        wall_time, successful = run_parallel_exploration(websites, num_workers)

if __name__ == "__main__":
    main() 