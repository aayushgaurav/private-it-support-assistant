
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Step 1: Create a sample document
document = Document(
    page_content="""
    Employees must use multi-factor authentication
    when accessing company applications.

    Passwords must contain at least 12 characters.

    Employees must connect to the company VPN
    before accessing internal resources.

    If an employee forgets their password,
    they must contact the IT support team.
    """,
    metadata={
        "source": "IT_Security_Policy.pdf",
        "page": 1,
        "department": "IT"
    }
)

# Step 2: Create a text splitter
splitter = RecursiveCharacterTextSplitter(
    chunk_size=100,
    chunk_overlap=20
)

# Step 3: Split the document
chunks = splitter.split_documents([document])

# Step 4: Display the chunks
print("Total chunks:", len(chunks))

for index, chunk in enumerate(chunks):
    print(f"\n--- Chunk {index + 1} ---")
    print("Content:", chunk.page_content)
    print("Metadata:", chunk.metadata)
