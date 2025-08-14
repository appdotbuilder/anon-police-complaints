from nicegui import ui, events, app
from datetime import datetime
from typing import List
import logging

from app.complaint_service import ComplaintService
from app.models import ComplaintCreate, ComplaintCategory, ComplaintUrgency

logger = logging.getLogger(__name__)


def create():
    """Create complaint submission module"""

    @ui.page("/")
    def index_page():
        """Main landing page with mobile-responsive design"""
        # Apply modern mobile-friendly theme
        ui.colors(
            primary="#1e40af",  # Professional blue
            secondary="#64748b",  # Subtle gray
            accent="#10b981",  # Success green
            positive="#10b981",
            negative="#ef4444",  # Error red
            warning="#f59e0b",  # Warning amber
        )

        # Add mobile-specific CSS
        ui.add_head_html("""
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <style>
        body { margin: 0; padding: 0; background-color: #f8fafc; }
        .mobile-container { min-height: 100vh; }
        .glass-card { 
            background: rgba(255, 255, 255, 0.95); 
            backdrop-filter: blur(10px); 
            border: 1px solid rgba(255, 255, 255, 0.3);
        }
        .gradient-header {
            background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
        }
        @media (max-width: 640px) {
            .q-card { margin: 0.5rem; }
            .q-btn { min-width: auto; }
        }
        </style>
        """)

        # Mobile-first responsive container
        with ui.column().classes("w-full max-w-md mx-auto p-4 gap-6"):
            # Header
            with ui.card().classes("p-6 bg-gradient-to-r from-blue-600 to-blue-700 text-white"):
                ui.label("Police Complaint Portal").classes("text-2xl font-bold text-center")
                ui.label("Submit Anonymous Complaints").classes("text-center text-blue-100 mt-2")

            # Introduction card
            with ui.card().classes("p-4 bg-blue-50 border-l-4 border-blue-500"):
                ui.label("Your Voice Matters").classes("text-lg font-semibold text-blue-900 mb-2")
                ui.label(
                    "This platform allows you to submit complaints about police conduct "
                    "anonymously and securely. Your identity will be protected."
                ).classes("text-blue-800 text-sm leading-relaxed")

            # Action buttons
            with ui.column().classes("gap-3 w-full"):
                ui.button("Submit New Complaint", on_click=lambda: ui.navigate.to("/submit")).classes(
                    "w-full bg-blue-600 hover:bg-blue-700 text-white py-4 px-6 rounded-lg "
                    "text-lg font-medium shadow-lg transition-colors"
                )

                ui.button("Track Existing Complaint", on_click=lambda: ui.navigate.to("/track")).classes(
                    "w-full bg-gray-600 hover:bg-gray-700 text-white py-4 px-6 rounded-lg "
                    "text-lg font-medium shadow-lg transition-colors"
                )

            # Footer information
            with ui.card().classes("p-4 bg-gray-50"):
                ui.label("Anonymous & Secure").classes("font-semibold text-gray-800 mb-2")
                ui.label(
                    "• No registration required\n"
                    "• Your IP address is not stored permanently\n"
                    "• Track your complaint with a unique ID\n"
                    "• All data is encrypted and secure"
                ).classes("text-sm text-gray-600 whitespace-pre-line leading-relaxed")

    @ui.page("/submit")
    def submit_complaint_page():
        """Complaint submission form"""
        service = ComplaintService()

        # Mobile-responsive container
        with ui.column().classes("w-full max-w-2xl mx-auto p-4"):
            # Header with back button
            with ui.row().classes("w-full items-center mb-4"):
                ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to("/")).classes("text-gray-600").props(
                    "flat round"
                )
                ui.label("Submit Complaint").classes("text-xl font-bold text-gray-800 ml-2")

            # Form container
            with ui.card().classes("w-full p-6"):
                # Form fields
                title_input = ui.input(label="Complaint Title", placeholder="Brief description of the issue").classes(
                    "w-full mb-4"
                )
                title_input.props('counter maxlength="200"')

                # Category selection
                category_select = ui.select(
                    label="Category",
                    options={
                        ComplaintCategory.EXCESSIVE_FORCE.value: "Excessive Force",
                        ComplaintCategory.MISCONDUCT.value: "Professional Misconduct",
                        ComplaintCategory.DISCRIMINATION.value: "Discrimination",
                        ComplaintCategory.CORRUPTION.value: "Corruption",
                        ComplaintCategory.HARASSMENT.value: "Harassment",
                        ComplaintCategory.ABUSE_OF_POWER.value: "Abuse of Power",
                        ComplaintCategory.OTHER.value: "Other",
                    },
                    value=ComplaintCategory.OTHER.value,
                ).classes("w-full mb-4")

                # Urgency selection
                urgency_select = ui.select(
                    label="Urgency Level",
                    options={
                        ComplaintUrgency.LOW.value: "Low - General concern",
                        ComplaintUrgency.MEDIUM.value: "Medium - Significant issue",
                        ComplaintUrgency.HIGH.value: "High - Serious misconduct",
                        ComplaintUrgency.CRITICAL.value: "Critical - Emergency response needed",
                    },
                    value=ComplaintUrgency.MEDIUM.value,
                ).classes("w-full mb-4")

                # Description
                description_input = ui.textarea(
                    label="Detailed Description", placeholder="Please provide a detailed description of the incident..."
                ).classes("w-full mb-4")
                description_input.props('rows="5" counter maxlength="5000"')

                # Optional incident details
                ui.label("Incident Details (Optional)").classes("text-sm font-medium text-gray-700 mt-6 mb-2")

                with ui.row().classes("w-full gap-4"):
                    incident_date = ui.date("Incident Date").classes("flex-1")
                    incident_time = ui.time("Incident Time").classes("flex-1")

                location_input = ui.input(
                    label="Location of Incident", placeholder="Address, intersection, or general area"
                ).classes("w-full mb-4")

                with ui.row().classes("w-full gap-4"):
                    officer_name = ui.input(label="Officer Name (if known)", placeholder="Officer's name").classes(
                        "flex-1"
                    )
                    badge_number = ui.input(label="Badge Number (if visible)", placeholder="Badge #").classes("flex-1")

                # Optional contact information
                ui.label("Contact Information (Optional)").classes("text-sm font-medium text-gray-700 mt-6 mb-2")
                ui.label("Providing contact information allows follow-up but is completely optional").classes(
                    "text-xs text-gray-500 mb-3"
                )

                with ui.row().classes("w-full gap-4"):
                    contact_email = ui.input(label="Email Address", placeholder="your@email.com").classes("flex-1")
                    contact_phone = ui.input(label="Phone Number", placeholder="(555) 123-4567").classes("flex-1")

                # File upload section
                ui.label("Media Attachments (Optional)").classes("text-sm font-medium text-gray-700 mt-6 mb-2")
                ui.label("Upload photos, videos, audio recordings, or documents (max 50MB per file)").classes(
                    "text-xs text-gray-500 mb-3"
                )

                uploaded_files: List[dict] = []

                @ui.refreshable
                def show_uploaded_files():
                    if uploaded_files:
                        ui.label(f"{len(uploaded_files)} file(s) ready for upload").classes(
                            "text-sm text-green-600 font-medium mb-2"
                        )
                        for file_info in uploaded_files:
                            with ui.row().classes("items-center gap-2 mb-1"):
                                ui.icon("attachment").classes("text-gray-500")
                                ui.label(f"{file_info['name']} ({file_info['size_mb']:.1f} MB)").classes(
                                    "text-sm text-gray-700"
                                )

                def handle_upload(e: events.UploadEventArguments):
                    if not e.content:
                        ui.notify("Empty file uploaded", type="negative")
                        return

                    # Handle both bytes and file-like objects
                    try:
                        if hasattr(e.content, "read"):
                            content_bytes = e.content.read()
                            e.content.seek(0)  # Reset for later use
                        else:
                            content_bytes = e.content

                        if not isinstance(content_bytes, bytes):
                            ui.notify("Invalid file content", type="negative")
                            return

                        file_size_mb = len(content_bytes) / (1024 * 1024)
                    except Exception as ex:
                        logger.error(f"Error processing uploaded file: {str(ex)}")
                        ui.notify("Error processing file", type="negative")
                        return
                    if file_size_mb > 50:
                        ui.notify(f"File too large: {file_size_mb:.1f}MB (max 50MB)", type="negative")
                        return

                    uploaded_files.append(
                        {
                            "name": e.name,
                            "content": content_bytes,  # Use the processed bytes
                            "type": e.type,
                            "size_mb": file_size_mb,
                        }
                    )

                    ui.notify(f'File "{e.name}" ready for upload', type="positive")
                    show_uploaded_files.refresh()

                ui.upload(on_upload=handle_upload, multiple=True, max_file_size=50_000_000).classes(
                    "w-full mb-4"
                ).props('accept="image/*,video/*,audio/*,.pdf,.txt"')

                show_uploaded_files()

                # Submit button
                async def submit_complaint():
                    # Validate required fields
                    if not title_input.value or len(title_input.value.strip()) < 5:
                        ui.notify("Please provide a complaint title (at least 5 characters)", type="negative")
                        return

                    if not description_input.value or len(description_input.value.strip()) < 10:
                        ui.notify("Please provide a detailed description (at least 10 characters)", type="negative")
                        return

                    try:
                        # Prepare complaint data
                        incident_datetime = None
                        if incident_date.value:
                            # Parse date and add time if provided
                            incident_dt = datetime.fromisoformat(incident_date.value)
                            if incident_time.value:
                                time_parts = incident_time.value.split(":")
                                incident_dt = incident_dt.replace(hour=int(time_parts[0]), minute=int(time_parts[1]))
                            incident_datetime = incident_dt

                        complaint_data = ComplaintCreate(
                            title=title_input.value.strip(),
                            description=description_input.value.strip(),
                            category=ComplaintCategory(category_select.value),
                            urgency=ComplaintUrgency(urgency_select.value),
                            incident_date=incident_datetime,
                            incident_location=location_input.value.strip() if location_input.value else None,
                            officer_name=officer_name.value.strip() if officer_name.value else None,
                            officer_badge_number=badge_number.value.strip() if badge_number.value else None,
                            contact_email=contact_email.value.strip() if contact_email.value else None,
                            contact_phone=contact_phone.value.strip() if contact_phone.value else None,
                        )

                        # Get client IP (basic tracking) - simplified for now
                        client_ip = None

                        # Create complaint
                        complaint, tracking_id = service.create_complaint(complaint_data, client_ip)

                        if not complaint or not complaint.id:
                            ui.notify("Failed to create complaint", type="negative")
                            return

                        # Upload files if any
                        for file_info in uploaded_files:
                            try:
                                service.add_media_attachment(
                                    complaint.id, file_info["name"], file_info["content"], file_info["type"]
                                )
                            except Exception as e:
                                logger.error(f"Failed to upload file {file_info['name']}: {str(e)}")
                                ui.notify(f"Warning: Failed to upload {file_info['name']}", type="warning")

                        # Store tracking ID for display
                        app.storage.tab["submitted_tracking_id"] = tracking_id

                        # Navigate to success page
                        ui.navigate.to("/success")

                    except Exception as e:
                        logger.error(f"Error submitting complaint: {str(e)}")
                        ui.notify(
                            "An error occurred while submitting your complaint. Please try again.", type="negative"
                        )

                # Submit button
                ui.button("Submit Complaint", on_click=submit_complaint).classes(
                    "w-full bg-blue-600 hover:bg-blue-700 text-white py-3 px-6 rounded-lg "
                    "text-lg font-medium shadow-lg transition-colors mt-6"
                )

                # Disclaimer
                with ui.card().classes("p-4 bg-yellow-50 border-l-4 border-yellow-400 mt-6"):
                    ui.label("Important Notice").classes("font-semibold text-yellow-800 mb-2")
                    ui.label(
                        "This system is for non-emergency complaints only. If you are experiencing "
                        "an emergency, please call 911 immediately."
                    ).classes("text-sm text-yellow-700")

    @ui.page("/success")
    async def success_page():
        """Complaint submission success page"""
        # Wait for connection to access tab storage
        await ui.context.client.connected()
        tracking_id = app.storage.tab.get("submitted_tracking_id")

        with ui.column().classes("w-full max-w-md mx-auto p-4"):
            # Success header
            with ui.card().classes("p-6 bg-green-50 border-l-4 border-green-500 text-center"):
                ui.icon("check_circle").classes("text-green-500 text-4xl mb-2")
                ui.label("Complaint Submitted Successfully").classes("text-xl font-bold text-green-800")

                if tracking_id:
                    ui.label("Your Tracking ID:").classes("text-sm text-green-700 mt-4 mb-2")
                    ui.label(tracking_id).classes(
                        "text-2xl font-mono font-bold text-green-800 bg-green-100 px-4 py-2 rounded"
                    )
                    ui.label("Please save this tracking ID to check the status of your complaint").classes(
                        "text-sm text-green-600 mt-2"
                    )

            # Next steps
            with ui.card().classes("p-4 bg-blue-50"):
                ui.label("What Happens Next?").classes("font-semibold text-blue-900 mb-3")
                ui.label(
                    "1. Your complaint has been received and will be reviewed\n"
                    "2. You can track the status using your tracking ID\n"
                    "3. If you provided contact information, you may be contacted for additional details\n"
                    "4. The review process typically takes 5-10 business days"
                ).classes("text-sm text-blue-800 whitespace-pre-line leading-relaxed")

            # Action buttons
            with ui.column().classes("gap-3 w-full mt-6"):
                ui.button("Track This Complaint", on_click=lambda: ui.navigate.to("/track")).classes(
                    "w-full bg-blue-600 hover:bg-blue-700 text-white py-3 px-6 rounded-lg"
                )

                ui.button("Submit Another Complaint", on_click=lambda: ui.navigate.to("/submit")).classes(
                    "w-full bg-gray-600 hover:bg-gray-700 text-white py-3 px-6 rounded-lg"
                )

                ui.button("Return to Home", on_click=lambda: ui.navigate.to("/")).classes(
                    "w-full bg-gray-400 hover:bg-gray-500 text-white py-3 px-6 rounded-lg"
                )
