from flask import current_app
from ..extensions import db
from ..models import Alert


def notify(emergency, name, phone, msg):
    """Emergency routing hook. Logs + records the alert; swap the log line for Twilio / MSG91 / Exotel."""
    db.session.add(Alert(emergency_id=emergency.id, to_name=name, to_phone=phone, channel="SMS"))
    current_app.logger.warning("SMS -> %s (%s): %s", name, phone, msg)
