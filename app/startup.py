from app.database import create_tables
import app.complaint_form
import app.complaint_tracking


def startup() -> None:
    # this function is called before the first request
    create_tables()

    # Register all modules
    app.complaint_form.create()
    app.complaint_tracking.create()
