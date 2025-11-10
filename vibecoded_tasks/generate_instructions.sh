#!/bin/bash

# Script to generate instructions (JSON) from Python task files
# This script runs each Python file in the specified folder to generate tasks with instructions
# Usage: ./generate_instructions.sh <classification>
# Example: ./generate_instructions.sh Hotel
# Example: ./generate_instructions.sh Housing

if [ $# -eq 0 ]; then
    echo "Usage: $0 <classification>"
    echo "Example: $0 Hotel"
    echo "Example: $0 Housing"
    echo "Example: $0 Job"
    echo "Example: $0 Music"
    exit 1
fi

CLASSIFICATION="$1"

echo "Generating instructions from ${CLASSIFICATION} Python files..."

# Set the base directory
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLASSIFICATION_DIR="${BASE_DIR}/python_files/${CLASSIFICATION}"
OUTPUT_DIR="${BASE_DIR}/../outputs/json_tasks/${CLASSIFICATION}"

# Create output directory
mkdir -p "${OUTPUT_DIR}"

# Check if classification directory exists
if [ ! -d "${CLASSIFICATION_DIR}" ]; then
    echo "Error: ${CLASSIFICATION} directory not found at ${CLASSIFICATION_DIR}"
    exit 1
fi

# Set PYTHONPATH to include the tasks module
export PYTHONPATH="${BASE_DIR}/../"

# Change to the project root for uv run
cd "${BASE_DIR}/.."

# Counter for processed files
count=0
failed=0

# Process each Python file in the classification folder
for py_file in "${CLASSIFICATION_DIR}"/tasks_*.py; do
    if [ -f "$py_file" ]; then
        # Extract domain from filename (e.g., tasks_booking_com.py -> booking_com)
        filename=$(basename "$py_file")
        domain=$(echo "$filename" | sed 's/tasks_//' | sed 's/\.py$//')
        output_file="${OUTPUT_DIR}/task_${domain}.json"
        
        echo ""
        echo "========================================="
        echo "Processing: ${filename}"
        echo "Domain: ${domain}"
        echo "Output: ${output_file}"
        echo "========================================="
        
        # Run the Python file with fire to generate JSON
        # The main() function takes filepath as first argument
        if uv run python "$py_file" --filepath "${output_file}"; then
            echo "✓ Successfully generated: ${output_file}"
            count=$((count + 1))
        else
            echo "✗ Failed to generate: ${output_file}"
            failed=$((failed + 1))
        fi
    fi
done

echo ""
echo "========================================="
echo "Generation complete!"
echo "Successfully processed: ${count} files"
echo "Failed: ${failed} files"
echo "Output directory: ${OUTPUT_DIR}"
echo "========================================="

