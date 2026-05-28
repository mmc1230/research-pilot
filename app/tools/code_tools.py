import ast
from pathlib import Path
from typing import Any

from app.tools.tool_registry import register_tool


IGNORED_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "build",
    "dist",
    ".idea",
    ".vscode",
}
CODE_EXTENSIONS = {".py", ".cpp", ".c", ".h", ".hpp", ".md", ".yaml", ".yml", ".json", ".toml", ".txt"}


def _is_ignored(path: Path) -> bool:
    return any(part in IGNORED_DIRS for part in path.parts)


@register_tool(
    name="scan_project_tree",
    description="Scan a local project path and return a filtered tree plus candidate source files.",
    args_schema={"project_path": "string"},
)
def scan_project_tree(project_path: str, max_files: int = 300) -> dict[str, Any]:
    root = Path(project_path).resolve()
    if not root.exists() or not root.is_dir():
        raise FileNotFoundError(f"Project directory not found: {project_path}")

    files = []
    tree_lines = [root.name + "/"]
    count = 0
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if _is_ignored(rel):
            continue
        depth = len(rel.parts)
        if path.is_dir():
            if path.name in IGNORED_DIRS:
                continue
            if depth <= 4:
                tree_lines.append("  " * depth + path.name + "/")
            continue
        if path.suffix.lower() not in CODE_EXTENSIONS:
            continue
        files.append(str(path))
        count += 1
        if depth <= 4:
            tree_lines.append("  " * depth + path.name)
        if count >= max_files:
            break

    return {
        "project_path": str(root),
        "tree": "\n".join(tree_lines),
        "source_files": files,
        "file_count": len(files),
        "truncated": count >= max_files,
    }


def _summarize_python(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    try:
        module = ast.parse(text)
    except SyntaxError:
        return {"classes": [], "functions": [], "imports": [], "syntax_error": True}
    classes = [node.name for node in module.body if isinstance(node, ast.ClassDef)]
    functions = [node.name for node in module.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    imports = []
    for node in module.body:
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
    return {"classes": classes, "functions": functions, "imports": imports, "syntax_error": False}


@register_tool(
    name="summarize_code_file",
    description="Summarize a code or config file and extract major Python classes/functions when possible.",
    args_schema={"file_path": "string"},
)
def summarize_code_file(file_path: str, max_chars: int = 6000) -> dict[str, Any]:
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"Code file not found: {file_path}")
    text = path.read_text(encoding="utf-8", errors="ignore")
    summary = {
        "file_path": str(path),
        "extension": path.suffix.lower(),
        "line_count": len(text.splitlines()),
        "preview": text[:max_chars],
        "classes": [],
        "functions": [],
        "imports": [],
    }
    if path.suffix.lower() == ".py":
        summary.update(_summarize_python(path))
    return summary
