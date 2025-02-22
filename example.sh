#!/bin/bash
echo "Setting venv..."
# Activate the virtual environment
source .venv/bin/activate

echo "set your api key: "
echo "% export GROK_API_KEY='xai-key_here'"
echo $GROK_API_KEY

python ./example.py

# Deactivate the virtual environment
deactivate
echo "Exiting venv"
