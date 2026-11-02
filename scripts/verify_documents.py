
from app.rag.retrieve import vector_store

document_id = "ed429c957e144b32a769b8f0e51f5488"

results = vector_store.get(
    where={"document_id": document_id},
    include=["documents", "metadatas"]
)

print("Chunks stored:", len(results["ids"]))

for index, content in enumerate(results["documents"][:3], start=1):
    print(f"\nCHUNK {index}:")
    print(content[:300])
