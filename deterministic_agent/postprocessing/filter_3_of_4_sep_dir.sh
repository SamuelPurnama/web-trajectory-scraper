#!/bin/bash

# This script finds successful trajectories from specified source directories
# and copies them to a new directory, avoiding duplicates.

set -x # print commands.

echo "DEBUG: Script starting..."

# Set the base directory where data is located
BASE_DIR="/root/weka/oe-training-default/webolmo/datasets/node_traversal"

# Define the source directories
SOURCE_DIRS=(
    "530_websites_76k_tasks_july_28"
    "530_websites_76k_tasks_july_28_second_run_job_id_0"
    "530_websites_76k_tasks_july_28_second_run_second_attempt_job_id_1"
)

# Define the destination directory for successful trajectories
DEST_DIR="${BASE_DIR}/completed_3_of_4"

# Create the destination directory if it doesn't exist
mkdir -p "${DEST_DIR}"

# Counters for reporting
total_successful_found=0
total_copied=0
total_skipped=0

# Process each source directory
for src_dirname in "${SOURCE_DIRS[@]}"; do
    src_path="${BASE_DIR}/${src_dirname}"
    
    if [ ! -d "${src_path}" ]; then
        echo "Warning: Source directory not found, skipping: ${src_path}"
        continue
    fi

    # Find all subdirectories (task folders) in the current source directory
    # Using -print0 and read -d '' to handle names with spaces or special characters
    while IFS= read -r -d '' task_dir || [[ -n "${task_dir}" ]]; do
        verdict_file="${task_dir}/verdict.json"
        
        # Check if verdict.json exists and is readable
        if [ ! -f "${verdict_file}" ]; then
            continue
        fi

        # Check if the status is "success" (case-insensitive)
        if grep -q -i '"progress": 0.67,' "${verdict_file}"; then
            ((total_successful_found++))
            task_name=$(basename "${task_dir}")
            dest_task_path="${DEST_DIR}/${task_name}"
            
            # Check if this trajectory has already been copied
            if [ ! -d "${dest_task_path}" ]; then
                echo "DEBUG: About to copy ${task_dir} to ${DEST_DIR}/"
                cp -r "${task_dir}" "${DEST_DIR}/"
                ((total_copied++))
            else
                # This trajectory is already in the destination, so we skip it.
                ((total_skipped++))
            fi
        fi
    done < <(find "${src_path}" -mindepth 1 -maxdepth 1 -type d -print0)
done

echo "DEBUG: Loop finished. Printing summary..."
echo "----------------------------------------"
echo "Script finished."
echo "Total successful trajectories found: ${total_successful_found}"
echo "New unique trajectories copied: ${total_copied}"
echo "Skipped (already existing) trajectories: ${total_skipped}"
echo "All unique successful trajectories are located in: ${DEST_DIR}"
