# 🔒 VaultMind: Private AI Knowledge Assistant

VaultMind is a fully private, on-premise AI assistant designed for Small to Medium Enterprises (SMEs). It allows employees to query the entire company document library in plain English—with zero data leaving the network, zero cloud subscriptions, and zero per-user fees.

## 💼 Business Case
SMEs lose significant productivity to information search waste and face high compliance risks from "Shadow AI" (employees using public LLMs with confidential data). VaultMind solves this by providing a sanctioned, local alternative that guarantees data sovereignty and reduces onboarding friction.

## 🏗️ Architecture
VaultMind follows a **Retrieval-Augmented Generation (RAG)** architecture:
`User Interface (Next.js)` $\rightarrow$ `API Gateway (FastAPI)` $\rightarrow$ `RAG Pipeline (LangChain)` $\rightarrow$ `Vector Store (ChromaDB)` $\rightarrow$ `Local LLM (Ollama)`.

### Tech Stack
- **Frontend**: Next.js, Tailwind CSS, TypeScript.
- **Backend API**: Python / FastAPI.
- **RAG Framework**: LangChain.
- **Vector Database**: ChromaDB (Local).
- **LLM Runtime**: Ollama (Local).
- **Document Parsing**: PyMuPDF (fitz).
- **Security**: JWT Tokens with Role-Based Access Control (RBAC).
- **Deployment**: Docker & Docker Compose.

## 🚀 Getting Started

### Prerequisites
- **Docker & Docker Compose** installed.
- **Ollama** installed locally (or running in Docker).
- **GPU** (NVIDIA RTX 4090 recommended for optimal performance).

### Installation
1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd onboarding_guide
   ```

2. **Start the Backend**:
   ```bash
   cd rag_backend
   docker-compose up -d
   ```

3. **Pull Required Models via Ollama**:
   ```bash
   ollama pull llama3
   ollama pull nomic-embed-text
   ```

4. **Start the Frontend**:
   ```bash
   # From root directory
   npm install
   npm run dev
   ```
   Access the app at `http://localhost:3000`.

## 🔐 Security & Permissions
VaultMind implements granular access control:
- **Users**: Can query documents and receive cited answers.
- **Admins**: Can upload new documents to the knowledge base via the Admin Dashboard.
- **RBAC**: Enforced via JWT claims (e.g., `department: "Finance"`).

## 📊 Expected ROI
- **Search Waste**: Recovers ~2 hours of productivity per employee/day.
- **Cost**: Eliminates per-seat cloud AI subscriptions ($30-$60/user/mo).
- **Risk**: 100% elimination of data leakage to third-party LLM providers.
