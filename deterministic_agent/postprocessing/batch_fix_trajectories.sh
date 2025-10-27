#!/bin/bash

# This script copies trajectory directories from a source to a destination
# and then runs the fix_legacy_jsons.py post-processing script on the copies.

set -e  # Exit immediately if a command exits with a non-zero status.

# --- Argument Validation ---
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <source_directory> <destination_directory>"
    echo "Example: $0 ./old_trajectories ./fixed_trajectories"
    exit 1
fi

SOURCE_DIR=$1
DEST_DIR=$2
SCRIPT_DIR=$(dirname "$(realpath "$0")")
FIX_SCRIPT_PATH="$SCRIPT_DIR/fix_legacy_jsons.py"

if [ ! -d "$SOURCE_DIR" ]; then
    echo "Error: Source directory '$SOURCE_DIR' not found."
    exit 1
fi

if [ ! -f "$FIX_SCRIPT_PATH" ]; then
    echo "Error: The fix script was not found at '$FIX_SCRIPT_PATH'."
    exit 1
fi

# Create the destination directory if it doesn't exist
mkdir -p "$DEST_DIR"
echo "Destination directory '$DEST_DIR' is ready."

# --- Copy Trajectories ---
echo "Copying all trajectory subdirectories from '$SOURCE_DIR' to '$DEST_DIR'..."

# Use rsync for efficient copying and better handling of paths
rsync -a --prune-empty-dirs --include '*/' --include '*.*' --exclude '*' "$SOURCE_DIR/" "$DEST_DIR/"

echo "Copying complete."

# --- Run Post-Processing ---
echo "Running post-processing script to fix JSON files in '$DEST_DIR'..."

# The fix script supports wildcards, so we can pass all subdirectories at once.
# The quotes are important to handle spaces or special characters in paths.
uv run python "$FIX_SCRIPT_PATH" "$DEST_DIR"/*/

echo "--------------------------------------------------"
echo "Success! Fixed trajectories are located in: $DEST_DIR"
echo "--------------------------------------------------"
