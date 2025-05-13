from flask import Flask, request, Response, jsonify
import requests
import logging
import os
import time
import json
# from shared.debugger_client import log_to_debugger, record_exchange

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== Private Helper Functions =====

def _get_targets_from_env():
    """Get target configurations from environment variables"""
    return {
        "oggo": {
            "base_url": os.environ.get("OGGO_BASE_URL"),
            "auth_type": "bearer",
            "auth_key": os.environ.get("OGGO_API_KEY")
        },
        "hubspot": {
            "base_url": os.environ.get("HUBSPOT_BASE_URL"),
            "auth_type": "bearer",
            "auth_key": os.environ.get("HUBSPOT_API_KEY")
        }
    }

def _validate_target(target):
    """Validate that the target is allowed"""
    target = target.lower()
    if target not in ALLOWED_TARGETS:
        return None, jsonify({"error": f"Target '{target}' not allowed"}), 403
    
    return target, None, None

def _build_target_url(target, endpoint):
    """Build the target URL from the configuration"""
    target_config = ALLOWED_TARGETS[target]
    return f"{target_config['base_url']}/{endpoint}"

def _prepare_headers(target, original_headers):
    """Prepare headers for the proxied request, including authentication"""
    # Filter headers
    headers = {
        key: value for key, value in original_headers.items() 
        if key.lower() not in ['host', 'content-length']
    }
    
    # Add authentication
    target_config = ALLOWED_TARGETS[target]
    auth_type = target_config.get('auth_type')
    
    if auth_type == 'bearer' and target_config.get('auth_key'):
        headers['Authorization'] = f"Bearer {target_config['auth_key']}"
    elif auth_type == 'apikey' and target_config.get('auth_key'):
        headers['X-API-Key'] = target_config['auth_key']
        
    return headers

def _execute_proxy_request(method, url, headers, data):
    """Execute the proxy request and handle errors"""
    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            data=data,
            timeout=30  # Added timeout
        )
        
        return Response(
            response.content,
            status=response.status_code,
            headers=dict(response.headers)
        )
        
    except requests.RequestException as e:
        logger.error(f"Proxy request failed: {str(e)}")
        return jsonify({
            "error": f"Failed to proxy request: {str(e)}",
            "url": url
        }), 500

def _log_request(target, endpoint, method, target_url):
    """Log information about the proxy request"""
    logger.info(f"Proxying {method} request to {target}: {endpoint}")
    logger.info(f"Target URL: {target_url}")

# ===== Global Configuration =====

# Load target configurations
ALLOWED_TARGETS = _get_targets_from_env()

# ===== Public API Endpoints =====

@app.route('/proxy/<target>/<path:endpoint>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def proxy_request(target, endpoint):
    """
    Proxy requests to external services
    
    Example: 
    - /proxy/oggo/contacts -> forwards to https://api.oggo.com/contacts
    - /proxy/hubspot/crm/v3/objects/contacts -> forwards to https://api.hubspot.com/crm/v3/objects/contacts
    """
    # Validate target
    target, error_response, error_code = _validate_target(target)
    if error_response:
        return error_response, error_code
        
    # Build target URL
    target_url = _build_target_url(target, endpoint)
    
    
    # Prepare headers with authentication
    headers = _prepare_headers(target, request.headers)
    
    # Get request data
    request_data = request.get_data()
    
    # Execute the proxy request
    return _execute_proxy_request(request.method, target_url, headers, request_data)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "ok", 
        "service": "proxy",
        "targets": list(ALLOWED_TARGETS.keys())
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)