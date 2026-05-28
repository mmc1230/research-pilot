from pathlib import Path

from app.tools.tool_registry import register_tool


@register_tool(
    name="read_text_file",
    description="Read a UTF-8 compatible text file from disk.",
    args_schema={"file_path": "string"},
)
def read_text_file(file_path: str, max_chars: int = 20000) -> dict:
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")
    text = path.read_text(encoding="utf-8", errors="ignore")
    return {
        "file_path": str(path),
        "text": text[:max_chars],
        "truncated": len(text) > max_chars,
        "char_count": len(text),
    }
