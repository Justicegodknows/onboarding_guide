import importlib
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings


class RAGService:
    def __init__(self):
        self.embedding_model = "nomic-embed-text"
        self.llm_model = settings.LM_STUDIO_MODEL
        self.persist_directory = "./chroma_db"

        vectorstores = importlib.import_module("langchain_community.vectorstores")
        embeddings_mod = importlib.import_module("langchain_community.embeddings")

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

        self.embeddings = embeddings_mod.OllamaEmbeddings(model=self.embedding_model)
        self.vector_store = vectorstores.Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings,
        )

    def chunk(self, text: str) -> List[str]:
        return self._splitter.split_text(text)

    def ingest(self, document: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if isinstance(document, dict):
            content = str(document.get("text") or document.get("content") or "").strip()
            if not content:
                return {"status": "skipped", "chunks_added": 0}
            doc_metadata = {**(metadata or {}), **{k: v for k, v in document.items() if k not in {"text", "content"}}}
            docs = [self._Document(page_content=content, metadata=doc_metadata)]
            self.vector_store.add_documents(docs)
            return {"status": "success", "chunks_added": 1}

        file_path = str(document)
        text = ""
        with self._fitz.open(file_path) as doc:
            for page in doc:
                text += page.get_text()

        chunks = self.chunk(text)
        documents = []
        for chunk_text in chunks:
            doc_metadata = {**(metadata or {}), "source": file_path}
            documents.append(self._Document(page_content=chunk_text, metadata=doc_metadata))

        self.vector_store.add_documents(documents)
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
        base_url = runtime_settings.LM_STUDIO_BASE_URL.rstrip("/")
        url = f"{base_url}/v1/chat/completions"

        headers = {"Content-Type": "application/json"}
        if runtime_settings.LLM_API_KEY:
            headers["Authorization"] = f"Bearer {runtime_settings.LLM_API_KEY}"

        payload = {
            "model": runtime_settings.LM_STUDIO_MODEL,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 700,
        }

        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

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
                    "LM Studio returned 401 Unauthorized. "
                    "Check LLM_API_KEY and LM Studio authentication settings."
                )
            return (
                f"LM Studio request failed with status {exc.response.status_code}. "
                "Please verify LM Studio is running and the selected model is loaded."
            )
        except (httpx.ConnectError, httpx.ConnectTimeout, OSError):
            return (
                "LM Studio is unavailable right now. "
                "Please start LM Studio and retry."
            )
