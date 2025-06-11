from flask import Flask, request, jsonify
import logging
import requests

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



@app.route('/transform', methods=['POST'])
def transform_data():
    try:
        request_data = request.json

        if not request_data:
            return jsonify({"error": "No data provided"}), 400
        
        # Extract parameters
        data = request_data.get('data', [])
        entity_type = request_data.get('entity_type', '')
        
        if not entity_type:
            return jsonify({"error": "entity_type is required"}), 400
        
       
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
        result[f"{entity_type}s"] = transformed_items
    return result

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)