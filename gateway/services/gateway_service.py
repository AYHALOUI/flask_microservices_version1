import logging
import requests
from flask import Response, jsonify
from services.discovery_service import DiscoveryService


class GatewayService:
    """Service class for handling gateway operations"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.discovery_service = DiscoveryService()
        self.services = self.discovery_service.initialize_services()
    
    def get_available_services(self):
        """Get dictionary of available services"""
        return self.services
    
    def route_request(self, service, route, method, data, headers):
        """Route a request to the appropriate service"""
        
        # Validate service exists
        service_name = self._validate_service(service)
        
        # Build service URL
        service_url = self._build_service_url(service_name, route)
        
        # Forward the request
        return self._forward_request(service_url, method, data, headers)
    
    def _validate_service(self, service):
        """Validate that the requested service exists"""
        service = service.lower()
        if service not in self.services:
            self.logger.warning(f"Service not found: {service}")
            raise ValueError(f"Service '{service}' not found")
        return service
    
    def _build_service_url(self, service, route):
        """Build the complete service URL"""
        return f"{self.services[service]}/{route}"
    
    def _forward_request(self, service_url, method, data, headers=None):
        """Forward the request to the target service"""
        try:
            
            # Prepare headers
            if headers is None:
                headers = {}
            
            # Make the request
            resp = requests.request(
                method=method,
                url=service_url,
                headers=headers,
                data=data,
                timeout=30
            )
            
            # Create Flask response
            response = Response(
                resp.content,
                status=resp.status_code,
                headers=dict(resp.headers)
            )
            
            return response
            
        except requests.RequestException as e:
            self.logger.error(f"Service communication error: {str(e)}")
            raise Exception(f"Service communication error: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error in request forwarding: {str(e)}")
            raise 