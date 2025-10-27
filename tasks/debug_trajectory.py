import os
import random

import fire

from tasks.generate_trajectories import eval_task


def main(
    output_dir: str,
    steps: list[str] | str,
    eps_name: str = "debug",
    step_timeout_in_s: float = 30,
    max_steps: int = 20,
):

    task = {
        "steps": steps if isinstance(steps, list) else [steps],
        "task_type": "debugging_task",
        "instruction": {
            "high_level": "HL instruction",
            "mid_level": "ML instruction",
            "low_level": "LL instruction",
        },
    }
    eval_task(
        eps_name=eps_name,
        steps=task["steps"],
        instructions=task["instruction"],
        task_type=task["task_type"],
        start_url=random.choice(
            [
                "https://www.google.com/",
                "https://bing.com",
                "https://wikipedia.org",
                "https://arxiv.org",
            ]
        ),
        task=task,
        outdir=os.path.join(output_dir, eps_name),
        max_steps=max_steps,
        step_timeout_in_s=step_timeout_in_s,
    )


if __name__ == "__main__":
    fire.Fire(main)
    """
    $PYTHON -m tasks.debug_trajectory --output_dir /root/weka/oe-training-default/webolmo/tanmayg/webolmo-synthetic/generated_trajectories/debug --eps_name debug_example --steps "Go to url 'https://allrecipes.com'. Use the search box to search for Pasta. Take a noop action with reason loading. Let the user know 2 receipes that you see on the page" --max_steps 7
    """
