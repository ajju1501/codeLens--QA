# Repository Indexing - Path Handling Summary

## ✅ Verified: Indexing Flow is Working Correctly

### How It Works

1. **User enters repository path** (local or GitHub URL)
2. **Backend processes the path:**
   - If GitHub URL → Clones to `temp_repos/{repo_name}`
   - If local path → Uses path directly
3. **Indexes the repository:**
   - Calls `index_repo(path)` to extract code units
   - Creates **new** `QueryPipeline` with fresh units
   - Replaces global `pipeline` variable
4. **All subsequent queries** use the newly indexed repository

### Path Resolution

```python
# In ast_indexer.py
def index_repo(repo_path: str):
    repo_path = Path(repo_path).resolve()  # ✅ Converts to absolute path
    # ... walks directory and indexes files
```

### Pipeline Update

```python
# In app.py /index endpoint
units = index_repo(repo_path)          # ✅ Index new repo
pipeline = QueryPipeline(units)        # ✅ Create fresh pipeline
return {"status": "indexed", "count": len(units)}
```

### Query Execution

```python
# In app.py /query endpoint
result = pipeline.run(req.question)    # ✅ Uses current pipeline
```

## 🔧 Fix Applied: Prevent Server Reload on Index

### Problem
When indexing GitHub repos, files are cloned to `temp_repos/`. The `uvicorn --reload` watcher detected these changes and restarted the server, loading the default repository again.

### Solution
Exclude `temp_repos/` from the reload watcher:

```bash
uvicorn src.web.app:app --reload --reload-exclude 'temp_repos/*'
```

### Usage

**Option 1: Use the startup script (recommended)**
```bash
./start_server.sh
```

**Option 2: Manual command**
```bash
uvicorn src.web.app:app --reload --reload-exclude 'temp_repos/*'
```

## 📊 Test Results

From the logs, we confirmed:
- ✅ Initial startup: Indexed 6 units from `examples/sample_repo`
- ✅ GitHub clone: Successfully cloned Data-Structures-and-Algorithms
- ✅ Re-indexing: Indexed 494 units from the new repository
- ✅ Pipeline updated: Created new pipeline with 494 units
- ✅ Query execution: Uses the newly indexed repository

## 🎯 Summary

**The indexing system is working perfectly!**

- ✅ Paths are correctly resolved (absolute paths)
- ✅ GitHub URLs are properly cloned
- ✅ Each index operation creates a fresh pipeline
- ✅ Queries always use the most recently indexed repository
- ✅ No caching or stale data issues

The only issue was the server auto-reload, which is now fixed by excluding `temp_repos/` from the watcher.
