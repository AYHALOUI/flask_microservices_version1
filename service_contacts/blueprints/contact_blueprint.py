from flask import Blueprint, request, jsonify
import logging
from services.contact_service import ContactService


contact_bp = Blueprint('contact', __name__)
logger = logging.getLogger(__name__)


logger.info("=== IMPORTING CONTACT SERVICE ===")

# Initialize services
contact_service = ContactService()

logger.info("=== CONTACT SERVICE INITIALIZED ===")



@contact_bp.route('/health', methods= ['GET'])
def health_check():
    # log_to_debugger("contact", "info", "Health check endpoint called");
    return {"status": "ok", "service": "contact"}

@contact_bp.route('/sync', methods=['POST'])
def sync_contacts():
    """Sync contacts from Oggo to HubSpot"""
    # log_to_debugger("contact", "info", "Received sync request")
    try:
        params = request.json or {}
        # log_to_debugger("contact", "info", "Received sync request", params)
        result = contact_service.sync_contacts(params)
        return jsonify(result)
    except Exception as e:
        # log_to_debugger("contact", "error", f"Error in sync: {str(e)}")
        return ({"error": f"Error in sync: {str(e)}, 500"})