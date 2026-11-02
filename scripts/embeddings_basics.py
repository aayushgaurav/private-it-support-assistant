
from sentence_transformers import SentenceTransformer

# Load a small embedding model
model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)

sentences = [
    "How do I reset my password?",
    "How can I change my login credentials?",
    "Where is the company cafeteria?"
]

# Convert sentences into vectors
embeddings = model.encode(sentences)

# Display results
for sentence, vector in zip(sentences, embeddings):
    print("\nSentence:", sentence)
    print("Vector dimensions:", len(vector))
    print("First 5 values:", vector[:5])
