from flask import Blueprint, request, jsonify
import logging
from services.gateway_service import GatewayService
from shared.debugger_client import log_simple_flow

gateway_bp = Blueprint('gateway', __name__)
logger = logging.getLogger(__name__)

# Initialize service
gateway_service = GatewayService()



@gateway_bp.route('/api/<service>/<path:route>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def gateway_router(service, route):
    """Main gateway router that forwards requests to appropriate services""" 

    # Log: External Client → Gateway
    log_simple_flow("external_client", "gateway", "incoming_request")
    
    # Log: Gateway → Target Service
    log_simple_flow("gateway", f"service_{service}", "routing")
    try:
        # Use the service to handle the routing
        response = gateway_service.route_request(
            service=service,
            route=route,
            method=request.method,
            data=request.get_data(),
            headers=dict(request.headers)
        )

        # Log: Target Service → Gateway (response)
        log_simple_flow(f"service_{service}", "gateway", "response")
        
        # Log: Gateway → External Client (response)
        log_simple_flow("gateway", "external_client", "response")

        return response
        
    except Exception as e:        
        return jsonify({"error": f"Gateway error: {str(e)}"}), 500