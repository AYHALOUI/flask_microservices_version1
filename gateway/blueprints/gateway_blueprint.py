from flask import Blueprint, request, jsonify
import logging
from services.gateway_service import GatewayService
from shared.debugger_client import log_to_debugger

gateway_bp = Blueprint('gateway', __name__)
logger = logging.getLogger(__name__)

# Initialize service
gateway_service = GatewayService()



@gateway_bp.route('/api/<service>/<path:route>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def gateway_router(service, route):
    """Main gateway router that forwards requests to appropriate services"""
    
    log_to_debugger("gateway", "info", f"Routing request to {service}/{route}", {
        "method": request.method,
        "headers": dict(request.headers),
        "service": service
    })
    
    try:
        # Use the service to handle the routing
        response = gateway_service.route_request(
            service=service,
            route=route,
            method=request.method,
            data=request.get_data(),
            headers=dict(request.headers)
        )
        
        log_to_debugger("gateway", "info", f"Successfully routed request to {service}/{route}", {
            "status_code": response.status_code,
            "service": service
        })
        
        return response
        
    except Exception as e:        
        log_to_debugger("gateway", "error", f"Failed to route request to {service}/{route}", {
            "error": str(e),
            "service": service
        })
        
        return jsonify({"error": f"Gateway error: {str(e)}"}), 500