#!/usr/bin/env python3

import os
import json
import argparse
from pathlib import Path
from collections import Counter
import matplotlib.pyplot as plt
import numpy as np


def parse_verdict_file(verdict_path):
    """Parse a verdict.json file and extract success/failure information."""
    try:
        with open(verdict_path, 'r', encoding='utf-8') as f:
            verdict_data = json.load(f)
            return verdict_data
            
    except Exception as e:
        print(f"Error reading {verdict_path}: {e}")
        return None


def categorize_result(verdict_data):
    """Categorize the result as success or failure with failure type."""
    if verdict_data is None:
        return "failure", "file_read_error"
    
    if not isinstance(verdict_data, dict):
        return "failure", "invalid_format"
    
    status = verdict_data.get("status", "").upper()
    reason = verdict_data.get("reason", "")
    
    if status == "SUCCESS":
        return "success", None
    
    if reason:
        reason_lower = reason.lower()
        
        reason_mappings = {
            "fingerprint_error": ["invalid browsersettings.fingerprint", "failed to generate a consistent fingerprint"],
            "navigation_timeout": ["page.goto: timeout", "timeout 45000ms exceeded trying to navigate"],
            "timeout": ["timeout", "timed_out", "time_limit_exceeded"],
            "error": ["error", "exception", "failed", "crash"],
            # New: Specific scrolled-to-bottom error
            "scrolled_but_element_not_found": [
                "scrolled to bottom, but element not found in viewport"
            ],
            # Keep generic element not found for other cases
            "element_not_found": ["element not found", "not found in viewport"]
        }
        
        for failure_type, indicators in reason_mappings.items():
            if any(indicator in reason_lower for indicator in indicators):
                return "failure", failure_type
        
        # If reason is not empty and not matched, classify as unclassified_error
        if reason:
            return "failure", f"unclassified_error: {reason}"
        
        return "failure", "unknown"
    
    return "failure", "unknown"


def analyze_directory(root_dir):
    """Analyze all verdict.json files in subdirectories."""
    root_path = Path(root_dir)
    
    if not root_path.exists():
        print(f"Directory {root_dir} does not exist!")
        return []
    
    results = []
    verdict_files = list(root_path.rglob("verdict.json"))
    
    print(f"Found {len(verdict_files)} verdict.json files")
    
    for verdict_path in verdict_files:
        task_name = verdict_path.parent.name
        verdict_data = parse_verdict_file(verdict_path)
        status, failure_type = categorize_result(verdict_data)
        
        progress = verdict_data.get("progress", 0.0) if verdict_data else 0.0
        total_urls = verdict_data.get("total_urls", 0) if verdict_data else 0
        urls_visited = verdict_data.get("urls_visited_successfully", 0) if verdict_data else 0
        
        results.append({
            "task_name": task_name,
            "status": status,
            "failure_type": failure_type,
            "progress": progress,
            "total_urls": total_urls,
            "urls_visited": urls_visited,
        })
    
    return results


def create_progress_histogram(results):
    """Create and save a progress histogram."""
    if not results:
        return
    
    progress_values = [r["progress"] for r in results if r["progress"] is not None]
    
    if not progress_values:
        return
    
    bins = np.linspace(0, 1, 11)
    bin_labels = [f"{int(i*10)}-{int((i+0.1)*10)}%" for i in bins[:-1]]
    counts, _ = np.histogram(progress_values, bins=bins)
    
    print("\nPROGRESS HISTOGRAM")
    print("="*60)
    
    max_count = max(counts) if max(counts) > 0 else 1
    for i, (label, count) in enumerate(zip(bin_labels, counts)):
        percentage = (count / len(progress_values)) * 100
        bar_length = int((count / max_count) * 40)
        bar = "█" * bar_length
        print(f"{label:>8}: {bar:<40} {count:>3} ({percentage:.1f}%)")
    
    print(f"\nTotal tasks: {len(progress_values)}")
    print(f"Average progress: {np.mean(progress_values):.2f} ({np.mean(progress_values)*100:.1f}%)")
    print(f"Median progress: {np.median(progress_values):.2f} ({np.median(progress_values)*100:.1f}%)")
    
    success_count = sum(1 for r in results if r["status"] == "success")
    total_count = len(results)
    success_percentage = (success_count / total_count) * 100 if total_count > 0 else 0
    print(f"Tasks with status SUCCESS: {success_count} ({success_percentage:.1f}%)")

    # Save plot
    try:
        plt.figure(figsize=(10, 6))
        plt.hist(progress_values, bins=bins, alpha=0.7, color='skyblue', edgecolor='black')
        plt.xlabel('Progress (0.0 = 0%, 1.0 = 100%)')
        plt.ylabel('Number of Tasks')
        plt.title('Progress Distribution Across Tasks')
        plt.xticks(bins, [f"{int(b*100)}%" for b in bins], rotation=45)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        plt.savefig('progress_histogram.png', dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Progress histogram saved to: progress_histogram.png")
    except Exception as e:
        print(f"Error creating plot: {e}")


def print_results(results):
    """Print analysis results."""
    if not results:
        print("No results to analyze!")
        return
    
    total_tasks = len(results)
    successes = [r for r in results if r["status"] == "success"]
    failures = [r for r in results if r["status"] == "failure"]
    
    success_count = len(successes)
    failure_count = len(failures)
    success_rate = (success_count / total_tasks) * 100 if total_tasks > 0 else 0
    
    # Calculate averages
    avg_total_urls = np.mean([r["total_urls"] for r in results if r["total_urls"] > 0])
    avg_urls_visited = np.mean([r["urls_visited"] for r in results if r["urls_visited"] > 0])
    
    print(f"Total Tasks: {total_tasks}")
    print(f"Successes: {success_count}")
    print(f"Failures: {failure_count}")
    print(f"Success Rate: {success_rate:.1f}%")
    print(f"Average Path Length: {avg_total_urls:.1f} URLs")
    print(f"Average URLs Visited: {avg_urls_visited:.1f}")
    
    if successes:
        print("\nSUCCESSFUL TRAJECTORIES:")
        for success in successes:
            print(f"  ✓ {success['task_name']} ({success['urls_visited']}/{success['total_urls']} URLs)")
    
    if failures:
        print("\nFAILURE BREAKDOWN:")
        failure_types = Counter([f["failure_type"] for f in failures])
        for failure_type, count in failure_types.most_common():
            percentage = (count / total_tasks) * 100
            print(f"  {failure_type}: {count} ({percentage:.1f}%)")


def main():
    parser = argparse.ArgumentParser(description="Analyze trajectory results")
    parser.add_argument("directory", help="Root directory to analyze")
    
    args = parser.parse_args()
    
    results = analyze_directory(args.directory)
    
    if results:
        print_results(results)
        create_progress_histogram(results)


if __name__ == "__main__":
    main() 