# CodeLens QA

CodeLens QA is an LLM-augmented repository explorer. It indexes your Python code, builds a dependency graph, and allows you to ask natural language questions about the codebase.

## Features

- 🔍 **Smart Code Indexing**: Parses Python, Java, JavaScript, TypeScript, and more
- 🕸️ **Dependency Graph**: Visualizes function calls and relationships
- 🤖 **AI-Powered Q&A**: Uses Hugging Face (free), OpenAI, or offline analysis
- 🌐 **Web Interface**: Easy-to-use browser interface
- 📦 **GitHub Integration**: Clone and analyze public repositories directly
- ⚡ **Fast & Offline**: Works without internet when using offline mode

## Architecture

1. **AST Indexer**: Parses Python files to extract functions and classes.
2. **Graph Builder**: Constructs a call graph using NetworkX.
3. **Retriever**: Uses TF-IDF to find relevant code snippets.
4. **LLM Pipeline**: Generates answers using Hugging Face, OpenAI, or offline analysis.

## Installation

```bash
cd CodeLens-QA
python3 -m venv venv
source venv/bin/activate
pip install -e ".[test]"
```

## Quick Start

### 1. Configure LLM (Optional but Recommended)

For AI-powered answers, set up Hugging Face (free):

```bash
export HUGGINGFACE_API_KEY="your_token_here"
export LLM_PROVIDER="huggingface"
```

See [LLM_CONFIGURATION.md](LLM_CONFIGURATION.md) for detailed setup instructions.

### 2. Index a Repository

```bash
python -m codelens.cli index --repo examples/sample_repo
```

### 3. Ask Questions

```bash
python -m codelens.cli query --repo examples/sample_repo --q "What does the main function do?"
```

## Usage

### Web UI (Recommended)
```bash
# Start the server (excludes temp_repos from reload)
./start_server.sh

# Or manually:
uvicorn src.web.app:app --reload --reload-exclude 'temp_repos/*'
```

Then open http://localhost:8000 in your browser.

**Features:**
- Index local repositories or GitHub URLs
- Ask questions in natural language
- View structured analysis with call flows and hotspots
- Automatic re-indexing when switching repositories

## LLM Providers

CodeLens QA supports multiple LLM providers:

| Provider | Cost | Setup | Quality |
|----------|------|-------|---------|
| **Hugging Face** | Free | [Guide](LLM_CONFIGURATION.md) | Good |
| **OpenAI** | Paid | [Guide](LLM_CONFIGURATION.md) | Excellent |
| **Offline** | Free | None needed | Good |

**Recommended**: Use Hugging Face for free AI-powered insights!

## Documentation

- [WALKTHROUGH.md](WALKTHROUGH.md) - Detailed architecture and usage
- [LLM_CONFIGURATION.md](LLM_CONFIGURATION.md) - LLM setup guide
- [USAGE_GUIDE.md](USAGE_GUIDE.md) - Advanced usage examples

## Testing

Run tests with pytest:
```bash
pytest
```

## Example Queries

- "How does data loading work?"
- "What are the main classes in this project?"
- "Explain the authentication flow"
- "Where is error handling implemented?"

## Demo

See `notebooks/quick_demo.ipynb` for a walkthrough.
