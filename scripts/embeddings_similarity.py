
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim

model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)

sentences = [
    "How do I reset my password?",
    "How can I change my login credentials?",
    "Where is the company cafeteria?"
]

# Convert all sentences into embeddings
embeddings = model.encode(sentences)

# Compare the first sentence with the other two
similarity_scores = cos_sim(
    embeddings[0],
    embeddings[1:]
)

print("Question:", sentences[0])

for sentence, score in zip(
    sentences[1:],
    similarity_scores[0]
):
    print(f"\nCompared with: {sentence}")
    print(f"Similarity: {score.item():.4f}")
