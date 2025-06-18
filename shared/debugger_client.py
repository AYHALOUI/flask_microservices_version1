# shared/debugger_client.py - Fixed version
import requests
import time
import logging
import uuid
import json

logger = logging.getLogger(__name__)

class FlowTracker:
    def __init__(self, request_id=None):
        self.request_id = request_id or str(uuid.uuid4())[:8]
        print(f"🔍 DEBUG: FlowTracker created with request_id: {self.request_id}")
    
    def log_flow(self, from_service, to_service, action, data=None):
        """Log request flow step with debug info"""
        try:
            payload = {
                "service": "flow",
                "level": "info",
                "message": f"{from_service} → {to_service} ({action})",
                "from_service": from_service,
                "to_service": to_service,
                "action": action,
                "request_id": self.request_id,
                "timestamp": time.time()
            }
            
            if data:
                payload["data"] = data
            
            print(f"🔍 DEBUG: About to send log: {payload}")
            
            response = requests.post("http://service_logs:5000/logs", json=payload, timeout=2)
            
            print(f"🔍 DEBUG: Log sent, response status: {response.status_code}")
            
        except Exception as e:
            print(f"🔍 DEBUG: Failed to log flow: {str(e)}")
            logger.error(f"Failed to log flow: {str(e)}")

    def log_error(self, service, error_message, context=None):
        """Simple error logging with debug info"""
        try:
            print(f"🔍 DEBUG: Logging error for {service}: {error_message}")
            
            payload = {
                "service": "error",
                "level": "error", 
                "message": f"ERROR in {service}: {error_message}",
                "from_service": service,
                "to_service": "ERROR",
                "action": f"{error_message[:50]}...",
                "request_id": self.request_id,
                "timestamp": time.time()
            }
            
            if context:
                payload["context"] = str(context)
            
            print(f"🔍 DEBUG: About to send error log: {payload}")
            response = requests.post("http://service_logs:5000/logs", json=payload, timeout=2)
            print(f"🔍 DEBUG: Error log sent, response status: {response.status_code}")
                
        except Exception as e:
            print(f"🔍 DEBUG: Failed to log error: {str(e)}")
            logger.error(f"Failed to log error: {str(e)}")

    def log_request_payload(self, service, method, endpoint, payload_data=None, headers=None):
        """Log incoming request with payload"""
        try:
            log_payload = {
                "service": "request",
                "level": "info",
                "message": f"INCOMING: {method} {endpoint}",
                "from_service": "external_client",
                "to_service": service,
                "action": "incoming_request_with_payload",
                "request_id": self.request_id,
                "timestamp": time.time(),
                "method": method,
                "endpoint": endpoint
            }
            
            if payload_data:
                # Limit payload size for logging
                payload_str = json.dumps(payload_data) if isinstance(payload_data, dict) else str(payload_data)
                if len(payload_str) > 1000:  # Limit to 1000 chars
                    log_payload["payload"] = payload_str[:1000] + "... [truncated]"
                else:
                    log_payload["payload"] = payload_data
            
            if headers:
                # Only log important headers
                important_headers = {k: v for k, v in headers.items() 
                                   if k.lower() in ['content-type', 'authorization', 'x-api-key']}
                log_payload["headers"] = important_headers
                
            requests.post("http://service_logs:5000/logs", json=log_payload, timeout=2)
        except Exception as e:
            logger.error(f"Failed to log request payload: {str(e)}")

    def log_response(self, service, status_code, response_data=None, response_time_ms=None):
        """Log response with data"""
        try:
            log_payload = {
                "service": "response",
                "level": "info",
                "message": f"RESPONSE: {status_code}",
                "from_service": service,
                "to_service": "external_client",
                "action": "final_response",
                "request_id": self.request_id,
                "timestamp": time.time(),
                "status_code": status_code
            }
            
            if response_time_ms:
                log_payload["response_time_ms"] = response_time_ms
            
            if response_data:
                # Limit response size for logging
                response_str = json.dumps(response_data) if isinstance(response_data, dict) else str(response_data)
                if len(response_str) > 1000:  # Limit to 1000 chars
                    log_payload["response"] = response_str[:1000] + "... [truncated]"
                else:
                    log_payload["response"] = response_data
                
            requests.post("http://service_logs:5000/logs", json=log_payload, timeout=2)
        except Exception as e:
            logger.error(f"Failed to log response: {str(e)}")

# Enhanced tracking functions
def track_incoming_request_with_payload(to_service, method, endpoint, payload=None, headers=None, request_id=None):
    """Track incoming request with full payload information"""
    tracker = FlowTracker(request_id)
    tracker.log_request_payload(to_service, method, endpoint, payload, headers)
    return tracker

def track_final_response(tracker, service, status_code, response_data=None, response_time_ms=None):
    """Track final response with data"""
    tracker.log_response(service, status_code, response_data, response_time_ms)

def track_error(tracker, service, error_message, context=None):
    """Track an error - FIXED VERSION WITH DEBUG"""
    print(f"🔍 DEBUG: track_error called: {service} - {error_message}")
    tracker.log_error(service, error_message, context)

# Existing functions (unchanged)
def track_incoming_request(to_service, request_id=None):
    tracker = FlowTracker(request_id)
    tracker.log_flow("external_client", to_service, "incoming_request")
    return tracker

def track_routing(tracker, from_service, to_service):
    tracker.log_flow(from_service, to_service, "routing")

def track_api_call(tracker, from_service, to_service, api_name):
    """Track API call - FIXED VERSION WITH DEBUG"""
    print(f"🔍 DEBUG: track_api_call called: {from_service} → {to_service} ({api_name})")
    tracker.log_flow(from_service, to_service, api_name)

def track_response(tracker, from_service, to_service):
    tracker.log_flow(from_service, to_service, "response")