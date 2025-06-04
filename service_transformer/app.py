from flask import Flask, request, jsonify
import os
import json
import logging
import time
import requests
from shared.debugger_client import log_to_debugger, record_exchange

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_mapping_from_service(entity_type):
    """Get mapping from the mapping service"""
    try:
        response = requests.get(f'http://service_mapping:5000/mappings/{entity_type}')
        if response.status_code == 200:
            mapping_data = response.json()
            return mapping_data.get('rules', {})
        else:
            logger.error(f"Failed to fetch mapping from service: {response.status_code}")
            return {}
    except Exception as e:
        logger.error(f"Error fetching mapping from service: {str(e)}")
        return {}

def get_mapping_from_file(entity_type):
    """Try multiple locations to find mapping file"""
    possible_paths = [
        f'/service_contacts/mappings/{entity_type}_mapping.json',
        f'/app/mappings/contacts/{entity_type}_mapping.json', 
        f'/app/mappings/{entity_type}_mapping.json'
    ]
    
    for mapping_path in possible_paths:
        try:
            logger.info(f"Trying to load mapping from: {mapping_path}")
            if os.path.exists(mapping_path):
                with open(mapping_path, 'r') as f:
                    mapping_rules = json.load(f)
                logger.info(f"✅ Successfully loaded mapping from {mapping_path}")
                return mapping_rules
            else:
                logger.info(f"❌ File not found: {mapping_path}")
        except Exception as e:
            logger.error(f"❌ Error reading {mapping_path}: {str(e)}")
    logger.error(f"❌ Could not find mapping file for {entity_type} in any location")
    return {}

@app.route('/transform', methods=['POST'])
def transform_data():
    try:
        request_data = request.json

        if not request_data:
            return jsonify({"error": "No data provided"}), 400
        
        # Extract parameters
        data = request_data.get('data', [])
        entity_type = request_data.get('entity_type', '')
        
        logger.info(f"=== TRANSFORM REQUEST ===")
        logger.info(f"Entity type: {entity_type}")
        logger.info(f"Data count: {len(data)}")
        
        if not entity_type:
            return jsonify({"error": "entity_type is required"}), 400
        
        # Try to get mapping from file first, then from service
        mapping_rules = get_mapping_from_file(entity_type)
        
        if not mapping_rules:
            logger.warning(f"No mapping found in files for {entity_type}, trying mapping service...")
            mapping_rules = get_mapping_from_service(entity_type)
        
        if not mapping_rules:
            error_msg = f"No mapping rules found for entity type: {entity_type}"
            logger.error(error_msg)
            return jsonify({"error": error_msg}), 404
            
        # Transform the data
        transformed_data = transform_using_mapping(data, mapping_rules, entity_type)   

        return jsonify(transformed_data)
    
    except Exception as e:
        logger.error(f"Error in transform: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "service": "transform"})

def transform_using_mapping(data, mapping_rules, entity_type):
    result = {}
    transformed_items = []
    
    for item in data:
        transformed_item = {}
        
        # Set default hubspot_id to null for contacts
        if entity_type == 'contact':
            transformed_item['hubspot_id'] = item.get('id')
        
        # For each field in the mapping rules
        for source_field, target_field in mapping_rules.items():
            if source_field in item:
                # Handle nested properties
                if '.' in target_field:
                    parts = target_field.split('.')
                    parent = parts[0]
                    child = parts[1]
                    
                    if parent not in transformed_item:
                        transformed_item[parent] = {}
                    transformed_item[parent][child] = item[source_field]
                else:
                    # Direct field mapping
                    transformed_item[target_field] = item[source_field]
        
        transformed_items.append(transformed_item)
    
    # Package according to entity type
    if entity_type == 'contact':
        result['contacts'] = transformed_items
    else:
        # Generic fallback
        result[f"{entity_type}s"] = transformed_items
    return result

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)