"""
app/services/document_parser.py — Document loading and semantic text chunking.

Chunking strategy
─────────────────
Uses LangChain's SemanticChunker (langchain_experimental) which embeds every
sentence and groups consecutive sentences whose meaning is similar.  This keeps
each chunk topically coherent — important for trade documents where a single
paragraph might cover one tariff line or one regulatory clause.

The breakpoint threshold type is "percentile" by default: the splitter finds
the (threshold)th-percentile distance between adjacent sentences and splits
there.  Higher threshold → fewer, larger chunks.  Lower → more, smaller chunks.

Add support for new file types here without touching the pipeline.
"""

from pathlib import Path

from langchain_community.document_loaders import (
    Docx2txtLoader,
    PyPDFLoader,
    TextLoader,
    UnstructuredPowerPointLoader,
)
from langchain_core.documents import Document
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings

from app.config import settings

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".txt"}

# Lazy singleton — re-used across calls to avoid recreating the embeddings
# client on every document (each construction validates the API key).
_semantic_chunker: SemanticChunker | None = None


def _get_chunker() -> SemanticChunker:
    global _semantic_chunker
    if _semantic_chunker is None:
        embeddings = OpenAIEmbeddings(
            model=settings.embedding_model,
            openai_api_key=settings.openai_api_key,
            dimensions=settings.embedding_dimensions,
        )
        _semantic_chunker = SemanticChunker(
            embeddings=embeddings,
            breakpoint_threshold_type=settings.semantic_breakpoint_type,
            breakpoint_threshold_amount=settings.semantic_breakpoint_threshold,
        )
    return _semantic_chunker


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


def parse_and_chunk(file_path: str) -> list[Document]:
    """
    Load a document and split it into semantically coherent chunks.

    Returns a list of LangChain Document objects, each with
    .page_content (str) and .metadata (dict).

    SemanticChunker works on plain text, so we join all pages into a single
    string and then re-attach source metadata to each resulting chunk.
    """
    loader = get_loader(file_path)
    raw_docs = loader.load()
    if not raw_docs:
        raise RuntimeError("Document parser returned no content.")

    # SemanticChunker.create_documents() accepts a list of strings.
    # We pass each page's text individually so sentence-boundary detection
    # stays within a single page (avoids cross-page semantic bleeding).
    chunker = _get_chunker()
    chunks: list[Document] = []

    for doc in raw_docs:
        if not doc.page_content.strip():
            continue
        page_chunks = chunker.create_documents(
            texts=[doc.page_content],
            metadatas=[doc.metadata],
        )
        chunks.extend(page_chunks)

    if not chunks:
        raise RuntimeError("Semantic chunking produced zero chunks.")

    return chunks
