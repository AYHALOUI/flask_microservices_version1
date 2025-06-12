from flask import Flask, jsonify, request
import json
import os
import logging
import requests

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)

@app.route('/api/entity-types', methods=['GET'])
def get_entity_types():
    """Return available entity types for mapping"""
    try:
        entity_types = [
            {"value": "contact", "label": "Contacts"},
            {"value": "project", "label": "Projects"},
        ]
        return jsonify({"entity_types": entity_types})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def get_service_mapping_directory(entity_type):
    """Get the correct service directory path for an entity type"""
    service_directories = {
        "contact": "/service_contacts/mappings",    
        "project": "/service_projects/mappings",
        "contract": "/service_contracts/mappings"
    }
    return service_directories.get(entity_type)

# API endpoint to get existing mappings
@app.route('/mappings/<entity_type>', methods=['GET'])
def get_mapping(entity_type):
    """Get existing mapping for an entity type"""
    try:
        # Get the appropriate service directory
        service_mapping_dir = get_service_mapping_directory(entity_type)
        if not service_mapping_dir:
            return jsonify({"error": f"Unknown entity type: {entity_type}"}), 400        
        mapping_file = f"{service_mapping_dir}/{entity_type}_mapping.json"
        if os.path.exists(mapping_file):
            with open(mapping_file, 'r') as f:
                mapping_data = json.load(f)
            return jsonify({"rules": mapping_data})
        else:
            return jsonify({"error": f"No mapping found for {entity_type} at {mapping_file}"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API endpoint to save mappings
@app.route('/mappings/<entity_type>', methods=['POST'])
def save_mapping(entity_type):
    """Save mapping for an entity type"""    
    try:
        mapping_data = request.json        
        if not mapping_data:
            return jsonify({"error": "No mapping data provided"}), 400
        
        service_mapping_dir = get_service_mapping_directory(entity_type)
        if not service_mapping_dir:
            return jsonify({"error": f"Unknown entity type: {entity_type}"}), 400
        
        # Create absolute path
        abs_service_dir = os.path.abspath(service_mapping_dir)        
        os.makedirs(abs_service_dir, exist_ok=True)        
        mapping_file = f"{abs_service_dir}/{entity_type}_mapping.json"
        
        # Write the file
        with open(mapping_file, 'w') as f:
            json.dump(mapping_data, f, indent=2)

        return jsonify({"status": "success", })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API endpoint to serve the HTML interface
@app.route('/', methods=['GET'])
def mapping_interface():
    """Serve the mapping interface"""
    try:
        with open('index.html', 'r') as f:
            return f.read()
    except FileNotFoundError:
        return "index.html not found", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)