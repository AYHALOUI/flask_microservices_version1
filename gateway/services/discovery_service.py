import logging
import os
import docker

class DiscoveryService:
    """Service class for discovering and managing service endpoints"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def initialize_services(self):
        """Initialize the services dictionary from Docker or environment variables"""
        services = {}
        # Try Docker discovery first
        try:
            services = self._discover_services_via_docker()
        except Exception as e:
            self.logger.error(f"Docker service discovery failed: {str(e)}")
        
        if not services:
            services = self._get_services_from_env()        
        return services
    
    def _discover_services_via_docker(self):
        """Discover services using Docker API"""
        try:
            client = docker.from_env()
            services = {}
            
            containers = client.containers.list()
            
            for container in containers:
                # Check if container is part of current Docker Compose project
                labels = container.labels
                if 'com.docker.compose.service' in labels:
                    service_name = labels['com.docker.compose.service']
                    
                    # Get the container's network IP
                    networks = container.attrs['NetworkSettings']['Networks']
                    
                    for network_name, network_info in networks.items():
                        if 'microservices_network' in network_name:
                            ip = network_info['IPAddress']
                            
                            # Make the service name simpler - remove "service_" prefix for easier access
                            simplified_name = service_name
                            if service_name.startswith('service_'):
                                simplified_name = service_name[8:]  # Remove "service_" prefix
                            
                            services[simplified_name.lower()] = f'http://{ip}:5000'
                            # Also add the original name to avoid confusion
                            services[service_name.lower()] = f'http://{ip}:5000'
                            break
            
            return services
            
        except Exception as e:
            return {}
    
    def _get_services_from_env(self):
        """Get service URLs from environment variables"""
        services = {}
        for key, value in os.environ.items():
            if key.startswith('SERVICE_'):
                service_name = key[8:].lower()  # Remove 'SERVICE_' prefix
                services[service_name] = value
        return services