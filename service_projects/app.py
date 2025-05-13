import os
import time
import logging
from flask import Flask, request, jsonify
from tinydb import TinyDB, Query
from shared.debugger_client import log_to_debugger, record_exchange

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

data_dir = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(data_dir, exist_ok=True)
projects_db = TinyDB(os.path.join(data_dir, 'projects.json'))

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "service": "project"})

@app.route('/projects', methods=['GET'])
def get_projects():
    """Get all projects with optional filtering"""
    try:
        status = request.args.get('status')
        contact_id = request.args.get('contact_id')
        
        # Build query
        Project = Query()
        query_parts = []
        
        if status:
            query_parts.append(Project.status == status)
        if contact_id:
            query_parts.append(Project.contact_id == contact_id)
        
        # Execute query
        if query_parts:
            from functools import reduce
            query = reduce(lambda a, b: a & b, query_parts)
            projects = projects_db.search(query)
        else:
            projects = projects_db.all()
        
        return jsonify({"projects": projects})
    
    except Exception as e:
        logger.error(f"Error retrieving projects: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/projects/<project_id>', methods=['GET'])
def get_project(project_id):
    """Get a specific project by ID"""
    try:
        Project = Query()
        projects = projects_db.search(Project.id == project_id)
        
        if not projects:
            return jsonify({"error": "Project not found"}), 404
        
        return jsonify({"project": projects[0]})
    
    except Exception as e:
        logger.error(f"Error retrieving project {project_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/projects', methods=['POST'])
def create_project():
    """Create a new project"""
    try:
        project_data = request.json
        
        if not project_data:
            return jsonify({"error": "No project data provided"}), 400
        
        # Generate ID if not provided
        if 'id' not in project_data:
            project_data['id'] = f"proj_{int(time.time())}"
        
        # Add timestamps
        project_data['created_at'] = time.time()
        project_data['updated_at'] = time.time()
        
        # Add default status if not provided
        if 'status' not in project_data:
            project_data['status'] = 'new'
        
        # Insert into database
        projects_db.insert(project_data)    
        return jsonify({
            "status": "success",
            "message": "Project created successfully",
            "project": project_data
        }), 201
    
    except Exception as e:
        logger.error(f"Error creating project: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/projects/<project_id>', methods=['PUT'])
def update_project(project_id):
    """Update an existing project"""
    try:
        project_data = request.json
        
        if not project_data:
            return jsonify({"error": "No project data provided"}), 400        
        Project = Query()
        if not projects_db.search(Project.id == project_id):
            return jsonify({"error": "Project not found"}), 404
        
        project_data['updated_at'] = time.time()
        projects_db.update(project_data, Project.id == project_id)
        
        return jsonify({
            "status": "success",
            "message": "Project updated successfully",
            "project": project_data
        })
    
    except Exception as e:
        logger.error(f"Error updating project {project_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/projects/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    """Delete a project"""
    try:
        # Find the project
        Project = Query()
        if not projects_db.search(Project.id == project_id):
            return jsonify({"error": "Project not found"}), 404
        
        # Delete from database
        projects_db.remove(Project.id == project_id)   
        return jsonify({
            "status": "success",
            "message": "Project deleted successfully"
        })
    
    except Exception as e:
        logger.error(f"Error deleting project {project_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500



def store_transaction(type_name, status, details):
    """Store a transaction record in the storage service"""
    try:
        payload = {
            "service": "project",
            "type": type_name,
            "status": status,
            "details": details,
            "timestamp": time.time()
        }
        
        import requests
        requests.post("http://service_storage:5000/store/transaction", json=payload)
    except Exception as e:
        logger.error(f"Failed to store transaction: {str(e)}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)