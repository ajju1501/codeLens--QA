# CodeLens QA - Usage Guide

## Quick Start

### 1. Installation
```bash
cd CodeLens-QA
python3 -m venv venv
source venv/bin/activate
pip install -e ".[test]"
```

### 2. Index a Repository

#### Option A: Local Repository
```bash
python -m codelens.cli index --repo /path/to/your/repo --out index.json
```

#### Option B: GitHub Repository (Public Only)
The web interface supports cloning public GitHub repositories automatically.

**Note**: Private repositories require authentication. For private repos, clone them manually first:
```bash
git clone https://github.com/username/private-repo
python -m codelens.cli index --repo private-repo --out index.json
```

### 3. Query the Repository

```bash
python -m codelens.cli query --repo /path/to/your/repo --q "Your question here" --k 5
```

The query command will:
- Load `index.json` if it exists (faster)
- Otherwise, re-index the repository on the fly

### 4. Web Interface

Start the server:
```bash
uvicorn src.web.app:app --reload
```

Then open `http://localhost:8000` in your browser.

**Features**:
- **Index Repository**: Enter a local path or public GitHub URL
- **Ask Questions**: Query the indexed codebase

## Supported File Types

- **Python** (`.py`): Full AST parsing with function/class extraction
- **Java** (`.java`): Indexed as complete files
- **JavaScript/TypeScript** (`.js`, `.ts`): Indexed as complete files
- **Markdown/Text** (`.md`, `.txt`): Indexed as complete files

## LLM Configuration

The system supports OpenAI's API for enhanced answers:

1. **With OpenAI API Key**: Set the key in `src/codelens/llm.py` (line 9)
   - Provides structured, LLM-generated answers
   - **Note**: Requires active OpenAI credits

2. **Without API Key** (Fallback): 
   - Uses deterministic template-based answers
   - Works completely offline
   - Still provides component summaries, call flows, and hotspots

## Example Queries

- "How does data loading work?"
- "What are the main classes in this project?"
- "Explain the authentication flow"
- "Where is error handling implemented?"

## Troubleshooting

### "Repository is private or requires authentication"
- Use a public repository URL, or
- Clone the repository manually first, then index the local path

### "OpenAI quota exceeded"
- The API key has no credits remaining
- The system will automatically fall back to offline mode
- Answers will still be generated using the fallback logic

### "Indexed 0 units"
- Check that the repository contains supported file types
- Verify the path is correct
- Check logs for parsing errors

## Advanced Usage

### Custom Index File
```bash
# Create a custom index
python -m codelens.cli index --repo /path/to/repo --out my_custom_index.json

# Use it (rename to index.json or modify the code)
mv my_custom_index.json index.json
python -m codelens.cli query --repo /path/to/repo --q "question"
```

### Running Tests
```bash
pytest
```

### API Endpoints

- `POST /index?repo_path=<path>` - Index a repository
- `POST /query` - Query with JSON body: `{"question": "...", "k": 5}`
