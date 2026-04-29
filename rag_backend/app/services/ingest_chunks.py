import os
import json
from app.services.rag_service import RAGService

HELP_DIR = os.path.join(os.path.dirname(__file__), '../../../help')
CHUNKS_PATH = os.path.join(HELP_DIR, 'chunks.json')



def ingest_chunks():
    rag = RAGService()
    with open(CHUNKS_PATH, 'r') as f:
        chunks = json.load(f)
    success = 0
    errors = 0
    for chunk in chunks:
        result = rag.ingest(chunk)
        if result:
            success += 1
        else:
            errors += 1
    print(f"Successfully ingested {success} chunks. {errors} errors or duplicates.")

if __name__ == "__main__":
    ingest_chunks()
