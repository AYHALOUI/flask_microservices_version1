from flask import Flask, jsonify, request
import json
import os
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)

# API endpoint to get available entity types
@app.route('/api/entity-types', methods=['GET'])
def get_entity_types():
    """Return available entity types for mapping"""
    try:
        entity_types = [
            {"value": "contact", "label": "Contacts"},
            {"value": "project", "label": "Projects"},
            {"value": "contract", "label": "Contracts"}
        ]
        return jsonify({"entity_types": entity_types})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API endpoint to get source fields (from Oggo)
@app.route('/api/source-fields/<entity_type>', methods=['GET'])
def get_source_fields(entity_type):
    """Return available source fields for the given entity type"""
    try:
        # Define source fields based on entity type
        source_fields = {
            "contact": [
                {"value": "id", "label": "Contact ID"},
                {"value": "first_name", "label": "First Name"},
                {"value": "last_name", "label": "Last Name"},
                {"value": "email", "label": "Email Address"},
                {"value": "phone", "label": "Phone Number"},
                {"value": "company", "label": "Company Name"},
                {"value": "created_at", "label": "Created Date"},
                {"value": "updated_at", "label": "Updated Date"}
            ],
            "project": [
                {"value": "id", "label": "Project ID"},
                {"value": "name", "label": "Project Name"},
                {"value": "description", "label": "Description"},
                {"value": "status", "label": "Status"},
                {"value": "start_date", "label": "Start Date"},
                {"value": "end_date", "label": "End Date"},
                {"value": "budget", "label": "Budget"}
            ],
            "contract": [
                {"value": "id", "label": "Contract ID"},
                {"value": "title", "label": "Contract Title"},
                {"value": "value", "label": "Contract Value"},
                {"value": "status", "label": "Status"},
                {"value": "start_date", "label": "Start Date"},
                {"value": "end_date", "label": "End Date"}
            ]
        }
        
        fields = source_fields.get(entity_type, [])
        return jsonify({"fields": fields})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API endpoint to get target fields (HubSpot)
@app.route('/api/target-fields/<entity_type>', methods=['GET'])
def get_target_fields(entity_type):
    """Return available target fields for the given entity type"""
    try:
        # Define target fields based on entity type
        target_fields = {
            "contact": [
                {"value": "hubspot_id", "label": "HubSpot Contact ID"},
                {"value": "properties.firstname", "label": "First Name"},
                {"value": "properties.lastname", "label": "Last Name"},
                {"value": "properties.email", "label": "Email"},
                {"value": "properties.phone", "label": "Phone"},
                {"value": "properties.company", "label": "Company"},
                {"value": "properties.created_date", "label": "Created Date"},
                {"value": "properties.last_modified_date", "label": "Last Modified Date"},
                {"value": "properties.jobtitle", "label": "Job Title"},
                {"value": "properties.website", "label": "Website"}
            ],
            "project": [
                {"value": "hubspot_id", "label": "HubSpot Project ID"},
                {"value": "properties.name", "label": "Project Name"},
                {"value": "properties.description", "label": "Description"},
                {"value": "properties.hs_pipeline_stage", "label": "Pipeline Stage"},
                {"value": "properties.start_date", "label": "Start Date"},
                {"value": "properties.end_date", "label": "End Date"},
                {"value": "properties.budget", "label": "Budget"}
            ],
            "contract": [
                {"value": "hubspot_id", "label": "HubSpot Contract ID"},
                {"value": "properties.contract_name", "label": "Contract Name"},
                {"value": "properties.contract_value", "label": "Contract Value"},
                {"value": "properties.status", "label": "Status"},
                {"value": "properties.start_date", "label": "Start Date"},
                {"value": "properties.end_date", "label": "End Date"}
            ]
        }
        
        fields = target_fields.get(entity_type, [])
        return jsonify({"fields": fields})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def get_service_mapping_directory(entity_type):
    """Get the correct service directory path for an entity type"""
    service_directories = {
        "contact": "../service_contacts/mappings",
        "project": "../service_projects/mappings",
        "contract": "../service_contracts/mappings"
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
        
        # Look for mapping file in the service directory
        mapping_file = f"{service_mapping_dir}/{entity_type}_mapping.json"
        
        print(f"Looking for mapping file at: {mapping_file}")  # Debug log
        print(f"File exists: {os.path.exists(mapping_file)}")  # Debug log
        
        if os.path.exists(mapping_file):
            with open(mapping_file, 'r') as f:
                mapping_data = json.load(f)
            return jsonify({"rules": mapping_data})
        else:
            return jsonify({"error": f"No mapping found for {entity_type} at {mapping_file}"}), 404
    except Exception as e:
        print(f"Error in get_mapping: {str(e)}")  # Debug log
        return jsonify({"error": str(e)}), 500

# API endpoint to save mappings
@app.route('/mappings/<entity_type>', methods=['POST'])
def save_mapping(entity_type):
    """Save mapping for an entity type"""
    app.logger.info(f"=== SAVE MAPPING CALLED FOR {entity_type} ===")
    
    try:
        mapping_data = request.json
        app.logger.info(f"Received mapping data: {mapping_data}")
        
        if not mapping_data:
            app.logger.error("No mapping data received!")
            return jsonify({"error": "No mapping data provided"}), 400
        
        # Get the appropriate service directory
        service_mapping_dir = get_service_mapping_directory(entity_type)
        app.logger.info(f"Service mapping directory: {service_mapping_dir}")
        
        if not service_mapping_dir:
            app.logger.error(f"Unknown entity type: {entity_type}")
            return jsonify({"error": f"Unknown entity type: {entity_type}"}), 400
        
        # Get current working directory
        current_dir = os.getcwd()
        app.logger.info(f"Current working directory: {current_dir}")
        
        # Create absolute path
        abs_service_dir = os.path.abspath(service_mapping_dir)
        app.logger.info(f"Absolute service directory: {abs_service_dir}")
        
        # Ensure the service mappings directory exists
        app.logger.info(f"Creating directory: {abs_service_dir}")
        os.makedirs(abs_service_dir, exist_ok=True)
        
        # Save mapping file with the correct naming pattern
        mapping_file = f"{abs_service_dir}/{entity_type}_mapping.json"
        app.logger.info(f"Full mapping file path: {mapping_file}")
        
        # Write the file
        with open(mapping_file, 'w') as f:
            json.dump(mapping_data, f, indent=2)
        
        # Verify the file was created
        file_exists = os.path.exists(mapping_file)
        app.logger.info(f"File created successfully: {file_exists}")
        
        if file_exists:
            # Get file size to confirm it has content
            file_size = os.path.getsize(mapping_file)
            app.logger.info(f"File size: {file_size} bytes")
        
        app.logger.info("=== SAVE MAPPING COMPLETED ===")
        
        return jsonify({
            "status": "success", 
            "message": f"Mapping saved for {entity_type}",
            "file_path": mapping_file,
            "file_exists": file_exists,
            "debug_info": {
                "current_dir": current_dir,
                "service_dir": service_mapping_dir,
                "absolute_path": mapping_file
            }
        })
    except Exception as e:
        app.logger.error(f"ERROR in save_mapping: {str(e)}")
        app.logger.error(f"Exception type: {type(e)}")
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
    print("Starting mapping service...")
    print("Current working directory:", os.getcwd())
    print("Available services:", ["contact", "project", "contract"])
    app.run(host='0.0.0.0', port=5000, debug=True)