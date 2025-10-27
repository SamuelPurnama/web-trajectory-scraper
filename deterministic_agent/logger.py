import json
import os
from typing import Any, Dict
import asyncio
from PIL import Image
import io
import re
import pkgutil
from datetime import datetime

import fasthtml.common as ft
from playwright.async_api import async_playwright
from browserbase import Browserbase

API, PROJ = os.environ["BROWSERBASE_API_KEY"], os.environ["BROWSERBASE_PROJECT_ID"]
CAPTCHA_WAIT_MS = 5000
BROWSERGYM_ID_ATTRIBUTE = "bid"

IGNORED_AXTREE_ROLES = [
    "RootWebArea",
    "SvgRoot",
    "graphics-symbol",
]

IGNORED_AXTREE_PROPERTIES = [
    "readonly",
    "focusable",
    "editable",
    "describedby",
    "multiline",
    "keyshortcuts",
    "roledescription",
    "valuemin",
    "valuemax",
    "valuenow",
    "controls",
    "flowto",
    "autocomplete",
]


# This is the async equivalent of browsergym.observation._pre_extract
async def pre_extract(page, tags_to_mark="all"):
    js_frame_mark_elements = pkgutil.get_data(__name__, "javascript/frame_mark_elements.js").decode("utf-8")

    async def mark_frames_recursive(frame, frame_bid: str):
        try:
            if frame.is_detached():
                return

            await frame.evaluate(js_frame_mark_elements, [frame_bid, BROWSERGYM_ID_ATTRIBUTE, tags_to_mark])
            
            for child_frame in frame.child_frames:
                if child_frame.is_detached():
                    continue
                
                child_frame_elem = await child_frame.frame_element()
                child_frame_bid = await child_frame_elem.get_attribute(BROWSERGYM_ID_ATTRIBUTE)
                
                if child_frame_bid is None:
                    continue
                
                await mark_frames_recursive(child_frame, frame_bid=child_frame_bid)
        except Exception as e:
            # Ignore detached frame errors as they are common race conditions
            if "Frame was detached" not in str(e) and "has been detached" not in str(e):
                print(f"Warning: Error during pre_extract: {e}")


    await mark_frames_recursive(page.main_frame, frame_bid="")

# This is the async equivalent of browsergym.observation._post_extract
async def post_extract(page):
    js_frame_unmark_elements = pkgutil.get_data(__name__, "javascript/frame_unmark_elements.js").decode("utf-8")
    for frame in page.frames:
        try:
            if not frame.is_detached():
                await frame.evaluate(js_frame_unmark_elements)
        except Exception as e:
            # Ignore detached frame errors
            if "Frame was detached" not in str(e) and "has been detached" not in str(e):
                print(f"Warning: Error during post_extract: {e}")

# This is the async equivalent of browsergym.observation.extract_dom_snapshot
async def extract_dom_snapshot(page):
    cdp = await page.context.new_cdp_session(page)
    dom_snapshot = await cdp.send(
        "DOMSnapshot.captureSnapshot",
        {
            "computedStyles": [],
            "includeDOMRects": True,
            "includePaintOrder": True,
        },
    )
    await cdp.detach()
    return dom_snapshot

# This is the async equivalent of browsergym.observation.extract_all_frame_axtrees
async def extract_all_frame_axtrees(page):
    cdp = await page.context.new_cdp_session(page)
    frame_tree = await cdp.send("Page.getFrameTree")
    frame_ids = []
    frames_to_process = [frame_tree["frameTree"]]
    while frames_to_process:
        frame = frames_to_process.pop()
        frames_to_process.extend(frame.get("childFrames", []))
        frame_ids.append(frame["frame"]["id"])

    frame_axtrees = {}
    for frame_id in frame_ids:
        try:
            frame_axtrees[frame_id] = await cdp.send(
                "Accessibility.getFullAXTree", {"frameId": frame_id}
            )
        except Exception:
            continue
    await cdp.detach()

    for ax_tree in frame_axtrees.values():
        for node in ax_tree["nodes"]:
            data_items = []
            if "properties" in node:
                for i, prop in enumerate(node["properties"]):
                    if prop["name"] == "roledescription":
                        match = re.match(r"browsergym_id_(\S+)\s?(.*)", prop["value"]["value"])
                        if match:
                            bid, new_value = match.groups()
                            data_items.append(bid)
                            prop["value"]["value"] = new_value
                            if new_value == "":
                                del node["properties"][i]
                            break
            if data_items:
                node["browsergym_id"] = data_items[0]
    return frame_axtrees

