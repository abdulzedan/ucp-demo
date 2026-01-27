#!/bin/bash
# UCP Demo Setup Script

set -e

echo "Setting up UCP Demo..."

# Check Python version
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
echo "Python version: $python_version"

# Install Poetry if not available
if ! command -v poetry &> /dev/null; then
    echo "Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
fi

# Install Python dependencies
echo "Installing Python dependencies..."
cd "$(dirname "$0")/.."
poetry install

# Install frontend dependencies
echo "Installing frontend dependencies..."
cd frontend
npm install

echo ""
echo "Setup complete! Run './scripts/run_demo.sh' to start the demo."
