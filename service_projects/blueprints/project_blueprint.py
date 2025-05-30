from flask import Blueprint, request, jsonify
import logging
from services.project_service import ProjectService

project_bp = Blueprint('project', __name__)
logger = logging.getLogger(__name__)

# Initialize services
project_service = ProjectService()

@project_bp.route('/health', methods=['GET'])
def health_check():
    return {"status": "ok", "service": "project"}

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

# Keep existing project CRUD endpoints
@project_bp.route('/projects', methods=['GET'])
def get_projects():
    """Get all projects with optional filtering"""
    try:
        status = request.args.get('status')
        contact_id = request.args.get('contact_id')
        
        # Your existing logic here...
        return jsonify({"projects": []})  # Replace with actual implementation
    except Exception as e:
        logger.error(f"Error retrieving projects: {str(e)}")
        return jsonify({"error": str(e)}), 500

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