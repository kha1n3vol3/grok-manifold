import importlib.util
import sys
import json

# Load the module dynamically
module_path = "./grok-starficient.py"
module_name = "grok_starficient"

spec = importlib.util.spec_from_file_location(module_name, module_path)
grok_starficient = importlib.util.module_from_spec(spec)
sys.modules[module_name] = grok_starficient
spec.loader.exec_module(grok_starficient)

# Check if Pipe class exists in the module
if hasattr(grok_starficient, "Pipe"):
    # Initialize Pipe class
    pipe_instance = grok_starficient.Pipe()

    # Prepare the API request payload based on the curl command
    payload = {
        "messages": [
            {"role": "system", "content": "You are a test assistant."},
            {"role": "user", "content": "Testing. Just say hi and hello world and nothing else."}
        ],
        "model": "grok-2-latest",
        "stream": False,
        "temperature": 0
    }

    # Call the API using the pipe method
    if hasattr(pipe_instance, "pipe"):
        response = pipe_instance.pipe(payload)
        print(json.dumps(response, indent=4))
    else:
        print("Error: The 'Pipe' class does not have a 'pipe' method.")
else:
    print("Error: 'Pipe' class not found in the module.")

