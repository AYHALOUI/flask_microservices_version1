from flask import Blueprint, request, jsonify
import logging
from services.gateway_service import GatewayService
from shared.debugger_client import track_incoming_request, track_routing, track_response

gateway_bp = Blueprint('gateway', __name__)
logger = logging.getLogger(__name__)

# Initialize service
gateway_service = GatewayService()



@gateway_bp.route('/api/<service>/<path:route>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def gateway_router(service, route):
    """Main gateway router that forwards requests to appropriate services""" 

    tracker = track_incoming_request("gateway")
        
    # Track routing decision
    track_routing(tracker, "gateway", f"service_{service}")
    
    # Add request ID to headers for downstream services
    headers = dict(request.headers)
    headers['X-Request-ID'] = tracker.request_id

    try:
        # Use the service to handle the routing
        response = gateway_service.route_request(
            service=service,
            route=route,
            method=request.method,
            data=request.get_data(),
            headers=headers
        )

        # Track response back to client
        track_response(tracker, "gateway", "external_client")
        return response
        
    except Exception as e:        
        return jsonify({"error": f"Gateway error: {str(e)}"}), 500