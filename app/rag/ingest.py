
from pathlib import Path

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma


# 1. Define project paths
PROJECT_DIR = Path(__file__).resolve().parents[2]

DOCUMENT_PATH = (
    PROJECT_DIR / "data" / "documents" / "it_security_policy.txt"
)

CHROMA_PATH = PROJECT_DIR / "data" / "chroma_db"


# 2. Load the document
loader = TextLoader(
    str(DOCUMENT_PATH),
    encoding="utf-8"
)

documents = loader.load()

print("Documents loaded:", len(documents))


# 3. Split the document into chunks
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=350,
    chunk_overlap=50,
    add_start_index=True
)

chunks = text_splitter.split_documents(documents)

# Add demonstration metadata
for chunk in chunks:
    chunk.metadata["document_id"] = "it-security-policy"
    chunk.metadata["department"] = "IT"
    chunk.metadata["access_level"] = "ALL_EMPLOYEES"

print("Total chunks created:", len(chunks))


# 4. Load the embedding model
embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


# 5. Connect to persistent ChromaDB
vector_store = Chroma(
    collection_name="private_it_knowledge",
    embedding_function=embedding_model,
    persist_directory=str(CHROMA_PATH)
)


# 6. Store chunks and their embeddings
chunk_ids = [
    f"it-security-policy-{index}"
    for index in range(len(chunks))
]

vector_store.add_documents(
    documents=chunks,
    ids=chunk_ids
)

print("Chunks stored in ChromaDB:", len(chunks))
print("Ingestion completed successfully!")
