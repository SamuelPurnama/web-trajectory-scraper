'''

Peters old implementation of the node traversal agent.
Shouldnt be used anymore, but lets keep it around for now.

Use the agent in deterministic_agent
'''

import re
import os
from typing import Any, Dict, List, Tuple
from urllib.parse import urljoin, urlparse, parse_qs

from browsergym.utils.obs import flatten_axtree_to_str

from agent.actions import (
    ActionOutput, 
    Click, 
    Goto, 
    SendMsgToUser, 
    Scroll, 
    ReportInfeasible,
    Hover,
    describe_action
)
from agent.utils import AgentBase


class NodeTraversalAgent(AgentBase):
    """Simple agent that navigates through a path of URLs using basic actions."""
    
    def __init__(self, path: List[str]):
        """Initialize with a list of URLs to navigate through."""
        self.path = path
        self.current_step = 0
        self.past_actions: List[Dict[str, Any]] = []
        self.past_urls: List[str] = []
        self.last_model_inputs: Dict[str, Any] | None = None
        self.scroll_attempts = 0
        self.max_scroll_attempts = 60  # Should be set to 20 in real use. using 3 for testing
        self.last_content_signature = ""  # Track page content to detect any changes
        self.task_infeasible = False
        self._last_url = ""
        self.expanded_axtrees: Dict[int, str] = {}  # Store expanded axtrees by interaction step
        self.interaction_step = 0  # Track current interaction step for logging alignment
        self.hover_candidates: Dict[int, List[str]] = {}  # Store hover candidates by interaction step
        self.last_action_was_hover = False  # Track if the last action was a hover
        self.just_clicked_target_link = False  # Track if we just clicked a link intended for current target
        self.scroll_stop_reason = ""  # Track why scrolling stopped
        
    def reset(self):
        """Reset agent state."""
        self.current_step = 0
        self.past_actions = []
        self.past_urls = []
        self.last_model_inputs = None
        self.scroll_attempts = 0
        self.last_content_signature = ""
        self.task_infeasible = False
        self._last_url = ""
        self.expanded_axtrees = {}
        self.interaction_step = 0
        self.hover_candidates = {}
        self.last_action_was_hover = False
        self.just_clicked_target_link = False
        self.scroll_stop_reason = ""
        
    def predict_action(self, obs: Dict[str, Any], env=None) -> Dict[str, Any]:
        """Predict next action based on current observation."""
        # Increment interaction step for logging alignment
        self.interaction_step += 1
        
        if self.task_infeasible:
            return self._end_episode("Task was already reported as infeasible, ending episode.")
            
        current_url = obs["url"]
        self._last_url = current_url
        axtree_str = self._get_axtree_str(obs)
        
        self.last_model_inputs = {
            "axtree_str": axtree_str,
            "current_url": current_url,
            "current_step": self.current_step,
            "target_path": self.path,
            "user_message": f"NodeTraversalAgent - Step {self.current_step}: Navigate from {current_url} to path {self.path}",
            "system_message": "NodeTraversalAgent: Simple agent for URL navigation",
            "page_index": int(obs["active_page_index"][0]) if "active_page_index" in obs else 0,
            "url": current_url,
            "open_pages_titles": obs.get("open_pages_titles", []),
            "open_pages_urls": obs.get("open_pages_urls", []),
        }
        
        if self.current_step >= len(self.path):
            return self._end_episode("Navigation complete!")
            
        target_url = self.path[self.current_step]
        
        # Handle initial navigation
        if self.current_step == 0 and current_url != target_url:
            action_output = ActionOutput(
                thought=f"Going to start URL: {target_url}",
                action=Goto(url=target_url)
            )
            self.current_step += 1
            return self._create_action_dict(action_output, obs)
        
        # Check if we've reached the target URL
        url_match_result = self._url_matches(current_url, target_url)
        
        if url_match_result:
            #########
            # so there is an issue here:
            # often times you click a link but where you end up is not the link you clicked.
            # some sort of redirect is happening.
            # if this case we should continue still 
            #########
            # print(f"[DEBUG] URL match: {current_url} matches {target_url}")
            self.current_step += 1
            self.scroll_attempts = 0
            self.last_content_signature = ""  # Reset for next target
            self.last_action_was_hover = False  # Reset hover tracking
            self.just_clicked_target_link = False  # Reset click tracking
            if self.current_step >= len(self.path):
                return self._end_episode("All URLs visited successfully!")
            target_url = self.path[self.current_step]
        
        # Check if we just clicked a link intended for current target (handles redirects)
        elif self.just_clicked_target_link:
            # print(f"[DEBUG] Redirect detected: {current_url} (target was {target_url})")
            self.current_step += 1
            self.scroll_attempts = 0
            self.last_content_signature = ""  # Reset for next target
            self.last_action_was_hover = False  # Reset hover tracking
            self.just_clicked_target_link = False  # Reset click tracking
            if self.current_step >= len(self.path):
                return self._end_episode("All URLs visited successfully!")
            target_url = self.path[self.current_step]

        # If last action was hover, give it a moment and check if target link is now visible
        if self.last_action_was_hover:
            # print(f"[DEBUG] Checking if hover revealed target link...")
            self.last_action_was_hover = False  # Reset the flag
            # Small delay to allow DOM to update after hover
            import time
            time.sleep(0.5)
            
        # Check if target link is directly visible
        link_bid = self._find_link(obs, target_url)
        
        if link_bid:
            # Try clicking with retry logic for frame issues
            click_result = self._try_click_with_retry(obs, link_bid, target_url)
            if click_result:
                self.scroll_attempts = 0
                return click_result
            else:
                # Click failed after all retries, exit/report infeasible
                return self._stop_infeasible(f"Cannot navigate to {target_url} - click failed after all retry attempts")
        else:
            # print(f"No link found for target URL: {target_url}")
            pass
        
        # Try hover candidates before scrolling (only on first attempt and if env is available)
        if self.scroll_attempts == 0 and env is not None:
            # print(f"Link not found in current view, checking hover candidates...")
            hover_candidates = self._try_find_hover_candidates(obs, target_url, env)
            if hover_candidates:
                # print(f"Found hover candidates: {hover_candidates}, trying hover approach")
                # Try hovering over the first candidate
                first_candidate = hover_candidates[0]
                self.last_action_was_hover = True  # Set tracking flag
                self.just_clicked_target_link = False  # Reset click tracking since we're hovering
                action_output = ActionOutput(
                    thought=f"Hovering over element {first_candidate} to reveal link to {target_url}",
                    action=Hover(bid=first_candidate)
                )
                self.scroll_attempts += 1  # Count hover as an attempt
                return self._create_action_dict(action_output, obs)
        
        # Handle scrolling for subsequent attempts or when hover isn't available
        current_content = self._get_content_signature(obs)
        content_changed = current_content != self.last_content_signature
        
        if self.scroll_attempts < self.max_scroll_attempts and (self.scroll_attempts == 0 or content_changed):
            self.scroll_attempts += 1
            self.last_content_signature = current_content  # new hash for comparison
            self.just_clicked_target_link = False  # Reset click tracking since we're scrolling
            
            # print(f"[DEBUG] Scrolling attempt {self.scroll_attempts}/{self.max_scroll_attempts} for: {target_url}")
            
            # calculate 90% of screen height for relative scrolling
            screenshot = obs.get("screenshot")
            if screenshot is not None:
                screen_height = screenshot.shape[0]
                scroll_distance = int(screen_height * 0.9)
            else:
                # Fallback to fixed distance if screenshot not available
                scroll_distance = 500
            
            reason = "continuing search" if self.scroll_attempts > 1 else "initial search"
            action_output = ActionOutput(
                thought=f"Scrolling to find link to {target_url} ({reason}, attempt {self.scroll_attempts})",
                action=Scroll(delta_x=0, delta_y=scroll_distance)
            )
            return self._create_action_dict(action_output, obs)
        
        # Determine why scrolling stopped
        if self.scroll_attempts >= self.max_scroll_attempts:
            self.scroll_stop_reason = "ran out of scroll capacity"
            return self._stop_infeasible(f"Cannot find link to {target_url} - ran out of scroll capacity after {self.max_scroll_attempts} scrolls")
        elif not content_changed and self.scroll_attempts > 0:
            self.scroll_stop_reason = "scrolled to the bottom and didn't find link"
            return self._stop_infeasible(f"Cannot find link to {target_url} - scrolled to the bottom and didn't find link")
        else:
            self.scroll_stop_reason = "unknown scroll stop reason"
            return self._stop_infeasible(f"Cannot find link to {target_url} - unknown reason")
    
    def _try_find_hover_candidates(self, obs: Dict[str, Any], target_url: str, env) -> List[str]:
        """Find hover candidates that might reveal the target URL. Returns list of candidate BIDs or empty list."""
        try:
            # Get regular axtree before expansion
            regular_axtree_str = self._get_axtree_str(obs)
            
            # First expand all hoverable elements
            self._expand_hoverable_elements(env)
            
            # Get fresh observation after expansion
            import time
            time.sleep(1)  # Allow time for DOM changes
            expanded_obs = env.unwrapped._get_obs()
            expanded_axtree_str = self._get_axtree_str(expanded_obs)
            
            # Store expanded axtree for later logging
            self.expanded_axtrees[self.interaction_step] = expanded_axtree_str
            # print(f"Stored expanded axtree for interaction step {self.interaction_step}")
            
            # Check if target URL appears in expanded tree
            expanded_link_bid = self._find_link_in_axtree_str(expanded_axtree_str, expanded_obs, target_url)
            
            hover_candidates = []
            if expanded_link_bid is not None:
                # print(f"Target URL {target_url} found in expanded tree at bid {expanded_link_bid}")
                
                # Reset page after expansion to remove JS artifacts
                current_url = obs["url"]
                # print(f"Resetting page after expansion to remove JS artifacts...")
                try:
                    env.unwrapped.page.goto(current_url)
                    time.sleep(1)  # Allow time for page to load
                    # print("Page reset completed")
                except Exception as e:
                    # print(f"WARNING: Failed to reset page: {e}")
                    pass
                
                # Get fresh observation after reset
                try:
                    fresh_obs = env.unwrapped._get_obs()
                    fresh_axtree_str = self._get_axtree_str(fresh_obs)
                    # print("Fresh observation after reset obtained")
                except Exception as e:
                    # print(f"WARNING: Failed to get fresh observation: {e}")
                    fresh_axtree_str = regular_axtree_str  # Fallback
                
                # Recalculate hover candidates using fresh axtree after reset
                hover_candidates = self._find_hover_candidates(fresh_axtree_str, expanded_axtree_str, target_url)
                
                # Store hover candidates for inclusion in verdict
                if not hasattr(self, 'hover_candidates'):
                    self.hover_candidates = {}
                self.hover_candidates[self.interaction_step] = hover_candidates
                # print(f"Found hover candidates (after reset): {hover_candidates}")
            else:
                # Reset page even if no candidates found
                current_url = obs["url"]
                # print(f"Resetting page after expansion (no candidates found)...")
                try:
                    env.unwrapped.page.goto(current_url)
                    time.sleep(1)  # Allow time for page to load
                    # print("Page reset completed")
                except Exception as e:
                    # print(f"WARNING: Failed to reset page: {e}")
                    pass
            
            return hover_candidates
            
        except Exception as e:
            # print(f"DEBUG: Failed to check expanded tree: {e}")
            return []
    
    def _expand_hoverable_elements(self, env) -> None:
        """Expand all hoverable/dropdown elements to reveal hidden links."""
        try:
            js = r"""
            (() => {
              const show = e => {
                if (!e) return;
                e.style.display = 'block';
                e.style.visibility = 'visible';
                e.style.opacity = '1';
                e.style.maxHeight = 'none';
                e.style.height = 'auto';
                e.style.transform = 'none';
              };
              const maybe = e => {
                const s = getComputedStyle(e);
                if (s.display === 'none' || s.visibility === 'hidden' || s.opacity === '0') show(e);
              };
              document.head.insertAdjacentHTML('beforeend', `<style>
                [hidden], [aria-hidden="true"], nav ul, .dropdown, .submenu, .flyout, .menu {
                  display:block!important;visibility:visible!important;opacity:1!important;
                  max-height:none!important;transform:none!important;
                }
              </style>`);
              document.querySelectorAll('[aria-expanded="false"]').forEach(el => {
                el.setAttribute('aria-expanded', 'true');
                el.dispatchEvent(new MouseEvent('mouseover', {bubbles:1}));
              });
              document.querySelectorAll('li').forEach(li => {
                const sub = li.querySelector('ul,.dropdown,.submenu,.flyout');
                if (sub) maybe(sub);
                li.dispatchEvent(new MouseEvent('mouseover', {bubbles:1}));
              });
              document.querySelectorAll('.dropdown,.submenu,.menu,.flyout,nav ul,nav li ul').forEach(maybe);
            })();
            """
            
            # Execute the expansion JavaScript on the page
            env.unwrapped.page.evaluate(js)
            
        except Exception as e:
            # print(f"DEBUG: Failed to expand elements: {e}")
            pass
    


    
    def _find_link_in_axtree_str(self, axtree_str: str, obs: Dict[str, Any], target_url: str) -> str | None:
        """Find clickable element that links to target URL in provided axtree string."""
        extra_properties = obs["extra_element_properties"]
        current_url = obs["url"]
        
        # Updated pattern to handle both single and double quotes around link text
        link_pattern = r'\[(\d+)\] link (?:\'[^\']*\'|"[^"]*"), clickable(?:, visible)?, url=\'([^\']+)\''
        
        for match in re.finditer(link_pattern, axtree_str):
            bid = match.group(1)
            href = match.group(2)
            
            if bid not in extra_properties:
                continue
                
            element_props = extra_properties[bid]
            if not element_props.get("clickable", False):
                continue
            
            absolute_url = urljoin(current_url, href)
            
            if self._url_matches(absolute_url, target_url):
                return bid
                
        return None
    
    def _find_hover_candidates(self, regular_axtree_str: str, expanded_axtree_str: str, target_url: str) -> List[str]:
        """
        Find BID candidates in regular axtree to hover over to reveal target URL.
        Returns list of BIDs in priority order:
        1. Smallest listitem BID above target (if exists)
        2. 3 largest listitem BIDs below target
        
        Returns list of up to 4 BIDs in priority order.
        """
        import re
        
        # print(f"DEBUG: Finding hover candidates for target URL: {target_url}")
        
        # Step 1: Find target URL BID in expanded axtree
        target_bid_expanded = self._find_target_bid_in_expanded(expanded_axtree_str, target_url)
        if not target_bid_expanded:
            # print("DEBUG: Target URL not found in expanded axtree")
            return []
        
        target_bid_num = int(target_bid_expanded)
        # print(f"DEBUG: Target BID in expanded: {target_bid_expanded}")
        
        # Step 2: Find all listitem BIDs in regular axtree
        listitem_pattern = r'\[(\d+)\] listitem \'[^\']*\', visible'
        listitem_bids = []
        
        for match in re.finditer(listitem_pattern, regular_axtree_str):
            bid_num = int(match.group(1))
            listitem_bids.append(bid_num)
        
        # print(f"DEBUG: Found listitem BIDs: {sorted(listitem_bids)}")
        
        # Step 3: Find smallest BID above target
        above_target = [bid for bid in listitem_bids if bid > target_bid_num]
        above_target.sort()  # Smallest first
        smallest_above = above_target[0] if above_target else None
        
        # Step 4: Find 3 largest BIDs below target
        below_target = [bid for bid in listitem_bids if bid < target_bid_num]
        below_target.sort(reverse=True)  # Largest first
        largest_below = below_target[:3]
        
        # Step 5: Build final candidate list - smallest above goes first
        candidates = []
        #########################################################
        # maybe there is an issue with how bids get selected I am removing this one for now but we can come back to it. 
        # if smallest_above is not None:
        #     candidates.append(str(smallest_above))
        #     print(f"DEBUG: Added smallest above target: {smallest_above}")
        

        #########################################################


        # Add the 3 largest below target
        candidates.extend([str(bid) for bid in largest_below])
        
        # print(f"DEBUG: Final hover candidates: {candidates}")
        # print(f"DEBUG: Priority order - smallest above {target_bid_num}: {smallest_above if smallest_above else 'none'}, largest below: {largest_below}")
        
        return candidates
    
    def _find_target_bid_in_expanded(self, expanded_axtree_str: str, target_url: str) -> str | None:
        """Find the BID of target URL in expanded axtree."""
        import re
        
        # Look for the target URL in link elements
        link_pattern = r'\[(\d+)\] link \'[^\']*\', clickable(?:, visible)?, url=\'([^\']+)\''
        
        for match in re.finditer(link_pattern, expanded_axtree_str):
            bid = match.group(1)
            url = match.group(2)
            if target_url == url:
                return bid
        return None
    

    
    def _url_matches(self, current_url: str, target_url: str) -> bool:
        """Check if target URL is a subset of current URL."""
        try:
            current_parsed = urlparse(current_url)
            target_parsed = urlparse(target_url)
            
            if current_parsed.scheme != target_parsed.scheme: # http
                return False
                
            if current_parsed.netloc != target_parsed.netloc: # www.bbc.com
                return False
                
            # Normalize paths to handle trailing slash differences
            current_path = current_parsed.path.rstrip('/') if current_parsed.path != '/' else ''
            target_path = target_parsed.path.rstrip('/') if target_parsed.path != '/' else ''
            
            if current_path != target_path: # /culture   
                return False
            
            current_params = parse_qs(current_parsed.query)
            target_params = parse_qs(target_parsed.query)
            
            for key, value in target_params.items():
                if key not in current_params:
                    return False
                if current_params[key] != value:
                    return False
                    
            return True
            
        except Exception as e:
            exact_match = current_url == target_url
            if not exact_match:
                # print(f"URL parsing failed, no match: {e}")
                pass
            return exact_match
    
    def _find_link(self, obs: Dict[str, Any], target_url: str) -> str | None:
        """Find clickable element that links to target URL using flattened axtree for parsing but extra_properties for validation."""
        axtree_str = self._get_axtree_str(obs)
        extra_properties = obs["extra_element_properties"]
        current_url = obs["url"]
        
        # Updated pattern to handle both single and double quotes around link text
        link_pattern = r'\[(\d+)\] link (?:\'[^\']*\'|"[^"]*"), clickable(?:, visible)?, url=\'([^\']+)\''
        
        found_links = 0
        all_links_found = []
        
        # print(f"[DEBUG] Searching for: {target_url}")
        
        for match in re.finditer(link_pattern, axtree_str):
            bid = match.group(1)
            href = match.group(2)
            found_links += 1
            all_links_found.append((bid, href))
            
            if bid not in extra_properties:
                continue
                
            element_props = extra_properties[bid]
            if not element_props.get("clickable", False):
                continue
            
            absolute_url = urljoin(current_url, href)
            
            if self._url_matches(absolute_url, target_url):
                # print(f"[DEBUG] FOUND MATCH: bid={bid}, url='{absolute_url}'")
                return bid
        
        # print(f"[DEBUG] No match found. Total links: {found_links}")
        return None
    
    def _try_click_with_retry(self, obs: Dict[str, Any], original_bid: str, target_url: str) -> Dict[str, Any] | None:
        """Try clicking with retry logic to handle frame/document issues."""
        import time
        
        # First attempt with original element
        if self._validate_element_before_click(obs, original_bid):
            # print(f"DEBUG: First click attempt with original bid {original_bid}")
            self.just_clicked_target_link = True  # Mark that we're clicking a link for current target
            action_output = ActionOutput(
                thought=f"Clicking link to navigate to {target_url}",
                action=Click(bid=original_bid, button="left", click_type="single")
            )
            return self._create_action_dict(action_output, obs)
        
        # If original element failed, try to re-find the link
        # print(f"DEBUG: Original element {original_bid} failed validation, re-finding link")
        # print(f"[DEBUG] Click validation failed for bid {original_bid}, trying alternatives...")
        time.sleep(0.3)  # Short delay for DOM stabilization
        
        # Re-find the link with fresh observation
        fresh_bid = self._find_link(obs, target_url)
        if fresh_bid and fresh_bid != original_bid:
            # print(f"DEBUG: Found fresh element {fresh_bid} for same target")
            if self._validate_element_before_click(obs, fresh_bid):
                self.just_clicked_target_link = True  # Mark that we're clicking a link for current target
                action_output = ActionOutput(
                    thought=f"Clicking re-found link to navigate to {target_url}",
                    action=Click(bid=fresh_bid, button="left", click_type="single")
                )
                return self._create_action_dict(action_output, obs)
        
        # Final retry: wait 3 seconds and try once more
        # print(f"DEBUG: Click approaches failed, waiting 3 seconds for final retry")
        time.sleep(3.0)  # Wait 3 seconds as requested
        
        # Try to find the link one more time
        final_bid = self._find_link(obs, target_url)
        if final_bid and self._validate_element_before_click(obs, final_bid):
            self.just_clicked_target_link = True  # Mark that we're clicking a link for current target
            action_output = ActionOutput(
                thought=f"Final retry: clicking link to navigate to {target_url}",
                action=Click(bid=final_bid, button="left", click_type="single")
            )
            return self._create_action_dict(action_output, obs)
        
        # If all attempts failed, exit/report infeasible
        # print(f"DEBUG: All click attempts failed for {target_url}, reporting as infeasible")
        return None  # Return None to indicate failure, caller should handle exit
    
    def _validate_element_before_click(self, obs: Dict[str, Any], bid: str) -> bool:
        """Validate element is still clickable before attempting to click."""
        import time
        
        # Small delay to allow for any DOM stabilization
        time.sleep(0.5)
        
        extra_properties = obs["extra_element_properties"]
        
        # Check if element still exists in extra_properties
        if bid not in extra_properties:
            # print(f"DEBUG: Element {bid} no longer in extra_properties")
            return False
            
        element_props = extra_properties[bid]
        
        # Check if element is still clickable
        if not element_props.get("clickable", False):
            # print(f"DEBUG: Element {bid} no longer clickable")
            return False
            
        # Check if element is still visible  
        if element_props.get("visibility") != 1:
            # print(f"DEBUG: Element {bid} no longer visible (visibility: {element_props.get('visibility')})")
            return False
            
        # print(f"DEBUG: Element {bid} validation passed")
        return True
    
    def _get_content_signature(self, obs: Dict[str, Any]) -> str:
        """Create a signature of page content to detect any changes."""
        import hashlib
        
        # Get the full axtree string which contains all visible content
        axtree_str = self._get_axtree_str(obs)
        
        # hash content of the current page 
        # to detect changes in text, links, images, any DOM elements
        # hashing is fastest imho
        content_hash = hashlib.md5(axtree_str.encode('utf-8')).hexdigest()
        
        # print(f"Content signature: {content_hash[:8]}... (length: {len(axtree_str)})") # to get the hash 
        return content_hash
    
    def _end_episode(self, message: str) -> Dict[str, Any]:
        """End episode with success message."""
        action_output = ActionOutput(
            thought=message,
            action=SendMsgToUser(msg="[EXIT]")
        )
        obs = {
            "url": getattr(self, '_last_url', ''),
            "active_page_index": [0],
            "open_pages_titles": [],
            "open_pages_urls": [],
            "axtree_object": {},
            "extra_element_properties": {}
        }
        return self._create_action_dict(action_output, obs)
    
    def _stop_infeasible(self, reason: str) -> Dict[str, Any]:
        """Stop due to infeasible task."""
        self.task_infeasible = True
        action_output = ActionOutput(
            thought=reason,
            action=ReportInfeasible(infeasibility_reason=reason)
        )
        obs = {
            "url": getattr(self, '_last_url', ''),
            "active_page_index": [0],
            "open_pages_titles": [],
            "open_pages_urls": [],
            "axtree_object": {},
            "extra_element_properties": {}
        }
        return self._create_action_dict(action_output, obs)
    
    def _create_action_dict(self, action_output: ActionOutput, obs: Dict[str, Any]) -> Dict[str, Any]:
        """Create action dictionary."""
        action_dict = {
            "action_output": action_output,
            "thought": action_output.thought,
            "action_str": action_output.to_str(),
            "action_description": describe_action(
                action_output.action,
                obs.get("axtree_object", {}),
                obs.get("extra_element_properties", {}),
            ) if obs else "",
        }
        
        self.past_actions.append(action_dict)
        if obs:
            self.past_urls.append(obs["url"])
        
        return action_dict
    
    def get_last_model_inputs(self) -> Dict[str, Any] | None:
        """Get last model inputs."""
        return self.last_model_inputs

    def _get_axtree_str(self, obs: Dict[str, Any]) -> str:
        """Get accessibility tree string."""
        return flatten_axtree_to_str(
            obs["axtree_object"],
            extra_properties=obs["extra_element_properties"],
            with_visible=True,
            filter_visible_only=True,
            filter_with_bid_only=True,
            with_clickable=True,
            skip_generic=True,
        )
