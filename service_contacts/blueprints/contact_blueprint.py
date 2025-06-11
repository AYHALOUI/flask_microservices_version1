from flask import Blueprint, request, jsonify
import logging
from services.contact_service import ContactService

contact_bp = Blueprint('contact', __name__)
logger = logging.getLogger(__name__)


# Initialize services
contact_service = ContactService()


@contact_bp.route('/sync', methods=['POST'])
def sync_contacts():
    try:
        params = request.json or {}
        result = contact_service.sync_contacts(params)
        return jsonify(result)
    except Exception as e:
        return ({"error": f"Error in sync: {str(e)}, 500"})