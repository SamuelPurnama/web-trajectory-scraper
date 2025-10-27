from typing import Literal

import fire
from beaker import (
    Beaker,
    BeakerConstraints,
    BeakerDataMount,
    BeakerDataSource,
    BeakerEnvVar,
    BeakerExperimentSpec,
    BeakerImageSource,
    BeakerJobPriority,
    BeakerResultSpec,
    BeakerTaskContext,
    BeakerTaskResources,
    BeakerTaskSpec,
    BeakerWorkspace,
)

beaker = Beaker.from_env(default_workspace="ai2/webolmo")


def create_task_spec(job_id: int, num_jobs: int, task_prefix: str):
    return BeakerTaskSpec(
        name=f"webolmo_synthetic_{job_id}_of_{num_jobs}",
        command=["/bin/bash", "-c"],
        arguments=[
            f"$PYTHON -m tasks.generate_trajectories --task_prefix {task_prefix} --tasks_json /root/weka/oe-training-default/webolmo/tanmayg/webolmo-synthetic/tasks/{task_prefix}_tasks.json --output_dir /root/weka/oe-training-default/webolmo/tanmayg/webolmo-synthetic/generated_trajectories/{task_prefix}2 --num_jobs {num_jobs} --job_id {job_id} --num_workers 5"
        ],
        image=BeakerImageSource(
            beaker="tanmayg/webolmo-synthetic-20250528201324"
        ),
        datasets=[
            BeakerDataMount(
                source=BeakerDataSource(
                    beaker="tanmayg/code-webolmo-synthetic-20250528201827",
                ),
                mount_path="/root/webolmo-synthetic",
            ),
            BeakerDataMount(
                source=BeakerDataSource(weka="oe-training-default"),
                mount_path="/root/weka/oe-training-default",
            ),
        ],
        env_vars=[
            BeakerEnvVar(name="OPENAI_API_KEY", secret="TG_OPENAI_API_KEY"),
            BeakerEnvVar(
                name="BROWSERBASE_API_KEY", secret="BROWSERBASE_API_KEY"
            ),
            BeakerEnvVar(
                name="BROWSERBASE_PROJECT_ID", secret="BROWSERBASE_PROJECT_ID"
            ),
        ],
        context=BeakerTaskContext(
            priority=BeakerJobPriority.normal, preemptible=False
        ),
        result=BeakerResultSpec(path="/unused"),
        resources=BeakerTaskResources(cpu_count=6, gpu_count=None),
        constraints=BeakerConstraints(
            cluster=[
                "ai2/neptune-cirrascale",
                "ai2/rhea-cirrascale",
                "ai2/ceres-cirrascale",
            ],
        ),
        host_networking=True,
    )


def main(num_jobs: int, task_prefix: str):
    desc = f"Webolmo Data Generation - {task_prefix}"
    beaker.experiment.create(
        # workspace=BeakerWorkspace("ai2/webolmo"),
        spec=BeakerExperimentSpec(
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
