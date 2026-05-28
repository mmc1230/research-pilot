from dataclasses import dataclass


@dataclass
class DocumentRecord:
    id: int
    filename: str
    file_path: str
    doc_type: str
    collection_name: str
    created_at: str
    chunk_count: int = 0


@dataclass
class ToolCallRecord:
    session_id: str
    tool_name: str
    args: str
    result_summary: str
    created_at: str
