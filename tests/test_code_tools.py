from pathlib import Path

from app.tools.code_tools import scan_project_tree, summarize_code_file


def test_scan_and_summarize_python(tmp_path: Path):
    (tmp_path / ".git").mkdir()
    (tmp_path / "main.py").write_text(
        "import os\n\nclass Runner:\n    pass\n\ndef main():\n    return 1\n",
        encoding="utf-8",
    )
    scan = scan_project_tree(str(tmp_path))
    assert "main.py" in scan["tree"]
    assert ".git" not in scan["tree"]

    summary = summarize_code_file(str(tmp_path / "main.py"))
    assert "Runner" in summary["classes"]
    assert "main" in summary["functions"]
