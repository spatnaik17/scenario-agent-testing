#!/bin/bash
# Script to install the Scenario testing library with UV

# Check if UV is installed
if ! command -v uv &> /dev/null; then
    echo "UV (Universal Virtualenv) is not installed. Installing now..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

# Create a virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating a virtual environment..."
    uv venv
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install the library in development mode
echo "Installing Scenario library with dependencies..."
uv pip install -e .

# Install additional development dependencies
echo "Installing development dependencies..."
uv pip install pytest pytest-cov

echo ""
echo "Installation complete! You can now use Scenario testing library."
echo ""
echo "To get started, write your first test:"
echo "1. Create a file like 'test_my_agent.py'"
echo "2. Import the library: 'from scenario import Scenario, TestingAgent'"
echo "3. Define your agent function and scenarios"
echo "4. Run your tests with: 'python -m pytest -v'"
echo ""
echo "For more examples, check the documentation and example files."