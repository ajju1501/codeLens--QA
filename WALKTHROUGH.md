# CodeLens QA Walkthrough

This document details the steps to set up, run, and understand the CodeLens QA project.

## 1. Project Setup & Structure

The project was initialized with a standard Python structure:

- `src/codelens`: Core logic (Indexer, Graph Builder, Retriever, LLM Pipeline).
- `src/web`: FastAPI web application.
- `examples/sample_repo`: A minimal Python project used for demonstration.
- `tests`: Unit tests using `pytest`.

Key files created:
- `pyproject.toml`: Defines dependencies and project metadata.
- `src/codelens/ast_indexer.py`: Uses Python's `ast` module to parse code.
- `src/codelens/graph_builder.py`: Uses `networkx` to map dependencies.

## 2. Installation

To run this project, you need Python 3.10+.

1.  **Create a Virtual Environment** (recommended):
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -e ".[test]"
    ```
    This installs `fastapi`, `uvicorn`, `networkx`, `scikit-learn`, `pytest`, etc.

## 3. Indexing Code

The first step in the pipeline is to index a repository. This parses the code into "units" (functions and classes).

**Command:**
```bash
python -m codelens.cli index --repo examples/sample_repo
```

**What happens:**
- The `ast_indexer.py` walks through files in `examples/sample_repo`.
- It extracts code, docstrings, and function calls.
- It saves the result to `index.json`.

## 4. Running a Query

Once indexed, you can ask questions. The system uses TF-IDF (or Embeddings if configured) to find relevant code, builds a call graph context, and generates an answer.

**Command:**
```bash
python -m codelens.cli query --repo examples/sample_repo --q "How does data loading work?"
```

**Output:**
A JSON object containing:
- `component_summary`: Description of relevant functions/classes.
- `call_flow`: How the components interact (e.g., `main -> DataLoader.load`).
- `hotspots`: Important logic points.
- `sources`: IDs of the code units used.

## 5. Web Interface

For a more interactive experience, use the Web UI.

**Start the Server:**
```bash
uvicorn src.web.app:app --reload
```

**Use:**
- Open `http://localhost:8000` in your browser.
- **Configure Repo**: Enter the absolute path to the repository you want to index in the "Repo Path" field and click "Index Repo".
- **Ask**: Type a question and click "Ask".
- The backend API `/query` handles the request using the same pipeline as the CLI.

## 6. Testing

The project includes a test suite to ensure reliability.

**Run Tests:**
```bash
pytest
```

**Tests Cover:**
- `test_ast_indexer.py`: Verifies that functions and classes are correctly extracted.
- `test_graph_builder.py`: Verifies that call edges are created (e.g., `main` calls `DataLoader`).
- `test_retriever.py`: Verifies TF-IDF search relevance.
- `test_query_pipeline.py`: Verifies the end-to-end flow.

## 7. Architecture Details

- **AST Parsing**: We use the built-in `ast` library to avoid heavy dependencies like `tree-sitter` for this MVP, making it easy to run anywhere.
- **Graph**: `networkx` is used to build a directed graph. Edges are inferred by matching function call names to defined function names (heuristic).
- **Retrieval**: `scikit-learn`'s `TfidfVectorizer` provides a robust, offline-capable search mechanism.
- **LLM**: The system checks for `OPENAI_API_KEY`. If missing, it falls back to a deterministic logic that formats the retrieved context into a structured answer, ensuring the demo always works.
