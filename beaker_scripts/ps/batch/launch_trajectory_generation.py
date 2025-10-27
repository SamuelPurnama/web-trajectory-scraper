from typing import Literal

import fire
from beaker import (
    Beaker,
    Constraints,
    DataMount,
    DataSource,
    EnvVar,
    ExperimentSpec,
    ImageSource,
    JobFailedError,
    JobTimeoutError,
    Priority,
    ResultSpec,
    TaskContext,
    TaskResources,
    TaskSpec,
)

beaker = Beaker.from_env(default_workspace="ai2/webolmo")


def create_task_spec(job_id: int, num_jobs: int, task_prefix: str):
    return TaskSpec(
        name=f"webolmo_synthetic_{job_id}_of_{num_jobs}",
        command=["/bin/bash", "-c"],
        arguments=[
            f"$PYTHON -m tasks.generate_trajectories --task_prefix {task_prefix} --tasks_json /root/weka/oe-training-default/webolmo/peters/webolmo-synthetic/tasks/{task_prefix}_tasks.json --output_dir /root/weka/oe-training-default/webolmo/peters/webolmo-synthetic/generated_trajectories/{task_prefix} --num_jobs {num_jobs} --job_id {job_id} --num_workers 5"
        ],
        image=ImageSource(beaker="tanmayg/webolmo-synthetic-20250504190901"),
        datasets=[
            DataMount(
                source=DataSource(
                    beaker="tanmayg/code-webolmo-synthetic-20250519072324",
                ),
                mount_path="/root/webolmo-synthetic",
            ),
            DataMount(
                source=DataSource(weka="oe-training-default"),
                mount_path="/root/weka/oe-training-default",
            ),
        ],
        env_vars=[
            EnvVar(name="OPENAI_API_KEY", secret="TG_OPENAI_API_KEY"),
            EnvVar(name="BROWSERBASE_API_KEY", secret="BROWSERBASE_API_KEY"),
            EnvVar(
                name="BROWSERBASE_PROJECT_ID", secret="BROWSERBASE_PROJECT_ID"
            ),
        ],
        context=TaskContext(priority="normal", preemptible=False),
        result=ResultSpec(path="/unused"),
        resources=TaskResources(cpu_count=6, gpu_count=0),
        constraints=Constraints(
            cluster=["ai2/neptune-cirrascale", "ai2/rhea-cirrascale"],
        ),
    )


def main(num_jobs: int, task_prefix: str):
    desc = f"Webolmo Data Generation - {task_prefix}"
    beaker.experiment.create(
        ExperimentSpec(
            budget="ai2/prior",
            description=desc,
            tasks=[
                create_task_spec(
                    job_id=i, num_jobs=num_jobs, task_prefix=task_prefix
                )
                for i in range(num_jobs)
            ],
        ),
    )
    print(f"Expriment created: {desc}")


if __name__ == "__main__":
    fire.Fire(main)
