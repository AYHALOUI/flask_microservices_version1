
import logging
import os
import requests
import json
import time


class ContactService:
    """Service class for handling contact operations"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.service_transform = os.environ.get('SERVICE_TRANSFORM')
        self.service_connect = os.environ.get('SERVICE_CONNECT')


    def sync_contacts(self, params):
        """Main method to sync contacts from Oggo to HubSpot"""
        
        try:
            # Step 1: Fetch contacts from Oggo
            self.logger.info("=== STEP 1: FETCHING FROM OGGO ===")
            contacts = self._fetch_contacts_from_oggo(params)
            self.logger.info(f"Contacts result: {contacts}")
            self.logger.info(f"Contacts type: {type(contacts)}")
            
            if not contacts:
                return {"message": "No contacts found to sync"}
            
            # Step 2: Transform contacts
            self.logger.info("=== STEP 2: TRANSFORMING CONTACTS ===")
            transformed_data = self._transform_contacts(contacts)
            self.logger.info(f"Transformed data: {transformed_data}")
            self.logger.info(f"Transformed data type: {type(transformed_data)}")
            
            # Step 3: Send to HubSpot
            self.logger.info("=== STEP 3: SENDING TO HUBSPOT ===")
            hubspot_response = self._send_to_hubspot(transformed_data)
            self.logger.info(f"HubSpot response: {hubspot_response}")
            self.logger.info(f"HubSpot response type: {type(hubspot_response)}")
            
            return {
                "status": "success",
                "message": f"Successfully processed {len(contacts)} contacts",
                "data": transformed_data,
                "hubspot_response": hubspot_response,
            }
            
        except Exception as e:
            self.logger.error(f"Exception caught: {str(e)}")
            self.logger.error(f"Exception type: {type(e)}")
            raise e
        



    #============ private Methods ===============
    def _send_to_hubspot(self, transformed_data):
        """Send transformed data to Hubspot via connect service"""
        url, headers, payload = self._build_hubspot_request(transformed_data)

        try:
            response = requests.post(url=url, headers=headers, json=payload)
            if response.status_code != 200:
                error_msg = f"HubSpot API error: Status code {response.status_code}"
            
            hubspot_response = response.json()
            # log_to_debugger("contact", "info", "Successfully sent contacts to HubSpot")
            return hubspot_response

        except requests.RequestException as e:
            error_msg = f"Failed to sync data to Hubspot: {str(e)}"
            raise Exception(error_msg)
    
    def _build_hubspot_request(self, transformed_data):
        """Build the request configuration for HubSpot API"""
        url = f"{self.service_connect}/proxy/hubspot/crm/v3/objects/contacts/batch/create"
        headers = {"Content-Type": "application/json"}
        hubspot_contacts = transformed_data.get('contacts', [])
        payload = {
            "inputs": [
                {
                    "properties": contact.get('properties', {})
                } for contact in hubspot_contacts
            ]
        }
        return url, headers, payload
    


    def _fetch_contacts_from_oggo(self, params):
        """Fetch contacts from oggo via proxy service"""
        url, headers = self._build_oggo_request()
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            contacts = response.json()
            # log_to_debugger("contact", "info", f"Retrieved {len(contacts)} contacts from Oggo")
            return contacts
        except requests.RequestException as e:
            error_msg = f"Failed to fetch contacts from Oggo: {str(e)}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
    
    def _build_oggo_request(self):
        """Build the request configuration from Oggo Api"""
        url = f"{self.service_connect}/proxy/oggo/contacts"
        headers = {"Content-Type": "application/json"}
        return url, headers

    def _transform_contacts(self, contacts):
        """Transform contact using the transformation service"""
        # log_to_debugger("contact", "info", "Sending contacts for transformation", {"count": len(contacts)})
        url, headers, payload = self._build_transfrom_request(contacts)

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
            error_msg = f"Failed to transform contacts: {str(e)}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
    
    def _build_transfrom_request(self, contacts):
        """Build the request configuration for Transform service"""
        url = f"{self.service_transform}/transform"
        headers = {"Content-Type": "application/json"}
        payload = {
            "data": contacts,
            "entity_type": "contact",
            "mapping_file": "contact_mapping.json"
        }
        return url, headers, payload