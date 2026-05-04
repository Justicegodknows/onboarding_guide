import os
from typing import List, Dict, Any
import fitz  # PyMuPDF
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.llms import Ollama
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:  # Backward compatibility with older LangChain installs
    from langchain.text_splitter import RecursiveCharacterTextSplitter
try:
    from langchain_core.documents import Document
except ImportError:  # Backward compatibility with older LangChain installs
    from langchain.docstore.document import Document

class RAGService:
    def __init__(self):
        # Configuration from environment or defaults
        self.embedding_model = "nomic-embed-text"
        self.llm_model = "llama3"
        self.persist_directory = "./chroma_db"

        # Initialize Ollama Embeddings
        self.embeddings = OllamaEmbeddings(model=self.embedding_model)

        # Initialize Vector Store
        self.vector_store = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings
        )

        # Initialize Ollama LLM
        self.llm = Ollama(model=self.llm_model)

    def ingest(self, file_path: str, metadata: Dict[str, Any] = None):
        """
        Full pipeline: Parse PDF -> Chunk -> Embed -> Store
        """
        # 1. Parse PDF using PyMuPDF
        text = ""
        with fitz.open(file_path) as doc:
            for page in doc:
                text += page.get_text()

        # 2. Chunk text
        chunks = self.chunk(text)

        # 3. Convert to LangChain Documents with metadata
        documents = []
        for chunk in chunks:
            doc_metadata = metadata or {}
            doc_metadata["source"] = file_path
            documents.append(Document(page_content=chunk, metadata=doc_metadata))

        # 4. Embed and store in ChromaDB
        self.vector_store.add_documents(documents)
        return {"status": "success", "chunks_added": len(documents)}

    def chunk(self, text: str) -> List[str]:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
            length_function=len,
        )
        return text_splitter.split_text(text)

    def retrieve(self, query: str, top_k: int = 3, filter_metadata: Dict = None) -> List[Dict]:
        """
        Retrieve the most relevant chunks from the vector store.
        """
        # Perform semantic search
        results = self.vector_store.similarity_search_with_relevance_scores(
            query,
            k=top_k,
            filter=filter_metadata
        )

        # Format results
        retrieved_docs = []
        for doc, score in results:
            retrieved_docs.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": score
            })

        return retrieved_docs

    def generate(self, context_docs: List[Dict], question: str) -> str:
        """
        Generate a grounded answer using the retrieved context and Ollama.
        """
        # Format context as a string with source markers
        context_text = "\n\n".join([
            f"Source [{i+1}] ({doc['metadata'].get('source', 'Unknown')}): {doc['content']}"
            for i, doc in enumerate(context_docs)
        ])

        system_prompt = (
            "You are VaultMind, a private corporate AI assistant. "
            "Answer the question strictly using the provided context. "
            "If the answer is not in the context, say 'I do not have enough information in the knowledge base to answer this.' "
            "Always cite your sources using [1], [2] format."
        )

        prompt = f"{system_prompt}\n\nContext:\n{context_text}\n\nQuestion: {question}\n\nAnswer:"

        response = self.llm.invoke(prompt)
        return response.strip()
