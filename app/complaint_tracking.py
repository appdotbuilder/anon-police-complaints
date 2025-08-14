from nicegui import ui

from app.complaint_service import ComplaintService
from app.models import ComplaintStatus


def create():
    """Create complaint tracking module"""

    @ui.page("/track")
    def track_complaint_page():
        """Complaint tracking page"""
        service = ComplaintService()

        with ui.column().classes("w-full max-w-md mx-auto p-4"):
            # Header with back button
            with ui.row().classes("w-full items-center mb-4"):
                ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to("/")).classes("text-gray-600").props(
                    "flat round"
                )
                ui.label("Track Complaint").classes("text-xl font-bold text-gray-800 ml-2")

            # Tracking form
            with ui.card().classes("w-full p-6"):
                ui.label("Enter Your Tracking ID").classes("text-lg font-semibold text-gray-800 mb-4")
                ui.label("Enter the tracking ID you received when you submitted your complaint").classes(
                    "text-sm text-gray-600 mb-4"
                )

                tracking_input = ui.input(label="Tracking ID", placeholder="PC-XXXXXXXX").classes("w-full mb-4")
                tracking_input.props("upper-case")

                # Result container
                @ui.refreshable
                def show_complaint_status():
                    # This will be updated when search is performed
                    pass

                async def search_complaint():
                    if not tracking_input.value or len(tracking_input.value.strip()) < 3:
                        ui.notify("Please enter a valid tracking ID", type="negative")
                        return

                    complaint = service.get_complaint_by_tracking_id(tracking_input.value.strip().upper())

                    if not complaint:
                        # Show "not found" message within the refreshable
                        with show_complaint_status.element:
                            show_complaint_status.element.clear()
                            with ui.card().classes("p-4 bg-red-50 border-l-4 border-red-400 mt-4"):
                                ui.icon("error").classes("text-red-500 text-2xl mb-2")
                                ui.label("Complaint Not Found").classes("font-semibold text-red-800 mb-2")
                                ui.label(
                                    "No complaint found with this tracking ID. Please check the ID and try again."
                                ).classes("text-sm text-red-700")
                        return

                    # Show complaint details within the refreshable
                    with show_complaint_status.element:
                        show_complaint_status.element.clear()
                        with ui.card().classes("p-4 bg-blue-50 border-l-4 border-blue-400 mt-4"):
                            ui.label("Complaint Found").classes("font-semibold text-blue-800 mb-4")

                            # Status with color coding
                            status_color = {
                                ComplaintStatus.PENDING: "text-yellow-600 bg-yellow-100",
                                ComplaintStatus.UNDER_REVIEW: "text-blue-600 bg-blue-100",
                                ComplaintStatus.RESOLVED: "text-green-600 bg-green-100",
                                ComplaintStatus.DISMISSED: "text-red-600 bg-red-100",
                            }.get(complaint.status, "text-gray-600 bg-gray-100")

                            ui.label(f"Status: {complaint.status.value.replace('_', ' ').title()}").classes(
                                f"inline-block px-3 py-1 rounded-full text-sm font-medium {status_color} mb-3"
                            )

                            # Complaint details
                            with ui.column().classes("gap-2 text-sm"):
                                with ui.row().classes("justify-between"):
                                    ui.label("Title:").classes("font-medium text-gray-700")
                                    ui.label(complaint.title).classes("text-gray-900")

                                with ui.row().classes("justify-between"):
                                    ui.label("Category:").classes("font-medium text-gray-700")
                                    ui.label(complaint.category.value.replace("_", " ").title()).classes(
                                        "text-gray-900"
                                    )

                                with ui.row().classes("justify-between"):
                                    ui.label("Submitted:").classes("font-medium text-gray-700")
                                    ui.label(complaint.created_at.strftime("%B %d, %Y at %I:%M %p")).classes(
                                        "text-gray-900"
                                    )

                                with ui.row().classes("justify-between"):
                                    ui.label("Last Updated:").classes("font-medium text-gray-700")
                                    ui.label(complaint.updated_at.strftime("%B %d, %Y at %I:%M %p")).classes(
                                        "text-gray-900"
                                    )

                            # Status descriptions
                            status_descriptions = {
                                ComplaintStatus.PENDING: "Your complaint has been received and is waiting for initial review.",
                                ComplaintStatus.UNDER_REVIEW: "Your complaint is currently being investigated by the appropriate department.",
                                ComplaintStatus.RESOLVED: "Your complaint has been reviewed and resolved. Thank you for your submission.",
                                ComplaintStatus.DISMISSED: "Your complaint has been reviewed and closed without further action.",
                            }

                            if complaint.status in status_descriptions:
                                with ui.card().classes("p-3 bg-gray-50 mt-3"):
                                    ui.label(status_descriptions[complaint.status]).classes("text-sm text-gray-700")

                # Search button
                ui.button("Search Complaint", on_click=search_complaint).classes(
                    "w-full bg-blue-600 hover:bg-blue-700 text-white py-3 px-6 rounded-lg "
                    "text-lg font-medium shadow-lg transition-colors"
                )

                # Show results area
                show_complaint_status()

            # Information card
            with ui.card().classes("p-4 bg-yellow-50 border-l-4 border-yellow-400 mt-6"):
                ui.label("Can't Find Your Complaint?").classes("font-semibold text-yellow-800 mb-2")
                ui.label(
                    "• Make sure you entered the correct tracking ID\n"
                    "• Tracking IDs are case-insensitive\n"
                    "• If you lost your tracking ID, unfortunately we cannot retrieve it for privacy reasons"
                ).classes("text-sm text-yellow-700 whitespace-pre-line")

    @ui.page("/admin")
    def admin_dashboard():
        """Simple admin dashboard for viewing all complaints"""
        service = ComplaintService()

        with ui.column().classes("w-full max-w-6xl mx-auto p-4"):
            ui.label("Complaint Dashboard").classes("text-2xl font-bold text-gray-800 mb-6")

            # Statistics cards
            try:
                stats = service.get_complaint_statistics()

                with ui.row().classes("gap-4 w-full mb-6"):
                    # Total complaints
                    with ui.card().classes("p-4 bg-blue-50 border-l-4 border-blue-500"):
                        ui.label(str(stats["total_complaints"])).classes("text-2xl font-bold text-blue-800")
                        ui.label("Total Complaints").classes("text-sm text-blue-600")

                    # Pending
                    with ui.card().classes("p-4 bg-yellow-50 border-l-4 border-yellow-500"):
                        ui.label(str(stats["pending_complaints"])).classes("text-2xl font-bold text-yellow-800")
                        ui.label("Pending Review").classes("text-sm text-yellow-600")

                    # Resolved
                    with ui.card().classes("p-4 bg-green-50 border-l-4 border-green-500"):
                        ui.label(str(stats["resolved_complaints"])).classes("text-2xl font-bold text-green-800")
                        ui.label("Resolved").classes("text-sm text-green-600")

            except Exception as e:
                import logging

                logger = logging.getLogger(__name__)
                logger.error(f"Error loading statistics: {str(e)}")
                ui.label(f"Error loading statistics: {str(e)}").classes("text-red-600")

            # Recent complaints
            try:
                complaints = service.get_all_complaints(limit=20)

                if complaints:
                    ui.label("Recent Complaints").classes("text-lg font-semibold text-gray-800 mb-4")

                    # Create table data
                    columns = [
                        {"name": "tracking_id", "label": "Tracking ID", "field": "tracking_id", "align": "left"},
                        {"name": "title", "label": "Title", "field": "title", "align": "left"},
                        {"name": "category", "label": "Category", "field": "category", "align": "left"},
                        {"name": "status", "label": "Status", "field": "status", "align": "left"},
                        {"name": "created_at", "label": "Submitted", "field": "created_at", "align": "left"},
                    ]

                    rows = [
                        {
                            "tracking_id": complaint.tracking_id,
                            "title": complaint.title[:50] + ("..." if len(complaint.title) > 50 else ""),
                            "category": complaint.category.value.replace("_", " ").title(),
                            "status": complaint.status.value.replace("_", " ").title(),
                            "created_at": complaint.created_at.strftime("%m/%d/%Y %I:%M %p"),
                        }
                        for complaint in complaints
                    ]

                    ui.table(columns=columns, rows=rows).classes("w-full")

                else:
                    with ui.card().classes("p-6 bg-gray-50 text-center"):
                        ui.label("No complaints submitted yet").classes("text-gray-600")

            except Exception as e:
                import logging

                logger = logging.getLogger(__name__)
                logger.error(f"Error loading complaints: {str(e)}")
                ui.label(f"Error loading complaints: {str(e)}").classes("text-red-600")

            # Back to public interface
            ui.button("Back to Public Interface", on_click=lambda: ui.navigate.to("/")).classes(
                "bg-gray-600 hover:bg-gray-700 text-white py-2 px-4 rounded mt-6"
            )
