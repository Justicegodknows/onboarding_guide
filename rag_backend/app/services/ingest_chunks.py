import os
import json
from app.services.rag_service import RAGService

HELP_DIR = os.path.join(os.path.dirname(__file__), '../../../help')
CHUNKS_PATH = os.path.join(HELP_DIR, 'chunks.json')


def ingest_chunks():
    rag = RAGService()
    with open(CHUNKS_PATH, 'r') as f:
        chunks = json.load(f)
    for chunk in chunks:
        rag.ingest(chunk)
    print(f"Ingested {len(chunks)} chunks.")

if __name__ == "__main__":
    ingest_chunks()
