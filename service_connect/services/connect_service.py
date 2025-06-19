import logging
import os
import requests
from flask import Response
from shared.debugger_client import FlowTracker, track_api_call, track_response


class ConnectService:
    """Service class for handling external API connections and proxying"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.targets = self._load_target_configurations()

    def _load_target_configurations(self):
        """Load target configurations from environment variables"""
        return {
            "oggo": {
                "base_url": os.environ.get("OGGO_BASE_URL"),
                "auth_type": "bearer",
                "auth_key": os.environ.get("OGGO_API_KEY"),
            },
            "hubspot": {
                "base_url": os.environ.get("HUBSPOT_BASE_URL"),
                "auth_type": "bearer", 
                "auth_key": os.environ.get("HUBSPOT_API_KEY"),
            }
        }

    
    # def proxy_request(self, target, endpoint, method, headers, data, params=None):
    #     """Proxy a request to an external service with enhanced tracking"""

    #     # Get request ID from headers if available
    #     request_id = headers.get('X-Request-ID')
    #     tracker = FlowTracker(request_id)
        
    #     # Validate target
    #     target = self._validate_target(target)
        
    #     # Build target URL
    #     target_url = self._build_target_url(target, endpoint)
        
    #     # Prepare headers with authentication
    #     prepared_headers = self._prepare_headers(target, headers)

    #     # Track outgoing API call to external service
    #     track_api_call(tracker, "service_connect", f"external_{target}", f"api_call")
        
    #     response = self._execute_proxy_request(method, target_url, prepared_headers, data, params)

    #     # Track response from external service
    #     track_response(tracker, f"external_{target}", "service_connect")
        
    #     # NEW: Track sending response back to calling service
    #     calling_service = self._detect_calling_service(headers, endpoint)
    #     track_response(tracker, "service_connect", calling_service)

    #     return response

    # def proxy_request(self, target, endpoint, method, headers, data, params=None):
    #     """Proxy a request to an external service with complete tracking"""

    #     # Get request ID from headers if available
    #     request_id = headers.get('X-Request-ID')
    #     tracker = FlowTracker(request_id)
        
    #     # Validate target
    #     target = self._validate_target(target)
        
    #     # Build target URL
    #     target_url = self._build_target_url(target, endpoint)
        
    #     # Prepare headers with authentication
    #     prepared_headers = self._prepare_headers(target, headers)

    #     # Track outgoing API call to external service
    #     track_api_call(tracker, "service_connect", f"external_{target}", "api_call")
        
    #     response = self._execute_proxy_request(method, target_url, prepared_headers, data, params)

    #     # Track response from external service
    #     track_response(tracker, f"external_{target}", "service_connect")
        
    #     # Track sending response back to calling service
    #     calling_service = self._detect_calling_service(headers, endpoint)
    #     track_response(tracker, "service_connect", calling_service)

    #     return response

    def proxy_request(self, target, endpoint, method, headers, data, params=None):
        """Enhanced proxy request with maximum tracking detail"""

        # Get request ID from headers if available
        request_id = headers.get('X-Request-ID')
        tracker = FlowTracker(request_id)
        
        # Validate target
        target = self._validate_target(target)
        
        # Build target URL
        target_url = self._build_target_url(target, endpoint)
        
        # Prepare headers with authentication
        prepared_headers = self._prepare_headers(target, headers)

        # MORE SPECIFIC: Track the specific API call based on endpoint
        if 'contacts' in endpoint and method == 'GET':
            track_api_call(tracker, "service_connect", f"external_{target}", "fetch_contacts")
        elif 'projects' in endpoint and method == 'GET':
            track_api_call(tracker, "service_connect", f"external_{target}", "fetch_projects")
        elif 'contacts' in endpoint and method == 'POST':
            track_api_call(tracker, "service_connect", f"external_{target}", "create_contacts")
        elif 'deals' in endpoint and method == 'POST':
            track_api_call(tracker, "service_connect", f"external_{target}", "create_deals")
        else:
            track_api_call(tracker, "service_connect", f"external_{target}", "api_call")
        
        response = self._execute_proxy_request(method, target_url, prepared_headers, data, params)

        # Track response from external service
        track_response(tracker, f"external_{target}", "service_connect")
        
        # Track sending response back to calling service
        calling_service = self._detect_calling_service(headers, endpoint)
        track_response(tracker, "service_connect", calling_service)

        return response



    # def _detect_calling_service(self, headers, endpoint):
    #     """Detect which service called us based on headers or endpoint"""
    #     # You can detect this from headers, endpoint patterns, etc.
    #     if 'contacts' in endpoint.lower():
    #         return "service_contacts"
    #     elif 'projects' in endpoint.lower():
    #         return "service_projects"
    #     else:
    #         return "service_unknown"

    def _detect_calling_service(self, headers, endpoint):
        """Detect which service called us based on headers or endpoint"""
        if 'contacts' in endpoint.lower():
            return "service_contacts"
        elif 'projects' in endpoint.lower() or 'deals' in endpoint.lower():
            return "service_projects"
        else:
            return "service_unknown"
    
    # ============ Private Methods ===============
    def _validate_target(self, target):
        """Validate that the target is allowed"""
        target = target.lower()
        if target not in self.targets:
            raise ValueError(f"Target '{target}' not allowed. Available targets: {list(self.targets.keys())}")
        return target

    def _build_target_url(self, target, endpoint):
        """Build the target URL from the configuration"""
        target_config = self.targets[target]
        base_url = target_config["base_url"]
        return f"{base_url}/{endpoint}"

    def _prepare_headers(self, target, original_headers):
        """Prepare headers for the proxied request, including authentication"""
        headers = {
            key: value for key, value in original_headers.items() 
            if key.lower() not in ['host', 'content-length']
        }        
        return headers

    def _execute_proxy_request(self, method, url, headers, data, params=None):
        """Execute the proxy request and handle errors"""
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                data=data,
                params=params,
                timeout=30
            )
             
            # Create Flask response that preserves original response
            flask_response = Response(
                response.content,
                status=response.status_code,
                headers=dict(response.headers)
            )
            return flask_response
        except (requests.Timeout, requests.ConnectionError, requests.RequestException) as e:
            raise Exception(f"Request error: {str(e)}")
        except Exception as e:
            raise Exception(f"Proxy error: {str(e)}")