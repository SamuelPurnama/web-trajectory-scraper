#!/usr/bin/env python3
import os
import shutil
from pathlib import Path

weka_dir = "/root/weka/oe-training-default/webolmo/datasets/node_traversal/successful_trajectories_postprocessed"

# Remove existing splits
for dirname in ["val_ood", "val_iid", "train_2_vals"]:
    dirpath = Path(weka_dir) / dirname
    if dirpath.exists():
        shutil.rmtree(dirpath)
    dirpath.mkdir()

# Get OOD websites from CSV
ood_websites = set()
with open("/data/peters/webolmo-synthetic/deterministic_agent/train_val_split/ood_val.csv") as f:
    for line in f:
        origin = line.split(",")[0].strip()
        if "://" in origin:
            host = origin.split("://")[1].lower()
            if host.startswith("www."):
                host = host[4:]
            base = host.split(".")[0] if "." in host else host
            ood_websites.add(base.replace("-", "").replace("_", ""))

# Get all task dirs
all_tasks = []
for item in os.listdir(weka_dir):
    if item.startswith("task_") and os.path.isdir(os.path.join(weka_dir, item)):
        all_tasks.append(item)

# Split into OOD and non-OOD
ood_tasks = []
other_tasks = []

for task in all_tasks:
    website = task.split("_")[1]
    website_norm = website.replace("-", "").replace("_", "")
    if website_norm in ood_websites:
        ood_tasks.append(task)
    else:
        other_tasks.append(task)

# Take exactly what we need
other_tasks = sorted(other_tasks)
ood_tasks = sorted(ood_tasks)

# Send all OOD tasks to val_ood
val_ood_tasks = ood_tasks

iid_tasks = other_tasks[:1100]
train_tasks = other_tasks[1100:]

# Create symlinks
def link_tasks(tasks, dirname):
    target_dir = Path(weka_dir) / dirname
    for task in tasks:
        src = Path(weka_dir) / task
        dst = target_dir / task
        os.symlink(f"../{task}", dst, target_is_directory=True)

link_tasks(val_ood_tasks, "val_ood")
link_tasks(iid_tasks, "val_iid") 
link_tasks(train_tasks, "train_2_vals")

print(f"val_ood: {len(val_ood_tasks)}")
print(f"val_iid: {len(iid_tasks)}")
print(f"train_2_vals: {len(train_tasks)}")
print(f"Total: {len(val_ood_tasks) + len(iid_tasks) + len(train_tasks)}")
