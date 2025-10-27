#!/usr/bin/env python3
"""
Compute per-website example counts by matching folder name slugs in a WEKA
dataset directory and append the result as a new Count column to a CSV.

Folder naming convention assumed: "task_<website_slug>_<numeric_id>"
Examples: task_famousbirthdays_50035, task_my_52488, task_sports_45929

CSV assumptions: Contains at least an "origin" column (e.g., https://www.bestbuy.com)
If a dedicated website slug column exists (e.g., website/site/name/slug), it will be used.
Otherwise, a slug will be derived from the origin URL's hostname (second-level label).

Usage:
  python compute_website_counts.py \
    --weka-dir /root/weka/oe-training-default/webolmo/datasets/node_traversal/successful_trajectories_postprocessed \
    --csv /root/weka/oe-training-default/webolmo/datasets/node_traversal/successful_trajectories_postprocessed/website_taxonomy.csv \
    --out /root/weka/oe-training-default/webolmo/datasets/node_traversal/successful_trajectories_postprocessed/website_taxonomy_with_counts.csv
"""

import argparse
import csv
import os
import sys
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse


def normalize_slug(value: str) -> str:
    """Normalize a slug-like string for matching.

    - Lowercase
    - Strip surrounding whitespace
    - Replace hyphens and periods with nothing
    - Remove any non-alphanumeric characters
    """
    if value is None:
        return ""
    s = value.strip().lower()
    s = s.replace("-", "").replace(".", "").replace(" ", "")
    # Keep alphanumeric only
    s = "".join(ch for ch in s if ch.isalnum())
    return s


def parse_folder_slug(folder_name: str) -> Optional[str]:
    """Extract website slug from folder name following task_<slug>_<id>.

    This is robust to slugs containing underscores by splitting on the last underscore
    and ensuring the right part is an integer id.
    """
    if not folder_name.startswith("task_"):
        return None
    body = folder_name[len("task_") :]
    if "_" not in body:
        return None
    slug_part, last_part = body.rsplit("_", 1)
    if not last_part.isdigit():
        return None
    return slug_part


def build_slug_counts(weka_dir: str) -> Dict[str, int]:
    """Scan WEKA directory and count occurrences per normalized slug."""
    counts: Dict[str, int] = {}
    try:
        with os.scandir(weka_dir) as it:
            for entry in it:
                if not entry.is_dir():
                    continue
                slug = parse_folder_slug(entry.name)
                if slug is None:
                    continue
                norm = normalize_slug(slug)
                if not norm:
                    continue
                counts[norm] = counts.get(norm, 0) + 1
    except PermissionError as e:
        print(f"Permission denied reading directory: {weka_dir}\n{e}", file=sys.stderr)
        sys.exit(1)
    return counts


def hostname_from_origin(origin: str) -> str:
    """Extract hostname from an origin-like string, tolerant of raw hosts."""
    if not origin:
        return ""
    parsed = urlparse(origin)
    host = parsed.netloc or parsed.path  # tolerate raw host without scheme
    return host


def derive_slug_from_origin(origin: str) -> str:
    """Derive a website slug from an origin URL/host.

    Heuristic:
    - Grab hostname; remove leading 'www.'
    - Split by '.'; if >= 2 labels, take the second-to-last as the base (second-level)
      otherwise take the first label
    - Normalize via normalize_slug
    """
    host = hostname_from_origin(origin).lower()
    if host.startswith("www."):
        host = host[4:]
    labels = [lbl for lbl in host.split(".") if lbl]
    if not labels:
        return ""
    base = labels[-2] if len(labels) >= 2 else labels[0]
    return normalize_slug(base)


def choose_slug_source(headers: Tuple[str, ...]) -> Optional[str]:
    """Pick a header to use as the slug source if present."""
    preferred = (
        "website",
        "site",
        "name",
        "slug",
        "origin_key",
        "origin_slug",
    )
    lower_to_actual = {h.lower(): h for h in headers}
    for key in preferred:
        if key in lower_to_actual:
            return lower_to_actual[key]
    return None


def compute_counts_for_csv(
    csv_path: str, slug_counts: Dict[str, int]
) -> Tuple[list, list]:
    """Read CSV, compute counts per row, and return (rows, fieldnames).

    Appends a 'Count' column in the returned fieldnames.
    """
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        slug_header = choose_slug_source(tuple(headers))
        origin_header = None
        if "origin" in {h.lower() for h in headers}:
            # Recover the actual case of the header
            origin_header = next(h for h in headers if h.lower() == "origin")

        for row in reader:
            if slug_header and row.get(slug_header):
                slug_raw = row.get(slug_header, "")
                slug_norm = normalize_slug(slug_raw)
            else:
                slug_norm = derive_slug_from_origin(row.get(origin_header, "") if origin_header else "")
            row["Count"] = str(slug_counts.get(slug_norm, 0))
            rows.append(row)

    fieldnames = list(rows[0].keys()) if rows else []
    if "Count" not in fieldnames:
        fieldnames.append("Count")
    return rows, fieldnames


def write_csv(csv_path: str, rows: list, fieldnames: list) -> None:
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Append Count column to website taxonomy CSV.")
    parser.add_argument("--weka-dir", required=True, help="Path to successful_trajectories_postprocessed directory")
    parser.add_argument("--csv", required=True, help="Path to website_taxonomy.csv")
    parser.add_argument(
        "--out", required=False, help="Output CSV path (default: <input> with _with_counts suffix)", default=None
    )
    args = parser.parse_args()

    slug_counts = build_slug_counts(args.weka_dir)
    rows, fieldnames = compute_counts_for_csv(args.csv, slug_counts)

    out_path = args.out
    if not out_path:
        base, ext = os.path.splitext(args.csv)
        out_path = f"{base}_with_counts{ext or '.csv'}"

    write_csv(out_path, rows, fieldnames)
    print(f"Wrote updated CSV with counts: {out_path}")
    print(f"Unique slugs found in WEKA dir: {len(slug_counts)}")


if __name__ == "__main__":
    main()


