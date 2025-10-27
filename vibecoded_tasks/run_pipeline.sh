#!/bin/bash

if [ $# -eq 0 ]; then
    echo "Usage: $0 <classification>"
    echo "Example: $0 Airlines"
    exit 1
fi

CLASSIFICATION="$1"

echo "Starting pipeline for classification: $CLASSIFICATION"

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p ./outputs/tasks_${CLASSIFICATION}

# Step 1: Generate the .py files for the classification
echo "Step 1: Generating Python task files for classification: $CLASSIFICATION"
cd vibecoded_tasks
uv run generate_website_tasks.py --classification "$CLASSIFICATION" --local-output-dir ./local_output

# # Step 2: Generate JSON from Python files
# echo "Step 2: Generating JSON from Python files..."
# cd ..
# export PYTHONPATH=.
# mkdir -p ./outputs/json_tasks/${CLASSIFICATION}
# for py_file in ./vibecoded_tasks/local_output/python_files/${CLASSIFICATION}/tasks_*.py; do
#     if [ -f "$py_file" ]; then
#         echo "Processing: $py_file"
#         # Extract domain from filename
#         domain=$(basename "$py_file" | sed 's/tasks_//' | sed 's/\.py$//')
#         # Generate JSON
#         uv run "$py_file" "./outputs/json_tasks/${CLASSIFICATION}/task_${domain}.json"
#     fi
# done

# # Step 3: Generate trajectories
# echo "Step 3: Generating trajectories..."
# uv run -m tasks.generate_trajectories \
#     --task_prefix vibecoded \
#     --tasks_json ./outputs/json_tasks/${CLASSIFICATION}/*.json \
#     --output_dir ./outputs/tasks_${CLASSIFICATION} \
#     --num_jobs 1 --job_id 0 \
#     --num_workers 40 \
#     --traj_timeout_in_s 300 \
#     --step_timeout_in_s 30 \
#     --seed 42 \
#     --max_steps 40

# # Step 4: Get judgements
# echo "Step 4: Getting judgements..."
# # Note: This step requires the webolmo-evals repository and judge_trajectories function
# # You'll need to adapt this based on your local evaluation setup
# d="./outputs/tasks_${CLASSIFICATION}"
# # The evaluation code would need to be adapted for local use

# echo "Pipeline completed for classification: $CLASSIFICATION"
