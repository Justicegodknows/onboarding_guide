"""
Admin RAG Service - Separate vector store and retrieval for administrator data.

This service maintains an exclusive ChromaDB collection for admin-only documents,
while also providing dual-database retrieval (admin + main RAG database).
"""
import importlib
from typing import Any, Dict, List, Optional

from app.services.rag_service import RAGService, NvidiaEmbeddings


class AdminRAGService(RAGService):
    """
    Extended RAG Service for administrator use with exclusive database.
    
    Features:
    - Separate ChromaDB collection: "admin_database"
    - Dual retrieval: can query both main RAG + admin database
    - Same chunking parameters as regular pipeline
    - Admin-specific metadata tagging
    """

    def __init__(self):
        # Initialize parent RAGService
        super().__init__()
        
        # Create separate admin vector store with dedicated collection
        self.admin_persist_directory = "./chroma_db_admin"
        self.admin_vector_store = self._Chroma(
            persist_directory=self.admin_persist_directory,
            embedding_function=self.embeddings,
            collection_name="admin_database",
        )
    
    def ingest_admin(
        self,
        document: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Ingest document into admin-exclusive database.
        
        Args:
            document: Dict with 'text'/'content' or file path
            metadata: Additional metadata to attach
            
        Returns:
            Ingestion result with status and chunk count
        """
        # Add admin-specific metadata
        admin_metadata = {**(metadata or {}), "data_type": "admin"}
        
        # Use parent's ingest logic but target admin store
        if isinstance(document, dict):
            content = str(document.get("text") or document.get("content") or "").strip()
            if not content:
                return {"status": "skipped", "chunks_added": 0, "target": "admin"}
            
            doc_metadata = {**admin_metadata, **{k: v for k, v in document.items() if k not in {"text", "content"}}}
            docs = [self._Document(page_content=content, metadata=doc_metadata)]
            doc_id = str(doc_metadata.get("chunk_id") or "")
            ids = [doc_id] if doc_id else None
            
            self.admin_vector_store.add_documents(docs, ids=ids)
            return {"status": "success", "chunks_added": 1, "target": "admin"}
        
        # Handle file path
        file_path = str(document)
        text = self._extract_text_from_file(file_path)
        chunks = self.chunk(text)
        
        documents = []
        ids: List[str] = []
        for idx, chunk_text in enumerate(chunks):
            doc_metadata = {**admin_metadata, "source": admin_metadata.get("source", file_path)}
            documents.append(self._Document(page_content=chunk_text, metadata=doc_metadata))
            doc_id = str(admin_metadata.get("doc_id") or "")
            ids.append(f"{doc_id}:{idx}" if doc_id else f"{file_path}:{idx}")
        
        self.admin_vector_store.add_documents(documents, ids=ids)
        return {"status": "success", "chunks_added": len(documents), "target": "admin"}
    
    def retrieve_dual(
        self,
        query: str,
        top_k: int = 6,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Retrieve from both main and admin databases.
        
        Args:
            query: Search query
            top_k: Number of results per database
            filter_metadata: Optional metadata filter
            
        Returns:
            Dict with keys "main" and "admin", each containing retrieved docs
        """
        # Retrieve from main database
        main_results = self.vector_store.similarity_search_with_relevance_scores(
            query,
            k=top_k,
            filter=filter_metadata,
        )
        
        # Retrieve from admin database
        admin_results = self.admin_vector_store.similarity_search_with_relevance_scores(
            query,
            k=top_k,
            filter=filter_metadata,
        )
        
        # Format results
        main_docs = [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": score,
                "source_db": "main",
            }
            for doc, score in main_results
        ]
        
        admin_docs = [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": score,
                "source_db": "admin",
            }
            for doc, score in admin_results
        ]
        
        return {
            "main": main_docs,
            "admin": admin_docs,
        }
    
    def retrieve_admin_only(
        self,
        query: str,
        top_k: int = 6,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve only from admin database.
        
        Args:
            query: Search query
            top_k: Number of results
            filter_metadata: Optional metadata filter
            
        Returns:
            List of retrieved documents from admin database
        """
        results = self.admin_vector_store.similarity_search_with_relevance_scores(
            query,
            k=top_k,
            filter=filter_metadata,
        )
        
        retrieved_docs = []
        for doc, score in results:
            retrieved_docs.append(
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": score,
                    "source_db": "admin",
                }
            )
        return retrieved_docs
