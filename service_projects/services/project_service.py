import logging
import os
import requests
import json
from flask import request
from shared.debugger_client import track_api_call, track_error, FlowTracker


class ProjectService:
    """Service class for handling project operations"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.service_transform = os.environ.get('TRANSFORM_SERVICE_URL')
        self.service_connect = os.environ.get('SERVICE_CONNECT')

    def sync_projects(self, params):
        """Main method to sync projects from Oggo to HubSpot - CLEAN VERSION"""
        try:
            request_id = request.headers.get('X-Request-ID') if request else None
            tracker = FlowTracker(request_id)
            
            # Step 1: Track call to connect service for fetching Oggo data
            track_api_call(tracker, "service_projects", "service_connect", "fetch_oggo_projects")

            # Fetch projects from Oggo
            projects = self._fetch_projects_from_oggo(params)
            
            if not projects:
                return {"message": "No projects found to sync"}
            
            # Step 2: Track call to transformer service
            track_api_call(tracker, "service_projects", "service_transformer", "transform_data")

            # Transform projects
            transformed_data = self._transform_projects(projects)
            
            # Step 3: Track call to connect service for sending to HubSpot
            track_api_call(tracker, "service_projects", "service_connect", "send_to_hubspot")

            # Send to HubSpot
            hubspot_response = self._send_to_hubspot(transformed_data)
            
            return {
                "status": "success",
                "message": f"Successfully processed {len(projects)} projects",
                "data": transformed_data,
                "hubspot_response": hubspot_response,
            }
            
        except Exception as e:
            track_error(tracker, "service_projects", str(e), f"Params: {params}")
            raise e

    def _fetch_projects_from_oggo(self, params):
        """Fetch projects from Oggo via proxy service"""
        url, headers = self._build_oggo_request()
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            projects = response.json()
            return projects
        except requests.RequestException as e:
            error_msg = f"Failed to fetch projects from Oggo: {str(e)}"
            raise Exception(error_msg)
    
    def _build_oggo_request(self):
        """Build the request configuration for Oggo API"""
        url = f"{self.service_connect}/proxy/oggo/projects"
        headers = {"Content-Type": "application/json"}
        return url, headers

    def _transform_projects(self, projects):
        """Transform projects using the transformation service"""
        url, headers, payload = self._build_transform_request(projects)

        try:
        
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code != 200:
                raise Exception(f"Transform service error: {response.text}")
            
            # Check if response is empty
            if not response.text.strip():
                return None
                
            transformed_data = response.json()
            return transformed_data
        
        except requests.RequestException as e:
            error_msg = f"Failed to transform projects: {str(e)}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
        
    def load_mapping(self, mapping_file):
        """Load mapping configuration from JSON file"""
        try:
            with open(mapping_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            raise e
    
    def _build_transform_request(self, projects):
        """Build the request configuration for Transform service"""
        url = f"{self.service_transform}/transform"
        headers = {"Content-Type": "application/json"}
        payload = {
            "data": projects,
            "entity_type": "project",  
            "mapping_file": self.load_mapping('./mappings/project_mapping.json')
        }
        return url, headers, payload

    def _send_to_hubspot(self, transformed_data):
        """Send transformed data to HubSpot via connect service"""
        url, headers, payload = self._build_hubspot_request(transformed_data)

        try:
            response = requests.post(url=url, headers=headers, json=payload)
            if response.status_code not in [200, 201]:
                error_msg = f"HubSpot API error: Status code {response.status_code}"
                raise Exception(error_msg)
            
            hubspot_response = response.json()
            return hubspot_response

        except requests.RequestException as e:
            error_msg = f"Failed to sync projects to HubSpot: {str(e)}"
            raise Exception(error_msg)
    
    def _build_hubspot_request(self, transformed_data):
        """Build the request configuration for HubSpot API"""
        # In HubSpot, projects are usually deals
        url = f"{self.service_connect}/proxy/hubspot/crm/v3/objects/deals/batch/create"
        headers = {"Content-Type": "application/json"}
        hubspot_projects = transformed_data.get('projects', [])
        payload = {
            "inputs": [
                {
                    "properties": project.get('properties', {})
                } for project in hubspot_projects
            ]
        }
        return url, headers, payload