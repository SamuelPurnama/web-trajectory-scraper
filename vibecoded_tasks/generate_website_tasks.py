#!/usr/bin/env python3
"""
Module to generate web task files for websites using ChatGPT via the ell library.

This module reads the 585_websites.csv file, processes each website,
sends requests to ChatGPT using the ell library, and saves the generated
Python task files to the python_files directory.
"""

import csv
import time
import json
import os
from pathlib import Path
from typing import Dict, Optional, List
from urllib.parse import urlparse

# Load environment variables from .env file BEFORE importing ell
script_dir = Path(__file__).parent
env_file = script_dir / ".env"
if env_file.exists():
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()
    print(f"✓ Loaded environment variables from {env_file}")
else:
    print(f"⚠️  .env file not found at {env_file}")

import ell

# Check if API key is loaded
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("WARNING: OPENAI_API_KEY not found in environment variables!")
    print("Make sure your .env file contains: OPENAI_API_KEY=your_api_key_here")
else:
    print(f"✓ OpenAI API key loaded successfully (starts with: {api_key[:10]}...)")

import sys
sys.path.append('./website_graph')

# Import the enhanced exploration
from enhanced_website_exploration import ContextGatherer

try:
    from webgraph_utils import get_accessibility_tree_simple, json_to_readable_txt
    WEBGRAPH_AVAILABLE = True
    # print("webgraph_utils imported successfully")
except ImportError as e:
    # print(f"Warning: webgraph_utils not available: {e}")
    WEBGRAPH_AVAILABLE = False
    # Create dummy functions
    def get_accessibility_tree_simple(url):
        return None
    def json_to_readable_txt(json_file, output_file):
        return output_file

