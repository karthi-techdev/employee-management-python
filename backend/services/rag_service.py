import os
from dotenv import load_dotenv
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader
import docx
from sqlalchemy.orm import Session

from repository.documents import DocumentRepository

load_dotenv()

INDEX_NAME = "hr-policies"
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

pc = Pinecone(api_key=PINECONE_API_KEY)
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
document_repository = DocumentRepository()

class RagService:
    def __init__(self):
        pass

    def get_pinecone_index(self):
        return pc.Index(INDEX_NAME)

    def extract_text_from_file(self, file_path: str):
        ext = os.path.splitext(file_path)[1].lower()

        # Case 1: PDF File
        if ext == ".pdf":
            reader = PdfReader(file_path)
            extracted_pages = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    extracted_pages.append(text.strip())
            return "\n\n".join(extracted_pages)

        # Case 2: DOCX File
        elif ext == ".docx":
            doc = docx.Document(file_path)
            extracted_paragraphs = []
            for p in doc.paragraphs:
                if p.text.strip():
                    extracted_paragraphs.append(p.text.strip())
            return "\n\n".join(extracted_paragraphs)

        else:
            raise ValueError("Unsupported file format. Only .pdf and .docx files are allowed.")

    def split_text_into_chunks(self, text: str, chunk_size: int = 500):
        lines = text.split("\n")
        chunks = []
        current_chunk = ""

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if len(current_chunk) + len(line) < chunk_size:
                if len(current_chunk) > 0:
                    current_chunk = current_chunk + " " + line
                else:
                    current_chunk = line
            else:
                if len(current_chunk) > 0:
                    chunks.append(current_chunk)
                current_chunk = line

        if len(current_chunk) > 0:
            chunks.append(current_chunk)

        return chunks

    def process_and_embed_document_file(self, file_path: str, title: str, version: str, effective_date, access_level: str, db: Session):
        # 1. Extract text
        full_text = self.extract_text_from_file(file_path)
        if not full_text.strip():
            raise ValueError("Could not extract any readable text from the file.")

        # 2. Save document record in PostgreSQL using ORM
        doc_id = document_repository.save_document(
            title=title,
            version=version,
            section="Full Policy Document",
            effective_date=effective_date,
            access_level=access_level,
            file_path=file_path,
            db=db
        )

        # 3. Split text into chunks
        chunks = self.split_text_into_chunks(full_text, chunk_size=500)

        # 4. Generate HuggingFace embeddings
        vectors_to_upsert = []
        chunk_index = 1

        for chunk in chunks:
            chunk_embedding = embedding_model.encode(chunk).tolist()
            vector_id = f"doc_{doc_id}_chunk_{chunk_index}"
            section_label = f"Section {chunk_index}"

            metadata = {
                "document_id": doc_id,
                "title": title,
                "section": section_label,
                "version": version,
                "effective_date": str(effective_date) if effective_date else "",
                "text": chunk
            }

            vectors_to_upsert.append({
                "id": vector_id,
                "values": chunk_embedding,
                "metadata": metadata
            })

            chunk_index += 1

        # 5. Upsert to Pinecone
        index = self.get_pinecone_index()
        index.upsert(vectors=vectors_to_upsert)

        return {
            "status": "success",
            "document_id": doc_id,
            "title": title,
            "chunks_count": len(chunks),
            "message": f"Document '{title}' ({len(chunks)} chunks) embedded and saved in Pinecone successfully."
        }

    def delete_single_policy(self, document_id: int, db: Session):
        doc = document_repository.get_by_id(document_id, db)
        if not doc:
            return False

        # Delete from Pinecone
        index = self.get_pinecone_index()
        chunk_ids = [f"doc_{document_id}_chunk_{i}" for i in range(1, 200)]
        chunk_ids.append(f"doc_{document_id}")

        try:
            index.delete(ids=chunk_ids)
        except Exception as e:
            print("Pinecone delete notice:", e)

        # Delete from database
        document_repository.delete_by_id(document_id, db)
        return True

    def clear_all_policies(self, db: Session):
        index = self.get_pinecone_index()
        try:
            index.delete(delete_all=True)
        except Exception as e:
            print("Pinecone clear notice:", e)

        document_repository.clear_all(db)
        return True

    def search_hr_policies(self, query: str, top_k: int = 3):
        index = self.get_pinecone_index()
        query_vector = embedding_model.encode(query).tolist()

        response = index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True
        )

        results = []
        for match in response.matches:
            meta = match.metadata or {}
            citation = f"{meta.get('title', 'HR Policy')} ({meta.get('section', 'General')}, v{meta.get('version', '1.0')})"
            results.append({
                "score": round(match.score, 4),
                "document_id": meta.get("document_id"),
                "title": meta.get("title"),
                "section": meta.get("section"),
                "version": meta.get("version"),
                "effective_date": meta.get("effective_date"),
                "text": meta.get("text", ""),
                "citation": citation
            })

        return results

rag_service = RagService()

# Export helper functions for backward compatibility
extract_text_from_file = rag_service.extract_text_from_file
split_text_into_chunks = rag_service.split_text_into_chunks
search_hr_policies = rag_service.search_hr_policies
