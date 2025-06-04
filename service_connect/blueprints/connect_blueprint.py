from flask import Blueprint, request, jsonify, Response
import logging
from services.connect_service import ConnectService
from shared.debugger_client import log_to_debugger

connect_bp = Blueprint('connect', __name__)
logger = logging.getLogger(__name__)

# Initialize services
connect_service = ConnectService()



@connect_bp.route('/proxy/<target>/<path:endpoint>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def proxy_request(target, endpoint):
    """
    Proxy requests to external services
    
    Example: 
    - /proxy/oggo/contacts -> forwards to external Oggo API
    - /proxy/hubspot/crm/v3/objects/contacts -> forwards to external HubSpot API
    """
    try:
        
        response = connect_service.proxy_request(
            target=target,
            endpoint=endpoint,
            method=request.method,
            headers=dict(request.headers),
            data=request.get_data(),
            params=dict(request.args)
        )
                
        return response
        
    except Exception as e:        
        return jsonify({"error": f"Proxy error: {str(e)}"}), 500


