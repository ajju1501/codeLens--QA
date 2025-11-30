import argparse
import sys
import json
from pathlib import Path
from .ast_indexer import index_repo
from .utils import save_json, load_json, logger
from .query_pipeline import QueryPipeline

def index_command(args):
    repo_path = args.repo
    out_path = args.out
    
    units = index_repo(repo_path)
    save_json(units, out_path)
    print(f"Index saved to {out_path}")

def query_command(args):
    repo_path = args.repo # Not used if we load index directly, but let's assume we re-index or load default
    # For simplicity, we'll assume a temporary index file or re-index on the fly if no index file provided
    # But the prompt says "index --repo ... --out index.json" and "query --repo ...".
    # So query might need to re-index or look for a standard index file. 
    # Let's re-index on the fly for simplicity in the CLI unless an index file is passed.
    # Actually, let's look for 'index.json' in the current dir or re-index.
    
    index_file = Path("index.json")
    if index_file.exists():
        logger.info("Loading existing index.json...")
        units = load_json(index_file)
    else:
        logger.info("No index.json found, indexing repo on the fly...")
        units = index_repo(repo_path)
        
    pipeline = QueryPipeline(units)
    result = pipeline.run(args.q, k=args.k)
    
    print("\n=== ANSWER ===")
    print(json.dumps(result, indent=2))
    
    with open("result.json", "w") as f:
        json.dump(result, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description="CodeLens QA CLI")
    subparsers = parser.add_subparsers(dest="command")
    
    # Index command
    idx_parser = subparsers.add_parser("index", help="Index a repository")
    idx_parser.add_argument("--repo", required=True, help="Path to repo")
    idx_parser.add_argument("--out", default="index.json", help="Output JSON file")
    
    # Query command
    q_parser = subparsers.add_parser("query", help="Ask a question")
    q_parser.add_argument("--repo", required=True, help="Path to repo")
    q_parser.add_argument("--q", required=True, help="Question")
    q_parser.add_argument("--k", type=int, default=5, help="Top K results")
    
    args = parser.parse_args()
    
    if args.command == "index":
        index_command(args)
    elif args.command == "query":
        query_command(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
