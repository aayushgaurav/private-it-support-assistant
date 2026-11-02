
import logging
from pathlib import Path

from docx import Document as WordDocument

from langchain_core.documents import Document
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.rag.retrieve import vector_store

logger = logging.getLogger(__name__)


def extract_document(file_path: Path):
    """
    Extract readable text from TXT, PDF or DOCX files.
    """

    extension = file_path.suffix.lower()

    if extension == ".txt":
        loader = TextLoader(
            str(file_path),
            encoding="utf-8"
        )
        documents = loader.load()

    elif extension == ".pdf":
        loader = PyPDFLoader(str(file_path))
        documents = loader.load()

    elif extension == ".docx":
        word_document = WordDocument(str(file_path))

        extracted_text = []

        # Extract paragraphs
        for paragraph in word_document.paragraphs:
            if paragraph.text.strip():
                extracted_text.append(paragraph.text)

        # Extract tables
        for table in word_document.tables:
            for row in table.rows:
                row_text = " | ".join(
                    cell.text.strip()
                    for cell in row.cells
                )
                if row_text.strip():
                    extracted_text.append(row_text)

        documents = [
            Document(
                page_content="\n".join(extracted_text),
                metadata={}
            )
        ]

    else:
        raise ValueError("Unsupported document format.")

    if not any(doc.page_content.strip() for doc in documents):
        raise ValueError("No readable text found in the document.")

    return documents


def process_document(
    file_path: Path,
    document_id: str,
    original_filename: str,
    access_level: str
):
    """
    Extract, chunk, embed and store a document.

    Compensating cleanup strategy:
    - If parsing or chunking fails, no ChromaDB write has occurred yet.
    - If ChromaDB indexing fails after a partial write, we attempt to
      delete any chunks already written for this document_id before
      re-raising, so no orphaned vectors are left behind.
    - The physical file cleanup is the caller's responsibility
      (handled in main.py upload_document).
    """

    # Step 1: Extract text (raises ValueError on parse failure — no DB write yet)
    documents = extract_document(file_path)

    # Step 2: Prepare metadata
    for document in documents:
        document.metadata["document_id"] = document_id
        document.metadata["original_filename"] = original_filename
        document.metadata["department"] = "IT"
        document.metadata["access_level"] = access_level

    # Step 3: Split text into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=350,
        chunk_overlap=50,
        add_start_index=True
    )

    chunks = splitter.split_documents(documents)

    if not chunks:
        raise ValueError("No text chunks could be created.")

    # Step 4: Generate unique IDs for chunks
    chunk_ids = [
        f"{document_id}-{index}"
        for index in range(len(chunks))
    ]

    # Step 5: Store chunks and embeddings in ChromaDB
    # If this raises, attempt compensating cleanup of any partial writes.
    try:
        vector_store.add_documents(
            documents=chunks,
            ids=chunk_ids
        )
    except Exception as chroma_error:
        logger.error(
            "ChromaDB indexing failed for document_id=%s — attempting cleanup",
            document_id,
        )
        try:
            existing = vector_store.get(
                where={"document_id": document_id},
                include=["metadatas"],
            )
            if existing["ids"]:
                vector_store.delete(ids=existing["ids"])
                logger.info(
                    "Compensating cleanup removed %d orphaned chunks for document_id=%s",
                    len(existing["ids"]),
                    document_id,
                )
        except Exception as cleanup_error:
            logger.error(
                "Compensating ChromaDB cleanup also failed for document_id=%s: %s",
                document_id,
                cleanup_error,
            )
        raise chroma_error

    return {
        "document_id": document_id,
        "filename": original_filename,
        "total_chunks": len(chunks),
        "status": "processed successfully"
    }


def list_processed_documents():
    results = vector_store.get(
        include=["metadatas"]
    )

    documents = {}

    for metadata in results["metadatas"]:
        document_id = metadata.get("document_id")

        if not document_id:
            continue

        if document_id not in documents:
            documents[document_id] = {
                "document_id": document_id,
                "original_filename": metadata.get("original_filename"),
                "department": metadata.get("department"),
                "access_level": metadata.get("access_level"),
                "total_chunks": 0
            }

        documents[document_id]["total_chunks"] += 1

    return list(documents.values())


def delete_processed_document(document_id: str, document_dir: Path):
    # Step 1: Find all ChromaDB chunks for this document
    results = vector_store.get(
        where={"document_id": document_id},
        include=["metadatas"]
    )
    chunk_ids = results["ids"]

    # Step 2: Locate the physical file (exact extension, no wildcards)
    physical_file: Path | None = None
    for extension in [".pdf", ".docx", ".txt"]:
        candidate = document_dir / f"{document_id}{extension}"
        # Security: confirm the resolved path stays inside document_dir
        if candidate.resolve().parent == document_dir.resolve() and candidate.is_file():
            physical_file = candidate
            break

    # Step 3: Nothing to delete at all
    if not chunk_ids and physical_file is None:
        return {
            "document_id": document_id,
            "deleted_chunks": 0,
            "deleted_file": False,
            "file_error": None,
            "status": "not_found",
        }

    # Step 4: Delete ChromaDB chunks (only if any exist)
    if chunk_ids:
        vector_store.delete(ids=chunk_ids)

    # Step 5: Delete the physical file
    deleted_file = False
    file_error: str | None = None

    if physical_file is not None:
        try:
            physical_file.unlink()
            deleted_file = True
        except OSError as exc:
            file_error = str(exc)

  
    # Step 6: Determine status
    if chunk_ids and deleted_file:
        status = "deleted"

    elif chunk_ids and physical_file is None:
        status = "chunks_deleted_file_missing"

    elif chunk_ids and file_error is not None:
        status = "chunks_deleted_file_failed"

    elif not chunk_ids and deleted_file:
        status = "orphaned_file_deleted"

    else:
        status = "orphaned_file_failed"

    return {
        "document_id": document_id,
        "deleted_chunks": len(chunk_ids),
        "deleted_file": deleted_file,
        "file_error": file_error,
        "status": status,
    }