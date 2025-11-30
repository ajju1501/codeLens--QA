#!/bin/bash
# Start the CodeLens QA web server
# Excludes temp_repos from reload watching to prevent restarts when indexing GitHub repos

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run uvicorn with comprehensive exclusions
uvicorn src.web.app:app --reload \
    --reload-dir src \
    --reload-exclude 'temp_repos/**' \
    --reload-exclude 'index.json'
