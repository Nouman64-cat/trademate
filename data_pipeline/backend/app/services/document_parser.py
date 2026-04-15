"""
app/services/document_parser.py — Document loading and text chunking.

Add support for new file types here without touching the pipeline.
"""

from pathlib import Path

from langchain_community.document_loaders import (
    Docx2txtLoader,
    PyPDFLoader,
    TextLoader,
    UnstructuredPowerPointLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".txt"}


def get_loader(file_path: str):
    """Return the appropriate LangChain loader for the given file path."""
    ext = Path(file_path).suffix.lower()
    loaders = {
        ".pdf":  lambda: PyPDFLoader(file_path),
        ".docx": lambda: Docx2txtLoader(file_path),
        ".pptx": lambda: UnstructuredPowerPointLoader(file_path),
        ".txt":  lambda: TextLoader(file_path, encoding="utf-8"),
    }
    if ext not in loaders:
        raise ValueError(
            f"Unsupported file type: '{ext}'. Supported: {sorted(SUPPORTED_EXTENSIONS)}"
        )
    return loaders[ext]()


def parse_and_chunk(file_path: str) -> list:
    """
    Load a document and split it into chunks.

    Returns a list of LangChain Document objects, each with
    .page_content (str) and .metadata (dict).
    """
    loader = get_loader(file_path)
    raw_docs = loader.load()
    if not raw_docs:
        raise RuntimeError("Document parser returned no content.")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        length_function=len,
    )
    chunks = splitter.split_documents(raw_docs)
    if not chunks:
        raise RuntimeError("Text splitting produced zero chunks.")

    return chunks
