import hashlib
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from sqlmodel import select

from app.database import get_session
from app.models import (
    Complaint,
    ComplaintCreate,
    ComplaintPublic,
    MediaAttachment,
    MediaType,
    ComplaintCategory,
    ComplaintStatus,
)


class ComplaintService:
    """Service layer for handling complaint operations"""

    UPLOAD_DIR = Path("uploads")
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    ALLOWED_MIME_TYPES = {
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
        "video/mp4",
        "video/webm",
        "video/quicktime",
        "audio/mpeg",
        "audio/wav",
        "audio/ogg",
        "application/pdf",
        "text/plain",
    }

    def __init__(self):
        self.UPLOAD_DIR.mkdir(exist_ok=True)

    def _generate_tracking_id(self) -> str:
        """Generate a unique tracking ID for anonymous complaint tracking"""
        return f"PC-{uuid.uuid4().hex[:8].upper()}"

    def _calculate_file_hash(self, content: bytes) -> str:
        """Calculate SHA-256 hash of file content"""
        return hashlib.sha256(content).hexdigest()

    def _determine_media_type(self, mime_type: str) -> MediaType:
        """Determine media type from MIME type"""
        if mime_type.startswith("image/"):
            return MediaType.IMAGE
        elif mime_type.startswith("video/"):
            return MediaType.VIDEO
        elif mime_type.startswith("audio/"):
            return MediaType.AUDIO
        else:
            return MediaType.DOCUMENT

    def _save_file(self, content: bytes, filename: str, complaint_id: int) -> Path:
        """Save uploaded file to disk"""
        # Create complaint-specific directory
        complaint_dir = self.UPLOAD_DIR / str(complaint_id)
        complaint_dir.mkdir(exist_ok=True)

        # Generate safe filename
        safe_filename = f"{uuid.uuid4().hex}_{filename}"
        file_path = complaint_dir / safe_filename

        with open(file_path, "wb") as f:
            f.write(content)

        return file_path

    def create_complaint(
        self, complaint_data: ComplaintCreate, client_ip: Optional[str] = None
    ) -> tuple[Complaint, str]:
        """Create a new anonymous complaint"""
        with get_session() as session:
            # Generate unique tracking ID
            tracking_id = self._generate_tracking_id()

            # Ensure tracking ID is unique
            while session.exec(select(Complaint).where(Complaint.tracking_id == tracking_id)).first():
                tracking_id = self._generate_tracking_id()

            # Create complaint
            complaint = Complaint(
                tracking_id=tracking_id,
                title=complaint_data.title,
                description=complaint_data.description,
                category=complaint_data.category,
                urgency=complaint_data.urgency,
                incident_date=complaint_data.incident_date,
                incident_location=complaint_data.incident_location,
                officer_badge_number=complaint_data.officer_badge_number,
                officer_name=complaint_data.officer_name,
                contact_email=complaint_data.contact_email,
                contact_phone=complaint_data.contact_phone,
                submitted_ip=client_ip,
                status=ComplaintStatus.PENDING,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            session.add(complaint)
            session.commit()
            session.refresh(complaint)

            return complaint, tracking_id

    def add_media_attachment(
        self, complaint_id: int, filename: str, content: bytes, mime_type: str
    ) -> Optional[MediaAttachment]:
        """Add media attachment to complaint"""
        if not self._is_valid_file(content, mime_type):
            return None

        with get_session() as session:
            complaint = session.get(Complaint, complaint_id)
            if not complaint:
                return None

            try:
                # Save file to disk
                file_path = self._save_file(content, filename, complaint_id)
                file_hash = self._calculate_file_hash(content)
                media_type = self._determine_media_type(mime_type)

                # Create media attachment record
                attachment = MediaAttachment(
                    filename=file_path.name,
                    original_filename=filename,
                    file_path=str(file_path),
                    file_size=len(content),
                    mime_type=mime_type,
                    media_type=media_type,
                    file_hash=file_hash,
                    complaint_id=complaint_id,
                    uploaded_at=datetime.utcnow(),
                    is_processed=True,
                )

                session.add(attachment)
                session.commit()
                session.refresh(attachment)
                return attachment

            except Exception as e:
                # Clean up file if database operation fails
                file_path = locals().get("file_path")
                if file_path and file_path.exists():
                    try:
                        file_path.unlink()
                    except Exception:
                        pass  # File cleanup failed, but we still want to raise the original exception
                raise e

    def _is_valid_file(self, content: bytes, mime_type: str) -> bool:
        """Validate file content and type"""
        if len(content) == 0 or len(content) > self.MAX_FILE_SIZE:
            return False

        if mime_type not in self.ALLOWED_MIME_TYPES:
            return False

        return True

    def get_complaint_by_tracking_id(self, tracking_id: str) -> Optional[ComplaintPublic]:
        """Get complaint status by tracking ID (public view)"""
        with get_session() as session:
            complaint = session.exec(select(Complaint).where(Complaint.tracking_id == tracking_id)).first()

            if not complaint:
                return None

            return ComplaintPublic(
                tracking_id=complaint.tracking_id,
                title=complaint.title,
                category=complaint.category,
                status=complaint.status,
                created_at=complaint.created_at,
                updated_at=complaint.updated_at,
            )

    def get_all_complaints(self, limit: int = 100) -> List[ComplaintPublic]:
        """Get all complaints (admin view) - limited for performance"""
        with get_session() as session:
            from sqlmodel import desc

            complaints = session.exec(select(Complaint).order_by(desc(Complaint.created_at)).limit(limit)).all()

            return [
                ComplaintPublic(
                    tracking_id=complaint.tracking_id,
                    title=complaint.title,
                    category=complaint.category,
                    status=complaint.status,
                    created_at=complaint.created_at,
                    updated_at=complaint.updated_at,
                )
                for complaint in complaints
            ]

    def get_complaint_statistics(self) -> dict:
        """Get basic complaint statistics"""
        with get_session() as session:
            total_complaints = len(session.exec(select(Complaint)).all())
            pending_complaints = len(
                session.exec(select(Complaint).where(Complaint.status == ComplaintStatus.PENDING)).all()
            )
            resolved_complaints = len(
                session.exec(select(Complaint).where(Complaint.status == ComplaintStatus.RESOLVED)).all()
            )

            # Category breakdown
            categories = {}
            for category in ComplaintCategory:
                count = len(session.exec(select(Complaint).where(Complaint.category == category)).all())
                categories[category.value] = count

            return {
                "total_complaints": total_complaints,
                "pending_complaints": pending_complaints,
                "resolved_complaints": resolved_complaints,
                "categories": categories,
            }

    def search_complaints(
        self,
        category: Optional[ComplaintCategory] = None,
        status: Optional[ComplaintStatus] = None,
        tracking_id: Optional[str] = None,
    ) -> List[ComplaintPublic]:
        """Search complaints with filters"""
        with get_session() as session:
            query = select(Complaint)

            if category:
                query = query.where(Complaint.category == category)
            if status:
                query = query.where(Complaint.status == status)
            if tracking_id:
                from sqlmodel import func

                query = query.where(func.upper(Complaint.tracking_id).like(f"%{tracking_id.upper()}%"))

            from sqlmodel import desc

            complaints = session.exec(query.order_by(desc(Complaint.created_at)).limit(50)).all()

            return [
                ComplaintPublic(
                    tracking_id=complaint.tracking_id,
                    title=complaint.title,
                    category=complaint.category,
                    status=complaint.status,
                    created_at=complaint.created_at,
                    updated_at=complaint.updated_at,
                )
                for complaint in complaints
            ]
