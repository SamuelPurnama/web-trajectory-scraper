#!/usr/bin/env python3

import os
import json
import networkx as nx
import argparse
import glob
from urllib.parse import urlparse

def locate_graph_file(website_name: str, base_dir: str) -> str:
    if website_name.startswith('http'):
        parsed = urlparse(website_name)
        website_filename = parsed.netloc.replace('.', '_').replace('www_', '')
    else:
        website_filename = website_name
    
    website_dir = os.path.join(base_dir, website_filename)
    if not os.path.exists(website_dir):
        raise FileNotFoundError(f"Website directory not found: {website_dir}")
    
    pattern = os.path.join(website_dir, f"{website_filename}_website_graph_*.json")
    graph_files = glob.glob(pattern)
    
    if not graph_files:
        raise FileNotFoundError(f"No graph files found for website: {website_name}")
    
    return max(graph_files, key=os.path.getctime)

def compute_paths(graph: nx.DiGraph) -> dict:
    root = next((node for node in graph.nodes() if graph.in_degree(node) == 0), None)
    if not root:
        return {"paths": {}}
    
    leaves = {node for node in graph.nodes() if graph.out_degree(node) == 0}
    all_paths = []
    
    def dfs(node, path):
        if node in leaves:
            all_paths.append(path[:])
            return
        
        for neighbor in graph.successors(node):
            if neighbor not in path:
                path.append(neighbor)
                dfs(neighbor, path)
                path.pop()
    
    dfs(root, [root])

    try:
        domain_name = urlparse(root).netloc.replace('www.', '').split('.')[0] or root
    except:
        domain_name = root
    
    formatted_paths = {}
    for i, path in enumerate(all_paths):
        cleaned_path = []
        for url in path:
            if '?' in url:
                cleaned_url = url.split('?')[0]
                cleaned_path.append(cleaned_url)
            else:
                cleaned_path.append(url)
        
        formatted_paths[str(i)] = {
            "path": cleaned_path,
            "length": len(cleaned_path),
            "name": domain_name
        }
    
    return {"paths": formatted_paths}

def process_website(website_name: str, base_dir: str, output_dir: str) -> str:
    graph_file = locate_graph_file(website_name, base_dir)
    with open(graph_file, 'r') as f:
        graph_data = json.load(f)
    graph = nx.node_link_graph(graph_data, directed=True, edges="links")

    paths_data = compute_paths(graph)
    
    if website_name.startswith('http'):
        parsed = urlparse(website_name)
        website_filename = parsed.netloc.replace('.', '_').replace('www_', '')
    else:
        website_filename = website_name
    
    output_file = os.path.join(output_dir, f"{website_filename}_all_paths.json")
    with open(output_file, 'w') as f:
        json.dump(paths_data, f, indent=2)
    
    return output_file

def extract_batch(batch_dir: str, output_dir: str) -> list:
    if not os.path.exists(batch_dir):
        raise FileNotFoundError(f"Batch directory not found: {batch_dir}")
    
    os.makedirs(output_dir, exist_ok=True)
    extracted_files = []
    
    for item in os.listdir(batch_dir):
        item_path = os.path.join(batch_dir, item)
        if os.path.isdir(item_path):
            try:
                output_file = process_website(item, batch_dir, output_dir)
                extracted_files.append(output_file)
            except Exception as e:
                print(f"Error processing {item}: {e}")
    
    return extracted_files

def main():
    parser = argparse.ArgumentParser(description='Batch path extraction from website graphs')
    parser.add_argument('--batch_directory', '-b', help='Directory containing website subdirectories', required=True)
    parser.add_argument('--output_directory', '-o', help='Directory to save the extracted paths', required=True)
    
    args = parser.parse_args()
    
    try:
        extract_batch(args.batch_directory, args.output_directory)
    except Exception as e:
        print(f"Error: {e}")
        return 1
    return 0

if __name__ == '__main__':
    exit(main())