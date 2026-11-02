
from pathlib import Path

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma


# Project paths
PROJECT_DIR = Path(__file__).resolve().parents[2]

CHROMA_PATH = PROJECT_DIR / "data" / "chroma_db"


# Initialize embedding model
embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


# Connect to ChromaDB
vector_store = Chroma(
    collection_name="private_it_knowledge",
    embedding_function=embedding_model,
    persist_directory=str(CHROMA_PATH)
)

#retrieve documents from ChromaDB based on a question, with optional parameters for number of results and maximum distance
def retrieve_documents(
    question: str,
    user_role: str,
    k: int = 3,
    max_distance: float = 1.3
):
    # Step 1: Validate user role
    if user_role not in {"employee", "admin"}:
        return []

    # Step 2: Apply document access permissions
    if user_role == "employee":
        results = vector_store.similarity_search_with_score(
            query=question,
            k=k,
            filter={
                "access_level": "ALL_EMPLOYEES"
            }
        )

    else:
        # Admin can retrieve all access levels
        results = vector_store.similarity_search_with_score(
            query=question,
            k=k
        )

    # Step 3: Apply relevance threshold
    relevant_documents = []

    for document, distance in results:
        if distance <= max_distance:
            relevant_documents.append(document)

    return relevant_documents

if __name__ == "__main__":

    questions = [
        "What should I do if I forget my password?",
        "What are the basic Docker commands for listing running containers?",
        "What is the company's annual employee bonus policy?"
    ]

    for question in questions:

        print("\nQUESTION:", question)

        documents = retrieve_documents(question)

        if not documents:
            print("No sufficiently relevant documents found.")
            continue

        for document in documents:
            print("\nRESULT:")
            print(document.page_content)
