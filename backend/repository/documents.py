from models.documents import HRDocument
from sqlalchemy.orm import Session
from core.config import Base, engine

Base.metadata.create_all(bind=engine)

class DocumentRepository:
    def __init__(self):
        pass

    def save_document(self, title: str, version: str, section: str, effective_date, access_level: str, file_path: str, db: Session):
        new_doc = HRDocument(
            title=title,
            version=version,
            section=section,
            effective_date=effective_date,
            access_level=access_level,
            file_path=file_path
        )
        db.add(new_doc)
        db.commit()
        db.refresh(new_doc)
        return new_doc.document_id

    def get_all(self, db: Session):
        return db.query(HRDocument).order_by(HRDocument.document_id.asc()).all()

    def get_by_id(self, document_id: int, db: Session):
        return db.query(HRDocument).filter(HRDocument.document_id == document_id).first()

    def delete_by_id(self, document_id: int, db: Session):
        doc = self.get_by_id(document_id, db)
        if doc:
            db.delete(doc)
            db.commit()
            return True
        return False

    def clear_all(self, db: Session):
        db.query(HRDocument).delete()
        db.commit()
        return True

