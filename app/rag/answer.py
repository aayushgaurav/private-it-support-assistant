
import re

from langchain_ollama import ChatOllama
from app.rag.retrieve import retrieve_documents


llm = ChatOllama(
    model="qwen2.5:1.5b",
    temperature=0,
)

FALLBACK = (
    "I could not find this information "
    "in the available IT documents."
)


def has_percentage_improvement_evidence(context: str) -> bool:
    number = r"\d+(?:\.\d+)?"
    percentage = rf"{number}\s*(?:%|percent(?:age)?)"

    patterns = [
        rf"\b(?:improv\w*|increas\w*|gain\w*)\b[^.\n]{{0,60}}{percentage}",
        rf"{percentage}[^.\n]{{0,60}}\b(?:improv\w*|increas\w*|gain\w*)\b",
    ]

    return any(
        re.search(pattern, context, re.IGNORECASE)
        for pattern in patterns
    )


def ask_question(question: str, user_role: str):

    documents = retrieve_documents(
        question=question,
        user_role=user_role,
        k=3,
    )

    if not documents:
        return {
            "question": question,
            "answer": FALLBACK,
            "sources": [],
        }

    context = "\n\n".join(
        document.page_content
        for document in documents
    )

    sources = [
        {
            "content": document.page_content,
            "metadata": {
                "document_id": document.metadata.get("document_id"),
                "original_filename": document.metadata.get("original_filename"),
                "department": document.metadata.get("department"),
                "access_level": document.metadata.get("access_level"),
                "page": document.metadata.get("page"),
                "start_index": document.metadata.get("start_index"),
            },
        }
        for document in documents
    ]

    # Numerical evidence guardrail
    asks_for_percentage_improvement = (
        re.search(r"percent(?:age)?|%", question, re.IGNORECASE)
        and re.search(
            r"\b(improv\w*|increas\w*|gain\w*)\b",
            question,
            re.IGNORECASE,
        )
    )

    if (
        asks_for_percentage_improvement
        and not has_percentage_improvement_evidence(context)
    ):
        return {
            "question": question,
            "answer": FALLBACK,
            "sources": sources,
        }

    prompt = f"""You are an IT support assistant.

Use only information explicitly supported by the context.

Rules:
1. Do not invent facts, numbers, or policies.
2. Keep experimental results specific to their described model.
3. Do not combine separate findings into new conclusions.
4. If the requested information is missing, reply exactly:
{FALLBACK}

CONTEXT:
{context}

QUESTION:
{question}

ANSWER:
"""

    try:
        response = llm.invoke(prompt)
        answer = response.content.strip()

    except Exception:
        answer = (
            "The local AI model is currently unavailable. "
            "Please check that Ollama is running and try again."
        )

    return {
        "question": question,
        "answer": answer,
        "sources": sources,
    }


if __name__ == "__main__":

    questions = [
        "What should I do if I forget my password?",
        "What are the password requirements for employees?",
        "What is the company's maternity leave policy?",
        "What is the exact accuracy percentage improvement achieved by RAG?",
    ]

    for question in questions:
        result = ask_question(question, "admin")

        print("\nQUESTION:", result["question"])
        print("ANSWER:", result["answer"])
        print("SOURCES:", len(result["sources"]))
