import json
import os
import argparse
import sys
import glob
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
import traceback
from openai import OpenAI

from generate_instruction import Instructions, find_steps, OPENAI_API_KEY
from pydantic import BaseModel, Field
from typing import List

# Define pydantic schema for steps refinement
class RefinedSteps(BaseModel):
    steps: List[str] = Field(description="List of refined step-by-step instructions")
    goal: str = Field(description="All steps combined into a single goal string")

def extract_urls_from_metadata(metadata_path):
    """Extract all URLs from the path field in metadata.json"""
    try:
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        return metadata.get("path", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def get_largest_axtree_index(trajectory):
    """Find the step with the largest index and return its axtree path"""
    if not trajectory:
        return None
    
    # Handle both list and dict formats
    if isinstance(trajectory, list):
        # For list format, get the last item
        if trajectory:
            last_step = trajectory[-1]
            return last_step.get("axtree")
        return None
    elif isinstance(trajectory, dict):
        # For dict format, get the step with the highest numeric key
        last_step_key = max(trajectory.keys(), key=lambda x: int(x) if x.isdigit() else 0)
        last_step = trajectory[last_step_key]
        return last_step.get("axtree")
    
    return None

def read_axtree_content(traj_dir, axtree_filename):
    """Read the content of the axtree file"""
    if not axtree_filename:
        return ""
    
    axtree_path = os.path.join(traj_dir, "axtree", axtree_filename)
    try:
        with open(axtree_path, 'r', encoding='utf-8') as f:
            return f.read()
    except (FileNotFoundError, UnicodeDecodeError) as e:
        print(f"Warning: Could not read axtree file {axtree_path}: {e}")
        return ""

def generate_detailed_steps_and_goal(urls):
    """Generate detailed step-by-step instructions and goal based on URL path"""
    if not urls:
        return [], ""
    
    steps = []
    
    # First step - go to the initial URL
    first_url = urls[0]
    domain = first_url.split('/')[2] if len(first_url.split('/')) > 2 else first_url
    steps.append(f"Unless already on {domain}, go to {first_url}")
    
    # Intermediate steps - navigate through the path
    for i in range(1, len(urls)):
        current_url = urls[i]
        previous_url = urls[i-1]
        
        # Extract meaningful parts from the URL
        current_parts = current_url.split('/')
        previous_parts = previous_url.split('/')
        
        # Find the new path segment
        new_segment = ""
        if len(current_parts) > len(previous_parts):
            new_segment = current_parts[-1]
        elif len(current_parts) == len(previous_parts):
            # Find the different segment
            for j in range(len(current_parts)):
                if j < len(previous_parts) and current_parts[j] != previous_parts[j]:
                    new_segment = current_parts[j]
                    break
        
        # Create a descriptive step
        if new_segment:
            # Clean up the segment (replace hyphens/underscores with spaces, etc.)
            clean_segment = new_segment.replace('-', ' ').replace('_', ' ').replace('%20', ' ')
            steps.append(f"Navigate to the {clean_segment} section by going to {current_url}")
        else:
            steps.append(f"Navigate to {current_url}")
    
    # Final step - inform user of completion
    steps.append("Inform the user once you have successfully navigated to the final page")
    
    # Create goal by joining all steps
    goal = "\n".join(steps)
    
    return steps, goal

def build_no_vision_prompt(urls, axtree_content):
    """Build the prompt for instruction generation without vision"""
    urls_text = "\n".join([f"- {url}" for url in urls])
    
    prompt_text = f"""
You are a web browsing expert. Given a sequence of URLs visited and the final page's accessibility tree (AXTree), you need to understand what the user was trying to accomplish and generate three levels of instructions.

Here are some examples of good instructions:

Example 1:
{{
    "high_level": "Find a model 123 size 11 shoe in blue on adidas.com",
    "mid_level": "Go to adidas.com, navigate to mens section, and find model 123 size 11 shoe in blue",
    "low_level": "Navigate to adidas.com, go to the mens section by clicking on the mens category, browse through shoes, and locate the specific model 123 shoe in size 11 and blue color variant"
}}

Example 2:
{{
    "high_level": "Search for cumin seed recipes on AllRecipes",
    "mid_level": "Go to AllRecipes.com and search for recipes that use cumin seeds as an ingredient",
    "low_level": "Navigate to AllRecipes.com, use the search functionality to look for 'cumin seeds', browse through the search results to find recipes that prominently feature cumin seeds in their ingredient list"
}}

Now, analyze this browsing session:

URLs visited in sequence:
{urls_text}

Final page accessibility tree (AXTree):
{axtree_content}

Based on the URL progression and the final page state shown in the AXTree, determine what the user was trying to accomplish. Generate three levels of instructions:

- high_level: A concise instruction for a very smart assistant (minimal details)
- mid_level: An instruction with moderate detail for a reasonably smart assistant  
- low_level: A detailed instruction with specific steps for an average assistant (but avoid itemized lists)

Important guidelines:
- You are NOT ALLOWED to put specific URLs into instructions -- only high level domain names like "reddit.com" or "adidas.com" are okay
- Do not include specific URL paths like "https://www.reddit.com/r/Minecraft/comments/1max9uz/" 
- Focus on the user's intent based on the URL progression and final page content
- Make instructions actionable and clear

Respond with a JSON object containing the three instruction levels.
"""
    return prompt_text

def build_steps_refinement_prompt(urls, raw_steps):
    """Build the prompt for refining the step-by-step instructions"""
    urls_text = "\n".join([f"- {url}" for url in urls])
    raw_steps_text = "\n".join([f"{i+1}. {step}" for i, step in enumerate(raw_steps)])
    
    prompt_text = f"""
You are a web browsing expert. I have automatically generated step-by-step instructions based on URL progression, but the URLs might be messy or unclear. Your job is to refine these steps to make them more natural and user-friendly while maintaining the same navigation flow.

URLs visited in sequence:
{urls_text}

Auto-generated steps (based on URL parsing):
{raw_steps_text}

Please refine these steps to:
1. Use more natural language
2. Clean up any messy URL segments (replace hyphens/underscores with proper words)
3. Make the navigation intent clearer
4. Keep the same number of steps and overall flow
5. Make each step actionable and clear

Example of good refined steps:
- "Unless already on AllRecipes, go to https://www.allrecipes.com/"
- "Navigate to the search section"
- "Search for quinoa recipes using the search functionality"
- "Select a recipe from the search results that contains quinoa"
- "Inform the user of the recipe name and ingredients"

Respond with a JSON object containing a "steps" array with the refined step-by-step instructions and a "goal" string that combines all steps with newlines.

Format:
{{
    "steps": ["step 1", "step 2", "step 3", ...],
    "goal": "step 1\\nstep 2\\nstep 3\\n..."
}}
"""
    return prompt_text

def run_no_vision_generation(input_dir, verbose=True):
    """Generate instructions using only URLs and AXTree data"""
    # Load metadata.json to get URLs
    metadata_path = os.path.join(input_dir, "metadata.json")
    urls = extract_urls_from_metadata(metadata_path)
    
    if not urls:
        if verbose: print(f"Error: No URLs found in metadata.json for {input_dir}")
        return (False, "No URLs found in metadata.json")
    
    # Load trajectory.json to get AXTree
    trajectory_path = os.path.join(input_dir, "trajectory.json")
    try:
        with open(trajectory_path) as f:
            trajectory_data = json.load(f)
    except FileNotFoundError:
        if verbose: print(f"Error: trajectory.json not found in {input_dir}")
        return (False, "trajectory.json not found")
    
    trajectory = find_steps(trajectory_data)
    if trajectory is None:
        if verbose: print(f"Error: Could not find trajectory steps in {trajectory_path}")
        return (False, "Could not find trajectory steps")
    
    # Get the AXTree with the largest index
    axtree_filename = get_largest_axtree_index(trajectory)
    axtree_content = read_axtree_content(input_dir, axtree_filename)
    
    if not axtree_content:
        if verbose: print(f"Warning: Could not read AXTree content for {input_dir}")
    
    # Generate raw detailed steps and goal (deterministic)
    raw_steps, _ = generate_detailed_steps_and_goal(urls)
    
    # Build prompts
    instruction_prompt = build_no_vision_prompt(urls, axtree_content)
    steps_prompt = build_steps_refinement_prompt(urls, raw_steps)
    
    # Save LLM inputs for debugging
    instruction_input_path = os.path.join(input_dir, "no_vision_instruction_input.txt")
    with open(instruction_input_path, "w", encoding='utf-8') as f:
        f.write(instruction_prompt)
    
    steps_input_path = os.path.join(input_dir, "no_vision_steps_input.txt")
    with open(steps_input_path, "w", encoding='utf-8') as f:
        f.write(steps_prompt)
    
    if verbose:
        print(f"Saved instruction LLM input to {instruction_input_path}")
        print(f"Saved steps LLM input to {steps_input_path}")
    
    # Call OpenAI for both instructions and refined steps
    client = OpenAI(api_key=OPENAI_API_KEY)
    try:
        # First call: Generate instructions
        instruction_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": instruction_prompt}],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        instructions_json = instruction_response.choices[0].message.content
        instructions = Instructions.model_validate_json(instructions_json)
        
        # Second call: Refine steps
        steps_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": steps_prompt}],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        refined_steps_json = steps_response.choices[0].message.content
        refined_steps = RefinedSteps.model_validate_json(refined_steps_json)
        
        # Save LLM outputs
        instruction_output_path = os.path.join(input_dir, "no_vision_instruction_output.json")
        with open(instruction_output_path, "w") as f:
            f.write(instructions.model_dump_json(indent=2))
        
        steps_output_path = os.path.join(input_dir, "no_vision_steps_output.json")
        with open(steps_output_path, "w") as f:
            f.write(refined_steps.model_dump_json(indent=2))
        
        if verbose:
            print(f"Saved instruction LLM output to {instruction_output_path}")
            print(f"Saved steps LLM output to {steps_output_path}")
            print("\nGenerated instructions:")
            print(instructions.model_dump_json(indent=2))
            print("\nRefined steps:")
            print(refined_steps.model_dump_json(indent=2))
        
        return (True, (instructions, refined_steps.steps, refined_steps.goal))
        
    except Exception as e:
        if verbose: print(f"An error occurred while communicating with OpenAI: {e}")
        return (False, f"An error occurred while communicating with OpenAI: {e}")

def update_metadata_with_no_vision_instructions(traj_dir, instructions, detailed_steps, goal):
    """Update metadata.json with the new instructions, steps, and goal"""
    metadata_path = os.path.join(traj_dir, "metadata.json")
    
    try:
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        # Update the goal field
        metadata["goal"] = goal
        
        # Update the task section
        task_section = metadata.setdefault("task", {})
        task_section["instruction"] = instructions.model_dump()
        task_section["steps"] = detailed_steps
        
        # Save updated metadata
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
            
        return True
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error updating metadata.json: {e}")
        return False

def no_vision_generation_worker(dir_path: str) -> tuple[str, str, str]:
    """Worker function for parallel processing"""
    try:
        success, result = run_no_vision_generation(dir_path, verbose=False)
        if success:
            # result is tuple of (instructions, detailed_steps, goal)
            instructions, detailed_steps, goal = result
            update_success = update_metadata_with_no_vision_instructions(dir_path, instructions, detailed_steps, goal)
            if update_success:
                return (dir_path, "SUCCESS", "Instructions, steps, and goal generated and metadata updated")
            else:
                return (dir_path, "PARTIAL", "Instructions generated but metadata update failed")
        else:
            return (dir_path, "FAILED", result)
    except Exception as e:
        tb_str = traceback.format_exc()
        return (dir_path, "FAILED", f"Unhandled exception: {e}\n{tb_str}")

def main():
    """Main function for regenerating instructions without vision"""
    parser = argparse.ArgumentParser(
        description="Regenerates instructions for web browsing tasks using only URLs and AXTree data (no screenshots).",
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
    
    # Discover trajectory directories (same logic as original)
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
    results = {"SUCCESS": 0, "PARTIAL": 0, "FAILED": 0}
    failed_dirs = []
    
    with ProcessPoolExecutor(max_workers=args.num_workers) as executor:
        future_to_dir = {executor.submit(no_vision_generation_worker, dir_path): dir_path for dir_path in sorted_dirs}
        
        progress = tqdm(as_completed(future_to_dir), total=len(sorted_dirs), desc="Regenerating Instructions (No Vision)", unit="dir")
        for future in progress:
            dir_path, status, message = future.result()
            results[status] += 1
            if status == "FAILED":
                failed_dirs.append((dir_path, message))
    
    # Print summary
    print("\n--- No Vision Instruction Generation Summary ---")
    print(f"Total directories processed: {len(sorted_dirs)}")
    print(f"  - Instructions, steps, and goals generated successfully: {results['SUCCESS']}")
    print(f"  - Partial success (generation ok, metadata update failed): {results['PARTIAL']}")
    print(f"  - Directories failed: {results['FAILED']}")
    
    if failed_dirs:
        print("\nFailed directories:")
        for dir_path, error in failed_dirs:
            print(f"  - {os.path.basename(dir_path)}: {error}")

if __name__ == "__main__":
    main()
