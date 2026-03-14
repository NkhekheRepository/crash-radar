#!/bin/bash
# Crash Radar Runner - Runs the pipeline with scheduled data fetching

cd /home/ubuntu/crash_radar

# Activate virtual environment
source venv/bin/activate

# Run with data fetching (recommended for live data)
export PYTHONPATH=.
python main.py --fetch

# Alternatively, run scheduled (commented out by default):
# python main.py
