# VaultMind Project Guidelines

VaultMind is a private, on-premise RAG system. This project requires strict adherence to data privacy and local LLM consistency.

## 🛠️ Technical Constraints
- **RAG Consistency**: The embedding model used for document ingestion MUST exactly match the model used for query retrieval (currently `nomic-embed-text` via Ollama).
- **Local-First**: No external API calls to OpenAI, Anthropic, or any cloud provider are permitted in the core RAG pipeline.
- **Security**: All backend endpoints (except `/auth/token` and `/health`) must be protected by JWT authentication.

## 🤖 Claude Code Interaction
- **RAG Debugging**: When troubleshooting retrieval quality, always prioritize reading the `chroma_db` metadata and comparing the retrieved chunks with the final LLM response.
- **Tool Preference**: Prefer `Read` and `Grep` for auditing the RAG pipeline logic. Avoid destructive shell commands in the `rag_backend` directory.
- **Boundary**: Do not attempt to modify binary vector files in the `chroma_db` folder; always interact via the `RAGService` API.

## 📁 Project Structure
- `/app`: Next.js Frontend (VaultMind UI)
- `/rag_backend`: FastAPI Backend (The RAG core, LangChain, ChromaDB)
- `README.md`: Product documentation and business case.
