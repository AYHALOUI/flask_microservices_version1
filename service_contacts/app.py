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
QUEUE_SERVICE_URL = os.environ.get('QUEUE_SERVICE_URL')

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
    log_to_debugger("contact", "info", "Fetching contacts from Oggo", params)
    url, headers = _build_oggo_request()
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        contacts = response.json()
        log_to_debugger("contact", "info", f"Retrieved {len(contacts)} contacts from Oggo", {"count": len(contacts)})
        return contacts
    except requests.RequestException as e:
        error_msg = f"Failed to fetch contacts from Oggo: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)

def _transform_contacts(contacts):
    """Transform contacts using the transformation service"""
    log_to_debugger("contact", "info", "Sending contacts for transformation", {"count": len(contacts)})
    url, headers, payload = _build_transform_request(contacts)
    try:
        # Record the exchange
        record_exchange(
            source="contact", 
            target="transform", 
            request_data=payload
        )
        
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            raise Exception(f"Transform service error: {response.text}")
        
        transformed_data = response.json()
        log_to_debugger("contact", "info", "Received transformed contacts", 
                {"count": len(transformed_data.get('contacts', []))})
        return transformed_data
    
    except requests.RequestException as e:
        error_msg = f"Failed to transform contacts: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)

def _send_to_hubspot(transformed_data):
    """Send transformed contacts to HubSpot via proxy service"""
    log_to_debugger("contact", "info", "Sending contacts to HubSpot", 
            {"count": len(transformed_data.get('contacts', []))})
    
    url, headers, payload = _build_hubspot_request(transformed_data)
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        # Check if response was successful
        if response.status_code != 200:
            # Add failed contacts to the queue
            error_msg = f"HubSpot API error: Status code {response.status_code}"
            log_to_debugger("contact", "error", error_msg)
            _queue_failed_items(transformed_data.get('contacts', []), error_msg)
            return None
        
        # Parse the response
        try:
            hubspot_response = response.json()
            log_to_debugger("contact", "info", "Received response from HubSpot")
            return hubspot_response
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse HubSpot response: {str(e)}"
            log_to_debugger("contact", "error", error_msg)
            _queue_failed_items(transformed_data.get('contacts', []), error_msg)
            return None
    
    except requests.RequestException as e:
        error_msg = f"Failed to sync data to HubSpot: {str(e)}"
        logger.error(error_msg)
        _queue_failed_items(transformed_data.get('contacts', []), error_msg)
        raise Exception(error_msg)

def _queue_failed_items(items, reason):
    """Add failed items to the queue service for later retry"""
    log_to_debugger("contact", "info", f"Queueing {len(items)} items for retry", {"reason": reason})
    
    for item in items:
        try:
            # Create a unique ID for the queue item
            item_id = item.get('hubspot_id', '') or f"contact_{int(time.time())}"
            
            # Create queue item payload
            queue_item = {
                "id": item_id,
                "entity_type": "contact",
                "data": item,
                "reason": reason
            }
            
            # Send to queue service
            response = requests.post(f"{QUEUE_SERVICE_URL}/queue", json=queue_item)
            
            if response.status_code == 200:
                log_to_debugger("contact", "info", f"Item {item_id} queued successfully")
            else:
                log_to_debugger("contact", "error", f"Failed to queue item {item_id}: {response.text}")
                
        except Exception as e:
            log_to_debugger("contact", "error", f"Error queueing item: {str(e)}")

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
        log_to_debugger("contact", "info", "Received sync request", params)
        
        # Step 1: Fetch contacts from Oggo
        contacts = _fetch_contacts_from_oggo(params)
        if not contacts:
            return jsonify({"message": "No contacts found to sync"}), 200
        
        # Step 2: Transform contacts
        transformed_data = _transform_contacts(contacts)
        
        # Step 3: Send to HubSpot
        hubspot_response = _send_to_hubspot(transformed_data)
        
        # Log operation metrics
        _log_operation_metrics("sync_contacts", start_time, len(contacts))
        
        # Check queue size
        try:
            queue_response = requests.get(f"{QUEUE_SERVICE_URL}/stats")
            queue_stats = queue_response.json() if queue_response.status_code == 200 else {}
            pending_count = queue_stats.get('by_status', {}).get('pending', 0)
            
            # Include queue info in response
            queue_info = {
                "pending_items": pending_count,
                "queue_url": f"{QUEUE_SERVICE_URL}/queue"
            }
        except:
            queue_info = {"error": "Could not fetch queue stats"}
        
        return jsonify({
            "status": "success",
            "message": f"Successfully processed {len(contacts)} contacts",
            "data": transformed_data,
            "hubspot_response": hubspot_response,
            "queue_info": queue_info
        })
    
    except Exception as e:
        return _build_error_response(f"Error in sync: {str(e)}")

@app.route('/retry-failed', methods=['POST'])
def retry_failed_contacts():
    """Trigger retry of failed contacts"""
    try:
        # Call the queue service to process retries
        response = requests.post(f"{QUEUE_SERVICE_URL}/retry")
        
        if response.status_code != 200:
            return _build_error_response(f"Failed to trigger retries: {response.text}")
            
        return jsonify(response.json())
        
    except Exception as e:
        return _build_error_response(f"Error triggering retries: {str(e)}")

@app.route('/queue-status', methods=['GET'])
def queue_status():
    """Get status of the queue"""
    try:
        # Get queue statistics
        response = requests.get(f"{QUEUE_SERVICE_URL}/stats")
        
        if response.status_code != 200:
            return _build_error_response(f"Failed to get queue stats: {response.text}")
            
        return jsonify(response.json())
        
    except Exception as e:
        return _build_error_response(f"Error getting queue status: {str(e)}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)