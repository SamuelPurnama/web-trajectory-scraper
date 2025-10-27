#!/usr/bin/env python3
"""
Website Explorer - Chains crawling, analysis, and graph building with BFS exploration
"""

import os
import json
import networkx as nx
from collections import deque
from urllib.parse import urlparse
import argparse
from typing import Set, Dict, List, Tuple
import time
import re
from pyvis.network import Network

from webgraph_utils import get_accessibility_tree_simple, get_filename_from_url, json_to_readable_txt, analyze_txt_file

class WebsiteExplorer:
    def __init__(self, max_depth: int = 3, output_dir: str = "website_exploration", max_items: int = 10, depth_max_items: str = None):
        self.max_depth = max_depth
        self.output_dir = output_dir
        self.max_items = max_items
        
        # Parse depth-specific max_items
        if depth_max_items:
            self.depth_max_items = [int(x.strip()) for x in depth_max_items.split(',')]
            while len(self.depth_max_items) < max_depth:
                self.depth_max_items.append(self.depth_max_items[-1] if self.depth_max_items else max_items)
        else:
            self.depth_max_items = [max_items] * max_depth
        
        self.blacklist: Set[str] = set()
        self.unselected_urls: Set[str] = set()
        self.graph = nx.DiGraph()
        self.visited_urls: Set[str] = set()
        self.processing_urls: Set[str] = set()
        self.url_to_filename: Dict[str, str] = {}
        self.website_dir = None
        self.start_url = None
        self.llm_calls_count = 0
        
    def _setup_website_directory(self, start_url: str):
        """Create a directory for the specific website"""

        base = get_filename_from_url(start_url)
        self.website_dir = os.path.join(self.output_dir, base)
        subdirs = ["axtree_json", "llm_input", "llm_output", "blacklists", "screenshots", "html"]
        for sub in subdirs:
            path = os.path.join(self.website_dir, sub)
            os.makedirs(path, exist_ok=True)
            setattr(self, f"{sub}_dir", path)
        return self.website_dir

    
    def crawl_and_analyze_url(self, url: str, depth: int) -> List[str]:
        if url in self.visited_urls or url in self.blacklist or url in self.processing_urls:
            return []

        self.processing_urls.add(url)
        try:
            obs = get_accessibility_tree_simple(url)
            if obs is None:
                print(f"Failed to get accessibility tree for {url}")
                return []

            # Generate filename
            url_safe = re.sub(r'[^a-zA-Z0-9_-]', '_', url.replace('://', '_').replace('/', '_').replace('?', '_').replace('&', '_').replace('=', '_'))[:100]
            short_filename = f"depth{depth}_{url_safe}"
            
            # save html
            if "html_content" in obs:
                html_file = os.path.join(self.html_dir, f"{short_filename}.html")
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(obs["html_content"])
            
            # Save json and txt
            json_file = os.path.join(self.axtree_json_dir, f"{short_filename}_axtree.json")
            with open(json_file, 'w') as f:
                json.dump(obs["axtree_object"], f, indent=2)

            txt_file = json_to_readable_txt(json_file, os.path.join(self.llm_input_dir, f"{short_filename}_axtree_summary.txt"))
            filtered_txt_file = self._filter_and_reindex_txt(txt_file, depth)

            # Add start URL to blacklist before LLM analysis
            if depth == 0 and self.start_url:
                self.blacklist.add(self.start_url)

            current_max_items = self.depth_max_items[depth] if depth < len(self.depth_max_items) else self.depth_max_items[-1]
            self.llm_calls_count += 1
            
            result = analyze_txt_file(filtered_txt_file, urlparse(url).netloc, current_max_items, url)
            interesting_links = result.get('links', [])
            reasoning = result.get('reasoning', 'No reasoning provided')
            
            llm_output_file = os.path.join(self.llm_output_dir, f"{short_filename}_llm_output.txt")
            with open(llm_output_file, 'w') as f:
                f.write(f"LLM Reasoning:\n{reasoning}\n\n")
                f.write(f"Selected Links ({len(interesting_links)}):\n")
                for i, link in enumerate(interesting_links, 1):
                    f.write(f"{i}. {link}\n")

            verified_urls = self._extract_and_verify_urls(filtered_txt_file, interesting_links)

            urls_to_explore = [url for url in verified_urls 
                             if url not in self.blacklist and url not in self.graph]

            # Limit to max_items
            if len(urls_to_explore) > current_max_items:
                urls_to_explore = urls_to_explore[:current_max_items]

            self._add_to_graph(url, urls_to_explore, depth)
            self._add_unselected_to_blacklist(filtered_txt_file, interesting_links)
            
            self.blacklist.add(url)
            self.visited_urls.add(url)
            self.processing_urls.remove(url)
            return urls_to_explore

        except Exception as e:
            print(f"Error processing {url}: {e}")
            self.visited_urls.add(url)
            self.processing_urls.discard(url)
            return []


    def _extract_urls_from_txt(self, txt_file: str) -> Dict[str, str]:
        """Extract URLs from TXT file and return as dict mapping URL to text"""
        with open(txt_file, 'r') as f:
            content = f.read()
        
        return {match.group(2).strip(): match.group(1).strip() 
                for match in re.finditer(r'\s*\d+\.\s*(.*?)\s*->\s*(https?://[^\s]+)', content)}
    
    def _filter_and_reindex_txt(self, txt_file: str, depth: int) -> str:
        """Filter out URLs that are already in the graph or blacklisted and reindex the TXT file"""
        try:
            with open(txt_file, 'r') as f:
                content = f.read()
            
            filtered_lines = []
            new_index = 1
            
            for line in content.split('\n'):
                match = re.search(r'\s*\d+\.\s*(.*?)\s*->\s*(https?://[^\s]+)', line)
                if match:
                    text, url = match.groups()
                    url = url.strip()
                    
                    if url not in self.graph and url not in self.blacklist and url not in self.unselected_urls:
                        filtered_lines.append(f"  {new_index}. {text.strip()} -> {url}")
                        new_index += 1
                else:
                    filtered_lines.append(line)
            
            filtered_txt_file = txt_file.replace('_axtree_summary.txt', '_filtered_axtree_summary.txt')
            with open(filtered_txt_file, 'w') as f:
                f.write('\n'.join(filtered_lines))
            
            return filtered_txt_file
        except Exception as e:
            print(f"Error filtering and reindexing TXT: {e}")
            return txt_file
    
    def _extract_and_verify_urls(self, txt_file: str, llm_links: List[str]) -> List[str]:
        """Extract URLs from LLM output and verify they exist in the TXT file"""
        try:
            txt_url_map = self._extract_urls_from_txt(txt_file)
            txt_urls = set(txt_url_map.keys())
            
            # Extract URLs from LLM output
            llm_urls = []
            for link in llm_links:
                if ' -> ' in link:
                    llm_urls.append(link.split(' -> ')[1].strip())
                else:
                    url_match = re.search(r'https?://[^\s]+', link)
                    if url_match:
                        llm_urls.append(url_match.group(0))
            
            # hallucination check
            verified_urls = []
            hallucinated_urls = []
            
            for llm_url in llm_urls:
                if llm_url in txt_urls:
                    verified_urls.append(llm_url)
                else:
                    # More strict partial matching - only allow if the core path matches
                    found_match = False
                    for txt_url in txt_urls:
                        llm_domain = urlparse(llm_url).netloc
                        txt_domain = urlparse(txt_url).netloc
                        
                        if llm_domain == txt_domain:
                            # Check if the path is substantially similar (not just a substring)
                            llm_path = urlparse(llm_url).path
                            txt_path = urlparse(txt_url).path
                            
                            if (llm_path == txt_path or 
                                (len(llm_path) > 10 and llm_path in txt_path) or
                                (len(txt_path) > 10 and txt_path in llm_path)):
                                verified_urls.append(txt_url)
                                found_match = True
                                break
                    
                    if not found_match:
                        hallucinated_urls.append(llm_url)

            return verified_urls
            
        except Exception as e:
            print(f"Error extracting and verifying URLs: {e}")
            return []
    
    def _add_unselected_to_blacklist(self, txt_file: str, selected_links: List[str]):
        """Add unselected URLs to unselected_urls set"""
        try:
            txt_url_map = self._extract_urls_from_txt(txt_file)
            all_urls = set(txt_url_map.keys())
            
            # Extract selected URLs
            selected_urls = set()
            for link in selected_links:
                if ' -> ' in link:
                    selected_urls.add(link.split(' -> ')[1].strip())
                else:
                    url_match = re.search(r'https?://[^\s]+', link)
                    if url_match:
                        selected_urls.add(url_match.group(0))
            
            # Add unselected URLs
            unselected = {url for url in all_urls 
                         if not any(url == selected_url or url in selected_url or selected_url in url 
                                  for selected_url in selected_urls)}
            
            self.unselected_urls.update(unselected)
        except Exception as e:
            print(f"Error updating URL lists: {e}")
    
    def _merge_unselected_to_blacklist(self):
        """Merge unselected_urls to blacklist and clear unselected_urls"""
        if self.unselected_urls:
            self.blacklist.update(self.unselected_urls)
            self.unselected_urls.clear()
    
    def _save_blacklist_for_depth(self, depth: int):
        """Save the current blacklist to a file for the specified depth"""
        if hasattr(self, 'blacklists_dir'):
            blacklist_file = os.path.join(self.blacklists_dir, f"depth{depth}_blacklist.txt")
            with open(blacklist_file, 'w') as f:
                f.write(f"Blacklist after completing depth {depth}\n")
                f.write(f"Total blacklisted URLs: {len(self.blacklist)}\n")
                f.write("=" * 50 + "\n\n")
                for url in sorted(self.blacklist):
                    f.write(f"{url}\n")
    
    def _add_to_graph(self, source_url: str, target_urls: List[str], depth: int):
        """Add nodes and edges to the graph layer by layer"""
        if source_url not in self.graph:
            self.graph.add_node(source_url, depth=depth, type='source')
        
        for target_url in target_urls:
            if target_url not in self.graph:
                self.graph.add_node(target_url, depth=depth + 1, type='target')
            self.graph.add_edge(source_url, target_url, depth=depth)
    
    def _print_node_children(self):
        """Print the number of nodes without children (leaf nodes)"""
        leaf_nodes = sum(1 for node in self.graph.nodes() if not list(self.graph.successors(node)))
        print(f"Number of nodes without children: {leaf_nodes}")
    
    def explore_website(self, start_url: str) -> nx.DiGraph:
        """Main exploration function using BFS"""
        print(f"Starting website exploration from: {start_url}")
        
        self.start_url = start_url
        website_dir = self._setup_website_directory(start_url)
        
        queue = deque([(start_url, 0)])
        current_depth = 0

        while queue:
            current_url, depth = queue.popleft()

            if depth > current_depth:
                self._merge_unselected_to_blacklist()
                self._save_blacklist_for_depth(current_depth)
                current_depth = depth
            
            if depth >= self.max_depth:
                print(f"Max depth reached for {current_url} (depth {depth}), skipping LLM analysis")
                continue
            
            interesting_links = self.crawl_and_analyze_url(current_url, depth)
            added_to_queue = 0
            
            if depth + 1 < self.max_depth:
                for link in interesting_links:
                    if link not in self.blacklist and link not in self.visited_urls:
                        queue.append((link, depth + 1))
                        added_to_queue += 1
        
        self._merge_unselected_to_blacklist()
        self._save_blacklist_for_depth(current_depth)
        
        print(f"\nExploration complete!")
        print(f"Total nodes: {self.graph.number_of_nodes()}")
        
        self._print_node_children()
        return self.graph
    
    def save_graph(self, start_url: str, filename: str = None):
        """Save the graph to files"""
        if filename is None:
            filename_base = get_filename_from_url(start_url)
            timestamp = int(time.time())
            filename = f"{filename_base}_website_graph_{timestamp}"
        
        if self.website_dir is None:
            self._setup_website_directory(start_url)
        
        files_to_save = [
            (f"{filename}.json", lambda f: json.dump(nx.node_link_data(self.graph, edges="links"), f, indent=2)),
            (f"{filename}_blacklist.txt", lambda f: f.write('\n'.join(sorted(self.blacklist)))),
            (f"{filename}_visited.txt", lambda f: f.write('\n'.join(sorted(self.visited_urls))))
        ]
        
        for file_name, write_func in files_to_save:
            with open(os.path.join(self.website_dir, file_name), 'w') as f:
                write_func(f)
        
        return os.path.join(self.website_dir, f"{filename}.json")
    
    def visualize_graph(self, start_url: str):
        """Create and save a visualization of the graph using pyvis"""
        if self.graph.number_of_nodes() == 0:
            return None
        
        # make the graph -- pyvis code
        net = Network(width=1000, height=1000, directed=True)
        net.from_nx(self.graph)
        
        depth_colors = ['#0072BB', '#2ECC71', '#FF9F40', '#9B59B6', '#E74C3C']
        
        for node in net.nodes:
            node['size'] = 15
            node['label'] = ''
            depth = self.graph.nodes[node['id']].get('depth', 0)
            node_type = self.graph.nodes[node['id']].get('type', 'unknown')
            node['color'] = depth_colors[min(depth, len(depth_colors) - 1)]
            node['title'] = f'Depth {depth} ({node_type}): <a href="{node["id"]}" target="_blank">{node["id"]}</a>'
        
        for edge in net.edges:
            edge['color'] = '#666666'
            edge['width'] = 2
        
        timestamp = int(time.time())
        filename_base = os.path.basename(self.website_dir)
        save_path = os.path.join(self.website_dir, f"{filename_base}_website_graph_{timestamp}.html")
        
        net.save_graph(save_path)
        return save_path

def main():
    parser = argparse.ArgumentParser(description='Explore website structure with BFS and LLM analysis')
    parser.add_argument('start_url', help='Starting URL for exploration')
    parser.add_argument('--max-depth', type=int, default=2, help='Maximum exploration depth (default: 2)')
    parser.add_argument('--max-items', type=int, default=5, help='Maximum number of interesting links per page (default: 5)')
    parser.add_argument('--depth-max-items', type=str, help='Comma-separated list of max_items per depth (e.g., "10,5,2")')
    parser.add_argument('--output-dir', default='website_exploration', help='Output directory (default: website_exploration)')
    
    args = parser.parse_args()
    
    # create explorer and run
    explorer = WebsiteExplorer(max_depth=args.max_depth, output_dir=args.output_dir, 
                              max_items=args.max_items, depth_max_items=args.depth_max_items)
    
    graph = explorer.explore_website(args.start_url)
    explorer.save_graph(args.start_url)
    explorer.visualize_graph(args.start_url)
    
    print("\nExploration complete!")

if __name__ == '__main__':
    main() 

'''
Usage:

python3 -m website_explorer https://allrecipes.com --max-depth 2 --depth-max-items "5,3"

'''