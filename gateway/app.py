from flask import Flask,  jsonify
import logging


app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SERVICES = {
    'contact': 'service_contact',
    'project': 'service_project'
}

def _validate_service(service):
    service = service.lower();
    if service not in SERVICES:
        return None, jsonify({
            "error": f"Service '{service}' not found",
            'error_code': 404
            })
    return service, None

@app.route('/')
def hello():
    logger.info('---------- > service and route is')
    return jsonify({
        "msg": "Hello World" 
        
    })

@app.route('/api/<service>/<path:route>', methods=['GET', 'PUT', 'DELETE', 'POST', 'PATCH'])
def getway_router(service, route):

    # print(f"service is ====> {service}")
    service, error_response = _validate_service(service)
    if error_response:
        return error_response
    return service

if __name__ == "__main__":
    app.run('0.0.0.0', port=5000, debug=True)





# from flask import Flask, request, jsonify, Response
# import requests
# import os
# import logging
# import time
# import json
# import docker
# from shared.debugger_client import log_to_debugger, record_exchange

# app = Flask(__name__)
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # ===== Private Helper Functions =====

# def _get_services_from_env():
#     """Get service URLs from environment variables"""
#     services = {}
#     for key, value in os.environ.items():
#         if key.startswith('SERVICE_'):
#             service_name = key[8:].lower()  # Remove 'SERVICE_' prefix
#             services[service_name] = value
#     return services

# def _discover_services_via_docker():
#     """Discover services using Docker API"""
#     try:
#         client = docker.from_env()
#         services = {}
        
#         containers = client.containers.list()

#         # example output of containers
#         # [
#         #     <Container: service_user>,
#         #     <Container: service_order>,
#         #     <Container: some_other_container>
#         # ]
        
#         for container in containers:
#             # Check if container is part of current Docker Compose project
#             labels = container.labels
#             if 'com.docker.compose.service' in labels:
#                 service_name = labels['com.docker.compose.service']
#                 # Get the container's network IP
#                 networks = container.attrs['NetworkSettings']['Networks']
                
#                 for network_name, network_info in networks.items():
#                     if 'microservices_network' in network_name:
#                         ip = network_info['IPAddress']
#                         # Make the service name simpler - remove "service_" prefix for easier access
#                         simplified_name = service_name
#                         if service_name.startswith('service_'):
#                             simplified_name = service_name[8:]  # Remove "service_" prefix
                        
#                         services[simplified_name.lower()] = f'http://{ip}:5000'
#                         # Also add the original name to avoid confusion
#                         services[service_name.lower()] = f'http://{ip}:5000'
#                         logger.debug(f"Discovered service: {service_name} at {ip}")
#                         break
#         return services
#     except Exception as e:
#         logger.error(f"Failed to discover services via Docker: {str(e)}")
#         return {}

# def _initialize_services():
#     """Initialize the services dictionary from Docker or environment variables"""
#     services = {}
    
#     # Try Docker discovery first
#     try:
#         logger.info("Attempting service discovery via Docker API...")
#         services = _discover_services_via_docker()
#         logger.info(f"Discovered services ----------> {services}")
#     except Exception as e:
#         # log_todebugger("gateway", "error", "Docker service discovery failed", {
#         #     "error": str(e)
#         # })
#         logger.error(f"Docker service discovery failed: {str(e)}")
    
#     # If Docker discovery yielded no results, use env vars
#     if not services:
#         logger.info("Using environment variables for services...")
#         services = _get_services_from_env()
    
#     if not services:
#         logger.warning("No services discovered! Gateway will be unable to route requests.")
#     else:
#         logger.info(f"Successfully initialized with {len(services)} services")
    
#     return services

# def _validate_service(service):
#     """Validate that the requested service exists"""
#     service = service.lower()
#     if service not in SERVICES:
#         logger.warning(f"Service not found: {service}")
#         return None, jsonify({"error": f"Service '{service}' not found"}), 404
    
#     return service, None, None

# def _build_service_url(service, route):
#     """Build the complete service URL"""
#     return f"{SERVICES[service]}/{route}"

# def _forward_request(service_url, method, data, headers=None):
#     """Forward the request to the target service"""
#     try:
#         logger.info(f"Forwarding {method} request to {service_url}")
        
#         if headers is None:
#             headers = {}
#             # Copy necessary headers from the original request
#             for key, value in request.headers.items():
#                 if key.lower() not in ['host', 'content-length']:
#                     headers[key] = value
        
#         resp = requests.request(
#             method=method,
#             url=service_url,
#             headers=headers,
#             data=data,
#             timeout=30
#         )        
#         response = Response(
#             resp.content,
#             status=resp.status_code,
#             headers=dict(resp.headers)
#         )
#         return response
    
#     except requests.RequestException as e:
#         logger.error(f"Service communication error: {str(e)}")
#         return jsonify({
#             "error": f"Service communication error: {str(e)}",
#             "url": service_url
#         }), 500


# # ===== Global Configuration =====

# # Initialize the services dictionary
# SERVICES = _initialize_services()

# # ===== Public API Endpoints =====

# @app.route('/services', methods=['GET'])
# def list_services():
#     """List all available services"""
#     return jsonify({
#         "services": list(SERVICES.keys()),
#         "count": len(SERVICES)
#     })


# @app.route('/api/<service>/<path:route>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
# def gateway_router(service, route):
#     """Main gateway router that forwards requests to appropriate services"""
#     log_to_debugger("gateway", "info", f"Routing request to {service}/{route}", {
#         "method": request.method,
#         "headers": dict(request.headers),
#         "service": service
#     })
#     # Validate service exists
#     service, error_response, error_code = _validate_service(service)
#     if error_response:
#         return error_response, error_code
    
    
#     # Build service URL
#     service_url = _build_service_url(service, route)
    
#     # Get request data
#     request_data = request.get_data().decode('utf-8') if request.get_data() else None
        
#     # Forward the request
#     response = _forward_request(service_url, request.method, request.get_data())
    
#     response_data = response.get_data().decode('utf-8') if response.get_data() else None

#      # After forwarding the request
#     log_to_debugger("gateway", "info", f"Successfully routed request to {service}/{route}", {
#         "status_code": response.status_code,
#         "service": service
#     })

#     log_to_debugger("gateway", "error", f"Failed to route request to {service}/{route}", {
#         "status_code": response.status_code,
#         "service": service
#     })
#     return response

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000, debug=True)