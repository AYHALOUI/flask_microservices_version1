print("🚨🚨🚨 CONNECT BLUEPRINT LOADED - THIS SHOULD APPEAR IN LOGS! 🚨🚨🚨")

from flask import Blueprint, request, jsonify
import logging

print("🚨 About to import ConnectService...")
try:
    from services.connect_service import ConnectService
    print("🚨 ConnectService imported successfully!")
except Exception as e:
    print(f"🚨 ERROR importing ConnectService: {e}")
    import traceback
    traceback.print_exc()

connect_bp = Blueprint('connect', __name__)
logger = logging.getLogger(__name__)

print("🚨 About to initialize ConnectService...")
try:
    connect_service = ConnectService()
    print("🚨 ConnectService initialized successfully!")
except Exception as e:
    print(f"🚨 ERROR initializing ConnectService: {e}")
    import traceback
    traceback.print_exc()


@connect_bp.route('/test', methods=['GET'])
def test_route():
    print("🚨 TEST ROUTE CALLED!")
    return "Test successful"

@connect_bp.route('/proxy/<target>/<path:endpoint>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def proxy_request(target, endpoint):
    print(f"🚨 PROXY ROUTE CALLED! target={target}, endpoint={endpoint}")
    return "Proxy function called"  # Simple return first

# @connect_bp.route('/proxy/<target>/<path:endpoint>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
# def proxy_request(target, endpoint):
#     """
#     Proxy requests to external services
#     """
#     print(f"🚨 BLUEPRINT: Function called with target={target}, endpoint={endpoint}")
#     print(f"🚨 BLUEPRINT: Request method={request.method}")
#     print(f"🚨 BLUEPRINT: Request path={request.path}")
    
#     try:
#         print(f"🚨 BLUEPRINT: About to call connect_service.proxy_request")
        
#         response = connect_service.proxy_request(
#             target=target,
#             endpoint=endpoint,
#             method=request.method,
#             headers=dict(request.headers),
#             data=request.get_data(),
#             params=dict(request.args)
#         )
        
#         print(f"🚨 BLUEPRINT: Got response, returning it")
#         return response
        
#     except Exception as e:        
#         print(f"🚨 BLUEPRINT: Exception occurred: {str(e)}")
#         import traceback
#         traceback.print_exc()
#         return jsonify({"error": f"Proxy error: {str(e)}"}), 500