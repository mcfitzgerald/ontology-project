#!/bin/bash

# Check if file argument is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <file>"
    exit 1
fi

# Find the line number of the last occurrence of "Contents:" (exact match)
last_contents_line=$(grep -n "^Contents:$" "$1" | tail -1 | cut -d: -f1)

# If "Contents:" is found, extract from that line to the end
if [ -n "$last_contents_line" ]; then
    tail -n +$last_contents_line "$1" | while IFS= read -r line; do
        # Truncate lines longer than 500 characters
        if [ ${#line} -gt 1000 ]; then
            echo "${line:0:500}..."
        else
            echo "$line"
        fi
    done
else
    echo "No line containing only 'Contents:' found"
    exit 1
fi