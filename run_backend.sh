#!/bin/bash

# TerraWatch Backend Startup Script

cd /Users/sameeksha/Documents/Career/hackthon/girls_in_code/terrawatch

# Activate virtual environment
source ./venv/bin/activate

# Set PYTHONPATH to include the project root
export PYTHONPATH="/Users/sameeksha/Documents/Career/hackthon/girls_in_code/terrawatch:$PYTHONPATH"

# Run the backend
cd backend
python3 main.py
