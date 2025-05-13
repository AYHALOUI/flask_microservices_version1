from flask import Flask, request, jsonify
import requests
import os
import logging
import json
import time
from shared.debugger_client import log_to_debugger, record_exchange

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
TRANSFORM_SERVICE_URL = os.environ.get('TRANSFORM_SERVICE_URL')
service_connect = os.environ.get('service_connect')

# ===== Private Helper Functions =====

def _build_error_response(message, status_code=500):
    """Helper function to build error responses"""
    log_to_debugger("contact", "error", message)
    return jsonify({"error": message}), status_code

def _build_oggo_request():
    """Build the request configuration for Oggo API"""
    url = f"{service_connect}/proxy/oggo/contacts"
    headers = {"Content-Type": "application/json"}
    return url, headers

def _build_transform_request(contacts):
    """Build the request configuration for Transform service"""
    url = f"{TRANSFORM_SERVICE_URL}/transform"
    headers = {"Content-Type": "application/json"}
    payload = {
        "data": contacts,
        "entity_type": "contact"
    }
    return url, headers, payload

def _build_hubspot_request(transformed_data):
    """Build the request configuration for HubSpot API"""
    url = f"{service_connect}/proxy/hubspot/crm/v3/objects/contacts/batch/create"
    headers = {"Content-Type": "application/json"}
    hubspot_contacts = transformed_data.get('contacts', [])
    
    # Format payload according to HubSpot batch API requirements
    payload = {
        "inputs": [
            {
                "properties": contact.get('properties', {})
            } for contact in hubspot_contacts
        ]
    }
    return url, headers, payload

def _fetch_contacts_from_oggo(params):
    """Fetch contacts from Oggo via proxy service"""
    url, headers = _build_oggo_request()
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        contacts = response.json()
        return contacts
    except requests.RequestException as e:
        error_msg = f"Failed to fetch contacts from Oggo: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)

def _transform_contacts(contacts):
    """Transform contacts using the transformation service"""
    url, headers, payload = _build_transform_request(contacts)
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            raise Exception(f"Transform service error: {response.text}")
        
        transformed_data = response.json()
        return transformed_data
    
    except requests.RequestException as e:
        error_msg = f"Failed to transform contacts: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)

def _send_to_hubspot(transformed_data):
    """Send transformed contacts to HubSpot via proxy service"""
    url, headers, payload = _build_hubspot_request(transformed_data)
    try:        
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()    
        return response.json()
    except requests.RequestException as e:
        error_msg = f"Failed to sync data to HubSpot: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)

def _validate_request(data):
    """Validate incoming request data"""
    # Add any validation logic here
    return data or {}

def _log_operation_metrics(operation, start_time, contacts_count=0):
    """Log metrics about operations"""
    duration = time.time() - start_time
    log_to_debugger("contact", "info", f"{operation} completed", {
        "duration_ms": int(duration * 1000),
        "contacts_count": contacts_count
    })

# ===== Public API Endpoints =====

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "ok", "service": "contact"})

@app.route('/sync', methods=['POST'])
def sync_contacts():
    """Sync contacts from Oggo to HubSpot"""
    start_time = time.time()
    
    try:
        # Validate request
        params = _validate_request(request.json)
        
        # Step 1: Fetch contacts from Oggo
        contacts = _fetch_contacts_from_oggo(params)
        if not contacts:
            return jsonify({"message": "No contacts found to sync"}), 200
        
        transformed_data = _transform_contacts(contacts)
        
        hubspot_response = _send_to_hubspot(transformed_data)
        
        return jsonify({
            "status": "success",
            "message": "Contacts synced successfully",
        })
    
    except Exception as e:
        return _build_error_response(f"Error in sync: {str(e)}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)