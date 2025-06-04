from flask import Blueprint, request, jsonify
import logging
from services.project_service import ProjectService
from shared.debugger_client import log_to_debugger


project_bp = Blueprint('project', __name__)
logger = logging.getLogger(__name__)

# Initialize services
project_service = ProjectService()


@project_bp.route('/sync', methods=['POST'])
def sync_projects():
    """Sync projects from Oggo to HubSpot"""
    try:
        params = request.json or {}
        logger.info("Received project sync request")
        result = project_service.sync_projects(params)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in project sync: {str(e)}")
        return jsonify({"error": f"Error in project sync: {str(e)}"}), 500

@project_bp.route('/projects', methods=['POST'])
def create_project():
    """Create a new project"""
    try:
        project_data = request.json
        # Your existing logic here...
        return jsonify({"status": "success", "project": project_data}), 201
    except Exception as e:
        logger.error(f"Error creating project: {str(e)}")
        return jsonify({"error": str(e)}), 500