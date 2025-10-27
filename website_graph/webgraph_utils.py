'''
Utils for website exploration.

'''

import json
import os
import re
import urllib.parse
from typing import List
from bs4 import BeautifulSoup
import ell
from pydantic import BaseModel, Field
import os, json, time, random, pathlib, urllib.parse as ul
from playwright.sync_api import sync_playwright
from browserbase import Browserbase

API, PROJ = os.environ["BROWSERBASE_API_KEY"], os.environ["BROWSERBASE_PROJECT_ID"]
CAPTCHA_WAIT_MS = 10000

def json_to_readable_txt(json_file_path, output_file_path=None):
    """Convert a JSON axtree file to a readable TXT summary"""
    with open(json_file_path, 'r') as f:
        data = json.load(f)
    
    nodes = data.get("nodes", [])
    
    # Extract all urls withoput duplicates 
    all_urls = []
    seen_urls = set()
    for node in nodes:
        name = node.get("name", {}).get("value", "")
        if "[URL:" in name:
            parts = name.split(" | ")
            text_part = parts[0] if parts[0] != "Link" else ""
            url_part = ""
            for part in parts:
                if part.startswith("[URL:"):
                    url_part = part[5:-1]  # Remove [URL: and ]
                    break
            
            if url_part and url_part not in seen_urls:
                all_urls.append((text_part, url_part))
                seen_urls.add(url_part)
    
    lines = [
        "Accessibility Tree Summary",
        "=" * 50,
        f"Total nodes: {len(nodes)}",
        ""
    ]
    
    if all_urls:
        lines.extend([
            f"ALL URLs FOUND ({len(all_urls)} total):",
            "-" * 50
        ])
        for i, (text, url) in enumerate(all_urls, 1):
            display_text = text if text and text != "Link" else "Link"
            lines.append(f"{i:3d}. {display_text} -> {url}")
        lines.append("")
    
    lines.append(f"Total URLs: {len(all_urls)}")
    
    if output_file_path is None:
        output_file_path = json_file_path.replace('.json', '_summary.txt')
    
    with open(output_file_path, 'w') as f:
        f.write('\n'.join(lines))
    
    return output_file_path

def get_filename_from_url(url):
    """Generate a filename from URL"""
    parsed = urllib.parse.urlparse(url)
    return parsed.netloc.replace('.', '_').replace('www_', '')

# the fucntions below are used to create the axtree_object

def _create_element_node(element, url, node_id, role, name_parts):
    """Create a node for an element with common structure"""
    node = {
        "nodeId": str(node_id),
        "role": {"value": role},
        "name": {"value": " | ".join(name_parts)},
        "childIds": [],
        "properties": [{"name": "clickable", "value": {"value": True}}]
    }
    
    element_id = element.get('id')
    if element_id:
        node["browsergym_id"] = element_id
    
    return node

def _create_link_node(link, url, node_id):
    """Create a node for a link element"""
    href = link.get('href')
    text = link.get_text(strip=True)
    
    full_url = href if href.startswith('http') else urllib.parse.urljoin(url, href)
    name_parts = [text if text else "Link", f"[URL: {full_url}]"]
    
    return _create_element_node(link, url, node_id, "link", name_parts)

def _create_button_node(button, node_id):
    """Create a node for a button element"""
    text = button.get_text(strip=True)
    button_type = button.get('type', 'button')
    onclick = button.get('onclick', '')
    
    name_parts = [text if text else "Button", f"[type: {button_type}]"]
    if onclick:
        name_parts.append(f"[onclick: {onclick[:30]}...]")
    
    return _create_element_node(button, None, node_id, "button", name_parts)

def _create_input_node(input_elem, node_id):
    """Create a node for an input element"""
    input_type = input_elem.get('type', 'text')
    placeholder = input_elem.get('placeholder', '')
    name_attr = input_elem.get('name', '')
    
    name_parts = [f"Input {name_attr}" if name_attr else "Input", f"[type: {input_type}]"]
    if placeholder:
        name_parts.append(f"[placeholder: {placeholder}]")
    
    properties = [{"name": "clickable", "value": {"value": True}}]
    if input_elem.get('required'):
        properties.append({"name": "required", "value": {"value": True}})
    if input_elem.get('disabled'):
        properties.append({"name": "disabled", "value": {"value": True}})
    
    node = _create_element_node(input_elem, None, node_id, f"input-{input_type}", name_parts)
    node["properties"] = properties
    return node

def _create_form_node(form, node_id):
    """Create a node for a form element"""
    action = form.get('action', '')
    method = form.get('method', 'get')
    
    name_parts = ["Form"]
    if action:
        name_parts.append(f"[action: {action}]")
    name_parts.append(f"[method: {method}]")
    
    return _create_element_node(form, None, node_id, "form", name_parts)

