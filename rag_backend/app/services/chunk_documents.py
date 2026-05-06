import os
from docx import Document
from typing import List

HELP_DIR = os.path.join(os.path.dirname(__file__), '../../../help')
CHUNK_SIZE = 500  # characters


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE) -> List[str]:
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]


def extract_docx_text(docx_path: str) -> str:
    doc = Document(docx_path)
    return '\n'.join([p.text for p in doc.paragraphs if p.text.strip()])


def chunk_all_help_docs() -> List[dict]:
    chunks = []
    for fname in os.listdir(HELP_DIR):
        if fname.endswith('.docx'):
            path = os.path.join(HELP_DIR, fname)
            text = extract_docx_text(path)
            for idx, chunk in enumerate(chunk_text(text)):
                chunks.append({
                    'source': fname,
                    'chunk_id': idx,
                    'text': chunk
                })
    return chunks

if __name__ == "__main__":
    import json
    all_chunks = chunk_all_help_docs()
    with open(os.path.join(HELP_DIR, "chunks.json"), "w") as f:
        json.dump(all_chunks, f, indent=2)
    print(f"Chunked {len(all_chunks)} chunks from help docs.")
