#!/bin/bash

while IFS= read -r website; do
    echo "=========================================="
    echo "Processing: $website"
    echo "=========================================="
    ./run_pipeline.sh "$website"
    echo ""
done < airlines.txt
