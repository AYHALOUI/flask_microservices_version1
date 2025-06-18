from flask import Blueprint, request, jsonify
import logging
import time
import json
from services.gateway_service import GatewayService
from shared.debugger_client import track_incoming_request_with_payload, track_routing, track_final_response

gateway_bp = Blueprint('gateway', __name__)
logger = logging.getLogger(__name__)

# Initialize service
gateway_service = GatewayService()

@gateway_bp.route('/api/<service>/<path:route>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def gateway_router(service, route):
    """Main gateway router that forwards requests to appropriate services with enhanced logging""" 
    
    start_time = time.time()
    
    # Capture request payload
    try:
        payload = request.get_json() if request.is_json else None
    except:
        payload = None
    
    # Enhanced tracking with payload information
    tracker = track_incoming_request_with_payload(
        to_service="gateway",
        method=request.method,
        endpoint=f"/api/{service}/{route}",
        payload=payload,
        headers=dict(request.headers)
    )
        
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

        # Calculate response time
        response_time_ms = round((time.time() - start_time) * 1000, 2)
        
        # Try to extract response data for logging
        try:
            response_data = json.loads(response.data) if response.data else None
        except:
            response_data = {"note": "Non-JSON response"}

        # Track final response with details
        track_final_response(
            tracker=tracker,
            service="gateway", 
            status_code=response.status_code,
            response_data=response_data,
            response_time_ms=response_time_ms
        )

        return response
        
    except Exception as e:
        # Calculate response time even for errors
        response_time_ms = round((time.time() - start_time) * 1000, 2)
        
        # Track error response
        track_final_response(
            tracker=tracker,
            service="gateway",
            status_code=500,
            response_data={"error": str(e)},
            response_time_ms=response_time_ms
        )
        
        return jsonify({"error": f"Gateway error: {str(e)}"}), 500