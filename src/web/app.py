from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
import sys

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from codelens.ast_indexer import index_repo
from codelens.query_pipeline import QueryPipeline
from codelens.utils import load_json

app = FastAPI()

# Global state
pipeline = None
current_repo_path = None  # Track which repo is currently indexed

class QueryRequest(BaseModel):
    question: str
    k: int = 5

@app.on_event("startup")
def startup_event():
    # Only load existing index if available, don't auto-index anything
    global pipeline, current_repo_path
    try:
        if Path("index.json").exists():
            units = load_json("index.json")
            pipeline = QueryPipeline(units)
            current_repo_path = "index.json (pre-existing)"
            print(f"Loaded {len(units)} units from existing index.json")
        else:
            print("No index.json found. Please index a repository via the web UI.")
    except Exception as e:
        print(f"Startup note: {e}")

import subprocess
import shutil
import os

@app.post("/index")
def trigger_index(repo_path: str):
    global pipeline, current_repo_path
    
    # Handle GitHub URLs
    if repo_path.startswith(("http://", "https://", "git@")):
        repo_name = repo_path.split("/")[-1].replace(".git", "")
        local_path = Path("temp_repos") / repo_name
        
        # Clean up existing
        if local_path.exists():
            shutil.rmtree(local_path)
        
        local_path.parent.mkdir(exist_ok=True)
        
        print(f"Cloning {repo_path} to {local_path}...")
        try:
            result = subprocess.run(
                ["git", "clone", repo_path, str(local_path)], 
                check=True,
                capture_output=True,
                text=True
            )
            repo_path = str(local_path)
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else str(e)
            if "Authentication failed" in error_msg or "Invalid username" in error_msg:
                raise HTTPException(
                    status_code=400, 
                    detail="Repository is private or requires authentication. Please use a public repository or provide a local path."
                )
            raise HTTPException(status_code=400, detail=f"Failed to clone repo: {error_msg}")

    # Index the repository
    units = index_repo(repo_path)
    
    # Save to index.json for persistence
    from codelens.utils import save_json  # Fixed: correct import path
    save_json(units, "index.json")
    
    # Update global pipeline
    pipeline = QueryPipeline(units)
    current_repo_path = repo_path
    
    print(f"✅ Indexed {len(units)} units from: {repo_path}")
    
    return {"status": "indexed", "count": len(units), "path": repo_path}

@app.post("/query")
def query(req: QueryRequest):
    if not pipeline:
        raise HTTPException(status_code=500, detail="Index not ready")
    
    result = pipeline.run(req.question, k=req.k)
    return result

app.mount("/", StaticFiles(directory="src/web/static", html=True), name="static")
