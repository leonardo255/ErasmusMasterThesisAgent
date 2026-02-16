from datetime import datetime, UTC
import os
import json
import re
import unicodedata
from tqdm import tqdm
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# --- Paths ---
PDF_DIR = "data/papers_raw"
OUTPUT_DIR = "data/papers"

# --- Chunking setup ---
CHUNK_SIZE = 1600
CHUNK_OVERLAP = 200

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", ".", " "]
)

# --- Helper functions ---
def normalize_text(s: str) -> str:
    """Normalize whitespace and Unicode; remove line breaks."""
    if not isinstance(s, str):
        return s
    # Normalize Unicode
    s = unicodedata.normalize('NFC', s)
    # Replace all whitespace (spaces, tabs, newlines) with a single space
    s = re.sub(r'\s+', ' ', s)
    return s.strip()


def chunk_pdf(pdf_path: str):
    """Load a PDF, split into text chunks, and save as JSON."""
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()
    joined_text = "\n".join(d.page_content for d in docs)
    
    # Split into chunks
    chunks = text_splitter.split_text(joined_text)

    # Prepare data structure
    normalized_chunks   = [normalize_text(chunk) for chunk in chunks]
    doc_id              = os.path.basename(pdf_path)
    timestamp           = datetime.now().isoformat()
    n_chunks            = len(normalized_chunks)

    metadata = {
        "source": {
            "doc_id": doc_id,
            "timestamp": timestamp,
            "n_chunks": n_chunks
        }
    }

    data = {
        "metadata": metadata,
        "chunks": [
            {
                "chunk_id": i,
                "text": chunk.strip(),
            }
            for i, chunk in enumerate(normalized_chunks)
        ]
    }
    
    # Write JSON file
    out_path = os.path.join(OUTPUT_DIR, f"{doc_id}.json")
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    tqdm.write(f"Processed {doc_id} ({len(chunks)} chunks)")
    return data


if __name__ == "__main__":
    pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith(".pdf")]
    for file in tqdm(pdf_files):
        pdf_path = os.path.join(PDF_DIR, file)
        chunk_pdf(pdf_path)
    
    print(f"\nProcessed {len(pdf_files)} PDFs.")