# This is the async equivalent of browsergym.observation.extract_merged_axtree
async def extract_merged_axtree(page):
    frame_axtrees = await extract_all_frame_axtrees(page)
    cdp = await page.context.new_cdp_session(page)
    merged_axtree = {"nodes": []}
    for ax_tree in frame_axtrees.values():
        merged_axtree["nodes"].extend(ax_tree["nodes"])
        for node in ax_tree["nodes"]:
            if node["role"]["value"] == "Iframe" and "backendDOMNodeId" in node:
                try:
                    dom_node = await cdp.send("DOM.describeNode", {"backendNodeId": node["backendDOMNodeId"]})
                    frame_id = dom_node.get("node", {}).get("frameId")
                    if frame_id in frame_axtrees:
                        frame_root_node = frame_axtrees[frame_id]["nodes"][0]
                        node["childIds"].append(frame_root_node["nodeId"])
                except Exception:
                    continue
    await cdp.detach()
    return merged_axtree

def extract_dom_extra_properties(dom_snapshot):
    def to_string(idx):
        return dom_snapshot["strings"][idx] if idx != -1 else None

    bid_string_id = dom_snapshot["strings"].index(BROWSERGYM_ID_ATTRIBUTE) if BROWSERGYM_ID_ATTRIBUTE in dom_snapshot["strings"] else -1
    vis_string_id = dom_snapshot["strings"].index("browsergym_visibility_ratio") if "browsergym_visibility_ratio" in dom_snapshot["strings"] else -1
    som_string_id = dom_snapshot["strings"].index("browsergym_setofmarks") if "browsergym_setofmarks" in dom_snapshot["strings"] else -1

    extra_properties = {}
    for doc_idx, document in enumerate(dom_snapshot["documents"]):
        for node_idx, node_attrs in enumerate(document["nodes"]["attributes"]):
            bid = None
            visibility = None
            som = None
            for i in range(0, len(node_attrs), 2):
                name_id = node_attrs[i]
                value_id = node_attrs[i+1]
                if name_id == bid_string_id:
                    bid = to_string(value_id)
                elif name_id == vis_string_id:
                    try:
                        visibility = float(to_string(value_id))
                    except (ValueError, TypeError):
                        visibility = 0.0
                elif name_id == som_string_id:
                    som = to_string(value_id) == "1"

            if bid:
                try:
                    layout_idx = document["layout"]["nodeIndex"].index(node_idx)
                    bounds = document["layout"]["bounds"][layout_idx]
                    clickable = node_idx in document["nodes"].get("isClickable", {}).get("index", [])
                    extra_properties[bid] = {
                        "visibility": visibility,
                        "bbox": bounds,
                        "clickable": clickable,
                        "set_of_marks": som
                    }
                except (ValueError, KeyError):
                     extra_properties[bid] = {
                        "visibility": visibility,
                        "bbox": None,
                        "clickable": False,
                        "set_of_marks": som
                    }

    return extra_properties


def _get_coord_str(coord, decimals):
    import ast
    if isinstance(coord, str):
        coord = list(map(float, ast.literal_eval(coord)))
    coord_format = f".{decimals}f"
    coord_str = ",".join([f"{c:{coord_format}}" for c in coord])
    return f"({coord_str})"


