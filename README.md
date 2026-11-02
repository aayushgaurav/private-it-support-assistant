# Private AI IT Support Assistant

A local-first, AI-powered IT support assistant that uses Retrieval-Augmented Generation (RAG) to answer technical questions from internal IT documents. Built with FastAPI, React, ChromaDB and Ollama, it provides secure document management, role-based access control and auditable AI-assisted support.

## Overview

The Private AI IT Support Assistant helps employees find answers to technical questions using an organization's internal knowledge base.

Instead of relying entirely on generic AI responses, the application retrieves relevant information from uploaded documents and uses a locally running language model to generate context-aware answers.

The application is designed with privacy, security and access control in mind.

## Key Features

### AI-Powered Question Answering
- Retrieval-Augmented Generation (RAG).
- Semantic document retrieval using ChromaDB.
- Local LLM inference through Ollama.
- Context-aware responses based on uploaded IT documentation.
- Source references for retrieved information.
- Friendly error handling when the local AI model is unavailable.

### Document Management
- Upload PDF, DOCX and TXT documents.
- Document processing and text extraction.
- Vector embeddings and semantic indexing.
- Document listing and deletion.
- Document-level access permissions.

### Authentication and Authorization
- User registration and login.
- JWT-based authentication.
- Argon2 password hashing.
- Role-Based Access Control (RBAC).
- Admin and employee roles.
- Active-user verification.

### Security and Auditing
- Upload file-size restrictions.
- File extension and content validation.
- Upload rate limiting.
- Protection against unauthorized document access.
- Secure document deletion and cleanup.
- Audit logging for important operations.
- Admin-only audit log access.
- Audit log retention management.

### Admin Dashboard
- Administrative dashboard.
- Document and user access controls.
- Audit log monitoring.
- Paginated audit log retrieval and filtering.

## Technology Stack

| Layer | Technologies |
|---|---|
| Frontend | React, TypeScript, Vite |
| Backend | Python, FastAPI |
| Database | SQLite |
| Vector Database | ChromaDB |
| AI / LLM | Ollama, Qwen 2.5, Gemma 2 |
| Embeddings | Sentence Transformers |
| Authentication | JWT, Argon2 |
| Document Processing | PDF, DOCX, TXT |
| API Documentation | Swagger UI |

## Architecture

```text
                  User
                   |
                   v
          React + TypeScript
                   |
                   v
             FastAPI Backend
                   |
          Authentication / RBAC
                   |
                   v
             RAG Pipeline
                   |
          +--------+--------+
          |                 |
          v                 v
      ChromaDB           Ollama
   Vector Retrieval    Local LLM
          |                 |
          +--------+--------+
                   |
                   v
             AI Response
                   |
                   v
             User Interface


       Supporting Components
       ----------------------
       SQLite       -> Users and audit logs
       File Storage -> Uploaded documents
```

## Project Structure

```text
Private-AI-IT-Support-Assistant/
│
├── app/
│   ├── main.py
│   ├── database.py
│   ├── models/
│   ├── routers/
│   ├── services/
│   └── rag/
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
│
├── data/
│
├── tests/
│   └── test_upload_security.py
│
├── scripts/
│
├── requirements.txt
├── .gitignore
└── README.md
```

## Getting Started

### Prerequisites

Install the following:

- Python 3.14 (or a compatible version for the dependencies)
- Node.js and npm
- Ollama
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/aayushgaurav/private-it-support-assistant.git

cd private-it-support-assistant
```

### 2. Create a Python Virtual Environment

Windows PowerShell:

```powershell
python -m venv venv

.\venv\Scripts\Activate.ps1
```

### 3. Install Backend Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install and Run Ollama

Install Ollama from:

https://ollama.com/

Pull a supported model:

```bash
ollama pull qwen2.5:1.5b
```

Alternatively:

```bash
ollama pull gemma2:2b
```

Make sure Ollama is running before testing AI-powered question answering.

### 5. Start the Backend

From the project root, run:

```bash
uvicorn app.main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

Swagger API documentation:

```text
http://127.0.0.1:8000/docs
```

### 6. Start the Frontend

Open another terminal:

```bash
cd frontend

npm install

npm run dev
```

Frontend:

```text
http://localhost:5173
```

Configure the frontend API base URL in its environment configuration:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Use the actual configuration expected by the frontend if it differs.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/auth/register` | Register a user |
| POST | `/auth/login` | Authenticate a user |
| GET | `/auth/me` | Get current user |
| POST | `/ask` | Ask an AI question |
| POST | `/upload` | Upload a document |
| GET | `/documents` | List documents |
| DELETE | `/documents/{document_id}` | Delete a document |
| GET | `/admin/dashboard` | Admin dashboard |
| GET | `/admin/audit-logs` | Retrieve audit logs |

Access to endpoints is controlled by authentication and authorization rules.

## Security Model

The application implements multiple security controls:

- JWT-based authentication.
- Argon2 password hashing.
- Role-based authorization.
- Document-level permissions (`ALL_EMPLOYEES` and `ADMIN_ONLY`).
- Upload validation using file signatures and content checks.
- Maximum upload size of 10 MB.
- Upload rate limiting.
- Document path containment checks.
- Audit logging.
- Restricted administrative operations.
- Cleanup of partially processed documents.

## Testing

The project includes automated upload security tests.

Run:

```bash
pytest tests/test_upload_security.py -v
```

**Latest recorded test result:** 28 tests passed.

Additional manual testing has covered authentication, authorization, document deletion, RAG retrieval and Ollama failure handling.

## Privacy-First Design

The application is designed to run AI inference locally through Ollama.

This reduces dependence on external LLM APIs and allows internal IT documents to be processed within the local application environment.

Actual privacy and data protection depend on the deployment configuration, network exposure and storage security.

## Deployment

The application currently runs locally and is being prepared for cloud deployment.

The planned deployment architecture includes:

- FastAPI backend.
- React frontend.
- Ollama inference.
- Persistent ChromaDB storage.
- Persistent SQLite database.
- Persistent uploaded-document storage.
- HTTPS and secure network configuration.

Cloud deployment is a work in progress.

## Future Improvements

- Cloud deployment with persistent storage.
- Advanced document ingestion and retrieval.
- Improved RAG evaluation and response accuracy.
- Monitoring and analytics.
- Automated database and document backups.
- Improved administrative reporting.
- Multi-user organizational deployment.

## Author

**Aayush Gaurav**

GitHub: https://github.com/aayushgaurav

## License

This project is currently provided for educational and development purposes. A formal open-source license can be added when the distribution terms are decided.
