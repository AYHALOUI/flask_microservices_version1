import logging
import os
import requests
import json
import time

class ProjectService:
    """Service class for handling project operations"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.service_transform = os.environ.get('TRANSFORM_SERVICE_URL')
        self.service_connect = os.environ.get('SERVICE_CONNECT')

    def sync_projects(self, params):
        """Main method to sync projects from Oggo to HubSpot"""
        
        try:
            # Step 1: Fetch projects from Oggo
            self.logger.info("=== STEP 1: FETCHING PROJECTS FROM OGGO ===")
            projects = self._fetch_projects_from_oggo(params)
            self.logger.info(f"Retrieved {len(projects)} projects from Oggo")
            
            if not projects:
                return {"message": "No projects found to sync"}
            
            # Step 2: Transform projects
            self.logger.info("=== STEP 2: TRANSFORMING PROJECTS ===")
            transformed_data = self._transform_projects(projects)
            self.logger.info(f"Transformed data: {transformed_data}")
            
            # Step 3: Send to HubSpot
            self.logger.info("=== STEP 3: SENDING TO HUBSPOT ===")
            hubspot_response = self._send_to_hubspot(transformed_data)
            self.logger.info(f"HubSpot response: {hubspot_response}")
            
            return {
                "status": "success",
                "message": f"Successfully processed {len(projects)} projects",
                "data": transformed_data,
                "hubspot_response": hubspot_response,
            }
            
        except Exception as e:
            self.logger.error(f"Exception caught: {str(e)}")
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
            self.logger.error(error_msg)
            raise Exception(error_msg)
    
    def _build_oggo_request(self):
        """Build the request configuration for Oggo API"""
        # For now, we'll use the same mock data as contacts
        # In real implementation, this would be a different endpoint
        url = f"{self.service_connect}/proxy/oggo/projects"
        headers = {"Content-Type": "application/json"}
        return url, headers

    def _transform_projects(self, projects):
        """Transform projects using the transformation service"""
        url, headers, payload = self._build_transform_request(projects)

        try:
            self.logger.info(f"Transform request payload: {payload}")
        
            response = requests.post(url, headers=headers, json=payload)
            self.logger.info(f"Transform response status: {response.status_code}")
            self.logger.info(f"Transform response text: {response.text}")
            
            if response.status_code != 200:
                raise Exception(f"Transform service error: {response.text}")
            
            # Check if response is empty
            if not response.text.strip():
                self.logger.error("Transform service returned empty response")
                return None
                
            transformed_data = response.json()
            return transformed_data
        
        except requests.RequestException as e:
            error_msg = f"Failed to transform projects: {str(e)}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
    
    def _build_transform_request(self, projects):
        """Build the request configuration for Transform service"""
        url = f"{self.service_transform}/transform"
        headers = {"Content-Type": "application/json"}
        payload = {
            "data": projects,
            "entity_type": "project",  # ✅ This will read project_mapping.json
            "mapping_file": "project_mapping.json"
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