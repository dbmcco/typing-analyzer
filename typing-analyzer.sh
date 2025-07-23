#!/bin/bash

# ABOUTME: Main typing analyzer launcher script
# Usage: ./typing-analyzer.sh [duration_in_hours]
# Examples: ./typing-analyzer.sh 0.5  (30 minutes)
#          ./typing-analyzer.sh 1    (1 hour)
#          ./typing-analyzer.sh 2    (2 hours)

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if python3 is available
if ! command -v python3 &> /dev/null; then
    print_error "python3 is required but not installed."
    exit 1
fi

# Setup virtual environment if needed
VENV_DIR="venv"
if [ ! -d "$VENV_DIR" ]; then
    print_status "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Check and install dependencies
print_status "Checking Python dependencies..."
if ! python3 -c "import pynput, yaml, pandas, numpy" 2>/dev/null; then
    print_status "Installing required packages..."
    python3 -m pip install -r requirements.txt
    print_success "Dependencies installed successfully"
else
    print_success "All required packages available"
fi

# Parse duration argument
DURATION=""
if [ $# -eq 1 ]; then
    # Convert decimal hours to minutes
    TOTAL_MINUTES=$(echo "scale=0; $1 * 60 / 1" | bc -l 2>/dev/null || echo "6")
    
    if [ "$TOTAL_MINUTES" -lt 60 ]; then
        # Less than 1 hour, use minutes
        DURATION="${TOTAL_MINUTES}m"
        print_status "Will run for $DURATION (${1} hours = ${TOTAL_MINUTES} minutes)"
    else
        # 1 hour or more, convert back to hours and minutes
        HOURS=$((TOTAL_MINUTES / 60))
        REMAINING_MINUTES=$((TOTAL_MINUTES % 60))
        
        if [ "$REMAINING_MINUTES" -eq 0 ]; then
            DURATION="${HOURS}h"
        else
            DURATION="${HOURS}h${REMAINING_MINUTES}m"
        fi
        print_status "Will run for $DURATION (${1} hours)"
    fi
elif [ $# -eq 0 ]; then
    print_status "No duration specified - will run until Ctrl+C"
else
    print_error "Usage: $0 [duration_in_hours]"
    print_error "Examples:"
    print_error "  $0 0.5    # 30 minutes" 
    print_error "  $0 1      # 1 hour"
    print_error "  $0 2      # 2 hours"
    exit 1
fi

# Check for accessibility permissions on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    print_status "Checking macOS accessibility permissions..."
    # The keylogger will handle the permission check and prompt
fi

# Create directories if they don't exist
mkdir -p data reports

print_success "Starting Typing Pattern Analyzer"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
print_status "Keylogger will capture typing patterns from all applications"
print_status "Data will be saved to: data/"
print_warning "Press Ctrl+C to stop and analyze results"
echo ""

# Start keylogger with signal handling
if [ -n "$DURATION" ]; then
    python3 src/keylogger.py --duration "$DURATION" &
    KEYLOGGER_PID=$!
else
    python3 src/keylogger.py &
    KEYLOGGER_PID=$!
fi

# Handle Ctrl+C gracefully
trap 'echo ""; print_warning "Stopping keylogger..."; kill $KEYLOGGER_PID 2>/dev/null; sleep 2' INT

# Wait for keylogger to finish or handle interruption
wait $KEYLOGGER_PID 2>/dev/null || {
    echo ""
    print_warning "Keylogger stopped - saving data..."
    # Give it a moment to save data
    sleep 2
}

# After keylogger stops, run analysis
echo ""
print_status "Analyzing captured typing data..."

if python3 src/analyzer.py; then
    echo ""
    print_success "Analysis complete!"
    
    # Find the latest report
    LATEST_HTML=$(ls -t reports/typing_analysis_*.html 2>/dev/null | head -n1)
    if [ -n "$LATEST_HTML" ]; then
        print_success "Report generated: $LATEST_HTML"
        
        # Try to open the report
        if command -v open &> /dev/null; then
            print_status "Opening report in browser..."
            open "$LATEST_HTML"
        elif command -v xdg-open &> /dev/null; then
            print_status "Opening report in browser..."
            xdg-open "$LATEST_HTML"
        else
            print_status "Open this file in your browser to view results:"
            echo "  file://$(pwd)/$LATEST_HTML"
        fi
    fi
else
    print_error "Analysis failed. Make sure you typed something during the session."
fi

print_success "Typing analysis session complete!"