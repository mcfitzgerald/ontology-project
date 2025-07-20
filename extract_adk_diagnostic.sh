#!/bin/bash

# Script to extract diagnostic information from adk_web.log
# Extracts from the last "Contents:" to the end of file
# Truncates lines to 1000 characters for readability

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default values
LOG_FILE="adk_web.log"
OUTPUT_FILE="adk_diagnostic.log"
MAX_LINE_LENGTH=1000

# Function to display usage
usage() {
    echo "Usage: $0 [-i input_log] [-o output_file] [-l max_line_length]"
    echo "  -i: Input log file (default: adk_web.log)"
    echo "  -o: Output diagnostic file (default: adk_diagnostic.log)"
    echo "  -l: Maximum line length (default: 1000)"
    exit 1
}

# Parse command line arguments
while getopts "i:o:l:h" opt; do
    case $opt in
        i) LOG_FILE="$OPTARG";;
        o) OUTPUT_FILE="$OPTARG";;
        l) MAX_LINE_LENGTH="$OPTARG";;
        h) usage;;
        *) usage;;
    esac
done

# Check if input file exists
if [ ! -f "$LOG_FILE" ]; then
    echo -e "${RED}Error: Log file '$LOG_FILE' not found${NC}"
    exit 1
fi

echo -e "${BLUE}Extracting diagnostic information from ADK log...${NC}"

# Find the line number of the last "Contents:" occurrence
LAST_CONTENTS_LINE=$(grep -n "Contents:" "$LOG_FILE" | tail -1 | cut -d: -f1)

if [ -z "$LAST_CONTENTS_LINE" ]; then
    echo -e "${RED}Error: No 'Contents:' found in log file${NC}"
    exit 1
fi

# Calculate total lines in file
TOTAL_LINES=$(wc -l < "$LOG_FILE")

# Calculate lines from last Contents: to end
LINES_TO_EXTRACT=$((TOTAL_LINES - LAST_CONTENTS_LINE + 1))

echo -e "${YELLOW}Found last 'Contents:' at line $LAST_CONTENTS_LINE${NC}"
echo -e "${YELLOW}Extracting $LINES_TO_EXTRACT lines${NC}"

# Extract from last Contents: to end, truncating long lines
tail -n +$LAST_CONTENTS_LINE "$LOG_FILE" | \
    awk -v max_len="$MAX_LINE_LENGTH" '{
        if(length($0) > max_len) 
            print substr($0, 1, max_len-3) "..."
        else 
            print $0
    }' > "$OUTPUT_FILE"

# Get statistics
EXTRACTED_LINES=$(wc -l < "$OUTPUT_FILE")
OUTPUT_SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)

echo -e "${GREEN}✓ Diagnostic log created successfully${NC}"
echo -e "  └─ Output file: ${BLUE}$OUTPUT_FILE${NC}"
echo -e "  └─ Lines extracted: $EXTRACTED_LINES"
echo -e "  └─ File size: $OUTPUT_SIZE"
echo -e "  └─ Max line length: $MAX_LINE_LENGTH chars"

# Show preview
echo -e "\n${YELLOW}Preview (first 5 lines):${NC}"
head -5 "$OUTPUT_FILE"

echo -e "\n${YELLOW}Last 3 lines:${NC}"
tail -3 "$OUTPUT_FILE"