def _grab_html(url):
    with sync_playwright() as pw:
        sess = Browserbase(api_key=API).sessions.create(
            project_id=PROJ,
            proxies=True,
            browser_settings={"advanced_stealth": True, "solve_captchas": True},
        )
        br = pw.chromium.connect_over_cdp(sess.connect_url)
        pg = br.contexts[0].pages[0]

        solved = {"ok": False}
        pg.on("console", lambda m: m.text == "browserbase-solving-finished" and solved.update(ok=True))

        pg.set_extra_http_headers({"Accept-Language": "en-US,en;q=0.9"})
        # pg.set_viewport_size({"width": 1280, "height": 800})
        pg.evaluate("""() => {
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        }""")

        for w in ("domcontentloaded", "load", "networkidle"):
            try:
                pg.goto(url, wait_until=w, timeout=90000)
                break
            except:
                continue

        if not solved["ok"]:
            pg.wait_for_timeout(CAPTCHA_WAIT_MS)

        html = pg.evaluate("() => document.documentElement.outerHTML")
        br.close()
        return html

def get_accessibility_tree_simple(url, out_dir=None, limit=1000):
    html_text = _grab_html(url)  
    soup = BeautifulSoup(html_text,"html.parser")

    nodes = []
    node_id_counter = 0
    
    def create_node(element, parent_id=None):
        nonlocal node_id_counter
        
        tag_name = element.name if element.name else 'text'
        
        # Determine role
        role_map = {
            'a': 'link', 'button': 'button', 'img': 'image',
            'h1': 'heading', 'h2': 'heading', 'h3': 'heading',
            'h4': 'heading', 'h5': 'heading', 'h6': 'heading'
        }
        role = role_map.get(tag_name, 'generic')
        if tag_name == 'input':
            role = f'input-{element.get("type", "text")}'
        
        # Build enhanced name
        text_content = element.get_text(strip=True) if element.name else str(element)
        name_parts = []
        
        if text_content:
            name_parts.append(text_content[:50])
        
        # Add specific attributes based on element type
        if tag_name == 'a' and element.get('href'):
            href = element.get('href')
            full_url = href if href.startswith('http') else urllib.parse.urljoin(url, href)
            name_parts.append(f"[URL: {full_url}]")
        elif tag_name == 'button':
            button_type = element.get('type', 'button')
            onclick = element.get('onclick', '')
            if onclick:
                name_parts.append(f"[onclick: {onclick[:30]}...]")
            name_parts.append(f"[type: {button_type}]")
        elif tag_name == 'input':
            input_type = element.get('type', 'text')
            placeholder = element.get('placeholder', '')
            name_parts.append(f"[type: {input_type}]")
            if placeholder:
                name_parts.append(f"[placeholder: {placeholder}]")
        elif tag_name == 'img':
            src = element.get('src', '')
            alt = element.get('alt', '')
            if src:
                name_parts.append(f"[src: {src}]")
            if alt:
                name_parts.append(f"[alt: {alt}]")
        elif tag_name == 'form':
            action = element.get('action', '')
            method = element.get('method', 'get')
            if action:
                name_parts.append(f"[action: {action}]")
            name_parts.append(f"[method: {method}]")
        elif tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            name_parts.append(f"[level: {tag_name[1]}]")
        
        # Create node
        node = {
            "nodeId": str(node_id_counter),
            "role": {"value": role},
            "name": {"value": " | ".join(name_parts) if name_parts else f"{tag_name} element"},
            "childIds": []
        }
        
        if element.get('id'):
            node["browsergym_id"] = element.get('id')
        
        # Add properties
        properties = []
        if tag_name in ['button', 'a', 'input']:
            properties.append({"name": "clickable", "value": {"value": True}})
        if tag_name == 'input' and element.get('required'):
            properties.append({"name": "required", "value": {"value": True}})
        if element.get('disabled'):
            properties.append({"name": "disabled", "value": {"value": True}})
        
        if properties:
            node["properties"] = properties
        
        nodes.append(node)
        current_id = node_id_counter
        node_id_counter += 1
        
        # Process children (limit to avoid too many nodes)
        if node_id_counter < 1000:
            for child in element.children:
                if child.name:
                    child_id = create_node(child, current_id)
                    if child_id is not None:
                        node["childIds"].append(str(child_id))
                elif child.string and child.string.strip():
                    text_node = {
                        "nodeId": str(node_id_counter),
                        "role": {"value": "StaticText"},
                        "name": {"value": child.string.strip()},
                        "childIds": []
                    }
                    nodes.append(text_node)
                    node["childIds"].append(str(node_id_counter))
                    node_id_counter += 1
        
        return current_id
    
    interactive_elements = []
    element_processors = [
        ('a[href]', _create_link_node),
        ('button', _create_button_node),
        ('input', _create_input_node),
        ('form', _create_form_node)
    ]
    
    for selector, processor in element_processors:
        for element in soup.select(selector):
            if selector == 'a[href]':
                nodes.append(processor(element, url, node_id_counter))
            else:
                nodes.append(processor(element, node_id_counter))
            interactive_elements.append(node_id_counter)
            node_id_counter += 1
    
    body = soup.find('body') or soup.find('html') or soup
    create_node(body)
    
    obs = {
        "axtree_object": {"nodes": nodes, "rootId": "0"},
        "extra_element_properties": {},
        "html_content": html_text
    }
    
    # print(f"Accessibility tree created with {len(nodes)} nodes")
    return obs