def _process_bid(
    bid,
    extra_properties: dict = None,
    with_visible: bool = False,
    with_clickable: bool = False,
    with_center_coords: bool = False,
    with_bounding_box_coords: bool = False,
    with_som: bool = False,
    filter_visible_only: bool = False,
    filter_with_bid_only: bool = False,
    filter_som_only: bool = False,
    coord_decimals: int = 0,
):
    if extra_properties is None:
        if any(
            (
                with_visible,
                with_clickable,
                with_center_coords,
                with_bounding_box_coords,
                with_som,
                filter_visible_only,
                filter_with_bid_only,
                filter_som_only,
            )
        ):
            raise ValueError("extra_properties argument required")
        else:
            extra_properties = {}
    skip_element = False
    attributes_to_print = []
    if bid is None:
        if filter_with_bid_only:
            skip_element = True
        if filter_som_only:
            skip_element = True
        if filter_visible_only:
            pass  # keep elements without visible property
    else:
        if bid in extra_properties:
            node_vis = extra_properties[bid]["visibility"]
            node_bbox = extra_properties[bid]["bbox"]
            node_is_clickable = extra_properties[bid]["clickable"]
            node_in_som = extra_properties[bid]["set_of_marks"]
            node_is_visible = node_vis >= 0.5
            if filter_visible_only and not node_is_visible:
                skip_element = True
            if filter_som_only and not node_in_som:
                skip_element = True
            if with_som and node_in_som:
                attributes_to_print.insert(0, f"som")
            if with_visible and node_is_visible:
                attributes_to_print.insert(0, f"visible")
            if with_clickable and node_is_clickable:
                attributes_to_print.insert(0, f"clickable")
            if with_center_coords and node_bbox is not None:
                x, y, width, height = node_bbox
                center = (x + width / 2, y + height / 2)
                attributes_to_print.insert(0, f'center="{_get_coord_str(center, coord_decimals)}"')
            if with_bounding_box_coords and node_bbox is not None:
                x, y, width, height = node_bbox
                box = (x, y, x + width, y + height)
                attributes_to_print.insert(0, f'box="{_get_coord_str(box, coord_decimals)}"')
    return skip_element, attributes_to_print


