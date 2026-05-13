import importlib
import csv
from typing import Any, Dict, List, Optional

import httpx
from openai import OpenAI

from app.core.config import settings


class NvidiaEmbeddings:
    """LangChain-compatible embeddings backed by a NVIDIA NIM microservice.

    NVIDIA NIM exposes an OpenAI-compatible ``/embeddings`` endpoint and
    accepts an extra ``input_type`` parameter that drives asymmetric retrieval:
      - ``"passage"``  — used when ingesting / indexing documents into ChromaDB.
      - ``"query"``    — used when embedding a user query at retrieval time.

    Both paths share the same model name, satisfying the RAG consistency
    requirement (CLAUDE.md): ingest and retrieve always use the same model.

    For a locally-hosted DGX Spark NIM container, set ``NVIDIA_BASE_URL``
    to the container's endpoint (e.g. ``http://localhost:8000/v1``).
    The ``NVIDIA_API_KEY`` can be left empty for local deployments that
    don't enforce authentication, or filled in for the NVIDIA cloud API.
    """

    def __init__(self):
        self._client = OpenAI(
            api_key=settings.NVIDIA_API_KEY or "no-key-needed",
            base_url=settings.NVIDIA_BASE_URL,
        )
        self._model = settings.NVIDIA_EMBED_MODEL
        self._truncate = settings.NVIDIA_EMBED_TRUNCATE
        self._input_type_passage = settings.NVIDIA_EMBED_INPUT_TYPE_PASSAGE
        self._input_type_query = settings.NVIDIA_EMBED_INPUT_TYPE_QUERY

    def _embed(self, texts: List[str], input_type: str) -> List[List[float]]:
        response = self._client.embeddings.create(
            input=texts,
            model=self._model,
            encoding_format="float",
            extra_body={
                "input_type": input_type,
                "truncate": self._truncate,
            },
        )
        # NIM returns data sorted by index; preserve that order.
        sorted_data = sorted(response.data, key=lambda item: item.index)
        return [item.embedding for item in sorted_data]

    # --- LangChain Embeddings interface ---

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents (passages) for indexing."""
        return self._embed(texts, self._input_type_passage)

    def embed_query(self, text: str) -> List[float]:
        """Embed a single user query for similarity search."""
        return self._embed([text], self._input_type_query)[0]


class RAGService:
    def __init__(self):
        self.embedding_model = settings.NVIDIA_EMBED_MODEL
        self.llm_model = settings.LM_STUDIO_MODEL
        self.persist_directory = "./chroma_db"

        try:
            chroma_mod = importlib.import_module("langchain_chroma")
            self._Chroma = chroma_mod.Chroma
        except ImportError:
            vectorstores = importlib.import_module("langchain_community.vectorstores")
            self._Chroma = vectorstores.Chroma

        try:
            splitters_mod = importlib.import_module("langchain_text_splitters")
        except ImportError:
            splitters_mod = importlib.import_module("langchain.text_splitter")

        try:
            docs_mod = importlib.import_module("langchain_core.documents")
        except ImportError:
            docs_mod = importlib.import_module("langchain.docstore.document")

        self._fitz = importlib.import_module("fitz")
        self._Document = docs_mod.Document
        self._splitter = splitters_mod.RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
            length_function=len,
        )

        self.embeddings = NvidiaEmbeddings()
        self.vector_store = self._Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings,
        )

    def chunk(self, text: str) -> List[str]:
        return self._splitter.split_text(text)

    def _extract_text_from_file(self, file_path: str) -> str:
        lower = file_path.lower()
        if lower.endswith(".pdf"):
            text = ""
            with self._fitz.open(file_path) as doc:
                for page in doc:
                    text += page.get_text()
            return text

        if lower.endswith(".docx"):
            docx_mod = importlib.import_module("docx")
            parsed = docx_mod.Document(file_path)
            return "\n".join(p.text for p in parsed.paragraphs if p.text.strip())

        if lower.endswith((".txt", ".md")):
            with open(file_path, "r", encoding="utf-8", errors="replace") as handle:
                return handle.read()

        if lower.endswith(".csv"):
            rows: List[str] = []
            with open(file_path, "r", encoding="utf-8", errors="replace", newline="") as handle:
                reader = csv.reader(handle)
                for row in reader:
                    line = " | ".join(cell.strip() for cell in row if str(cell).strip())
                    if line:
                        rows.append(line)
            return "\n".join(rows)

        raise ValueError(f"Unsupported file type for ingestion: {file_path}")

    def ingest(self, document: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if isinstance(document, dict):
            content = str(document.get("text") or document.get("content") or "").strip()
            if not content:
                return {"status": "skipped", "chunks_added": 0}
            doc_metadata = {**(metadata or {}), **{k: v for k, v in document.items() if k not in {"text", "content"}}}
            docs = [self._Document(page_content=content, metadata=doc_metadata)]
            doc_id = str(doc_metadata.get("chunk_id") or "")
            ids = [doc_id] if doc_id else None
            self.vector_store.add_documents(docs, ids=ids)
            return {"status": "success", "chunks_added": 1}

        file_path = str(document)
        text = self._extract_text_from_file(file_path)

        chunks = self.chunk(text)
        documents = []
        ids: List[str] = []
        for idx, chunk_text in enumerate(chunks):
            base_metadata = metadata or {}
            doc_metadata = {**base_metadata, "source": base_metadata.get("source", file_path)}
            documents.append(self._Document(page_content=chunk_text, metadata=doc_metadata))
            doc_id = str(base_metadata.get("doc_id") or "")
            ids.append(f"{doc_id}:{idx}" if doc_id else f"{file_path}:{idx}")

        self.vector_store.add_documents(documents, ids=ids)
        return {"status": "success", "chunks_added": len(documents)}

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        results = self.vector_store.similarity_search_with_relevance_scores(
            query,
            k=top_k,
            filter=filter_metadata,
        )

        retrieved_docs: List[Dict[str, Any]] = []
        for doc, score in results:
            retrieved_docs.append(
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": score,
                }
            )
        return retrieved_docs

    async def _generate_via_openai_compat(self, messages: List[Dict[str, str]], runtime_settings) -> str:
        """Send a chat completion request to NVIDIA NIM, falling back to LM Studio."""
        nvidia_base = runtime_settings.NVIDIA_BASE_URL.rstrip("/")
        nvidia_url = f"{nvidia_base}/chat/completions"

        nvidia_headers = {"Content-Type": "application/json"}
        if runtime_settings.NVIDIA_API_KEY:
            nvidia_headers["Authorization"] = f"Bearer {runtime_settings.NVIDIA_API_KEY}"

        payload = {
            "model": runtime_settings.NVIDIA_CHAT_MODEL,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 700,
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(nvidia_url, json=payload, headers=nvidia_headers)
                response.raise_for_status()
                data = response.json()
            return str(data["choices"][0]["message"].get("content", "")).strip()
        except (httpx.ConnectError, httpx.ConnectTimeout, OSError):
            # NVIDIA NIM unreachable — fall back to LM Studio
            pass
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code not in (502, 503, 504):
                raise

        # LM Studio fallback
        lm_base = runtime_settings.LM_STUDIO_BASE_URL.rstrip("/")
        lm_url = f"{lm_base}/v1/chat/completions"
        lm_headers = {"Content-Type": "application/json"}
        if runtime_settings.LLM_API_KEY:
            lm_headers["Authorization"] = f"Bearer {runtime_settings.LLM_API_KEY}"

        lm_payload = {
            "model": runtime_settings.LM_STUDIO_MODEL,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 700,
        }
        async with httpx.AsyncClient(timeout=45.0) as client:
            lm_response = await client.post(lm_url, json=lm_payload, headers=lm_headers)
            lm_response.raise_for_status()
            data = lm_response.json()
        return str(data["choices"][0]["message"].get("content", "")).strip()

    async def generate(
        self,
        context: Any,
        question: str,
        system_prompt: Optional[str] = None,
    ) -> str:
        if isinstance(context, list):
            context_text = "\n\n".join(str(item) for item in context)
        else:
            context_text = str(context or "")

        resolved_system_prompt = system_prompt or (
            "You are VaultMind onboarding assistant. "
            "Answer strictly from the supplied context. "
            "If context is insufficient, say so clearly."
        )

        user_content = (
            f"Context:\n{context_text}\n\n"
            f"Question:\n{question}\n\n"
            "Answer:"
        )
        messages = [
            {"role": "system", "content": resolved_system_prompt},
            {"role": "user", "content": user_content},
        ]

        try:
            return await self._generate_via_openai_compat(messages, settings)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401:
                return (
                    "NVIDIA NIM returned 401 Unauthorized. "
                    "Check NVIDIA_API_KEY in rag_backend/.env."
                )
            return (
                f"LLM request failed with status {exc.response.status_code}. "
                "Verify NVIDIA NIM is running and NVIDIA_CHAT_MODEL is correct."
            )
        except (httpx.ConnectError, httpx.ConnectTimeout, OSError):
            return (
                "NVIDIA NIM and LM Studio are both unreachable. "
                "Ensure your NIM container is running (or set NVIDIA_BASE_URL to the DGX Spark endpoint)."
            )
