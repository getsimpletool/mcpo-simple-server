#!/bin/bash

# Get path to parent directory of the script
mcpo_simple_server_path=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

# Set the Python path to include the current directory
export PYTHONPATH="$PYTHONPATH:$(pwd)"
export PYTHONPATH="$PYTHONPATH:/app"
export PYTHONPATH="$PYTHONPATH:$mcpo_simple_server_path/.."

# Run the server (uvicorn)
# uvicorn main:fastapi --reload --host 0.0.0.0 --port 8000

# Run the server using the __main__ module
if [ "$(pwd)" = "/app/mcpo_simple_server" ]; then
  python3 -m mcpo_simple_server --host 0.0.0.0 --port 8000
else
  python3 -m mcpo_simple_server --host 0.0.0.0 --port 8000 --reload
fi