def flatten_axtree_to_str(
    AX_tree,
    extra_properties: dict = None,
    with_visible: bool = False,
    with_clickable: bool = False,
    with_center_coords: bool = False,
    with_bounding_box_coords: bool = False,
    with_som: bool = False,
    skip_generic: bool = True,
    filter_visible_only: bool = False,
    filter_with_bid_only: bool = False,
    filter_som_only: bool = False,
    coord_decimals: int = 0,
    ignored_roles=IGNORED_AXTREE_ROLES,
    ignored_properties=IGNORED_AXTREE_PROPERTIES,
    remove_redundant_static_text: bool = True,
    hide_bid_if_invisible: bool = False,
    hide_all_children: bool = False,
    hide_all_bids: bool = False,
) -> str:
    node_id_to_idx = {}
    for idx, node in enumerate(AX_tree["nodes"]):
        node_id_to_idx[node["nodeId"]] = idx
    def dfs(node_idx: int, depth: int, parent_node_filtered: bool, parent_node_name: str) -> str:
        tree_str = ""
        node = AX_tree["nodes"][node_idx]
        indent = "\t" * depth
        skip_node = False
        filter_node = False
        node_role = node["role"]["value"]
        node_name = ""
        if node_role in ignored_roles:
            skip_node = True
            pass
        elif "name" not in node:
            skip_node = True
            pass
        else:
            node_name = node["name"]["value"]
            if "value" in node and "value" in node["value"]:
                node_value = node["value"]["value"]
            else:
                node_value = None
            bid = node.get("browsergym_id", None)
            # extract node attributes
            attributes = []
            for property in node.get("properties", []):
                if not "value" in property:
                    continue
                if not "value" in property["value"]:
                    continue
                prop_name = property["name"]
                prop_value = property["value"]["value"]
                # For image nodes, skip url property entirely
                if node_role == "image" and prop_name == "url":
                    continue
                if prop_name in ignored_properties:
                    continue
                elif prop_name in ("required", "focused", "atomic"):
                    if prop_value:
                        attributes.append(prop_name)
                else:
                    attributes.append(f"{prop_name}={repr(prop_value)}")
            if skip_generic and node_role == "generic" and not attributes:
                skip_node = True
            if hide_all_children and parent_node_filtered:
                skip_node = True
            # Always skip printing StaticText nodes
            if node_role == "StaticText":
                skip_node = True
            # Always skip printing graphics-object nodes
            if node_role == "graphics-object":
                skip_node = True
            else:
                filter_node, extra_attributes_to_print = _process_bid(
                    bid,
                    extra_properties=extra_properties,
                    with_visible=with_visible,
                    with_clickable=with_clickable,
                    with_center_coords=with_center_coords,
                    with_bounding_box_coords=with_bounding_box_coords,
                    with_som=with_som,
                    filter_visible_only=filter_visible_only,
                    filter_with_bid_only=filter_with_bid_only,
                    filter_som_only=filter_som_only,
                    coord_decimals=coord_decimals,
                )
                skip_node = skip_node or filter_node
                attributes = extra_attributes_to_print + attributes
            if not skip_node:
                if node_role == "generic" and not node_name:
                    node_str = f"{node_role}"
                else:
                    node_str = f"{node_role} {repr(node_name.strip())}"
                if not (
                    hide_all_bids
                    or bid is None
                    or (
                        hide_bid_if_invisible
                        and extra_properties.get(bid, {}).get("visibility", 0) < 0.5
                    )
                ):
                    node_str = f"[{bid}] " + node_str
                if node_value is not None:
                    node_str += f' value={repr(node["value"]["value"])}'
                if attributes:
                    node_str += ", ".join([""] + attributes)
                tree_str += f"{indent}{node_str}"
        for child_node_id in node["childIds"]:
            if child_node_id not in node_id_to_idx or child_node_id == node["nodeId"]:
                continue
            child_depth = depth if skip_node else (depth + 1)
            child_str = dfs(
                node_id_to_idx[child_node_id],
                child_depth,
                parent_node_filtered=filter_node,
                parent_node_name=node_name,
            )
            if child_str:
                if tree_str:
                    tree_str += "\n"
                tree_str += child_str
        return tree_str
    tree_str = dfs(0, 0, False, "")
    return tree_str


