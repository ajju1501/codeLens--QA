import ast
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from .utils import logger

class CodeUnit:
    def __init__(self, 
                 unit_id: str, 
                 file_path: str, 
                 name: str, 
                 kind: str, 
                 start_line: int, 
                 end_line: int, 
                 code: str, 
                 docstring: Optional[str] = None,
                 signature: Optional[str] = None,
                 imports: List[str] = None,
                 calls: List[str] = None):
        self.id = unit_id
        self.file_path = file_path
        self.name = name
        self.kind = kind # 'function' or 'class'
        self.start_line = start_line
        self.end_line = end_line
        self.code = code
        self.docstring = docstring
        self.signature = signature
        self.imports = imports or []
        self.calls = calls or []

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__

class ASTVisitor(ast.NodeVisitor):
    def __init__(self, file_content: str, file_path: str):
        self.units: List[CodeUnit] = []
        self.file_content = file_content
        self.lines = file_content.splitlines()
        self.file_path = file_path
        self.current_class = None
        self.imports = []

    def _get_code_snippet(self, node):
        start = node.lineno - 1
        end = node.end_lineno
        return "\n".join(self.lines[start:end])

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            self.imports.append(node.module)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self._process_function(node)

    def visit_AsyncFunctionDef(self, node):
        self._process_function(node)

    def _process_function(self, node):
        name = node.name
        if self.current_class:
            name = f"{self.current_class}.{name}"
        
        unit_id = f"{self.file_path}::{name}"
        docstring = ast.get_docstring(node)
        code = self._get_code_snippet(node)
        
        # Extract calls (simple heuristic)
        calls = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    calls.append(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    calls.append(child.func.attr)
        
        unit = CodeUnit(
            unit_id=unit_id,
            file_path=self.file_path,
            name=name,
            kind='function',
            start_line=node.lineno,
            end_line=node.end_lineno,
            code=code,
            docstring=docstring,
            signature=f"def {name}(...)", # Simplified
            imports=list(self.imports), # Snapshot current imports
            calls=list(set(calls))
        )
        self.units.append(unit)
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        prev_class = self.current_class
        self.current_class = node.name
        
        unit_id = f"{self.file_path}::{node.name}"
        docstring = ast.get_docstring(node)
        code = self._get_code_snippet(node)
        
        unit = CodeUnit(
            unit_id=unit_id,
            file_path=self.file_path,
            name=node.name,
            kind='class',
            start_line=node.lineno,
            end_line=node.end_lineno,
            code=code,
            docstring=docstring,
            signature=f"class {node.name}",
            imports=list(self.imports)
        )
        self.units.append(unit)
        
        self.generic_visit(node)
        self.current_class = prev_class

def index_repo(repo_path: str) -> List[Dict[str, Any]]:
    repo_path = Path(repo_path).resolve()
    all_units = []
    
    logger.info(f"Indexing repo at {repo_path}")
    
    for root, dirs, files in os.walk(repo_path):
        # Skip hidden dirs, venv, tests
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['venv', 'tests', 'node_modules', '__pycache__']]
        
        for file in files:
            full_path = Path(root) / file
            rel_path = full_path.relative_to(repo_path)
            
            if file.endswith('.py'):
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    tree = ast.parse(content)
                    visitor = ASTVisitor(content, str(rel_path))
                    visitor.visit(tree)
                    
                    all_units.extend([u.to_dict() for u in visitor.units])
                except Exception as e:
                    logger.error(f"Failed to parse {full_path}: {e}")
            elif file.endswith(('.java', '.js', '.ts', '.md', '.txt')):
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Create a single unit for the whole file
                    unit = CodeUnit(
                        unit_id=str(rel_path),
                        file_path=str(rel_path),
                        name=file,
                        kind='file',
                        start_line=1,
                        end_line=len(content.splitlines()),
                        code=content,
                        docstring=None,
                        signature=None
                    )
                    all_units.append(unit.to_dict())
                except Exception as e:
                    logger.error(f"Failed to read {full_path}: {e}")
                    
    logger.info(f"Indexed {len(all_units)} units")
    return all_units
