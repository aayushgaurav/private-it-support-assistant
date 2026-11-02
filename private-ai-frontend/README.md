# Private AI IT Support Assistant — Frontend

A React + TypeScript frontend for the existing FastAPI local-first RAG application.

## Requirements

- Node.js 20 or newer
- Existing FastAPI backend running separately
- Backend reachable from the browser

## Setup

```bash
npm install
copy .env.example .env
npm run dev
```

On macOS/Linux, use `cp .env.example .env` instead of `copy`.

Set `VITE_API_BASE_URL` in `.env` to the base URL of your FastAPI server.

## Build

```bash
npm run build
npm run preview
```

## API integration implemented from the supplied OpenAPI specification

- `POST /auth/register`: JSON `{ username, email, password }`
- `POST /auth/login`: form-urlencoded `{ username, password }`
- `GET /auth/me`: bearer token
- `POST /ask`: JSON `{ question }`
- `POST /upload`: multipart `{ file, access_level }`
- `GET /documents`
- `DELETE /documents/{document_id}`
- `GET /admin/dashboard`
- `GET /admin/audit-logs?limit=&offset=&action=`

The supplied OpenAPI file does not define detailed response schemas for `/ask`,
`/documents`, `/admin/dashboard`, or `/admin/audit-logs`. The frontend therefore
uses defensive response normalization for those endpoints. If your backend returns
a different shape, update `src/lib/normalizers.ts`.

## Authentication note

The API returns a bearer token. This starter stores it in `sessionStorage` so it
is cleared when the browser tab session ends. For production, consider moving
authentication to secure HttpOnly cookies by updating the backend and frontend
together. Do not expose JWT secrets in frontend environment variables.

## Local-first privacy

The frontend only calls the configured FastAPI server. It does not call a cloud
LLM provider. Ollama and ChromaDB remain behind the backend.

## CORS

When frontend and backend use different origins, configure FastAPI CORS to allow
the frontend origin. Do not use wildcard origins with credentialed requests.
