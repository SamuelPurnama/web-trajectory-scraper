#!/usr/bin/env python3
"""
Enhanced Website Exploration - Gathers context from main page and child pages
for comprehensive website task generation using Playwright's native accessibility trees.
"""

import os
import re
import requests
from urllib.parse import urlparse, urljoin
from typing import List, Dict, Set, Optional
from pathlib import Path
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Look for .env file in the parent directory (root of the project)
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"Loaded environment variables from {env_path}")
    else:
        # Fallback to current directory
        load_dotenv()
        print("Loaded environment variables from .env file in current directory")
except ImportError:
    print("python-dotenv not available, using system environment variables only")

class ContextGatherer:
    """Gathers context from main page and 3 child pages using Playwright's native accessibility trees."""
    
    def __init__(self, max_additional_pages: int = 3, output_dir: str = None, 
                 screenshot_mode: str = "multiple"):
        """
        Initialize the ContextGatherer.
        
        Args:
            max_additional_pages: Maximum number of child pages to analyze (default: 3)
            output_dir: Directory to save files (optional)
            screenshot_mode: Screenshot behavior - "none", "single", or "multiple"
        """
        self.max_additional_pages = max_additional_pages
        self.output_dir = Path(output_dir) if output_dir else None
        self.visited_urls: Set[str] = set()
        self.blacklist: Set[str] = set()
        self.screenshot_mode = screenshot_mode
        
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        parsed = urlparse(url)
        domain = parsed.netloc
        # Remove www. prefix if present
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    
    def _take_single_screenshot(self, url: str, output_path: str) -> bool:
        """Take a single viewport screenshot of the webpage."""
        try:
            # Set up Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # Create driver
            driver = webdriver.Chrome(options=chrome_options)
            
            # Navigate to URL
            driver.get(url)
            
            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Wait a bit more for dynamic content to load
            time.sleep(2)
            
            # Take screenshot (viewport only)
            driver.save_screenshot(output_path)
            driver.quit()
            
            print(f"    Single screenshot saved: {output_path}")
            return True
            
        except Exception as e:
            print(f"    Error taking screenshot of {url}: {e}")
            return False
    
    def _take_screenshots(self, url: str, output_dir: str) -> List[str]:
        """Take multiple strategic screenshots of the webpage."""
        screenshots = []
        try:
            # Set up Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # Create driver
            driver = webdriver.Chrome(options=chrome_options)
            
            # Navigate to URL
            driver.get(url)
            
            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Wait a bit more for dynamic content to load
            time.sleep(2)
            
            # Get page dimensions
            total_height = driver.execute_script("return document.body.scrollHeight")
            viewport_height = driver.execute_script("return window.innerHeight")
            
            # Calculate number of screenshots needed to cover entire page (max 9)
            num_screenshots = min(9, max(1, (total_height + viewport_height - 1) // viewport_height))
            
            # Generate scroll positions to cover the entire page
            scroll_positions = []
            for i in range(num_screenshots):
                scroll_pos = i * viewport_height
                scroll_positions.append(scroll_pos)
            
            for i, scroll_pos in enumerate(scroll_positions):
                # Scroll to position
                driver.execute_script(f"window.scrollTo(0, {scroll_pos});")
                time.sleep(1)  # Wait for scroll to complete
                
                # Take screenshot
                screenshot_path = f"{output_dir}/section_{i+1}.png"
                driver.save_screenshot(screenshot_path)
                screenshots.append(screenshot_path)
                
                print(f"    Screenshot {i+1} saved: {screenshot_path} (scroll: {scroll_pos}px)")
            
            driver.quit()
            return screenshots
            
        except Exception as e:
            print(f"    Error taking screenshots of {url}: {e}")
            return []
    
    def _get_playwright_axtree(self, url: str) -> Dict:
        """Get Playwright's native accessibility tree for a URL."""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                # Set user agent
                page.set_extra_http_headers({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                })
                
                # Navigate to URL
                page.goto(url, wait_until='networkidle', timeout=30000)
                
                # Wait for page to load
                page.wait_for_timeout(2000)
                
                # Get Playwright's native accessibility tree
                axtree = page.accessibility.snapshot()
                
                browser.close()
                return axtree
                
        except Exception as e:
            print(f"Error getting Playwright axtree for {url}: {e}")
            return None

    def _get_html_content(self, url: str) -> str:
        """Get HTML content from URL using Playwright to handle JavaScript-rendered content."""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                # Set user agent
                page.set_extra_http_headers({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                })
                
                # Navigate to URL
                page.goto(url, wait_until='networkidle', timeout=30000)
                
                # Wait for page to load
                page.wait_for_timeout(3000)
                
                # Get the HTML content
                html_content = page.content()
                
                browser.close()
                return html_content
                
        except Exception as e:
            print(f"Error fetching {url} with Playwright: {e}")
            # Fallback to requests if Playwright fails
            return self._get_html_content_fallback(url)
    
    def _get_html_content_fallback(self, url: str) -> str:
        """Fallback method to get HTML content using requests."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # Check if this is a booking.com pxgo redirect URL
            if 'booking.com/pxgo' in url and 'url=' in url:
                # Extract the target URL from the redirect
                from urllib.parse import urlparse, parse_qs
                parsed = urlparse(url)
                query_params = parse_qs(parsed.query)
                if 'url' in query_params:
                    target_url = query_params['url'][0]
                    print(f"  Detected redirect URL, following to: {target_url}")
                    # Try to get content from the target URL instead
                    response = requests.get(target_url, headers=headers, timeout=10, allow_redirects=True)
                    response.raise_for_status()
                    return response.text
            
            # Follow redirects to get the actual content
            response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
            response.raise_for_status()
            
            # Check if we got meaningful content (not just a redirect page)
            if len(response.text) < 1000:  # Very short content likely means redirect page
                print(f"  Warning: Short content ({len(response.text)} chars) from {url}")
                print(f"  Final URL: {response.url}")
            
            return response.text
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return ""
    
    def _calculate_navbar_score(self, element, soup) -> float:
        """
        Calculate a score indicating how likely an element is to be in a main navigation bar.
        
        Args:
            element: BeautifulSoup element
            soup: BeautifulSoup object for context
            
        Returns:
            Score from 0.0 to 1.0 (higher = more likely to be in navbar)
        """
        score = 0.0
        
        # Check element's own classes and attributes
        classes = element.get('class', [])
        class_str = ' '.join(classes).lower()
        
        # High-priority navbar indicators
        navbar_indicators = [
            'navbar', 'nav-bar', 'main-nav', 'primary-nav', 'top-nav', 
            'header-nav', 'site-nav', 'global-nav', 'primary-menu',
            'main-menu', 'top-menu', 'header-menu'
        ]
        
        for indicator in navbar_indicators:
            if indicator in class_str:
                score += 0.3
        
        # Check parent containers
        parent = element.parent
        depth = 0
        while parent and depth < 5:  # Check up to 5 levels up
            parent_classes = parent.get('class', [])
            parent_class_str = ' '.join(parent_classes).lower()
            
            # Check for navbar container classes
            for indicator in navbar_indicators:
                if indicator in parent_class_str:
                    score += 0.2 * (1.0 - depth * 0.1)  # Decrease with depth
            
            # Check for semantic HTML elements
            if parent.name in ['nav', 'header']:
                score += 0.15 * (1.0 - depth * 0.1)
            
            # Check for role attributes
            if parent.get('role') == 'navigation':
                score += 0.1 * (1.0 - depth * 0.1)
            
            parent = parent.parent
            depth += 1
        
        # Check element position (header area is more likely to be navbar)
        try:
            # Simple heuristic: elements closer to top of page are more likely navbar
            all_elements = soup.find_all(['a', 'button'])
            element_index = all_elements.index(element) if element in all_elements else len(all_elements)
            position_score = max(0, 1.0 - (element_index / len(all_elements)) * 0.5)
            score += position_score * 0.1
        except:
            pass
        
        # Check for common navbar text patterns
        text = element.get_text(strip=True).lower()
        navbar_text_patterns = [
            'home', 'about', 'contact', 'products', 'services', 'shop', 'store',
            'recipes', 'menu', 'categories', 'browse', 'explore', 'news', 'blog'
        ]
        
        for pattern in navbar_text_patterns:
            if pattern in text:
                score += 0.05
        
        # Check element styling hints (if available)
        style = element.get('style', '').lower()
        if any(style_hint in style for style_hint in ['display: flex', 'display: inline', 'float:']):
            score += 0.05
        
        return min(1.0, score)  # Cap at 1.0

    def _extract_navigation_elements(self, html_content: str, base_url: str) -> List[Dict[str, str]]:
        """
        Extract navigation elements from HTML content with navbar scoring.
        
        Args:
            html_content: HTML content of the page
            base_url: Base URL for resolving relative links
            
        Returns:
            List of navigation elements with text, URL, and navbar score
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        navigation_elements = []
        
        # Look for common navigation selectors
        nav_selectors = [
            'nav a', 'header a', '.navbar a', '.navigation a', '.menu a',
            '.nav a', '.main-nav a', '.primary-nav a', '.top-nav a',
            '.site-nav a', '.global-nav a', '.header-nav a'
        ]
        
        # Also look for links in common navigation containers
        nav_containers = [
            'nav', 'header', '[role="navigation"]', '.navbar', '.navigation',
            '.nav', '.main-nav', '.primary-nav', '.top-nav', '.site-nav',
            '.global-nav', '.header-nav', '.menu'
        ]
        
        found_links = set()
        
        # Extract links from navigation selectors
        for selector in nav_selectors:
            for element in soup.select(selector):
                href = element.get('href')
                text = element.get_text(strip=True)
                
                if href and text and len(text) < 100:  # Reasonable text length
                    # Resolve relative URLs
                    full_url = urljoin(base_url, href)
                    
                    # Avoid duplicates
                    if full_url not in found_links:
                        found_links.add(full_url)
                        navbar_score = self._calculate_navbar_score(element, soup)
                        navigation_elements.append({
                            "text": text,
                            "url": full_url,
                            "navbar_score": navbar_score
                        })
        
        # Extract links from navigation containers
        for container_selector in nav_containers:
            for container in soup.select(container_selector):
                for link in container.find_all('a', href=True):
                    href = link.get('href')
                    text = link.get_text(strip=True)
                    
                    if href and text and len(text) < 100:
                        full_url = urljoin(base_url, href)
                        
                        if full_url not in found_links:
                            found_links.add(full_url)
                            navbar_score = self._calculate_navbar_score(link, soup)
                            navigation_elements.append({
                                "text": text,
                                "url": full_url,
                                "navbar_score": navbar_score
                            })
        
        # Sort by navbar score (highest first) to prioritize main navbar elements
        navigation_elements.sort(key=lambda x: x['navbar_score'], reverse=True)
        
        return navigation_elements
    
    
    def _is_valid_navigation_url(self, url: str, base_domain: str, main_page_url: str = None) -> bool:
        """Check if URL is valid for navigation context gathering."""
        parsed = urlparse(url)
        url_domain = parsed.netloc
        
        # Remove www. prefix for comparison
        if url_domain.startswith('www.'):
            url_domain = url_domain[4:]
        if base_domain.startswith('www.'):
            base_domain = base_domain[4:]
            
        # Must be same domain
        if url_domain != base_domain:
            return False
        
        # Skip if it's the main page (already have its axtree)
        if main_page_url:
            main_parsed = urlparse(main_page_url)
            # Compare normalized URLs (remove trailing slashes, query params, fragments)
            url_normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}"
            main_normalized = f"{main_parsed.scheme}://{main_parsed.netloc}{main_parsed.path.rstrip('/')}"
            
            if url_normalized == main_normalized:
                return False
            
        # Skip certain patterns
        skip_patterns = [
            r'/login', r'/signin', r'/auth', r'/register', r'/signup',
            r'/logout', r'/signout', r'/account', r'/profile', r'/settings',
            r'/admin', r'/dashboard', r'/api/', r'/ajax/', r'/json',
            r'\.(pdf|doc|docx|xls|xlsx|ppt|pptx|zip|rar|exe|dmg)$',
            r'#', r'\?.*utm_', r'/search\?', r'/results\?'
        ]
        
        for pattern in skip_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return False
                
        return True
    
    def _analyze_navigation_links(self, navigation_links: List[Dict[str, str]], 
                                website_url: str, base_domain: str, classification: str) -> List[str]:
        """
        Use LLM to analyze and select the most important navigation links.
        
        Args:
            navigation_links: List of navigation links
            website_url: Original website URL
            base_domain: Base domain of the website
            
        Returns:
            List of selected URLs for context gathering
        """
        if not navigation_links:
            return []
        
        # Filter valid URLs (excluding main page)
        valid_links = []
        for link in navigation_links:
            if self._is_valid_navigation_url(link["url"], base_domain, website_url):
                valid_links.append(link)
        
        if not valid_links:
            return []
        
        # Format links for LLM analysis with navbar scores
        links_text = "\n".join([
            f"{i+1}. {link['text']} -> {link['url']} [Navbar Score: {link['navbar_score']:.2f}]"
            for i, link in enumerate(valid_links)
        ])
        
        # Screenshots are taken in the main gather_context method, not here
        
        # Use OpenAI library directly to select most important navigation links
        try:
            from openai import OpenAI
            import json
            
            client = OpenAI()
            
            # Create the prompt for navigation link selection
            system_prompt = (
                "You are an expert web analyst and user experience researcher. Your job is to identify the most important navigation pages "
                "that would provide valuable context for generating comprehensive web automation tasks. "
                "Think like a user: focus on pages that represent the core functionality users actually want to use, "
                "not just what's prominently displayed in navigation. Prioritize functional importance over visual prominence."
            )
            
            user_prompt = (
                f"Website: {website_url}\n\n"
                f"Select the most important navigation links for context gathering. "
                f"Each link shows: [Button Text] -> [URL] [Navbar Score: X.XX]\n\n"
                f"IMPORTANT: Ignore the navbar score - it's just a heuristic. Focus on FUNCTIONAL IMPORTANCE instead.\n\n"
                f"Select links based on these criteria (in order of importance):\n\n"
                f"1. FUNCTIONALITY: Which URLs unlock the most core functionalities of the website?\n"
                f"   - For booking sites: flights, hotels, car rentals (core booking functions)\n"
                f"   - For recipe sites: recipe categories, search, meal planning\n"
                f"   - For e-commerce: product categories, shopping cart, checkout\n"
                f"   - For news sites: article categories, search, archives\n\n"
                f"2. USER BEHAVIOR: Which URLs are users most likely to click and use?\n"
                f"   - Primary user goals and workflows\n"
                f"   - Most common user journeys\n"
                f"   - High-traffic functional areas\n\n"
                f"3. WEBSITE PURPOSE: Which URLs best represent the website's main purpose?\n"
                f"   - Core business functions\n"
                f"   - Primary value propositions\n"
                f"   - Main service offerings\n\n"
                f"AVOID these types of links:\n"
                f"- Legal pages (terms of service, privacy policy)\n"
                f"- Company info (about us, careers, press)\n"
                f"- Authentication (login, sign up, account)\n"
                f"- External or off-site links\n"
                f"- Search results or dynamic content\n"
                f"- Duplicate functionality\n\n"
                f"Available navigation links:\n{links_text}\n\n"
                f"ANALYSIS TIP: Focus on navbar elements and other important page sections. "
                f"Navbar elements are usually at the top of the page and contain the most important navigation links. "
                f"These typically lead to the core functionalities of the website.\n\n"
                f"Select up to {self.max_additional_pages} URLs that would provide the most valuable context "
                f"for understanding the website's core functionality and user workflows. "
                f"Think like a user: what would you actually use this website for?\n\n"
                f"Respond with a JSON object containing:\n"
                f'{{"selected_urls": ["url1", "url2", "url3"], "reasoning": "Brief explanation of why these URLs were selected"}}'
            )
            
            
            # Call OpenAI API directly
            response = client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            # Parse the response
            result_text = response.choices[0].message.content
            result = json.loads(result_text)
            return result.get("selected_urls", [])
            
        except Exception as e:
            print(f"Error in LLM analysis: {e}")
            # Fallback: return first few valid links
            return [link["url"] for link in valid_links[:self.max_additional_pages]]
    
    
    
    def _save_playwright_axtree(self, url: str, axtree_data: Dict, classification: str, 
                               page_type: str = "main") -> str:
        """Save Playwright's native axtree data to file."""
        domain = self._extract_domain(url)
        
        # Determine output directory
        if self.output_dir:
            output_dir = self.output_dir / classification / domain / "playwright_axtree"
        else:
            output_dir = Path(classification) / domain / "playwright_axtree"
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create filename
        if page_type == "main":
            filename = f"{domain}_playwright_axtree.txt"
        else:
            filename = f"{domain}_{page_type}_playwright_axtree.txt"
        
        # Save as readable text
        txt_file = output_dir / filename
        
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(f"=== {page_type.upper().replace('_', ' ')} PAGE PLAYWRIGHT AXTRESS ===\n")
            f.write(f"URL: {url}\n\n")
            
            if axtree_data:
                f.write("ACCESSIBILITY TREE:\n")
                f.write("-" * 50 + "\n")
                self._write_axtree_node(axtree_data, f, 0)
            else:
                f.write("No accessibility tree data available.\n")
        
        return str(txt_file)
    
    def _write_axtree_node(self, node: Dict, file, depth: int):
        """Recursively write axtree node to file."""
        if not node:
            return
        
        indent = "  " * depth
        
        # Write node information
        if 'role' in node:
            file.write(f"{indent}Role: {node['role']}\n")
        if 'name' in node and node['name']:
            file.write(f"{indent}Name: {node['name']}\n")
        if 'description' in node and node['description']:
            file.write(f"{indent}Description: {node['description']}\n")
        if 'value' in node and node['value']:
            file.write(f"{indent}Value: {node['value']}\n")
        if 'checked' in node:
            file.write(f"{indent}Checked: {node['checked']}\n")
        if 'pressed' in node:
            file.write(f"{indent}Pressed: {node['pressed']}\n")
        if 'level' in node:
            file.write(f"{indent}Level: {node['level']}\n")
        if 'expanded' in node:
            file.write(f"{indent}Expanded: {node['expanded']}\n")
        if 'disabled' in node:
            file.write(f"{indent}Disabled: {node['disabled']}\n")
        
        file.write("\n")
        
        # Write children recursively
        if 'children' in node and node['children']:
            for child in node['children']:
                self._write_axtree_node(child, file, depth + 1)
    
    def gather_context(self, website_url: str, classification: str) -> Dict[str, str]:
        """
        Gather context from main page and important navigation pages.
        
        Args:
            website_url: Main website URL
            classification: Website classification
            
        Returns:
            Dictionary mapping page type to axtree file path
        """
        print(f"Gathering context for {website_url}")
        
        base_domain = self._extract_domain(website_url)
        context_files = {}
        
        # Get main page HTML for navigation analysis
        print(f"  Getting main page content...")
        main_html = self._get_html_content(website_url)
        if not main_html:
            print(f"  Failed to get main page content")
            return context_files
        
        # Take screenshots of main page
        print(f"  Taking screenshots of main page...")
        if self.screenshot_mode == "single":
            domain = self._extract_domain(website_url)
            # Save to classification/domain/screenshots directory
            if self.output_dir:
                screenshot_path = self.output_dir / classification / domain / "screenshots" / f"{domain}_single_screenshot.png"
                screenshot_path.parent.mkdir(parents=True, exist_ok=True)
            else:
                screenshot_path = Path(classification) / domain / "screenshots" / f"{domain}_single_screenshot.png"
                screenshot_path.parent.mkdir(parents=True, exist_ok=True)
            
            if self._take_single_screenshot(website_url, str(screenshot_path)):
                print(f"  Main page screenshot saved: {screenshot_path}")
            else:
                print(f"  Failed to take screenshot of main page")
        elif self.screenshot_mode == "multiple":
            domain = self._extract_domain(website_url)
            # Save to classification/domain/screenshots directory
            if self.output_dir:
                screenshot_dir = self.output_dir / classification / domain / "screenshots" / f"{domain}_screenshots"
            else:
                screenshot_dir = Path(classification) / domain / "screenshots" / f"{domain}_screenshots"
            os.makedirs(screenshot_dir, exist_ok=True)
            screenshots = self._take_screenshots(website_url, str(screenshot_dir))
            if screenshots:
                print(f"  Main page screenshots saved: {len(screenshots)} screenshots in {screenshot_dir}")
            else:
                print(f"  Failed to take screenshots of main page")
        
        # Extract navigation elements from main page
        print(f"  Analyzing navigation elements...")
        navigation_elements = self._extract_navigation_elements(main_html, website_url)
        print(f"  Found {len(navigation_elements)} navigation elements")
        
        # Show top navigation elements with their navbar scores
        if navigation_elements:
            print(f"  Top navigation elements (sorted by navbar score):")
            for i, elem in enumerate(navigation_elements[:10]):  # Show top 10
                print(f"    {i+1}. {elem['text']} -> {elem['url']} [Score: {elem['navbar_score']:.2f}]")
        
        # Select important navigation pages using LLM
        if navigation_elements:
            selected_urls = self._analyze_navigation_links(navigation_elements, website_url, base_domain, classification)
            print(f"  Selected {len(selected_urls)} additional pages for context")
        else:
            print(f"  No navigation elements found, creating default page_1 folder for consistency")
            selected_urls = [website_url]  # Use main page as page_1 for consistency
        
        # Ensure we always have at least one page for consistency
        if not selected_urls:
            print(f"  No pages selected, creating default page_1 folder for consistency")
            selected_urls = [website_url]  # Use main page as page_1 for consistency
        
        # Step 1: Get main page Playwright axtree
        print(f"  Getting main page Playwright axtree...")
        main_playwright_axtree = self._get_playwright_axtree(website_url)
        if main_playwright_axtree:
            main_playwright_file = self._save_playwright_axtree(website_url, main_playwright_axtree, classification, "main")
            context_files["main_playwright"] = main_playwright_file
            print(f"  Main page Playwright axtree saved: {main_playwright_file}")
        else:
            print(f"  Failed to get main page Playwright axtree")
        
        # Step 2: Select exactly 3 child pages (limit to 3)
        child_urls = selected_urls[:3]  # Take only first 3 child pages
        print(f"  Selected {len(child_urls)} child pages for analysis")
        
        # Step 3: Get child pages Playwright axtrees
        child_pages_data = []
        for i, url in enumerate(child_urls):
            if url in self.visited_urls or url in self.blacklist:
                continue
            
            # Skip if this is the same as the main page URL (avoid duplicates)
            if url == website_url:
                print(f"  Skipping page {i+1} (same as main page): {url}")
                continue
                
            print(f"  Getting Playwright axtree for child page {i+1}: {url}")
            try:
                playwright_axtree = self._get_playwright_axtree(url)
                if playwright_axtree:
                    page_folder = f"child_{i+1}"
                    playwright_file = self._save_playwright_axtree(url, playwright_axtree, classification, page_folder)
                    context_files[f"child_{i+1}"] = playwright_file
                    child_pages_data.append({
                        'url': url,
                        'axtree_file': playwright_file,
                        'axtree_data': playwright_axtree
                    })
                    print(f"  Child page {i+1} Playwright axtree saved: {playwright_file}")
                else:
                    print(f"  Failed to get Playwright axtree for child page {i+1}")
                    
                self.visited_urls.add(url)
                
            except Exception as e:
                print(f"  Error getting Playwright axtree for {url}: {e}")
                self.blacklist.add(url)
        
        # Step 4: Analyze child pages with LLM to summarize functionalities
        print(f"  Analyzing {len(child_pages_data)} child pages with LLM...")
        child_pages_summary = self._analyze_child_pages_with_llm(child_pages_data, classification)
        if child_pages_summary:
            context_files["child_pages_summary"] = child_pages_summary
            print(f"  Child pages analysis saved: {child_pages_summary}")
        
        print(f"Context gathering complete. Collected {len(context_files)} files")
        return context_files
    
    def combine_axtrees(self, context_files: Dict[str, str]) -> str:
        """Combine multiple axtree files into a single comprehensive context."""
        combined_content = []
        
        for page_type, file_path in context_files.items():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                combined_content.append(content)
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
        
        return "\n\n".join(combined_content)
    
    def _analyze_child_pages_with_llm(self, child_pages_data: List[Dict], classification: str) -> str:
        """Analyze child pages axtrees with LLM to summarize user actions and components."""
        try:
            from openai import OpenAI
            
            if not child_pages_data:
                print(f"    No child pages found for analysis")
                return None
            
            # Collect child page axtrees content
            child_pages_content = []
            for i, page_data in enumerate(child_pages_data):
                try:
                    with open(page_data['axtree_file'], 'r', encoding='utf-8') as f:
                        content = f.read()
                    child_pages_content.append(f"=== CHILD PAGE {i+1} ===\nURL: {page_data['url']}\n\n{content}")
                except Exception as e:
                    print(f"    Error reading {page_data['axtree_file']}: {e}")
            
            if not child_pages_content:
                print(f"    No child pages content found for analysis")
                return None
            
            # Combine child pages content
            combined_child_content = "\n\n".join(child_pages_content)
            
            # Truncate if too long to avoid context length issues
            max_length = 15000  # Limit to ~15k characters
            if len(combined_child_content) > max_length:
                combined_child_content = combined_child_content[:max_length] + "\n\n[TRUNCATED - Full content available in individual files]"
            
            # Create prompt for LLM analysis
            prompt = f"""Analyze the following accessibility trees from child pages of a {classification} website and summarize all possible **user actions** that can be performed on each page.

For each page:
1. Identify **interactive elements** (buttons, links, inputs, dropdowns, toggles, etc.) and describe what they allow users to do.
   - Example: “Button labeled ‘Add to Cart’ → allows user to add product to shopping cart.”
   - Example: “Link labeled ‘Forgot Password’ → navigates to password recovery page.”
2. FOCUS ON THE CODE FUNCTIONALITIES THAT IS VISIBLE IN THAT PAGE:
    - Example: If the page is a product listing page, identify the filters and sorting options.
    - Example: If the page is a flight booking page, identify the flight options and booking options, all the buttons related to this functionality.
3. If possible, describe **common workflows or sequences** of actions.
   - Example: “User can search for a product → click on results → add to cart → proceed to checkout.”
4. Note any **unique or page-specific actions** (e.g., “toggle map view,” “expand FAQ answers”).

Format your output as:
- **Page Name or URL (if identifiable)**
  - **Action Category:** [category name]
    - Example Actions:
      - [action 1]
      - [action 2]
      - [action 3]

ACCESSIBILITY TREES FROM CHILD PAGES:
{combined_child_content}"""
            
            # Call OpenAI API
            client = OpenAI()
            response = client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": "You are an expert web accessibility analyst. Analyze accessibility trees and provide comprehensive summaries of user actions and components."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=4000
            )
            
            analysis = response.choices[0].message.content
            
            # Save analysis to file
            domain = self._extract_domain(child_pages_data[0]['url'])
            if self.output_dir:
                output_dir = self.output_dir / classification / domain / "analysis"
            else:
                output_dir = Path(classification) / domain / "analysis"
            
            output_dir.mkdir(parents=True, exist_ok=True)
            
            analysis_file = output_dir / f"{domain}_child_pages_analysis.txt"
            with open(analysis_file, 'w', encoding='utf-8') as f:
                f.write(f"=== CHILD PAGES ANALYSIS ===\n")
                f.write(f"Website: {domain}\n")
                f.write(f"Classification: {classification}\n")
                f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(analysis)
            
            return str(analysis_file)
            
        except Exception as e:
            print(f"    Error analyzing child pages with LLM: {e}")
            return None


def main():
    """Test the ContextGatherer."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Gather context from website navigation pages")
    parser.add_argument("website_url", help="Website URL to gather context from")
    parser.add_argument("--classification", default="General", help="Website classification")
    parser.add_argument("--max-pages", type=int, default=3, help="Maximum additional pages to gather")
    parser.add_argument("--output-dir", help="Output directory for axtree files")
    parser.add_argument("--screenshot-mode", choices=["none", "single", "multiple"], default="multiple", help="Screenshot mode: none, single viewport, or multiple sections")
    
    args = parser.parse_args()
    
    gatherer = ContextGatherer(max_additional_pages=args.max_pages, output_dir=args.output_dir, screenshot_mode=args.screenshot_mode)
    context_files = gatherer.gather_context(args.website_url, args.classification)
    
    print(f"\nCollected context files:")
    for page_type, file_path in context_files.items():
        print(f"  {page_type}: {file_path}")
    
    if len(context_files) > 1:
        combined = gatherer.combine_axtrees(context_files)
        print(f"\nCombined context length: {len(combined)} characters")


if __name__ == "__main__":
    main()