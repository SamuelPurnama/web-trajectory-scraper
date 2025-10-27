import json
import base64
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
import traceback
from pydantic import BaseModel, Field, ValidationError
from openai import OpenAI
from PIL import Image
import io
import os
import argparse
import sys
import glob

# Define the pydantic schema
class Instructions(BaseModel):
    high_level: str = Field(description="Instruction to a super smart web browsing assistant with minimal details")
    mid_level: str = Field(description="Instruction to a slightly less smart web browsing assistant with a few details")
    low_level: str = Field(description="Instruction to an average web browsing assistant with full details but avoiding itemized list of steps.")

# OpenAI API key (replace with your key)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

def build_prompt_text(urls):
    prompt_text = f"""
        Write three levels of instructions for a web browsing assistant based on a sequence of web page visits and their screenshots.

        Here are some examples of good instructions:

        Example 1:
        {{
            "high_level": "on allrecipes.com navigate to the page where you can find out how cumin seeds can enhance recipes.",
            "mid_level": "Find a page with recipe featuring cumin seeds on AllRecipes and let me know the details.",
            "low_level": "Head to "allrecipes.com" and use the search function to look for 'cumin seeds.' From the list of results, click on a recipe that has cumin seeds in the title or ingredient list, and navigate to the page."
        }}

        Example 2:
        {{
            "high_level": "Search for 'real world financial applications guidance' using a Google search and then navigate to the page",
            "mid_level": "Go to 'Google.com' and search for 'real world financial applications guidance', skipping any sign-in prompts, then go to the results page.",
            "low_level": "Navigate to Google, bypass any 'sign in' prompts, and use the search bar to look for 'real world financial applications guidance'. Finally, after reaching the search results, naviagte to the page."
        }}

        Now, for the following task:

        This is the sequence of web page visits:
        {urls}

        The screenshots for each page are provided. Write three levels of instructions. Respond with a JSON object like in the examples. You are NOT ALLOWED to put urls into instuctions -- only high level ones like reddit.com is ok, but https://www.reddit.com/r/Minecraft/comments/1max9uz/ is too specific andn not allowed
        """
    return prompt_text

def find_steps(data):
    """
    Finds and returns a list of trajectory steps from the loaded JSON data.
    The data can be a list of steps, or a dictionary containing steps as values.
    """
    if isinstance(data, list):
        if data and isinstance(data[0], dict):
            return data

    if isinstance(data, dict):
        # Handles the case of {"1": {...}, "2": {...}}
        if all(isinstance(v, dict) for v in data.values()) and data:
            try: # Sort by key to preserve order
                return [data[key] for key in sorted(data, key=int)]
            except (ValueError, TypeError): # Fallback for non-integer keys
                return list(data.values())
        
        # If not, maybe the list is one level deeper.
        for value in data.values():
            if isinstance(value, list) and value and isinstance(value[0], dict):
                 return value
    return None

def update_metadata_with_instructions(traj_dir: str):
    """Loads generated instructions and updates the metadata.json file."""
    instruction_path = os.path.join(traj_dir, "instruction_generation_output.json")
    metadata_path = os.path.join(traj_dir, "metadata.json")

    if not os.path.exists(instruction_path) or not os.path.exists(metadata_path):
        return

    try:
        with open(instruction_path, 'r') as f:
            instructions = json.load(f)
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)

        task_section = metadata.setdefault("task", {})
        task_section["instruction"] = instructions

        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    except (IOError, json.JSONDecodeError):
        pass

