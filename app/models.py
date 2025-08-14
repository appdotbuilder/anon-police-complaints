from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


# Enums for complaint categorization
class ComplaintStatus(str, Enum):
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class ComplaintCategory(str, Enum):
    EXCESSIVE_FORCE = "excessive_force"
    MISCONDUCT = "misconduct"
    DISCRIMINATION = "discrimination"
    CORRUPTION = "corruption"
    HARASSMENT = "harassment"
    ABUSE_OF_POWER = "abuse_of_power"
    OTHER = "other"


class ComplaintUrgency(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MediaType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"


# Persistent models (stored in database)
class Complaint(SQLModel, table=True):
    __tablename__ = "complaints"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)

    # Anonymous identifier for tracking (generated UUID-like string)
    tracking_id: str = Field(unique=True, max_length=50, index=True)

    # Complaint details
    title: str = Field(max_length=200)
    description: str = Field(max_length=5000)
    category: ComplaintCategory = Field(default=ComplaintCategory.OTHER)
    urgency: ComplaintUrgency = Field(default=ComplaintUrgency.MEDIUM)

    # Location and incident details
    incident_date: Optional[datetime] = Field(default=None)
    incident_location: Optional[str] = Field(default=None, max_length=500)
    officer_badge_number: Optional[str] = Field(default=None, max_length=50)
    officer_name: Optional[str] = Field(default=None, max_length=200)

    # Contact information (optional for anonymous submissions)
    contact_email: Optional[str] = Field(default=None, max_length=255)
    contact_phone: Optional[str] = Field(default=None, max_length=20)

    # System fields
    status: ComplaintStatus = Field(default=ComplaintStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # IP address for basic tracking (anonymized after processing)
    submitted_ip: Optional[str] = Field(default=None, max_length=45)

    # Additional metadata
    additional_metadata: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))

    # Relationships
    media_attachments: List["MediaAttachment"] = Relationship(back_populates="complaint")


class MediaAttachment(SQLModel, table=True):
    __tablename__ = "media_attachments"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)

    # File information
    filename: str = Field(max_length=255)
    original_filename: str = Field(max_length=255)
    file_path: str = Field(max_length=500)
    file_size: int = Field(gt=0)  # Size in bytes
    mime_type: str = Field(max_length=100)
    media_type: MediaType

    # File hash for integrity checking
    file_hash: str = Field(max_length=128)

    # Metadata
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    is_processed: bool = Field(default=False)

    # Foreign key
    complaint_id: int = Field(foreign_key="complaints.id")

    # Relationship
    complaint: Complaint = Relationship(back_populates="media_attachments")


class ComplaintNote(SQLModel, table=True):
    """Internal notes for complaint processing (not visible to submitter)"""

    __tablename__ = "complaint_notes"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)

    # Note content
    note: str = Field(max_length=2000)
    created_by: str = Field(max_length=100)  # Admin/reviewer identifier
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Foreign key
    complaint_id: int = Field(foreign_key="complaints.id")


class ComplaintStatistic(SQLModel, table=True):
    """Aggregated statistics for reporting (no personal data)"""

    __tablename__ = "complaint_statistics"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)

    # Time period
    period_start: datetime
    period_end: datetime

    # Statistics
    total_complaints: int = Field(default=0)
    by_category: Dict[str, int] = Field(default={}, sa_column=Column(JSON))
    by_status: Dict[str, int] = Field(default={}, sa_column=Column(JSON))
    by_urgency: Dict[str, int] = Field(default={}, sa_column=Column(JSON))

    # Generated timestamp
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# Non-persistent schemas (for validation, forms, API requests/responses)
class ComplaintCreate(SQLModel, table=False):
    title: str = Field(max_length=200, min_length=5)
    description: str = Field(max_length=5000, min_length=10)
    category: ComplaintCategory = Field(default=ComplaintCategory.OTHER)
    urgency: ComplaintUrgency = Field(default=ComplaintUrgency.MEDIUM)

    # Optional incident details
    incident_date: Optional[datetime] = None
    incident_location: Optional[str] = Field(default=None, max_length=500)
    officer_badge_number: Optional[str] = Field(default=None, max_length=50)
    officer_name: Optional[str] = Field(default=None, max_length=200)

    # Optional contact (for follow-up)
    contact_email: Optional[str] = Field(default=None, max_length=255)
    contact_phone: Optional[str] = Field(default=None, max_length=20)


class ComplaintUpdate(SQLModel, table=False):
    status: Optional[ComplaintStatus] = None
    category: Optional[ComplaintCategory] = None
    urgency: Optional[ComplaintUrgency] = None


class ComplaintPublic(SQLModel, table=False):
    """Public view of complaint (for tracking by submitter)"""

    tracking_id: str
    title: str
    category: ComplaintCategory
    status: ComplaintStatus
    created_at: datetime
    updated_at: datetime

    def model_dump_with_dates(self) -> Dict[str, Any]:
        """Custom serialization with proper date formatting"""
        return {
            "tracking_id": self.tracking_id,
            "title": self.title,
            "category": self.category.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class MediaUpload(SQLModel, table=False):
    """Schema for media file uploads"""

    filename: str = Field(max_length=255)
    file_size: int = Field(gt=0, le=50 * 1024 * 1024)  # Max 50MB
    mime_type: str = Field(max_length=100)
    media_type: MediaType


class ComplaintSearch(SQLModel, table=False):
    """Search parameters for complaints"""

    category: Optional[ComplaintCategory] = None
    status: Optional[ComplaintStatus] = None
    urgency: Optional[ComplaintUrgency] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    location: Optional[str] = None
    tracking_id: Optional[str] = None


class ComplaintSummary(SQLModel, table=False):
    """Summary information for dashboard"""

    total_complaints: int
    pending_complaints: int
    resolved_complaints: int
    by_category: Dict[str, int]
    by_urgency: Dict[str, int]
    recent_complaints: int  # Last 30 days
