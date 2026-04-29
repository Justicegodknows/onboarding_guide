# rag_service.py
# Ingest → Chunk → Embed → Retrieve → Generate


import datetime
from app.db import SessionLocal
from app.models.knowledge_base import KnowledgeChunk

class RAGService:
    def ingest(self, document):
        """
        Ingest a document chunk into the knowledge base, avoiding duplicates.
        document: dict with keys 'source', 'chunk_id', 'text', and optionally 'category_id', 'topic', 'tags'.
        """
        session = SessionLocal()
        chunk_uid = f"{document['source']}-{document['chunk_id']}"
        try:
            # Check for duplicate chunk_id
            exists = session.query(KnowledgeChunk).filter_by(chunk_id=chunk_uid).first()
            if exists:
                print(f"Chunk {chunk_uid} already exists. Skipping.")
                return False

            chunk = KnowledgeChunk(
                chunk_id=chunk_uid,
                title=document.get('source', ''),
                content=document.get('text', ''),
                created_at=datetime.datetime.utcnow(),
                updated_at=datetime.datetime.utcnow(),
                category_id=document.get('category_id'),
                topic=document.get('topic'),
                tags=document.get('tags')
            )
            session.add(chunk)
            session.commit()
            print(f"Ingested chunk {chunk_uid}")
            return True
        except Exception as e:
            session.rollback()
            print(f"Error ingesting chunk {chunk_uid}: {e}")
            return False
        finally:
            session.close()

    def chunk(self, document):
        # Placeholder for chunking logic
        pass

    def embed(self, chunks):
        # Placeholder for embedding logic
        pass

    def retrieve(self, query):
        # Placeholder for retrieval logic
        pass

    def generate(self, context, question):
        """
        Generate an answer using Hugging Face LLM (transformers pipeline).
        context: str or list of str (retrieved context)
        question: str (user question)
        """
        from transformers import pipeline
        # You can change the model to any supported text-generation model
        generator = pipeline("text-generation", model="gpt2")
        prompt = f"Context: {context}\nQuestion: {question}\nAnswer:"
        result = generator(prompt, max_length=256, num_return_sequences=1)
        return result[0]["generated_text"][len(prompt):].strip()
