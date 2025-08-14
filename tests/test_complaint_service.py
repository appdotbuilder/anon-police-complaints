import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import shutil

from app.database import reset_db
from app.complaint_service import ComplaintService
from app.models import ComplaintCreate, ComplaintCategory, ComplaintUrgency, ComplaintStatus


@pytest.fixture()
def new_db():
    reset_db()
    yield
    reset_db()


@pytest.fixture()
def service():
    # Create a temporary upload directory for testing
    temp_dir = Path(tempfile.mkdtemp())

    service = ComplaintService()
    original_upload_dir = service.UPLOAD_DIR
    service.UPLOAD_DIR = temp_dir

    yield service

    # Cleanup
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    service.UPLOAD_DIR = original_upload_dir


def test_generate_tracking_id(service: ComplaintService):
    """Test tracking ID generation"""
    tracking_id = service._generate_tracking_id()

    assert tracking_id.startswith("PC-")
    assert len(tracking_id) == 11  # 'PC-' + 8 hex characters
    assert tracking_id[3:].isupper()
    assert all(c in "0123456789ABCDEF" for c in tracking_id[3:])


def test_calculate_file_hash(service: ComplaintService):
    """Test file hash calculation"""
    test_content = b"test file content"
    hash_value = service._calculate_file_hash(test_content)

    assert len(hash_value) == 64  # SHA-256 produces 64-character hex string
    assert all(c in "0123456789abcdef" for c in hash_value)

    # Same content should produce same hash
    assert service._calculate_file_hash(test_content) == hash_value


def test_determine_media_type(service: ComplaintService):
    """Test media type determination from MIME types"""
    from app.models import MediaType

    assert service._determine_media_type("image/jpeg") == MediaType.IMAGE
    assert service._determine_media_type("image/png") == MediaType.IMAGE
    assert service._determine_media_type("video/mp4") == MediaType.VIDEO
    assert service._determine_media_type("video/webm") == MediaType.VIDEO
    assert service._determine_media_type("audio/mpeg") == MediaType.AUDIO
    assert service._determine_media_type("audio/wav") == MediaType.AUDIO
    assert service._determine_media_type("application/pdf") == MediaType.DOCUMENT
    assert service._determine_media_type("text/plain") == MediaType.DOCUMENT


def test_is_valid_file(service: ComplaintService):
    """Test file validation"""
    # Valid files
    assert service._is_valid_file(b"valid content", "image/jpeg")
    assert service._is_valid_file(b"pdf content", "application/pdf")

    # Empty file
    assert not service._is_valid_file(b"", "image/jpeg")

    # File too large
    large_content = b"x" * (51 * 1024 * 1024)  # 51MB
    assert not service._is_valid_file(large_content, "image/jpeg")

    # Invalid MIME type
    assert not service._is_valid_file(b"content", "application/octet-stream")


def test_create_complaint_basic(new_db, service: ComplaintService):
    """Test basic complaint creation"""
    complaint_data = ComplaintCreate(
        title="Test complaint",
        description="This is a test complaint description",
        category=ComplaintCategory.MISCONDUCT,
        urgency=ComplaintUrgency.HIGH,
    )

    complaint, tracking_id = service.create_complaint(complaint_data, "127.0.0.1")

    assert complaint is not None
    assert complaint.id is not None
    assert complaint.title == "Test complaint"
    assert complaint.description == "This is a test complaint description"
    assert complaint.category == ComplaintCategory.MISCONDUCT
    assert complaint.urgency == ComplaintUrgency.HIGH
    assert complaint.status == ComplaintStatus.PENDING
    assert complaint.tracking_id == tracking_id
    assert complaint.submitted_ip == "127.0.0.1"
    assert complaint.created_at is not None
    assert complaint.updated_at is not None