def analyze_txt_file(txt_file_path: str, website_name: str = None, max_items: int = 10, current_url: str = None) -> dict:
    """Analyze a txt file containing URLs and return interesting links"""
    if website_name is None:
        filename = txt_file_path.split('/')[-1]
        website_name = filename.replace('_axtree_summary.txt', '').replace('_', ' ').title()
    
    url_list = extract_urls_from_txt(txt_file_path)
    
    if not url_list:
        return {"links": [], "reasoning": "No URLs found in the file"}
    
    get_interesting_links = get_link_analyzer(max_items=max_items)
    return get_interesting_links(url_list, website_name, max_items, current_url)

def get_link_analyzer(max_items: int = 10):
    class InterestingLinks(BaseModel):
        links: List[str] = Field(
            description=f"List of {max_items} most interesting URLs for web agent navigation",
            max_items=max_items
        )
        reasoning: str = Field(description="Brief explanation of why these links were selected")

    @ell.complex(model="gpt-4o", response_format=InterestingLinks, temperature=1)
    def analyze_links(url_list_text: str, website_name: str, current_url: str = None):
        return [
            ell.system(
                "You are an expert web navigation analyst. Your job is to identify the most strategically important "
                "links for a web agent that needs to explore diverse use cases of a website. "
                "Focus on central navigation nodes that provide access to new functionality, content categories, "
                "or user flows. Avoid duplicate functionality and prioritize links that open up new areas of the site."
            ),
            ell.user(
                f"Analyze this list of URLs from {website_name} and select the {max_items} most interesting links "
                f"for a web agent to explore. The agent needs to cover diverse and common use cases.\n\n"
                f"Current page: {current_url or 'Unknown'}\n\n"
                f"Look for:\n"
                f"- Main navigation/category pages\n"
                f"- Search and discovery features\n"
                f"- User account/authentication flows\n"
                f"- Content browsing sections\n"
                f"- Interactive features\n"
                f"- Avoid duplicates and similar functionality\n\n"
                f"IMPORTANT RULES:\n"
                f"- DO NOT select the current page URL (if it appears in the list)\n"
                f"- DO NOT select the main/home page or root URL of the website\n"
                f"- DO NOT propose pages that lead to login pages (URLs containing 'authentication/login' or similar login-related paths)\n"
                f"- DO NOT propose URLs that are just the same page with a fragment identifier (e.g., if you see 'https://example.com/page/' and 'https://example.com/page/#main', only select one of them)\n"
                f"- Avoid URLs that would likely show the same content as the current page\n\n"
                f"- DO NOT propose URLS that werent supplied to you in the URL lis. Any URL you respond with must be in the list. \n"
                f"URL List:\n{url_list_text}\n\n"
                f"Select exactly {max_items} URLs that would give the agent the best coverage of the website's functionality."
            ),
        ]

    def get_interesting_links(url_list_text: str, website_name: str = "the website", max_items: int = 10, current_url: str = None) -> dict:
        """Analyze URL list and return most interesting links for web agent navigation"""
        try:
            result = analyze_links(url_list_text, website_name, current_url).parsed
            return {"links": result.links, "reasoning": result.reasoning}
        except Exception as e:
            print(f"Error analyzing links: {e}")
            return {"links": [], "reasoning": f"Error occurred: {e}"}

    return get_interesting_links

def extract_urls_from_txt(txt_file_path: str) -> str:
    """Extract URLs from the txt file and return as formatted text"""
    try:
        with open(txt_file_path, 'r') as f:
            content = f.read()
        
        urls = []
        for match in re.finditer(r'\s*\d+\.\s*(.*?)\s*->\s*(https?://[^\s]+)', content):
            text, url = match.groups()
            urls.append(f"{text.strip()} -> {url.strip()}")
        
        return "\n".join(urls)
    
    except Exception as e:
        print(f"Error reading file {txt_file_path}: {e}")
        return ""