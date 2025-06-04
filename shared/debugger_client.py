import requests
import time
import logging
import json

logger = logging.getLogger(__name__)

def log_to_debugger(service_name, level, message, additional_data=None):
    """Send logs to the debugger service"""
    try:
        payload = {
            "service": service_name,
            "level": level,
            "message": message,
            "timestamp": time.time()
        }
        if additional_data:
            payload["data"] = additional_data
            
        requests.post("http://service_debugger:5000/log", json=payload, timeout=2)
    except Exception as e:
        logger.error(f"Failed to send log to debugger: {str(e)}")

def record_exchange(source, target, request_data, response_data=None):
    """Record an exchange between services"""
    try:
        payload = {
            "source_service": source,
            "target_service": target,
            "request_data": request_data,
            "response_data": response_data,
            "timestamp": time.time()
        }
        
        requests.post("http://service_debugger:5000/exchange", json=payload, timeout=2)
    except Exception as e:
        logger.error(f"Failed to record exchange: {str(e)}")

def log_simple_flow(source, destination, action="request"):
    """Simple from->to logging"""
    log_entry = {
        "timestamp": time.time(),
        "flow": f"{source} → {destination}",
        "action": action,
        "service": "flow_tracker"
    }
        
    # Send to debugger service
    requests.post(
        "http://service_debugger:5000/log", 
        json=log_entry, 
        timeout=1
    )