import sys
import importlib

packages = [
    "fastapi",
    "uvicorn",
    "langchain",
    "chromadb",
    "sentence_transformers",
    "pypdf",
    "docx",
]

print("Python executable:", sys.executable)
print("\nChecking dependencies...\n")

for package in packages:
    try:
        importlib.import_module(package)
        print(f"[OK] {package}")
    except ImportError as error:
        print(f"[FAILED] {package}: {error}")