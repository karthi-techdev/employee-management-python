from sqlalchemy import Integer, Column, String, Date, DateTime, Text
from datetime import datetime
from core.config import Base

class HRDocument(Base):
    __tablename__ = "hr_documents"

    document_id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    version = Column(String)
    section = Column(String)
    effective_date = Column(Date, nullable=True)
    access_level = Column(String)
    file_path = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

