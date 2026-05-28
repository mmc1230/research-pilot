from langchain_text_splitters import RecursiveCharacterTextSplitter


def build_splitter(chunk_size: int = 1000, chunk_overlap: int = 150) -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )


def split_documents(documents, chunk_size: int = 1000, chunk_overlap: int = 150):
    return build_splitter(chunk_size, chunk_overlap).split_documents(documents)
