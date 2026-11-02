
from app.rag.retrieve import vector_store

questions = [
    "What are the basic Docker commands for listing running containers?",
    "What is the company's annual employee bonus policy?"
]

for question in questions:

    print("\nQUESTION:", question)

    results = vector_store.similarity_search_with_score(
        query=question,
        k=3
    )

    for document, distance in results:

        print("\nRAW DISTANCE:", round(distance, 4))
        print("CONTENT:", document.page_content[:250])
