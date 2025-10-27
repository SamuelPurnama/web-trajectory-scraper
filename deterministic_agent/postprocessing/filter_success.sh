#!/bin/bash

# check if weka is mounted here at /root or at /weka
BASE_DIR="/root/weka/oe-training-default/webolmo/datasets/node_traversal"

SOURCE_DIRS=(
    "530_websites_76k_tasks_july_28"
    "530_websites_76k_tasks_july_28_second_run_job_id_0"
    "530_websites_76k_tasks_july_28_second_run_second_attempt_job_id_1"
)

DEST_DIR="${BASE_DIR}/fully_completed_trajectories"

mkdir -p "${DEST_DIR}"

total_successful_found=0
total_copied=0
total_skipped=0

for src_dirname in "${SOURCE_DIRS[@]}"; do
    src_path="${BASE_DIR}/${src_dirname}"
    
    if [ ! -d "${src_path}" ]; then
        echo "Warning: Source directory not found, skipping: ${src_path}"
        continue
    fi

    while IFS= read -r -d '' task_dir || [[ -n "${task_dir}" ]]; do
        verdict_file="${task_dir}/verdict.json"
        
        if [ ! -f "${verdict_file}" ]; then
            continue
        fi

        if grep -q -i '"status": "success"' "${verdict_file}"; then
            ((total_successful_found++))
            task_name=$(basename "${task_dir}")
            dest_task_path="${DEST_DIR}/${task_name}"
            
            if [ ! -d "${dest_task_path}" ]; then
                cp -r "${task_dir}" "${DEST_DIR}/"
                ((total_copied++))
                if (( total_copied % 1000 == 0 )); then
                    echo "Progress: ${total_copied} trajectories copied so far..."
                fi
            else
                ((total_skipped++))
            fi
        fi
    done < <(find "${src_path}" -mindepth 1 -maxdepth 1 -type d -print0)
done

echo "----------------------------------------"
echo "Script finished."
echo "Total successful trajectories found: ${total_successful_found}"
echo "All unique successful trajectories are located in: ${DEST_DIR}"
