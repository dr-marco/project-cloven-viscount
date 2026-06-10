import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from database import Base

class Document(Base):
    __tablename__ = "documents"

    # Primary Key: The critical bridge between SQL and ChromaDB.
    # We use this UUID as a metadata filter in our vector store.
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    
    # The original name of the uploaded file
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # File size in bytes (useful for storage monitoring)
    file_size: Mapped[int] = mapped_column(Integer, nullable=True)

    # Ingestion status tracking (e.g., 'PENDING', 'COMPLETED', 'FAILED')
    # This allows the UI to eventually query SQL instead of relying solely on Celery task status
    status: Mapped[str] = mapped_column(String(50), default="PENDING")

    # Timestamp of when the document was registered in the system
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, filename='{self.filename}', status='{self.status}')>"