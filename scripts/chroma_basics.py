
import chromadb
from sentence_transformers import SentenceTransformer

# Load embedding model
model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)

# Create persistent ChromaDB client
client = chromadb.PersistentClient(
    path="data/chroma_db"
)

# Create a collection
collection = client.get_or_create_collection(
    name="it_support_documents"
)

# Sample documents
documents = [
    "Employees must reset their passwords every 90 days.",
    "Users must enable multi-factor authentication.",
    "Employees must connect to VPN before accessing internal resources.",
    "The company cafeteria serves lunch at 1 PM."
]

ids = ["doc1", "doc2", "doc3", "doc4"]

# Generate embeddings
embeddings = model.encode(documents).tolist()

# Store documents
collection.upsert(
    ids=ids,
    documents=documents,
    embeddings=embeddings
)

print("Documents stored:", collection.count())

# Search
question = "How frequently should I change my password?"

query_embedding = model.encode([question]).tolist()

results = collection.query(
    query_embeddings=query_embedding,
    n_results=2
)

print("\nSearch results:")

for document in results["documents"][0]:
    print("-", document)