class WebsiteTaskGenerator:
    """Generates web task files for websites using ChatGPT."""
    
    def __init__(self, 
                 csv_file_path: str = "739_websites.csv",
                 output_dir: str = "./outputs/json_tasks",
                 local_output_dir: str = "./local_output",
                 prompt_template_path: str = "prompt.txt",
                 reference_file_path: str = "reference_file.txt",
                 axtree_path: Optional[str] = None,
                 use_enhanced_exploration: bool = True,
                 screenshot_mode: str = "multiple"):
        """
        Initialize the WebsiteTaskGenerator.
        
        Args:
            csv_file_path: Path to the CSV file containing websites
            output_dir: Directory to save JSON files (datasets)
            local_output_dir: Directory to save Python files and axtrees (local)
            prompt_template_path: Path to the prompt template file
            reference_file_path: Path to the reference file
            axtree_path: Optional path to axtree file (if not provided, will use default)
            use_enhanced_exploration: Whether to use enhanced multi-page exploration
        """
        self.csv_file_path = Path(csv_file_path)
        self.output_dir = Path(output_dir)
        self.local_output_dir = Path(local_output_dir)
        self.prompt_template_path = Path(prompt_template_path)
        self.reference_file_path = Path(reference_file_path)
        self.axtree_path = Path(axtree_path) if axtree_path else None
        self.use_enhanced_exploration = use_enhanced_exploration
        self.screenshot_mode = screenshot_mode
        
        # Ensure output directory exists (create parent directories if needed)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load template files
        self.prompt_template = self._load_file(self.prompt_template_path)
        self.reference_file = self._load_file(self.reference_file_path)
        self.axtree = self._load_file(self.axtree_path) if self.axtree_path else ""
        
        # Rate limiting
        self.request_delay = 1.0  # seconds between requests
        
    def _load_file(self, file_path: Path) -> str:
        """Load content from a file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _get_reference_file(self, classification: str) -> str:
        """
        Get reference file content, trying classification-specific first, then fallback to general.
        
        Args:
            classification: The website classification
            
        Returns:
            Reference file content
        """
        # Try classification-specific reference file first
        classification_ref_file = self.local_output_dir / "reference_files" / classification / "reference_file.txt"
        
        try:
            with open(classification_ref_file, 'r', encoding='utf-8') as f:
                content = f.read()
            # print(f"        _get_reference_file: Using classification-specific reference file: {classification_ref_file}")
            return content
        except FileNotFoundError:
            # print(f"        _get_reference_file: Classification-specific reference file not found: {classification_ref_file}")
            # print(f"        _get_reference_file: Falling back to general reference file: {self.reference_file_path}")
            return self.reference_file
        except Exception as e:
            # print(f"        _get_reference_file: Error reading classification-specific reference file: {e}")
            # print(f"        _get_reference_file: Falling back to general reference file: {self.reference_file_path}")
            return self.reference_file
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        parsed = urlparse(url)
        domain = parsed.netloc
        # Remove www. prefix if present
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    
    def _clean_generated_code(self, code: str) -> str:
        if code.startswith('```python'):
            code = code[9:]
        elif code.startswith('```'):
            code = code[3:]
        
        if code.endswith('```'):
            code = code[:-3]
        
        code = code.strip()
        
        return code
    
    def _calculate_screenshot_distribution(self, total_pages: int) -> List[int]:
        """
        Calculate how many screenshots to take per page, distributing 6 total images.
        Max 2 screenshots per page.
        
        Args:
            total_pages: Total number of pages (main + additional pages)
            
        Returns:
            List of screenshot counts per page
        """
        total_screenshots = 6
        max_per_page = 2
        
        if total_pages == 0:
            return []
        
        # Calculate base screenshots per page
        base_per_page = total_screenshots // total_pages
        remainder = total_screenshots % total_pages
        
        # Distribute screenshots
        distribution = []
        for i in range(total_pages):
            screenshots_for_page = base_per_page
            if i < remainder:  # Distribute remainder to first pages
                screenshots_for_page += 1
            # Cap at max_per_page
            screenshots_for_page = min(screenshots_for_page, max_per_page)
            distribution.append(screenshots_for_page)
        
        return distribution
    
    def _collect_screenshots_and_elements(self, website: str, classification: str) -> tuple:
        """
        Collect screenshots and comprehensive elements from enhanced exploration.
        
        Args:
            website: Website URL
            classification: Website classification
            
        Returns:
            Tuple of (comprehensive_elements, screenshots_info)
        """
        from pathlib import Path
        import os
        
        domain = self._extract_domain(website)
        
        # Get comprehensive elements from main page
        main_elements_file = self.local_output_dir / classification / domain / "interactive_elements" / f"{domain}_interactive_elements.txt"
        
        # Get additional pages
        page_folders = []
        page_num = 1
        while True:
            page_folder = f"page_{page_num}"
            page_elements_file = self.local_output_dir / classification / domain / page_folder / "interactive_elements" / f"{domain}_interactive_elements.txt"
            if page_elements_file.exists():
                page_folders.append((page_folder, page_elements_file))
                page_num += 1
            else:
                break
        
        # Calculate screenshot distribution
        total_pages = 1 + len(page_folders)  # Main page + additional pages
        screenshot_distribution = self._calculate_screenshot_distribution(total_pages)
        
        # Collect comprehensive elements
        comprehensive_elements = []
        
        # Main page elements
        if main_elements_file.exists():
            with open(main_elements_file, 'r', encoding='utf-8') as f:
                main_content = f.read()
            comprehensive_elements.append(f"=== MAIN PAGE INTERACTIVE ELEMENTS ===\n{main_content}")
        
        # Additional pages elements
        for page_folder, elements_file in page_folders:
            if elements_file.exists():
                with open(elements_file, 'r', encoding='utf-8') as f:
                    page_content = f.read()
                comprehensive_elements.append(f"=== {page_folder.upper().replace('_', ' ')} INTERACTIVE ELEMENTS ===\n{page_content}")
        
        # Collect screenshots with distribution
        screenshots_info = []
        
        # Main page screenshots
        main_screenshots_dir = self.local_output_dir / classification / domain / "screenshots" / f"{domain}_screenshots"
        if main_screenshots_dir.exists():
            main_screenshots = sorted([f for f in os.listdir(main_screenshots_dir) if f.endswith('.png')])
            max_main_screenshots = screenshot_distribution[0] if screenshot_distribution else 2
            selected_main_screenshots = main_screenshots[:max_main_screenshots]
            screenshots_info.append({
                'page': 'main',
                'screenshots': [str(main_screenshots_dir / f) for f in selected_main_screenshots],
                'count': len(selected_main_screenshots)
            })
        
        # Additional pages screenshots
        for i, (page_folder, _) in enumerate(page_folders):
            page_screenshots_dir = self.local_output_dir / classification / domain / page_folder / "screenshots" / f"{domain}_{page_folder}_screenshots"
            if page_screenshots_dir.exists():
                page_screenshots = sorted([f for f in os.listdir(page_screenshots_dir) if f.endswith('.png')])
                max_page_screenshots = screenshot_distribution[i + 1] if i + 1 < len(screenshot_distribution) else 2
                selected_page_screenshots = page_screenshots[:max_page_screenshots]
                screenshots_info.append({
                    'page': page_folder,
                    'screenshots': [str(page_screenshots_dir / f) for f in selected_page_screenshots],
                    'count': len(selected_page_screenshots)
                })
        
        return '\n\n'.join(comprehensive_elements), screenshots_info
    
    def _collect_axtrees_and_images(self, website: str, classification: str) -> dict:
        """
        Collect main page axtree, screenshots, and child pages summary for LLM context.
        
        Args:
            website: Website URL
            classification: Website classification
            
        Returns:
            Dictionary with 'axtrees', 'images', and 'child_summary' keys
        """
        from pathlib import Path
        import os
        
        domain = self._extract_domain(website)
        
        # Collect main page Playwright axtree only
        axtrees_content = []
        main_playwright_file = self.local_output_dir / classification / domain / "playwright_axtree" / f"{domain}_playwright_axtree.txt"
        if main_playwright_file.exists():
            with open(main_playwright_file, 'r', encoding='utf-8') as f:
                axtrees_content.append(f"=== MAIN PAGE PLAYWRIGHT AXTRESS ===\n{f.read()}")
        
        # Collect child pages summary
        child_summary = ""
        child_analysis_file = self.local_output_dir / classification / domain / "analysis" / f"{domain}_child_pages_analysis.txt"
        if child_analysis_file.exists():
            with open(child_analysis_file, 'r', encoding='utf-8') as f:
                child_summary = f.read()
        
        # Collect images (limit to first 3 main page screenshots)
        images = []
        main_screenshots_dir = self.local_output_dir / classification / domain / "screenshots" / f"{domain}_screenshots"
        if main_screenshots_dir.exists():
            main_screenshots = sorted([f for f in os.listdir(main_screenshots_dir) if f.endswith('.png')])
            for screenshot in main_screenshots[:3]:  # Limit to 3 main page screenshots
                images.append(str(main_screenshots_dir / screenshot))
        
        # Truncate axtrees to avoid context length issues
        full_axtrees = '\n\n'.join(axtrees_content)
        max_length = 20000  # Limit to ~20k characters to stay within token limits
        
        if len(full_axtrees) > max_length:
            truncated_axtrees = full_axtrees[:max_length] + "\n\n[TRUNCATED - Full axtrees available in local files]"
        else:
            truncated_axtrees = full_axtrees
        
        return {
            'axtrees': truncated_axtrees,
            'images': images,
            'child_summary': child_summary
        }
    
    def save_website_axtree(self, website_url: str, classification: str, output_dir: str = None):
        domain = self._extract_domain(website_url)
        obs = get_accessibility_tree_simple(website_url)
        
        if obs and "axtree_object" in obs:
            if output_dir is None:
                output_dir = self.local_output_dir / "axtrees" / classification
            else:
                output_dir = Path(output_dir) / classification
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            temp_json_file = "/tmp/temp_axtree.json"
            with open(temp_json_file, 'w') as f:
                json.dump(obs["axtree_object"], f)
            
            txt_file = json_to_readable_txt(temp_json_file, f"{output_dir}/{domain}_axtree.txt")
    
    def _create_prompt(self, website: str, classification: str) -> str:
        # print(f"        _create_prompt: Starting for {website}")
        
        if self.use_enhanced_exploration:
            print(f"        _create_prompt: Gathering enhanced context...")
            
            # Use enhanced exploration to gather comprehensive context
            gatherer = ContextGatherer(max_additional_pages=3, output_dir=str(self.local_output_dir), screenshot_mode=self.screenshot_mode)
            context_files = gatherer.gather_context(website, classification)
            
            # Collect comprehensive elements and screenshots with distribution
            comprehensive_elements, screenshots_info = self._collect_screenshots_and_elements(website, classification)
            
            print(f"        _create_prompt: Enhanced context gathered from {len(context_files)} pages")
            print(f"        _create_prompt: Screenshots distribution: {[info['count'] for info in screenshots_info]}")
            
            # Use comprehensive elements instead of axtree
            website_context = comprehensive_elements
        else:
            print(f"        _create_prompt: Using simple axtree...")
            website_context = self._get_simple_axtree(website, classification)
            screenshots_info = []
        
        # Try to get classification-specific reference file, fallback to general
        reference_file_content = self._get_reference_file(classification)
        
        # Create screenshots section for prompt
        screenshots_section = ""
        if screenshots_info:
            screenshots_section = "\n\n=== SCREENSHOTS ===\n"
            for info in screenshots_info:
                screenshots_section += f"\n{info['page'].upper()} PAGE ({info['count']} screenshots):\n"
                for screenshot_path in info['screenshots']:
                    screenshots_section += f"- {screenshot_path}\n"
        
        # Add main page axtree, screenshots, and child pages summary
        axtrees_and_images = self._collect_axtrees_and_images(website, classification)
        
        # Build enhanced context with main page axtree and child pages summary
        enhanced_context = f"{website_context}{screenshots_section}"
        
        # Add main page axtree
        if axtrees_and_images['axtrees']:
            enhanced_context += f"\n\n=== MAIN PAGE ACCESSIBILITY TREE ===\n{axtrees_and_images['axtrees']}"
        
        # Add child pages summary as additional functions
        if axtrees_and_images['child_summary']:
            enhanced_context += f"\n\n=== ADDITIONAL FUNCTIONS FOUND IN CHILD PAGES ===\n{axtrees_and_images['child_summary']}"
        
        # print(f"        _create_prompt: Creating prompt...")
        prompt = self.prompt_template.format(
            website=website,
            axtree=enhanced_context,
            reference_file=reference_file_content
        )
        # print(f"        _create_prompt: Prompt created, length: {len(prompt)}")
        return prompt
    
    def _get_simple_axtree(self, website: str, classification: str) -> str:
        """Get simple axtree as fallback."""
        self.save_website_axtree(website, classification)
        domain = self._extract_domain(website)
        axtree_file = self.local_output_dir / "axtrees" / classification / f"{domain}_axtree.txt"
        
        try:
            with open(axtree_file, 'r') as f:
                return f.read()
        except Exception as e:
            print(f"        _get_simple_axtree: Simple axtree failed: {e}")
            return self.axtree
    
    def _generate_task_file(self, website: str, domain: str, classification: str) -> str:
        # print(f"      _generate_task_file: Creating prompt for {website}")
        prompt = self._create_prompt(website, classification)
        # print(f"      _generate_task_file: Prompt created, length: {len(prompt)}")
        
        # Collect axtrees and images for LLM
        axtrees_and_images = self._collect_axtrees_and_images(website, classification)
        
        # print(f"      _generate_task_file: Calling AI model...")
        # Use OpenAI library directly instead of ell
        from openai import OpenAI
        
        client = OpenAI()
        
        # Note: ell.image() is not available in this version of ell library
        # Images are included in the text prompt instead
        image_note = ""
        if axtrees_and_images['images']:
            image_note = f"\n\nNote: {len(axtrees_and_images['images'])} screenshots are available but cannot be processed due to library limitations. Using text-based analysis only."
        
        # Call OpenAI API directly
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": "You are a senior coding professional. Generate comprehensive Python task files with 20+ choices for variable selectors."},
                {"role": "user", "content": prompt + image_note}
            ],
            temperature=0.3,
            max_tokens=8000
        )
        
        generated_code = response.choices[0].message.content
        # print(f"      _generate_task_file: AI response received")
        
        generated_code = self._clean_generated_code(generated_code)
        
        return generated_code
    
    def _save_task_file(self, domain: str, content: str, classification: str) -> None:
        filename = f"tasks_{domain.replace('.', '_')}.py"
        # Save to main python_files directory with classification subfolder
        file_path = Path("python_files") / classification / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _process_website(self, website: str, domain: str, classification: str) -> None:
        print(f"    _process_website: Starting for {website}")
        # print(f"    _process_website: Generating task file...")
        generated_code = self._generate_task_file(website, domain, classification)
        # print(f"    _process_website: Saving task file...")
        self._save_task_file(domain, generated_code, classification)
        # print(f"    _process_website: Completed for {website}")
    
    def process_all_websites(self, start_index: int = 0, max_websites: Optional[int] = None, classification_filter: Optional[str] = None) -> Dict[str, int]:
        """
        Process all websites from the CSV file.
        
        Args:
            start_index: Index to start processing from
            max_websites: Maximum number of websites to process (None for all)
            classification_filter: Optional classification to filter by (e.g., "Airlines")
            
        Returns:
            Dictionary with success/failure counts
        """
        results = {"success": 0, "failed": 0, "skipped": 0}
        processed_count = 0
        processed_classifications = set()
        
        with open(self.csv_file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            websites = list(reader)
            
            # Filter by classification if specified
            if classification_filter:
                websites = [w for w in websites if w.get('Subdomain', '').strip() == classification_filter]
                print(f"Filtering for classification: {classification_filter}")
                print(f"Found {len(websites)} websites with classification '{classification_filter}'")
            
            # Apply start index and max limit
            websites = websites[start_index:]
            if max_websites:
                websites = websites[:max_websites]
            
            for i, row in enumerate(websites):
                website = row.get('origin', '').strip()
                print(f"Processing website {i+1}/{len(websites)}: {website}")
                
                if not website:
                    print(f"  Skipping: Empty website URL")
                    results["skipped"] += 1
                    continue
                
                # Skip Athlon Sports (403 error)
                if 'athlonsports.com' in website:
                    print(f"  Skipping: Athlon Sports (known to block requests)")
                    results["skipped"] += 1
                    continue
                
                domain = self._extract_domain(website)
                print(f"  Domain: {domain}")
                
                if not domain:
                    print(f"  Skipping: Could not extract domain")
                    results["skipped"] += 1
                    continue
                
                # Get classification from CSV
                classification = row.get('Subdomain', 'General').strip()
                if not classification:
                    classification = 'General'
                print(f"  Classification: {classification}")
                
                # Process the website
                print(f"  Starting to process website...")
                try:
                    self._process_website(website, domain, classification)
                    print(f"  ✓ Successfully processed {website}")
                    results["success"] += 1
                except Exception as e:
                    print(f"  ✗ Error processing {website}: {e}")
                    results["failed"] += 1
                
                # Save reference file and copy instruction_utils for this classification if not already saved
                if classification not in processed_classifications:
                    self.save_reference_file(classification)
                    self.copy_instruction_utils(classification)
                    processed_classifications.add(classification)
                
                processed_count += 1
                
                # Rate limiting
                if i < len(websites) - 1:
                    time.sleep(self.request_delay)
        
        return results
    
    def process_single_website(self, website: str, classification: str = "General") -> None:
        """
        Process a single website.
        
        Args:
            website: The website URL
            classification: The website classification (default: "General")
        """
        domain = self._extract_domain(website)
        self._process_website(website, domain, classification)
    
    def save_reference_file(self, classification: str) -> None:
        """
        Save the reference file in the classification-based directory structure.
        
        Args:
            classification: The website classification
        """
        reference_dir = self.local_output_dir / "reference_files" / classification
        reference_dir.mkdir(parents=True, exist_ok=True)
        
        reference_file_path = reference_dir / "reference_file.txt"
        with open(reference_file_path, 'w', encoding='utf-8') as f:
            f.write(self.reference_file)
    
    def copy_instruction_utils(self, classification: str) -> None:
        """
        Copy instruction_utils.py to the classification-based directory structure.
        
        Args:
            classification: The website classification
        """
        # Source instruction_utils.py file
        source_file = Path("python_files/tasks/instruction_utils.py")
        
        if source_file.exists():
            # Destination directory
            dest_dir = self.local_output_dir / "python_files" / classification
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy the file
            dest_file = dest_dir / "instruction_utils.py"
            with open(source_file, 'r', encoding='utf-8') as src:
                with open(dest_file, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
    


def main():
    """Main function to run the task generator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate web task files for websites using ChatGPT")
    parser.add_argument("--csv-file", default="739_websites.csv", help="Path to CSV file with websites")
    parser.add_argument("--output-dir", default="./outputs/json_tasks", help="Output directory for JSON files (datasets)")
    parser.add_argument("--local-output-dir", default="./local_output", help="Output directory for Python files and axtrees (local)")
    parser.add_argument("--prompt-template", default="prompt.txt", help="Path to prompt template file")
    parser.add_argument("--reference-file", default="reference_file.txt", help="Path to reference file")
    parser.add_argument("--axtree-file", help="Path to axtree file (optional)")
    parser.add_argument("--start-index", type=int, default=0, help="Index to start processing from")
    parser.add_argument("--max-websites", type=int, help="Maximum number of websites to process")
    parser.add_argument("--single-website", help="Process only a single website URL")
    parser.add_argument("--classification", help="Filter by classification (e.g., 'Airlines', 'Department', etc.)")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between requests in seconds")
    parser.add_argument("--enhanced-exploration", action="store_true", default=True, help="Use enhanced multi-page exploration")
    parser.add_argument("--simple-exploration", action="store_true", help="Use simple single-page exploration")
    parser.add_argument("--screenshot-mode", choices=["none", "single", "multiple"], default="multiple", help="Screenshot mode: none, single viewport, or multiple sections")
    
    args = parser.parse_args()
    
    # Determine exploration mode
    use_enhanced = args.enhanced_exploration and not args.simple_exploration
    
    # Initialize the generator
    generator = WebsiteTaskGenerator(
        csv_file_path=args.csv_file,
        output_dir=args.output_dir,
        local_output_dir=args.local_output_dir,
        prompt_template_path=args.prompt_template,
        reference_file_path=args.reference_file,
        axtree_path=args.axtree_file,
        use_enhanced_exploration=use_enhanced,
        screenshot_mode=args.screenshot_mode
    )
    
    # Set request delay
    generator.request_delay = args.delay
    
    if args.single_website:
        generator.process_single_website(args.single_website)
    else:
        results = generator.process_all_websites(
            start_index=args.start_index,
            max_websites=args.max_websites,
            classification_filter=args.classification
        )
        print(f"Results: {results}")


if __name__ == "__main__":
    main()
