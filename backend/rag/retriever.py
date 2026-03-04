"""RAG retriever for agent context."""
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.rag.vector_store import get_vector_store, add_documents, query_documents
from backend.rag.document_loader import load_document, chunk_text


class DocumentRetriever:
    """Retrieve relevant document context for agents."""

    def __init__(self, collection_name: str = "property_docs"):
        self.collection, self.embeddings = get_vector_store(collection_name)

    def add_file(self, file_path: str | Path, doc_id: str = None):
        """Load and index a document."""
        path = Path(file_path)
        doc_id = doc_id or path.stem
        text = load_document(path)
        chunks = chunk_text(text)
        add_documents(self.collection, self.embeddings, chunks, doc_id)

    def add_uploaded_file(self, uploaded_file, doc_id: str = None):
        """Add Streamlit uploaded file."""
        path = Path(uploaded_file.name)
        suffix = path.suffix.lower()
        doc_id = doc_id or path.stem

        if suffix == ".pdf":
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(uploaded_file.getvalue()))
            chunks = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    chunks.extend(chunk_text(text))
        elif suffix in (".docx", ".doc"):
            from docx import Document
            doc = Document(io.BytesIO(uploaded_file.getvalue()))
            text = "\n".join(p.text for p in doc.paragraphs)
            chunks = chunk_text(text)
        elif suffix == ".txt":
            text = uploaded_file.getvalue().decode("utf-8", errors="ignore")
            chunks = chunk_text(text)
        else:
            raise ValueError(f"Unsupported: {suffix}")

        if chunks:
            add_documents(self.collection, self.embeddings, chunks, doc_id)

    def retrieve(self, query: str, n: int = 5) -> str:
        """Retrieve relevant context as formatted string."""
        chunks = query_documents(self.collection, self.embeddings, query, n_results=n)
        if not chunks:
            return ""
        return "\n\n---\n\n".join(chunks)