def test_create_complaint_with_optional_fields(new_db, service: ComplaintService):
    """Test complaint creation with optional fields"""
    incident_date = datetime(2024, 1, 15, 14, 30)

    complaint_data = ComplaintCreate(
        title="Traffic stop complaint",
        description="Officer was unprofessional during traffic stop",
        category=ComplaintCategory.HARASSMENT,
        urgency=ComplaintUrgency.MEDIUM,
        incident_date=incident_date,
        incident_location="Main St and 5th Ave",
        officer_name="Officer Smith",
        officer_badge_number="1234",
        contact_email="witness@example.com",
        contact_phone="555-0123",
    )

    complaint, tracking_id = service.create_complaint(complaint_data)

    assert complaint.incident_date == incident_date
    assert complaint.incident_location == "Main St and 5th Ave"
    assert complaint.officer_name == "Officer Smith"
    assert complaint.officer_badge_number == "1234"
    assert complaint.contact_email == "witness@example.com"
    assert complaint.contact_phone == "555-0123"


def test_create_complaint_unique_tracking_id(new_db, service: ComplaintService):
    """Test that tracking IDs are unique"""
    complaint_data = ComplaintCreate(title="Test complaint", description="This is a test complaint description")

    complaint1, tracking_id1 = service.create_complaint(complaint_data)
    complaint2, tracking_id2 = service.create_complaint(complaint_data)

    assert tracking_id1 != tracking_id2
    assert complaint1.tracking_id != complaint2.tracking_id


def test_get_complaint_by_tracking_id(new_db, service: ComplaintService):
    """Test retrieving complaint by tracking ID"""
    complaint_data = ComplaintCreate(title="Findable complaint", description="This complaint should be findable")

    complaint, tracking_id = service.create_complaint(complaint_data)

    # Find the complaint
    found_complaint = service.get_complaint_by_tracking_id(tracking_id)

    assert found_complaint is not None
    assert found_complaint.tracking_id == tracking_id
    assert found_complaint.title == "Findable complaint"
    assert found_complaint.category == ComplaintCategory.OTHER  # Default
    assert found_complaint.status == ComplaintStatus.PENDING


def test_get_complaint_by_tracking_id_not_found(new_db, service: ComplaintService):
    """Test retrieving non-existent complaint"""
    found_complaint = service.get_complaint_by_tracking_id("PC-NOTFOUND")
    assert found_complaint is None


def test_add_media_attachment(new_db, service: ComplaintService):
    """Test adding media attachment to complaint"""
    # Create a complaint first
    complaint_data = ComplaintCreate(
        title="Complaint with media", description="This complaint will have media attached"
    )

    complaint, tracking_id = service.create_complaint(complaint_data)

    # Ensure complaint was created successfully
    assert complaint.id is not None

    # Add media attachment
    test_content = b"fake image content"
    attachment = service.add_media_attachment(complaint.id, "test_image.jpg", test_content, "image/jpeg")

    assert attachment is not None
    assert attachment.id is not None
    assert attachment.original_filename == "test_image.jpg"
    assert attachment.file_size == len(test_content)
    assert attachment.mime_type == "image/jpeg"
    assert attachment.media_type.value == "image"
    assert attachment.complaint_id == complaint.id
    assert attachment.is_processed

    # Verify file was saved
    file_path = Path(attachment.file_path)
    assert file_path.exists()
    assert file_path.read_bytes() == test_content


def test_add_media_attachment_invalid_file(new_db, service: ComplaintService):
    """Test adding invalid media attachment"""
    complaint_data = ComplaintCreate(title="Test complaint", description="Test description")

    complaint, _ = service.create_complaint(complaint_data)

    # Ensure complaint was created successfully
    assert complaint.id is not None

    # Try to add invalid file (unsupported MIME type)
    attachment = service.add_media_attachment(
        complaint.id, "test.exe", b"executable content", "application/x-executable"
    )

    assert attachment is None


def test_add_media_attachment_nonexistent_complaint(new_db, service: ComplaintService):
    """Test adding media attachment to non-existent complaint"""
    attachment = service.add_media_attachment(
        99999,  # Non-existent complaint ID
        "test.jpg",
        b"image content",
        "image/jpeg",
    )

    assert attachment is None


def test_get_all_complaints(new_db, service: ComplaintService):
    """Test retrieving all complaints"""
    # Create multiple complaints
    for i in range(3):
        complaint_data = ComplaintCreate(
            title=f"Complaint {i + 1}",
            description=f"Description for complaint {i + 1}",
            category=ComplaintCategory.MISCONDUCT,
        )
        service.create_complaint(complaint_data)

    complaints = service.get_all_complaints()

    assert len(complaints) == 3
    assert all(complaint.title.startswith("Complaint") for complaint in complaints)
    # Should be ordered by created_at desc
    assert complaints[0].title == "Complaint 3"
    assert complaints[2].title == "Complaint 1"