def run_generation(input_dir, verbose=True):
    # Load trajectory.json
    trajectory_path = os.path.join(input_dir, "trajectory.json")
    try:
        with open(trajectory_path) as f:
            trajectory_data = json.load(f)
    except FileNotFoundError:
        if verbose: print(f"Error: trajectory.json not found in {input_dir}")
        return (False, "trajectory.json not found")

    trajectory = find_steps(trajectory_data)
    
    if trajectory is None:
        if verbose: print(f"Error: Could not find a list of steps in {trajectory_path}")
        return (False, f"Could not find a list of steps in {trajectory_path}")

    # Filter for unique URLs and collect screenshots
    urls = []
    screenshot_paths = []
    last_url = None
    for step in trajectory:
        current_url = step.get("url")
        if not current_url:
            other_obs = step.get("other_obs")
            if isinstance(other_obs, dict):
                current_url = other_obs.get("url")
        
        if current_url and current_url != last_url:
            urls.append(current_url)
            screenshot_path = os.path.join(input_dir, "images", step["screenshot"])
            screenshot_paths.append(screenshot_path)
            last_url = current_url

    # Process screenshots (read, resize, base64)
    screenshots_b64 = []
    for s_path in screenshot_paths:
        try:
            image = Image.open(s_path)
            new_width = int(image.width * 0.25)
            new_height = int(image.height * 0.25)
            image = image.resize((new_width, new_height), Image.LANCZOS)
            buf = io.BytesIO()
            image.save(buf, format="PNG")
            img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
            screenshots_b64.append(img_b64)
        except FileNotFoundError:
            if verbose: print(f"Warning: Screenshot not found, skipping: {s_path}")
            screenshots_b64.append("")
        except Exception as e:
            if verbose: print(f"Error processing screenshot {s_path}: {e}")
            screenshots_b64.append("")

    # Build prompt and message for OpenAI
    # Per user request, skip the first URL and screenshot as it's a randomized start page and not relevant to the user's task.
    prompt_text = build_prompt_text(urls[1:])
    
    message_content = [{"type": "text", "text": prompt_text}]
    # Skip the first screenshot when building the message for the same reason.
    for img_b64 in screenshots_b64[1:]:
        if img_b64:
            message_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{img_b64}"}
            })

    # Save LLM input for debugging as HTML
    llm_input_path = os.path.join(input_dir, "instruction_generation_input.html")
    html_content = f"<h1>Prompt Text</h1><pre>{prompt_text}</pre><h1>Screenshots</h1>"
    # Skip the first screenshot for the HTML output as well.
    for i, img_b64 in enumerate(screenshots_b64[1:]):
        if img_b64:
            # Start screenshot numbering from 2 to reflect that the first was skipped.
            html_content += f"<h2>Screenshot {i+2}</h2><img src='data:image/png;base64,{img_b64}' style='max-width: 100%; border: 1px solid black;'/>"
    with open(llm_input_path, "w") as f:
        f.write(html_content)
    if verbose:
        print(f"Saved LLM input to {llm_input_path}")

    # Call OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": message_content}],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        instructions_json = response.choices[0].message.content
        instructions = Instructions.model_validate_json(instructions_json)

        # Save LLM output
        llm_output_path = os.path.join(input_dir, "instruction_generation_output.json")
        with open(llm_output_path, "w") as f:
            f.write(instructions.model_dump_json(indent=2))
        
        if verbose:
            print(f"Saved LLM output to {llm_output_path}")
            print("\nGenerated instructions:")
            print(instructions.model_dump_json(indent=2))
        return (True, llm_output_path)

    except ValidationError as ve:
        if verbose: print(f"Validation error from OpenAI response: {ve}")
        return (False, f"Validation error from OpenAI response: {ve}")
    except Exception as e:
        if verbose: print(f"An error occurred while communicating with OpenAI: {e}")
        return (False, f"An error occurred while communicating with OpenAI: {e}")

def generation_worker(dir_path: str) -> (str, str, str):
    """
    Worker function that calls run_generation for a single directory.
    """
    try:
        success, message = run_generation(dir_path, verbose=False)
        if success:
            update_metadata_with_instructions(dir_path)
            return (dir_path, "SUCCESS", message)
        else:
            return (dir_path, "FAILED", message)
    except Exception as e:
        # Capture the full traceback
        tb_str = traceback.format_exc()
        return (dir_path, "FAILED", f"Unhandled exception: {e}\n{tb_str}")

def main():
    """
    Finds and processes trajectory directories in parallel to generate instructions.
    """
    parser = argparse.ArgumentParser(
        description="Generates instructions for web browsing tasks from trajectory data.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('paths', nargs='+',
                        help="One or more paths to process.\n"
                             "Can be:\n"
                             "- An individual trajectory directory.\n"
                             "- A parent directory containing trajectories.\n"
                             "- A glob pattern (e.g., 'data/task_*').")
    parser.add_argument('--num-workers', type=int, default=os.cpu_count(),
                        help=f"Number of worker processes. Defaults to CPU cores ({os.cpu_count()}).")

    if len(sys.argv) < 2:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    # Discover trajectory directories
    input_paths = []
    for path_arg in args.paths:
        input_paths.extend(glob.glob(path_arg))

    trajectory_dirs_to_process = set()
    for path in input_paths:
        if not os.path.isdir(path):
            continue
        if os.path.exists(os.path.join(path, "trajectory.json")):
            trajectory_dirs_to_process.add(os.path.abspath(path))
        else:
            subdirectories = [d.path for d in os.scandir(path) if d.is_dir()]
            for subdir in subdirectories:
                if os.path.exists(os.path.join(subdir, "trajectory.json")):
                    trajectory_dirs_to_process.add(os.path.abspath(subdir))

    if not trajectory_dirs_to_process:
        print("\nNo valid trajectory directories found to process.")
        return

    sorted_dirs = sorted(list(trajectory_dirs_to_process))
    print(f"\nFound {len(sorted_dirs)} potential trajectories. Processing with {args.num_workers} workers...")

    # Process in parallel
    results = {"SUCCESS": 0, "FAILED": 0}
    failed_dirs = []

    with ProcessPoolExecutor(max_workers=args.num_workers) as executor:
        future_to_dir = {executor.submit(generation_worker, dir_path): dir_path for dir_path in sorted_dirs}
        
        progress = tqdm(as_completed(future_to_dir), total=len(sorted_dirs), desc="Generating Instructions", unit="dir")
        for future in progress:
            dir_path, status, message = future.result()
            results[status] += 1
            if status == "FAILED":
                failed_dirs.append((dir_path, message))

    # Print summary
    print("\n--- Instruction Generation Summary ---")
    print(f"Total directories processed: {len(sorted_dirs)}")
    print(f"  - Instructions generated: {results['SUCCESS']}")
    print(f"  - Directories failed: {results['FAILED']}")

    if failed_dirs:
        print("\nFailed directories:")
        for dir_path, error in failed_dirs:
            print(f"  - {os.path.basename(dir_path)}: {error}")

if __name__ == "__main__":
    main()
