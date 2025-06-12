# shared/debugger_client.py - Just add this one function
import requests
import time
import logging
import uuid

logger = logging.getLogger(__name__)

class FlowTracker:
    def __init__(self, request_id=None):
        self.request_id = request_id or str(uuid.uuid4())[:8]
    
    def log_flow(self, from_service, to_service, action, data=None):
        """Log request flow step"""
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
                
            requests.post("http://service_logs:5000/logs", json=payload, timeout=2)
        except Exception as e:
            logger.error(f"Failed to log flow: {str(e)}")

    def log_error(self, service, error_message, context=None):
        """Simple error logging"""
        try:
            payload = {
                "service": "error",
                "level": "error", 
                "message": f"ERROR in {service}: {error_message}",
                "from_service": service,
                "to_service": "ERROR",  # Make this more obvious
                "action": f"{error_message[:50]}...",  # Show part of error in action
                "request_id": self.request_id,
                "timestamp": time.time()
            }
            
            if context:
                payload["context"] = str(context)
                
            requests.post("http://service_logs:5000/logs", json=payload, timeout=2)
        except Exception as e:
            logger.error(f"Failed to log error: {str(e)}")

# Add this simple function at the bottom
def track_error(tracker, service, error_message, context=None):
    """Track an error - SIMPLE VERSION"""
    tracker.log_error(service, error_message, context)



# Existing functions (unchanged)
def track_incoming_request(to_service, request_id=None):
    tracker = FlowTracker(request_id)
    tracker.log_flow("external_client", to_service, "incoming_request")
    return tracker

def track_routing(tracker, from_service, to_service):
    tracker.log_flow(from_service, to_service, "routing")

def track_api_call(tracker, from_service, to_service, api_name):
    tracker.log_flow(from_service, to_service, api_name)

def track_response(tracker, from_service, to_service):
    tracker.log_flow(from_service, to_service, "response")