def test_get_all_complaints_limit(new_db, service: ComplaintService):
    """Test retrieving complaints with limit"""
    # Create 5 complaints
    for i in range(5):
        complaint_data = ComplaintCreate(title=f"Complaint {i + 1}", description=f"Description {i + 1}")
        service.create_complaint(complaint_data)

    complaints = service.get_all_complaints(limit=3)

    assert len(complaints) == 3


def test_get_complaint_statistics(new_db, service: ComplaintService):
    """Test getting complaint statistics"""
    # Create complaints with different categories and statuses
    complaints_data = [
        ComplaintCreate(title="Misconduct 1", description="Description", category=ComplaintCategory.MISCONDUCT),
        ComplaintCreate(title="Misconduct 2", description="Description", category=ComplaintCategory.MISCONDUCT),
        ComplaintCreate(title="Harassment", description="Description", category=ComplaintCategory.HARASSMENT),
    ]

    for complaint_data in complaints_data:
        service.create_complaint(complaint_data)

    stats = service.get_complaint_statistics()

    assert stats["total_complaints"] == 3
    assert stats["pending_complaints"] == 3  # All start as pending
    assert stats["resolved_complaints"] == 0
    assert stats["categories"]["misconduct"] == 2
    assert stats["categories"]["harassment"] == 1
    assert stats["categories"]["other"] == 0


def test_search_complaints_by_category(new_db, service: ComplaintService):
    """Test searching complaints by category"""
    # Create complaints with different categories
    misconduct_data = ComplaintCreate(
        title="Misconduct complaint", description="Description", category=ComplaintCategory.MISCONDUCT
    )
    harassment_data = ComplaintCreate(
        title="Harassment complaint", description="Description", category=ComplaintCategory.HARASSMENT
    )

    service.create_complaint(misconduct_data)
    service.create_complaint(harassment_data)

    # Search for misconduct complaints
    misconduct_complaints = service.search_complaints(category=ComplaintCategory.MISCONDUCT)
    assert len(misconduct_complaints) == 1
    assert misconduct_complaints[0].title == "Misconduct complaint"

    # Search for harassment complaints
    harassment_complaints = service.search_complaints(category=ComplaintCategory.HARASSMENT)
    assert len(harassment_complaints) == 1
    assert harassment_complaints[0].title == "Harassment complaint"


def test_search_complaints_by_tracking_id(new_db, service: ComplaintService):
    """Test searching complaints by tracking ID partial match"""
    complaint_data = ComplaintCreate(title="Searchable complaint", description="This complaint should be searchable")

    complaint, tracking_id = service.create_complaint(complaint_data)

    # Search with partial tracking ID
    partial_id = tracking_id[:6]  # First 6 characters
    results = service.search_complaints(tracking_id=partial_id)

    assert len(results) == 1
    assert results[0].tracking_id == tracking_id


def test_search_complaints_no_results(new_db, service: ComplaintService):
    """Test search with no matching results"""
    results = service.search_complaints(category=ComplaintCategory.CORRUPTION)
    assert len(results) == 0


def test_invalid_complaint_id_attachment(new_db, service: ComplaintService):
    """Test adding attachment to invalid complaint ID"""
    # Try to add attachment to non-existent complaint
    attachment = service.add_media_attachment(
        99999,  # Invalid ID
        "test.jpg",
        b"test content",
        "image/jpeg",
    )

    assert attachment is None


def test_edge_case_empty_strings(new_db, service: ComplaintService):
    """Test handling of empty string inputs"""
    # Test with minimal valid input
    complaint_data = ComplaintCreate(
        title="Short",  # 5 characters (minimum)
        description="A bit longer",  # 10+ characters
    )

    complaint, tracking_id = service.create_complaint(complaint_data)

    assert complaint is not None
    assert complaint.title == "Short"
    assert complaint.description == "A bit longer"
