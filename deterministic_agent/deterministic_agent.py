import re
import asyncio
import hashlib
import json
import os
from typing import Any, Dict, Literal
from urllib.parse import urljoin
from logger import flatten_axtree_to_str, pre_extract
from logger import extract_merged_axtree
# from click_utils import *

class DeterministicAgent:
    """
    A deterministic web navigation agent that follows a predefined path of URLs.

    This agent operates on a simple "plan-then-execute" model for each leg of the journey:
    1.  **Plan:** When a new navigation leg begins (self.plan is None), it finds
        the link for the next URL in the path and creates a plan.
    2.  **Execute:** It then executes this plan on each subsequent step:
        - If the target element is visible, it clicks it, which ends the current leg.
        - If the target element is not visible, it scrolls.
    """
    def __init__(self, start_url: str, path: list[str], logger, eps_name: str, debug: bool = False):
        self.path = path
        self.logger = logger
        self.eps_name = eps_name
        self.current_path_index = 0
        self.current_step = 0
        self.max_steps = 40 # 20 for default
        self.last_screenshot_hash = None
        self.plan = None  # The plan for how to reach the next url.
        self.just_hovered = False
        self.just_clicked = False
        self.previous_url = None
        self.previous_tab_count = 1  # Start with 1 tab
        self.debug = debug
        # plan will determine whether we need to just:
        # 1. click and scroll or
        # 2. hover or
        # 3. expand
        #4. check whetehr we can even do the task at all

    def reset(self):
        """Resets the agent's state for a new episode."""
        self.current_path_index = 0
        self.current_step = 0
        self.last_screenshot_hash = None
        self.plan = None
        self.just_clicked = False
        self.previous_url = None

    async def _run_hover_js(self, page, target_url_substring: str):
        # Run the hover_check.js script on the page - it doesn't need any parameters
        js_path = os.path.join(os.path.dirname(__file__), 'javascript', 'hover_check.js')
        with open(js_path, 'r') as f:
            js_code = f.read()
        
        # Execute the script directly - it's a self-executing function
        await page.evaluate(js_code)

    def _save_verdict(self, reason):
        total_urls = len(self.path)
        urls_visited_successfully = max(1, self.current_path_index + 1)
        
        # New progress calculation: (visited - 1) / (total - 1)
        progress = 0.0
        if total_urls > 1:
            progress = (urls_visited_successfully - 1) / (total_urls - 1)
            
        # New status calculation. Success is visiting ALL urls.
        status = "SUCCESS" if urls_visited_successfully == total_urls else "FAILURE"
        
        # If the reason for exit is explicit success, ensure status is SUCCESS.
        if reason == "Completed all URLs successfully.":
            status = "SUCCESS"
            
        verdict = {
            "total_urls": total_urls,
            "urls_visited_successfully": urls_visited_successfully,
            "status": status,
            "reason": reason,
            "progress": round(progress, 2),
            "path": self.path,
        }
        outdir = getattr(self.logger, 'outdir', '.')
        with open(os.path.join(outdir, 'verdict.json'), 'w') as f:
            json.dump(verdict, f, indent=2)

    @staticmethod
    def _strip_protocol(url):
        if url.startswith("https://"):
            return url[8:]
        if url.startswith("http://"):
            return url[7:]
        return url

    @staticmethod
    def _find_target_bid_in_axtree(axtree_str, target_url, debug=False):
        import re
        if debug:
            print(f"DEBUG: Searching for target '{target_url}' in axtree...")
        lines_with_url = 0
        lines_with_bid_and_url = 0
        
        for i, line in enumerate(axtree_str.splitlines()):
            if 'link' in line and 'url=' in line:
                lines_with_url += 1
                bid_match = re.search(r"\[(\d+)\]", line)
                url_match = re.search(r"url='([^']+)'", line)

                if url_match:
                    url = url_match.group(1)
                    # Use robust, protocol-stripped matching
                    if DeterministicAgent._strip_protocol(target_url) in DeterministicAgent._strip_protocol(url):
                        if debug:
                            print(f"DEBUG: Line {i}: Found target URL '{url}'")
                        if bid_match:
                            lines_with_bid_and_url += 1
                            bid = bid_match.group(1)
                            if debug:
                                print(f"DEBUG: Matched! BID: {bid}, URL: {url}")
                            return bid
                        else:
                            if debug:
                                print(f"DEBUG: Line {i}: Found target URL, but NO BID on the same line.")
                else:
                    if debug:
                        print(f"DEBUG: Line {i}: Found 'link' and 'url=' but could not parse URL from line: {line}")

        if debug:
            print(f"DEBUG: Search complete. Found {lines_with_url} lines with links/URLs. Found {lines_with_bid_and_url} with BIDs. Target was NOT found with a BID.")
        return None

    @staticmethod
    def _find_hover_parent_bid(regular_axtree_str, expanded_axtree_str, target_url):
        # Find the bid of the parent to hover over to reveal the target_url
        # Find the target bid in the expanded axtree
        target_bid = DeterministicAgent._find_target_bid_in_axtree(expanded_axtree_str, target_url)
        if not target_bid:
            return None
            
        target_bid_num = int(target_bid)
        
        # Find all BIDs in the regular axtree
        all_bids = []
        for match in re.finditer(r'\[(\d+)\]', regular_axtree_str):
            bid_num = int(match.group(1))
            all_bids.append(bid_num)
        
        # Find the largest BID that's smaller than the target BID
        smaller_bids = [bid for bid in all_bids if bid < target_bid_num]
        if smaller_bids:
            return str(max(smaller_bids))
        
        return None

    async def predict_action(self, obs: Dict[str, Any], page) -> Dict[str, Any]:
        # num_tabs = len(page.context.pages) # this was used to debug tabs
        # print(f"[{self.eps_name}] Tabs open: {num_tabs}")
        self.current_step += 1

        if self.current_step >= self.max_steps:
            self._save_verdict("Maximum number of steps exceeded")
            return {"action": "exit", "thought": "Maximum number of steps exceeded"}

        # Check if we just clicked and the URL didn't change
        if self.just_clicked:
            self.just_clicked = False
            current_tab_count = len(page.context.pages)

            if current_tab_count > self.previous_tab_count:
                # New tab was opened. This is a successful navigation.
                self.current_path_index += 1
                self.previous_tab_count = current_tab_count
                return {"action": "tab_focus", "thought": "A new tab was opened, switching to it."}

            current_url = page.url

            if self.debug:
                print(f"DEBUG: Post-click check. Previous URL: '{self.previous_url}', Current URL: '{current_url}'")
                print(f"DEBUG: URL comparison (current == previous): {current_url == self.previous_url}")

            if current_url == self.previous_url:
                self._save_verdict("Clicking didn't take me to the next url")
                return {"action": "exit", "thought": "Clicking didn't take me to the next url"}
            else:
                # URL changed successfully, now we can increment the path index
                self.current_path_index += 1

        if self.just_hovered:
            # After hover, the goal is to click any link matching the original substring from the path
            self.just_hovered = False
            target_url_substring = self.path[self.current_path_index + 1]
            axtree_str = obs.get('axtree_str')
            if not axtree_str:
                axtree_str = flatten_axtree_to_str(
                    obs['axtree'],
                    extra_properties=obs['extra_element_properties'],
                    with_visible=True,
                    filter_visible_only=True,
                    filter_with_bid_only=False,
                    with_clickable=True,
                    skip_generic=True,
                )
            bid = self._find_target_bid_in_axtree(axtree_str, target_url_substring, False)  # Disable debug for post-hover search
            if bid:
                self.plan = None
                self.last_screenshot_hash = None
                self.previous_url = page.url
                self.just_clicked = True
                self.previous_tab_count = len(page.context.pages)
                return {"action": "click", "bid": bid}
            else:
                self._save_verdict("Hover failed to reveal the target element.")
                return {"action": "exit", "thought": "Hover failed to reveal the target element."}

        if self.current_step == 1:
            return {"action": "goto", "url": self.path[0]}

        if self.plan is None:
            if self.current_path_index >= len(self.path) - 1:
                self._save_verdict("Completed all URLs successfully.")
                return {"action": "exit", "thought": "SUCCESSFULLY navigated the entire path."}

            target_url_substring = self.path[self.current_path_index + 1]
            stripped_target = self._strip_protocol(target_url_substring)

            # 1. Axtree-first approach: Check the global axtree.
            is_in_global_axtree = any(
                stripped_target in self._strip_protocol(prop.get("value", {}).get("value", ""))
                for node in obs['global_axtree'].get("nodes", [])
                for prop in node.get("properties", [])
                if prop.get("name") == "url"
            )

            if is_in_global_axtree:
                self.plan = {"type": "scroll_and_click"}
            else:
                # 2. If not in global axtree, try a hover plan.
                if self.debug:
                    print(f"[HOVER] Target not in global axtree, attempting hover expansion for: '{target_url_substring}'")
                
                regular_axtree_str = flatten_axtree_to_str(
                    obs['axtree_object'],
                    extra_properties=obs['extra_element_properties'],
                    with_visible=True,
                    filter_visible_only=True,
                    filter_with_bid_only=False,
                    with_clickable=True,
                    skip_generic=True,
                )
                
                await self._run_hover_js(page, target_url_substring)
                await asyncio.sleep(1)
                await pre_extract(page)
                
                expanded_axtree_object = await extract_merged_axtree(page)
                
                # After gathering data from the messy page, restore it to a clean state
                # before we continue planning. This ensures the next action is on a predictable view.
                await page.goto(page.url, wait_until="domcontentloaded")

                expanded_axtree_str = flatten_axtree_to_str(
                    expanded_axtree_object,
                    extra_properties=obs['extra_element_properties'],
                    with_visible=True,
                    filter_visible_only=False,
                    filter_with_bid_only=False,
                    with_clickable=True,
                    skip_generic=True,
                )

                # Save expanded axtree to file for debugging (removed console print to avoid flooding)
                
                hover_dir = os.path.join(getattr(self.logger, 'outdir', '.'), 'hover_expansion')
                os.makedirs(hover_dir, exist_ok=True)
                hover_file = os.path.join(hover_dir, f'hover_expansion_{self.current_step}.txt')
                with open(hover_file, 'w') as f:
                    f.write(expanded_axtree_str)
                
                target_bid_after_hover = self._find_target_bid_in_axtree(expanded_axtree_str, target_url_substring, self.debug)

                if target_bid_after_hover:
                    hover_bid = self._find_hover_parent_bid(regular_axtree_str, expanded_axtree_str, target_url_substring)
                    if hover_bid:
                        # Get the bbox of the PARENT element (what we need to hover over to reveal the target)
                        element_properties = obs['extra_element_properties'].get(hover_bid)
                        if element_properties and 'bbox' in element_properties and element_properties['bbox'] is not None:
                            bbox = element_properties['bbox']
                            
                            if self.debug:
                                print(f"[HOVER] target_bid={target_bid_after_hover}, hover_parent_bid={hover_bid}")
                                print(f"[HOVER] Using bbox of PARENT element (bid={hover_bid}) to reveal target: {bbox}")
                            
                            # Use [X,Y,W,H] format - hover at center of parent element
                            center_x = bbox[0] + bbox[2] / 2
                            center_y = bbox[1] + bbox[3] / 2
                            
                            if self.debug:
                                print(f"[HOVER] Hovering at center: ({center_x}, {center_y})")
                            
                            self.plan = {"type": "hover", "x": center_x, "y": center_y}
                        else:
                            self._save_verdict("Found element to hover, but could not get its coordinates.")
                            return {"action": "exit", "thought": "Found element to hover, but could not get its coordinates."}
                    else:
                        self._save_verdict("Found target after hover, but could not find a parent element to hover over.")
                        return {"action": "exit", "thought": "Found target after hover, but could not find a parent element to hover over."}
                else:
                    # 3. Last resort: Check if the link exists in the HTML at all.
                    html_content = await page.content()
                    hrefs = re.findall(r'<a [^>]*href=\"([^\"]*)\"', html_content)
                    found_in_html = False
                    for href in hrefs:
                        candidate_url = urljoin(page.url, href)
                        if self._strip_protocol(target_url_substring) in self._strip_protocol(candidate_url):
                            found_in_html = True
                            break
                    
                    if found_in_html:
                        self._save_verdict("Link exists in HTML but could not be found in the accessibility tree (regular or after hover).")
                        return {"action": "exit", "thought": "Link exists in HTML but could not be found in the accessibility tree (regular or after hover)."}
                    else:
                        self._save_verdict("Unachievable task, link not found in HTML or any accessibility tree.")
                        return {"action": "exit", "thought": "Unachievable task, link not found in HTML or any accessibility tree."}

        if self.plan and self.plan["type"] == "not_found":
            self._save_verdict("Could not make a plan on how to reach the next url.")
            return {"action": "exit", "thought": "Could not make a plan on how to reach the next url."}

        if self.plan and self.plan["type"] == "hover":
            # Perform the hover action
            x = self.plan["x"]
            y = self.plan["y"]
            self.just_hovered = True
            target_url_substring = self.path[self.current_path_index + 1]
            return {"action": "hover", "x": x, "y": y, "thought": f"hovering at ({x}, {y}) to reveal url {target_url_substring}"}

        if self.plan and self.plan["type"] == "scroll_and_click":
            # The goal is to find any link that contains the substring from the original path,
            # not the specific full_target_url found during planning.
            target_url_substring = self.path[self.current_path_index + 1]
            axtree_str = obs.get('axtree_str')
            if not axtree_str:
                axtree_str = flatten_axtree_to_str(
                    obs['axtree'],
                    extra_properties=obs['extra_element_properties'],
                    with_visible=True,
                    filter_visible_only=True,
                    filter_with_bid_only=False,
                    with_clickable=True,
                    skip_generic=True,
                )

            bid = self._find_target_bid_in_axtree(axtree_str, target_url_substring, False)  # Disable debug for scroll-and-click search
            if bid:
                self.plan = None
                self.last_screenshot_hash = None
                self.previous_url = page.url
                self.just_clicked = True
                self.previous_tab_count = len(page.context.pages)
                return {"action": "click", "bid": bid}
            else:
                current_screenshot_hash = hashlib.md5(obs['screenshot'].tobytes()).hexdigest()
                if self.last_screenshot_hash == current_screenshot_hash and self.last_screenshot_hash is not None:
                    self._save_verdict("Scrolled to bottom, but element not found in viewport.")
                    return {"action": "exit", "thought": "Scrolled to bottom, but element not found in viewport."}
                self.last_screenshot_hash = current_screenshot_hash
                return {"action": "scroll", "direction": "down"}

        return {"action": "exit", "thought": f"Unknown plan type: {self.plan.get('type') if self.plan else 'None'}"}

    # async def click_element_hardcore(
    #     self,
    #     page,
    #     bid: str,
    #     button: "Literal['left', 'middle', 'right']" = "left",
    #     modifiers: list = [],
    #     demo_mode: "Literal['off', 'default', 'all_blue', 'only_visible_elements']" = "off",
    #     retry_with_force: bool = True,
    # ):
    #     """
    #     Click based on pipers implementation 
    #     """
    #     selector = f'[bid="{bid}"]'
    #     await page.locator(selector).wait_for(state="visible", timeout=10000)
    #     elem = await get_elem_by_bid(page, bid, demo_mode != "off")
    #     await add_demo_mode_effects(page, elem, bid, demo_mode=demo_mode, move_cursor=True)

    #     async def do(force: bool):
    #         await elem.click(button=button, modifiers=modifiers, force=force, timeout=10000)

    #     await call_fun(do, retry_with_force)

    async def hover_element(self, page, bid: str = None, x: float = None, y: float = None):
        """Hovers over an element with the given ID or at given coordinates."""
        if x is not None and y is not None:
            await page.mouse.move(x, y)
            await asyncio.sleep(1)  # Give time for content to appear
        elif bid is not None:
            await page.locator(f'[bid="{bid}"]').hover(force=True)

    async def click_element(self, page, bid: str):
        """Clicks an element with the given ID."""
        await page.locator(f'[bid="{bid}"]').click(force=True)


    async def scroll_page(self, page, direction: str):
        """Scrolls the page and waits for it to re-render."""
        if direction == "down":
            await page.evaluate("window.scrollBy(0, window.innerHeight * 0.9)")
            await asyncio.sleep(0.6)

    '''
    The functions below are different implementations of click.

    The reason click didnt work initially is because it actually worked
    but it opened a new tab. We can check that with len(context.pages)
    '''
    # def find_text_from_bid(self, axtree_str: str, bid: str) -> str:
    #     """
    #     Given an axtree string and a bid, return the text value for that bid.
    #     Prints all bid/text pairs for debugging.
    #     """
    #     import re
    #     bid_text_pairs = []
    #     for line in axtree_str.splitlines():
    #         match = re.search(r"\[(\d+)\].*?'(.*?)'", line)
    #         if match:
    #             found_bid, text = match.groups()
    #             bid_text_pairs.append((found_bid, text))
    #     # print("[find_text_from_bid] All bid/text pairs:")
    #     # for b, t in bid_text_pairs:
    #     #     # print(f"  BID: {b} TEXT: '{t}'")
    #     for b, t in bid_text_pairs:
    #         if b == str(bid):
    #     #         # print(f"[find_text_from_bid] For BID {bid}, found text: '{t}'")
    #             return t
    #     print(f"[find_text_from_bid] No text found for BID {bid}")
    #     return None

    # async def click_by_text(self, page, axtree_str: str, bid: str):
    #     """
    #     Clicks an element by its text value, found via the bid in the axtree string.
    #     Prints the bid and text for debugging.
    #     """
    #     text = self.find_text_from_bid(axtree_str, bid)
    #     print(f"[click_by_text] Attempting to click by text for BID {bid}: '{text}'")
    #     if text:
    #         locator = page.locator(f'text="{text}"')
    #         await locator.first.wait_for(state="visible", timeout=10000)
    #         await locator.first.click()
    #         print(f"[click_by_text] Clicked element with text: '{text}'")
    #         return True
    #     else:
    #         print(f"[click_by_text] No text found for BID {bid}, cannot click.")
    #         return False

    # def xy_by_bid(self, extra_element_properties: dict, bid: str):
    #     """
    #     Given extra_element_properties and a bid, return the (x, y) center of the element's bbox.
    #     """
    #     props = extra_element_properties.get(bid)
    #     if props and 'bbox' in props and props['bbox']:
    #         bbox = props['bbox']  # [x, y, w, h]
    #         center_x = bbox[0] + bbox[2] / 2
    #         center_y = bbox[1] + bbox[3] / 2
    #         return center_x, center_y
    #     print(f"[xy_by_bid] No bbox found for BID {bid}")
    #     return None, None

    # async def click_by_xy(self, page, x: float, y: float):
    #     """
    #     Moves the mouse to (x, y) and clicks. The visualization is now handled by annotating the screenshot.
    #     """
    #     await page.mouse.move(x, y)
    #     await page.mouse.click(x, y)
    #     print(f"[click_by_xy] Clicked at ({x}, {y}).")