class PlaywrightLogger:
    def __init__(self, outdir: str, page=None, browser=None):
        self.outdir = outdir
        os.makedirs(outdir, exist_ok=True)
        self.browser = browser
        self.page = page
        self.session = None
        self._owns_session = page is None and browser is None
        self.interactions = []
        self.tab_focus_count = 0
        
    async def __aenter__(self):
        if self._owns_session:
            self.playwright = await async_playwright().start()
            
            # Set the test ID attribute to "bid" like browsergym
            self.playwright.selectors.set_test_id_attribute(BROWSERGYM_ID_ATTRIBUTE)
            
            self.session = Browserbase(api_key=API).sessions.create(
                project_id=PROJ,
                proxies=True,
                browser_settings={"advanced_stealth": True, "solve_captchas": True},
            )
            
            self.browser = await self.playwright.chromium.connect_over_cdp(self.session.connect_url)
            self.page = self.browser.contexts[0].pages[0]
            
            self.solved = {"ok": False}
            self.page.on("console", lambda m: m.text == "browserbase-solving-finished" and self.solved.update(ok=True))
            
            await self.page.set_extra_http_headers({"Accept-Language": "en-US,en;q=0.9"})
            await self.page.evaluate("""() => {
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            }""")
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._owns_session:
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright') and self.playwright:
                await self.playwright.stop()

    def write_to_file(self, content: str, fname: str):
        with open(os.path.join(self.outdir, fname), "w", encoding='utf-8') as file:
            file.write(content)

    def log_json(self, data: Any, fname: str, indent: int | None = 2):
        with open(os.path.join(self.outdir, fname), "w", encoding='utf-8') as file:
            json.dump(data, file, indent=indent, ensure_ascii=False)

    def log_image(self, img: Image.Image, fname: str):
        image_dir = os.path.join(self.outdir, "images")
        os.makedirs(image_dir, exist_ok=True)
        img.save(os.path.join(image_dir, fname))

    async def navigate_to_url(self, url: str):
        for w in ("domcontentloaded", "load", "networkidle"):
            try:
                await self.page.goto(url, wait_until=w, timeout=90000)
                break
            except:
                continue

        if not self.solved["ok"]:
            await self.page.wait_for_timeout(CAPTCHA_WAIT_MS)

    async def log_screenshot(self, step: int):
        file_step = step + 1
        screenshot_name = f"screenshot_{str(file_step).zfill(3)}.png"
        screenshot_bytes = await self.page.screenshot(full_page=False)
        
        img = Image.open(io.BytesIO(screenshot_bytes))
        self.log_image(img, screenshot_name)
        return screenshot_name

    async def log_current_url(self, step: int):
        file_step = step + 1
        os.makedirs(os.path.join(self.outdir, "urls"), exist_ok=True)
        url_name = f"url_{str(file_step).zfill(3)}.txt"
        current_url = self.page.url
        self.write_to_file(current_url, os.path.join("urls", url_name))
        return url_name

    async def log_html(self, step: int):
        file_step = step + 1
        os.makedirs(os.path.join(self.outdir, "html"), exist_ok=True)
        html_name = f"html_{str(file_step).zfill(3)}.html"
        html_content = await self.page.content()
        self.write_to_file(html_content, os.path.join("html", html_name))
        return html_name

    async def log_axtree(self, step: int):
        file_step = step + 1
        os.makedirs(os.path.join(self.outdir, "axtree"), exist_ok=True)
        os.makedirs(os.path.join(self.outdir, "global_axtree"), exist_ok=True)
        viewport_axtree_name = f"axtree_{str(file_step).zfill(3)}.txt"
        global_axtree_name = f"global_axtree_{str(file_step).zfill(3)}.txt"
        
        try:
            # 1. Mark elements
            await pre_extract(self.page)
            
            # 2. Extract DOM snapshot and AXTree
            dom_snapshot = await extract_dom_snapshot(self.page)
            axtree_object = await extract_merged_axtree(self.page)
            
            # 3. Extract extra properties from DOM snapshot
            extra_element_properties = extract_dom_extra_properties(dom_snapshot)

            if not axtree_object or not axtree_object.get("nodes"):
                self.write_to_file("", os.path.join("axtree", viewport_axtree_name))
                self.write_to_file("", os.path.join("global_axtree", global_axtree_name))
                return viewport_axtree_name
            
            # 4. Generate viewport axtree string (filtered by visibility)
            viewport_axtree_str = flatten_axtree_to_str(
                axtree_object,
                extra_properties=extra_element_properties,
                with_visible=True,
                filter_visible_only=True,
                filter_with_bid_only=False,
                with_clickable=True,
                skip_generic=True,
            )
            self.write_to_file(viewport_axtree_str, os.path.join("axtree", viewport_axtree_name))

            # 5. Generate global axtree string (not filtered by visibility)
            global_axtree_str = flatten_axtree_to_str(
                axtree_object,
                extra_properties=extra_element_properties,
                with_visible=True,
                filter_visible_only=False,
                filter_with_bid_only=False,
                with_clickable=True,
                skip_generic=True,
            )
            self.write_to_file(global_axtree_str, os.path.join("global_axtree", global_axtree_name))

            # 6. Clean up markings
            await post_extract(self.page)
            
            return viewport_axtree_name
            
        except Exception as e:
            print(f"Error extracting axtree: {str(e)}")
            self.write_to_file("", os.path.join("axtree", viewport_axtree_name))
            self.write_to_file("", os.path.join("global_axtree", global_axtree_name))
            await post_extract(self.page) # Try to cleanup even if there was an error
            return viewport_axtree_name

    async def log_extra_element_properties(self, step: int):
        file_step = step + 1
        os.makedirs(
            os.path.join(self.outdir, "extra_element_properties"), exist_ok=True
        )
        
        extra_element_properties_name = (
            f"extra_element_properties_{str(file_step).zfill(3)}.json"
        )
        
        await pre_extract(self.page)
        dom_snapshot = await extract_dom_snapshot(self.page)
        extra_element_properties = extract_dom_extra_properties(dom_snapshot)
        await post_extract(self.page)
        
        visible_properties = {
            bid: props for bid, props in extra_element_properties.items() if props.get("visibility") == 1.0
        }
        
        self.log_json(
            data=visible_properties,
            fname=os.path.join("extra_element_properties", extra_element_properties_name),
            indent=None
        )
        return extra_element_properties_name

    async def get_obs(self, step: int = 0):
        obs = await self.log_all_data(step, write_files=False)
        # Remove viewport node filtering; always use full axtree
        full_axtree_obj = obs['axtree_object']
        extra_props = obs['extra_element_properties']
        obs['axtree'] = full_axtree_obj
        obs['global_axtree'] = full_axtree_obj
        return obs

    async def write_log_files(self, obs, step):
        file_step = step + 1
        # Always use the full axtree_object for both outputs
        axtree_str = flatten_axtree_to_str(
            obs['axtree_object'],
            extra_properties=obs['extra_element_properties'],
            with_visible=True,
            filter_visible_only=True,
            filter_with_bid_only=False,
            with_clickable=True,
            skip_generic=True,
        )
        global_axtree_str = flatten_axtree_to_str(
            obs['axtree_object'],
            extra_properties=obs['extra_element_properties'],
            with_visible=True,
            filter_visible_only=False,
            filter_with_bid_only=False,
            with_clickable=True,
            skip_generic=True,
        )

        # Manually write the files from the observation dict
        # Ensure directories exist
        os.makedirs(os.path.join(self.outdir, "images"), exist_ok=True)
        os.makedirs(os.path.join(self.outdir, "urls"), exist_ok=True)
        os.makedirs(os.path.join(self.outdir, "html"), exist_ok=True)
        os.makedirs(os.path.join(self.outdir, "axtree"), exist_ok=True)
        os.makedirs(os.path.join(self.outdir, "global_axtree"), exist_ok=True)
        os.makedirs(os.path.join(self.outdir, "extra_element_properties"), exist_ok=True)

        self.log_image(obs['screenshot'], f"screenshot_{str(file_step).zfill(3)}.png")
        self.write_to_file(obs['url_str'], os.path.join("urls", f"url_{str(file_step).zfill(3)}.txt"))
        self.write_to_file(obs['html_str'], os.path.join("html", f"html_{str(file_step).zfill(3)}.html"))
        self.write_to_file(axtree_str, os.path.join("axtree", f"axtree_{str(file_step).zfill(3)}.txt"))
        self.write_to_file(global_axtree_str, os.path.join("global_axtree", f"global_axtree_{str(file_step).zfill(3)}.txt"))
        self.log_json(obs['extra_element_properties'], os.path.join("extra_element_properties", f"extra_element_properties_{str(file_step).zfill(3)}.json"))


    async def log_all_data(self, step: int = 0, write_files=True):
        results = {}
        
        await asyncio.sleep(3)
        
        # Capture raw data
        screenshot_bytes = await self.page.screenshot(full_page=False)
        results['screenshot'] = Image.open(io.BytesIO(screenshot_bytes))
        results['url_str'] = self.page.url
        results['html_str'] = await self.page.content()
        
        await pre_extract(self.page)
        dom_snapshot = await extract_dom_snapshot(self.page)
        axtree_object = await extract_merged_axtree(self.page)
        extra_element_properties = extract_dom_extra_properties(dom_snapshot)
        await post_extract(self.page)
        
        results['extra_element_properties'] = extra_element_properties
        results['axtree_object'] = axtree_object # Store the raw object
        
        if write_files:
            await self.write_log_files(results, step)
            
        return results

    def log_system_message(self, msg: str):
        self.write_to_file(content=msg, fname="system_message.md")

    def log_user_message(self, user_message_str: str, step: int):
        file_step = step + 1
        os.makedirs(os.path.join(self.outdir, "user_message"), exist_ok=True)
        user_message_name = f"user_message_{str(file_step).zfill(3)}.txt"
        self.write_to_file(
            user_message_str, os.path.join("user_message", user_message_name)
        )
        return user_message_name

    def record_interaction(self, step: int, obs: Dict, action: Dict, error: str | None = None):
        """Records the state, action, and outcome of a single step."""
        file_step = step + 1
        screenshot_name = f"screenshot_{str(file_step).zfill(3)}.png"
        axtree_name = f"axtree_{str(file_step).zfill(3)}.txt"
        global_axtree_name = f"global_axtree_{str(file_step).zfill(3)}.txt"
        extra_props_name = f"extra_element_properties_{str(file_step).zfill(3)}.json"

        if action.get("action") == "click" and "bid" in action:
            bid = action["bid"]
            action.setdefault("button", "left")
            action.setdefault("click_type", "single")

            extra_props = obs.get("extra_element_properties", {})
            if bid in extra_props:
                action["bbox"] = extra_props[bid].get("bbox")

            axtree_nodes = obs.get("axtree_object", {}).get("nodes", [])
            for node in axtree_nodes:
                if node.get("browsergym_id") == bid:
                    node_props = {
                        "role": node.get("role", {}).get("value"),
                        "value": node.get("name", {}).get("value")
                    }
                    if "value" in node and "value" in node["value"]:
                        node_props["value"] = node["value"]["value"]
                    action["node_properties"] = node_props
                    break
        
        interaction_data = {
            "step": file_step,
            "screenshot": os.path.join("images", screenshot_name),
            "axtree": os.path.join("axtree", axtree_name),
            "global_axtree": os.path.join("global_axtree", global_axtree_name),
            "extra_element_properties": os.path.join("extra_element_properties", extra_props_name),
            "action": action,
            "error": error,
            "timestamp": datetime.now().isoformat(),
            "url": obs.get("url_str", ""),
        }
        self.interactions.append(interaction_data)

    def log_trajectory_json(self):
        """Saves the recorded interactions to trajectory.json."""
        trajectory_data = {}
        for interaction in self.interactions:
            step = interaction["step"]
            action_dict = interaction.get("action", {})
            action_name = action_dict.get("action")
            action_params = {k: v for k, v in action_dict.items() if k != "action"}
            thought = action_params.pop("thought", "")

            action_str = ""
            action_description = ""
            if action_name:
                params_str = ", ".join(f"{k}={repr(v)}" for k, v in action_params.items() if k not in ["bbox", "node_properties"])
                action_str = f"{action_name}({params_str})"

                if action_name == "goto":
                    action_description = f"go to {action_params.get('url', '')}"
                elif action_name == "click":
                    node_props = action_params.get("node_properties", {})
                    role = node_props.get('role', 'element')
                    value = node_props.get('value', '')
                    button = action_params.get('button', 'left')
                    action_description = f"{button} click on {role} with value '{value}'"
                elif action_name == "type":
                    action_description = f"type '{action_params.get('text', '')}' in element with bid {action_params.get('bid', '')}"
                elif action_name == "scroll":
                    action_description = f"scroll on element with bid {action_params.get('bid', '')} in direction {action_params.get('direction', '')}"
                elif action_name == "tab_focus":
                    action_description = f"focus tab {action_params.get('tab_id', '')}"
                elif action_name == "exit":
                    action_description = "exit"
                else:
                    action_description = action_str


            new_interaction = {
                "screenshot": os.path.basename(interaction.get("screenshot", "")),
                "axtree": os.path.basename(interaction.get("axtree", "")),
                "user_message": "",
                "other_obs": {
                    "page_index": 0,
                    "url": interaction.get("url", ""),
                    "open_pages_titles": [],
                    "open_pages_urls": [interaction.get("url", "")]
                },
                "action": {
                    "action_str": action_str,
                    "action_description": action_description,
                    "action_output": {
                        "thought": thought,
                        "action": action_params,
                        "action_name": action_name
                    }
                },
                "error": interaction.get("error"),
                "action_timestamp": datetime.fromisoformat(interaction["timestamp"]).timestamp() if "timestamp" in interaction else None,
            }
            trajectory_data[str(step)] = new_interaction
        self.log_json(trajectory_data, "trajectory.json")

    def log_metadata(self, task: Dict, eps_name: str):
        """Saves the task path information to metadata.json."""
        task_details = {
            "task_type": task.get("task_type", ""),
            "keyword": task.get("keyword", ""),
            "steps": task.get("steps", []),
            "instruction": task.get("instruction", {
                "high_level": "",
                "mid_level": "",
                "low_level": ""
            })
        }
        
        metadata = {
            "goal": "",
            "eps_name": eps_name,
            "task": task_details,
            "path": task.get("path", []),
            "viewport": task.get("viewport", {}),
        }
        self.log_json(metadata, "metadata.json")

    def log_trajectory_html(self, task_name: str, task: Dict):
        """Creates an HTML report of the trajectory, visually aligned with the reference, using only original fields."""

        def create_page(elements):
            return ft.Html(
                ft.Head(ft.Title("Trajectory Report")),
                ft.Body(
                    ft.Div(
                        *elements,
                        cls="container",
                        style="margin: 20px auto; width: 90%;",
                    )
                ),
            )

        def create_card(header_content, body_content, footer_content=None):
            return ft.Card(
                ft.Div(
                    body_content,
                    cls="row",
                ),
                header=header_content,
                footer=footer_content,
            )

        # Header and task details
        elements = [
            ft.Div(
                ft.H1(f"{task_name}"),
                ft.H2("Task Details"),
                ft.Pre(ft.Code(json.dumps(task, indent=2))),
            ),
            ft.H2("Trajectory"),
        ]

        for interaction in self.interactions:
            screenshot = interaction.get("screenshot", "")
            axtree = interaction.get("axtree", "")
            global_axtree = interaction.get("global_axtree", "")
            extra_props = interaction.get("extra_element_properties", "")
            action = interaction.get("action", {})
            error = interaction.get("error", "")
            timestamp = interaction.get("timestamp", "")
            step = interaction.get("step", "")
            url = interaction.get("url", "")

            # Card header
            card_header = ft.Div(
                f"Step {step}",
                ft.Code(timestamp, style="float: right;"),
            )

            # Card body: two columns (screenshot, action JSON)
            card_body = ft.Div(
                ft.Div(
                    ft.Img(src=screenshot, style="width: 100%; max-width: 600px; border: 1px solid #ddd;"),
                    cls="col-xs-6",
                ),
                ft.Br(),
                ft.Div(
                    ft.H6("Action"),
                    ft.Pre(ft.Code(json.dumps(action, indent=2))),
                    cls="col-xs-6",
                ),
                cls="row",
            )

            # Card footer: diagnostics
            card_footer = ft.Div(
                ft.Details(
                    ft.Summary("Diagnostics"),
                    ft.Ul(
                        ft.Li(f"URL: {url}"),
                        ft.Li(f"AXTree: {axtree}"),
                        ft.Li(f"Global AXTree: {global_axtree}"),
                        ft.Li(f"Extra Properties: {extra_props}"),
                        ft.Li(f"Error: {error}"),
                    ),
                ),
            )

            elements.append(
                ft.Div(
                    create_card(
                        header_content=card_header,
                        body_content=card_body,
                        footer_content=card_footer,
                    ),
                )
            )

        html_content = ft.to_xml(create_page(elements))
        self.write_to_file(html_content, "trajectory.html")