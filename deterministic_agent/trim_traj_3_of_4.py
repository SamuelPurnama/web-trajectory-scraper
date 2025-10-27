import json
import os
import shutil
from glob import glob
from datetime import datetime
import fire
import fasthtml.common as ft

def write_to_file(outdir: str, content: str, fname: str):
    """Helper to write content to a file in a specific directory."""
    with open(os.path.join(outdir, fname), "w", encoding='utf-8') as file:
        file.write(content)

def regenerate_html(interactions: list, task: dict, outdir: str, task_name: str):
    """Creates an HTML report of the trajectory."""
    def create_page(elements):
        return ft.Html(
            ft.Head(ft.Title("Trajectory Report")),
            ft.Body(ft.Div(*elements, cls="container", style="margin: 20px auto; width: 90%;")),
        )

    def create_card(header_content, body_content):
        return ft.Card(ft.Div(body_content, cls="row"), header=header_content)

    elements = [
        ft.Div(
            ft.H1(f"{task_name}"),
            ft.H2("Task Details"),
            ft.Pre(ft.Code(json.dumps(task, indent=2))),
        ),
        ft.H2("Trajectory"),
    ]

    for interaction in interactions:
        card_header = ft.Div(f"Step {interaction.get('step', -1) + 1}", ft.Code(str(interaction.get('timestamp', '')), style="float: right;"))
        card_body = ft.Div(
            ft.Div(ft.Img(src=interaction.get("screenshot", ""), style="width: 100%; max-width: 600px; border: 1px solid #ddd;"), cls="col-xs-6"),
            ft.Br(),
            ft.Div(ft.H6("Action"), ft.Pre(ft.Code(json.dumps(interaction.get("action", {}), indent=2))), cls="col-xs-6"),
            cls="row",
        )
        elements.append(ft.Div(create_card(header_content=card_header, body_content=card_body)))

    write_to_file(outdir, ft.to_xml(create_page(elements)), "trajectory.html")

def to_legacy_format(interactions: list) -> dict:
    """Converts a list of interactions back to the legacy dictionary format."""
    traj_data = {}
    for i, interaction in enumerate(interactions):
        step_num = i + 1
        action_dict = interaction.get("action", {})
        action_name = action_dict.get("action")
        
        action_params = {k: v for k, v in action_dict.items() if k != "action"}
        thought = action_params.pop("thought", "")
        
        params_str = ", ".join(f"{k}={repr(v)}" for k, v in action_params.items())
        action_str = f"{action_name}({params_str})"
        action_description = action_str

        traj_data[str(step_num)] = {
            "screenshot": os.path.basename(interaction.get("screenshot", "")),
            "axtree": os.path.basename(interaction.get("axtree", "")),
            "user_message": "",
            "other_obs": {"url": interaction.get("url", "")},
            "action": {
                "action_str": action_str,
                "action_description": action_description,
                "action_output": {"thought": thought, "action": action_params, "action_name": action_name},
            },
            "error": interaction.get("error"),
            "action_timestamp": interaction.get("timestamp"),
        }
    return traj_data

def from_legacy_format(legacy_data: dict) -> list:
    """Converts the legacy dictionary format to a list of interactions."""
    interactions = []
    sorted_steps = sorted(legacy_data.items(), key=lambda item: int(item[0]))
    for step_str, legacy_interaction in sorted_steps:
        action_output = legacy_interaction.get("action", {}).get("action_output", {})
        action_name = action_output.get("action_name")
        action_params = action_output.get("action", {})
        thought = action_output.get("thought", "")
        
        full_action = {"action": action_name, "thought": thought, **action_params}
        
        interaction = {
            "step": int(step_str) - 1,
            "screenshot": os.path.join("images", legacy_interaction.get("screenshot", "")),
            "axtree": os.path.join("axtree", legacy_interaction.get("axtree", "")),
            "url": legacy_interaction.get("other_obs", {}).get("url"),
            "timestamp": legacy_interaction.get("action_timestamp"),
            "error": legacy_interaction.get("error"),
            "action": full_action,
        }
        interactions.append(interaction)
    return interactions

def trim_trajectories(root_dir: str):
    """Trims trajectories, creating copies in a new directory with a synthetic exit action."""
    output_root_dir = f"{root_dir.rstrip('/')}_trimmed"
    os.makedirs(output_root_dir, exist_ok=True)
    print(f"Output will be saved to: {output_root_dir}")

    traj_dirs = glob(os.path.join(root_dir, "task_*"))
    trimmed_count = 0

    for traj_dir in traj_dirs:
        traj_json_path = os.path.join(traj_dir, "trajectory.json")
        if not os.path.exists(traj_json_path):
            continue

        with open(traj_json_path, 'r') as f:
            raw_data = json.load(f)

        interactions = from_legacy_format(raw_data) if isinstance(raw_data, dict) else raw_data
        
        click_count = 0
        second_click_index = -1
        for i, interaction in enumerate(interactions):
            if interaction.get("action", {}).get("action") == "click":
                click_count += 1
                if click_count == 2:
                    second_click_index = i
                    break
        
        if second_click_index != -1 and second_click_index + 1 < len(interactions):
            new_traj_dir = os.path.join(output_root_dir, os.path.basename(traj_dir))
            print(f"Trimming: {traj_dir} -> {new_traj_dir}")

            if os.path.exists(new_traj_dir):
                shutil.rmtree(new_traj_dir)
            shutil.copytree(traj_dir, new_traj_dir)
            
            new_interactions = interactions[:second_click_index + 2]
            
            last_interaction = new_interactions[-1]
            last_interaction["action"] = {"action": "exit", "thought": "trajectory trimmed down from failed steps"}
            last_interaction["error"] = None
            
            for i, interaction in enumerate(new_interactions):
                interaction['step'] = i

            original_num_steps = len(interactions)
            new_num_steps = len(new_interactions)
            for step_to_delete in range(new_num_steps, original_num_steps + 1):
                step_str = str(step_to_delete).zfill(3)
                for pattern in [f"*/*_{step_str}.*"]:
                    for file_path in glob(os.path.join(new_traj_dir, pattern)):
                        if os.path.exists(file_path):
                            os.remove(file_path)

            with open(os.path.join(new_traj_dir, "trajectory.json"), 'w') as f:
                json.dump(to_legacy_format(new_interactions), f, indent=2)

            metadata_path = os.path.join(new_traj_dir, "metadata.json")
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                if isinstance(metadata.get("path"), list):
                    metadata["path"] = metadata["path"][:new_num_steps]

                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                regenerate_html(new_interactions, metadata.get("task", {}), new_traj_dir, metadata.get("eps_name", ""))
            
            trimmed_count += 1

    print(f"\nFinished processing. Trimmed {trimmed_count} directories.")

if __name__ == "__main__":
    fire.Fire(trim_trajectories)
