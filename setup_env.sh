#!/bin/bash
set -e

echo ">>> Setting up System Dependencies..."
# Still installing libpq-dev equivalent if needed for python
sudo apt-get update
sudo apt-get install -y libpq-dev curl

echo ">>> Installing uv..."
curl -LsSf https://astral.sh/uv/install.sh | sh

echo ">>> Setting up Frontend..."
if [ -d "frontend" ]; then
    cd frontend
    npm install
    cd ..
fi

echo ">>> Setup Complete."
