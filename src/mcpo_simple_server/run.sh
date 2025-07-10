#!/bin/sh

# Get path to parent directory of the script
mcpo_simple_server_path=$(cd "$(dirname "$0")" && pwd)

# Set the Python path to include the current directory
export PYTHONPATH="$PYTHONPATH:$(pwd)"
export PYTHONPATH="$PYTHONPATH:/app"
export PYTHONPATH="$PYTHONPATH:$mcpo_simple_server_path/.."
export PYTHONUNBUFFERED=1



# Parse --force option to kill port 8000 listener
while [ "$1" != "" ]; do
  case $1 in
    --force) FORCE=true ;; 
    *) echo "Usage: $0 [--force]"; exit 1 ;; 
  esac
  shift
done

# If --force is set, kill any process on port 8000
if [ "$FORCE" = true ]; then
  echo "Force mode: killing any processes on port 8000"
  pids=$(lsof -ti tcp:8000)
  if [ -n "$pids" ]; then
    echo "Killing processes: $pids"
    for pid in $pids; do
      echo "Killing process $pid"
      kill -9 $pid
    done
  fi
fi

# Check if .env exist - it not add mandatory env variables
if [ ! -f "$mcpo_simple_server_path/.env" ]; then
  JWT_SECRET_KEY=$(openssl rand -base64 64)
  API_KEY_ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key())")
  echo "JWT_SECRET_KEY=$JWT_SECRET_KEY" >> "$mcpo_simple_server_path/.env"
  echo "API_KEY_ENCRYPTION_KEY=$API_KEY_ENCRYPTION_KEY" >> "$mcpo_simple_server_path/.env"
fi


# Kill all other instances of python
pkill -f "python3 -u -m mcpo_simple_server"

# Run the server using the __main__ module
if [ "$(pwd)" = "/app/mcpo_simple_server" ]; then
  python3 -u -m mcpo_simple_server --host 0.0.0.0 --port 8000
else
  python3 -u -m mcpo_simple_server --host 0.0.0.0 --port 8000 --reload
fi