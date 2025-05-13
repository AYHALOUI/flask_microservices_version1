from flask import Flask, request, jsonify, send_file, make_response
from tinydb import TinyDB, Query
import requests
import os
import json
import logging
import io
import docker

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = app.logger

# Simple database for mappings
os.makedirs('data', exist_ok=True)
mappings_db = TinyDB('data/mappings.json')

@app.route('/mappings/<entity_type>', methods=['GET'])
def get_mapping(entity_type):
    """Get mapping for an entity type"""
    Mapping = Query()
    mapping = mappings_db.get(Mapping.entity_type == entity_type)
    
    if not mapping:
        return jsonify({"error": "Mapping not found"}), 404
        
    return jsonify(mapping)

@app.route('/mappings/<entity_type>', methods=['POST'])
def save_mapping(entity_type):
    """Save/update mapping for an entity type to a separate file"""
    rules = request.json
    
    # Create directory if it doesn't exist
    os.makedirs('mappings', exist_ok=True)
    
    # Write the rules to a file
    mapping_file = f"mappings/{entity_type}_mapping.json"
    with open(mapping_file, 'w') as f:
        json.dump(rules, f, indent=2)
    
    return jsonify({"status": "success", "file": mapping_file})

@app.route('/api/source-fields/<entity_type>', methods=['GET'])
def get_source_fields(entity_type):
    """Get source fields for a specific entity type"""
    try:
        # Define fields for each entity type
        if entity_type == 'contact':
            fields = [
                {"value": "id", "label": "ID"},
                {"value": "first_name", "label": "First Name"},
                {"value": "last_name", "label": "Last Name"},
                {"value": "email", "label": "Email Address"},
                {"value": "phone", "label": "Phone Number"},
                {"value": "company", "label": "Company Name"},
                {"value": "created_at", "label": "Created Date"},
                {"value": "updated_at", "label": "Updated Date"}
            ]
        elif entity_type == 'project':
            fields = [
                {"value": "id", "label": "ID"},
                {"value": "name", "label": "Project Name"},
                {"value": "description", "label": "Description"},
                {"value": "status", "label": "Status"},
                {"value": "start_date", "label": "Start Date"},
                {"value": "end_date", "label": "End Date"},
                {"value": "budget", "label": "Budget"},
                {"value": "contact_id", "label": "Contact ID"},
                {"value": "created_at", "label": "Created Date"},
                {"value": "updated_at", "label": "Updated Date"}
            ]
        elif entity_type == 'contract':
            fields = [
                {"value": "id", "label": "ID"},
                {"value": "title", "label": "Contract Title"},
                {"value": "description", "label": "Description"},
                {"value": "value", "label": "Contract Value"},
                {"value": "start_date", "label": "Start Date"},
                {"value": "end_date", "label": "End Date"},
                {"value": "status", "label": "Status"},
                {"value": "project_id", "label": "Project ID"},
                {"value": "contact_id", "label": "Contact ID"},
                {"value": "created_at", "label": "Created Date"},
                {"value": "updated_at", "label": "Updated Date"}
            ]
        else:
            return jsonify({"error": f"Unknown entity type: {entity_type}"}), 400
            
        return jsonify({"fields": fields})
        
    except Exception as e:
        logger.error(f"Error getting source fields: {str(e)}")
        return jsonify({"error": f"Error getting source fields: {str(e)}"}), 500
        
    except Exception as e:
        logger.error(f"Error in get_source_fields: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/target-fields/<entity_type>', methods=['GET'])
def get_target_fields(entity_type):
    """Get target fields for a specific entity type"""
    try:
        # Define target fields for each entity type
        if entity_type == 'contact':
            fields = [
                {"value": "hubspot_id", "label": "HubSpot ID"},
                {"value": "properties.firstname", "label": "First Name"},
                {"value": "properties.lastname", "label": "Last Name"},
                {"value": "properties.email", "label": "Email"},
                {"value": "properties.phone", "label": "Phone"},
                {"value": "properties.company", "label": "Company"},
                {"value": "properties.created_date", "label": "Created Date"},
                {"value": "properties.last_modified_date", "label": "Last Modified Date"},
                {"value": "properties.jobtitle", "label": "Job Title"},
                {"value": "properties.address", "label": "Address"},
                {"value": "properties.city", "label": "City"},
                {"value": "properties.state", "label": "State"},
                {"value": "properties.zip", "label": "Zip Code"},
                {"value": "properties.country", "label": "Country"},
                {"value": "properties.leadsource", "label": "Lead Source"},
                {"value": "properties.firstname1", "label": "First Name (Custom)"},
                {"value": "properties.lastname1", "label": "Last Name (Custom)"}
            ]
        elif entity_type == 'project':
            fields = [
                {"value": "hubspot_id", "label": "HubSpot ID"},
                {"value": "properties.name", "label": "Project Name"},
                {"value": "properties.description", "label": "Description"},
                {"value": "properties.hs_pipeline_stage", "label": "Status"},
                {"value": "properties.start_date", "label": "Start Date"},
                {"value": "properties.end_date", "label": "End Date"},
                {"value": "properties.amount", "label": "Budget"},
                {"value": "properties.contact_id", "label": "Contact ID"},
                {"value": "properties.createdate", "label": "Created Date"},
                {"value": "properties.hs_lastmodifieddate", "label": "Last Modified Date"}
            ]
        elif entity_type == 'contract':
            fields = [
                {"value": "hubspot_id", "label": "HubSpot ID"},
                {"value": "properties.contract_name", "label": "Contract Title"},
                {"value": "properties.description", "label": "Description"},
                {"value": "properties.contract_value", "label": "Contract Value"},
                {"value": "properties.start_date", "label": "Start Date"},
                {"value": "properties.end_date", "label": "End Date"},
                {"value": "properties.status", "label": "Status"},
                {"value": "properties.project_id", "label": "Project ID"},
                {"value": "properties.contact_id", "label": "Contact ID"},
                {"value": "properties.createdate", "label": "Created Date"},
                {"value": "properties.hs_lastmodifieddate", "label": "Last Modified Date"}
            ]
        else:
            return jsonify({"error": f"Unknown entity type: {entity_type}"}), 400
            
        return jsonify({"fields": fields})
        
    except Exception as e:
        logger.error(f"Error getting target fields: {str(e)}")
        return jsonify({"error": f"Error getting target fields: {str(e)}"}), 500


def transform_item(item, mapping_rules, entity_type):
    """Transform a single item using the mapping rules"""
    result = {}
    
    # Default hubspot_id for contacts
    if entity_type == 'contact':
        result['hubspot_id'] = None
    
    # Apply mapping rules
    for source_field, target_field in mapping_rules.items():
        if source_field in item:
            # Handle nested properties
            if '.' in target_field:
                parts = target_field.split('.')
                parent = parts[0]
                child = parts[1]
                
                if parent not in result:
                    result[parent] = {}
                result[parent][child] = item[source_field]
            else:
                # Direct field mapping
                result[target_field] = item[source_field]
    
    # Package according to entity type
    if entity_type == 'contact':
        return {"contacts": [result]}
    else:
        return {f"{entity_type}s": [result]}

@app.route('/')
def index():
    return open('index.html').read()

@app.route('/api/entity-types', methods=['GET'])
def get_entity_types():
    """Get available entity types from Docker services"""
    try:
        
        # Mapping of service names to entity types
        service_mapping = {
            'service_contacts': 'contact',
            'service_projects': 'project', 
            'service_contracts': 'contract',
            'contacts': 'contact',
            'projects': 'project',
            'contracts': 'contract'
        }
        
        # Labels for entity types
        labels = {
            'contact': 'Contacts',
            'project': 'Projects',
            'contract': 'Contracts'
        }
        
        # Try to discover services from Docker
        logger.info("Initializing Docker client")
        try:
            client = docker.from_env()
        except Exception as e:
            logger.error(f"Failed to connect to Docker: {str(e)}")
            return jsonify({"error": f"Failed to connect to Docker: {str(e)}"}), 500
        
        logger.info("Listing containers")
        try:
            containers = client.containers.list()
            logger.info(f"Found {len(containers)} containers")
        except Exception as e:
            logger.error(f"Failed to list containers: {str(e)}")
            return jsonify({"error": f"Failed to list containers: {str(e)}"}), 500
        
        found_types = set()
        
        for container in containers:
            container_name = container.name
            service_name = container.labels.get('com.docker.compose.service', '')
            logger.info(f"Container: {container_name}, Service: {service_name}")
            
            if service_name in service_mapping:
                entity_type = service_mapping[service_name]
                found_types.add(entity_type)
                logger.info(f"Found entity type: {entity_type}")
        
        # If we found services, create entity types
        if found_types:
            logger.info(f"Returning {len(found_types)} found entity types")
            return jsonify({
                "entity_types": [
                    {"value": entity_type, "label": labels[entity_type]} 
                    for entity_type in found_types
                ]
            })
        
        # If no types found, return error
        logger.error("No entity types found in Docker services")
        return jsonify({"error": "No entity types found in Docker services"}), 404
        
    except Exception as e:
        # Log error and return the error
        logger.error(f"Error getting entity types: {str(e)}")
        return jsonify({"error": f"Error getting entity types: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)