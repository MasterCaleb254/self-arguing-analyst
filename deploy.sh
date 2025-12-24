#!/bin/bash
# deploy.sh

echo "Deploying Self-Arguing Multi-Agent Analyst..."

# Install dependencies
pip install -r requirements-enhanced.txt

# Set up directories
mkdir -p data/synthetic
mkdir -p cache/mitre
mkdir -p artifacts
mkdir -p results

# Set up environment
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << EOF
OPENAI_API_KEY=your_key_here
LOG_LEVEL=INFO
STORAGE_PATH=./artifacts
CACHE_PATH=./cache
EOF
    echo "Please edit .env file with your OpenAI API key"
fi

# Run tests
echo "Running tests..."
python -m pytest tests/ -v

# Start API server
echo "Starting API server..."
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload