from flask import Flask, request, jsonify
import os
import logging
import time
import uuid

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock API keys
API_KEYS = {
    'mock-oggo-key': 'valid',
    'mock-hubspot-key': 'valid'
}

# Simple token storage
oauth_tokens = {
    'request_tokens': {},  # token -> { secret, client }
    'access_tokens': {}    # token -> { secret, client }
}

# Mock data - contacts
contacts = [
    { 
        'id': '1', 
        'first_name': 'aymene', 
        'last_name': 'haloui', 
        'email': 'john@example.com',
        'phone': '+1234567890',
        'company': 'Acme Inc',
        'created_at': '2023-01-15T10:30:00Z',
        'updated_at': '2023-04-20T14:15:00Z'
    },
    { 
        'id': '2', 
        'first_name': 'abd1',
        'last_name': 'rabiai', 
        'email': 'jane@example.com',
        'phone': '+1987654321',
        'company': 'XYZ Corp',
        'created_at': '2023-02-20T08:45:00Z',
        'updated_at': '2023-04-15T11:30:00Z'
    },
    { 
        'id': '3', 
        'first_name': 'youness', 
        'last_name': 'sabr', 
        'email': 'alice@example.com',
        'phone': '+1122334455',
        'company': 'Tech Solutions',
        'created_at': '2023-03-10T16:20:00Z',
        'updated_at': '2023-04-10T09:45:00Z'
    }
]

# Mock data - projects
projects = [
    {
        'id': 'proj_1',
        'name': 'Website Redesign',
        'description': 'Complete website redesign for Q2',
        'status': 'in_progress',
        'start_date': '2023-01-15',
        'end_date': '2023-06-30',
        'budget': 50000
    },
    {
        'id': 'proj_2', 
        'name': 'Mobile App Development',
        'description': 'New mobile app for customer portal',
        'status': 'planning',
        'start_date': '2023-03-01',
        'end_date': '2023-12-31',
        'budget': 120000
    },
    {
        'id': 'proj_3',
        'name': 'Database Migration',
        'description': 'Migrate legacy database to cloud',
        'status': 'completed',
        'start_date': '2022-09-01',
        'end_date': '2023-02-28',
        'budget': 75000
    }
]

# Authorization middleware - commented out for development
# @app.before_request
# def check_auth():
#     """Simple authorization check"""
#     # Skip auth for development
#     pass

# OAuth endpoints
@app.route('/oauth/request_token', methods=['POST'])
def request_token():
    """Simple OAuth 1.0 request token endpoint"""
    # Generate token
    token = f"rt_{uuid.uuid4().hex[:8]}"
    secret = f"rs_{uuid.uuid4().hex[:12]}"
    
    # Store token
    oauth_tokens['request_tokens'][token] = {
        'secret': secret,
        'created_at': time.time()
    }
    
    logger.info(f"Created request token: {token}")
    return f"oauth_token={token}&oauth_token_secret={secret}&oauth_callback_confirmed=true"

@app.route('/oauth/authorize', methods=['GET'])
def authorize():
    """OAuth 1.0 authorize endpoint"""
    token = request.args.get('oauth_token')
    
    if token not in oauth_tokens['request_tokens']:
        return jsonify({'error': 'Invalid token'}), 400
    
    # Generate verifier
    verifier = f"v_{uuid.uuid4().hex[:8]}"
    oauth_tokens['request_tokens'][token]['verifier'] = verifier
    
    logger.info(f"Authorized token: {token} with verifier: {verifier}")
    return f"<h1>Authorized!</h1><p>Your verifier is: {verifier}</p>"

@app.route('/oauth/access_token', methods=['POST'])
def access_token():
    """OAuth 1.0 access token endpoint"""
    # In a real implementation, we would verify the request token and verifier
    # For simplicity, we'll just generate a new token
    
    token = f"at_{uuid.uuid4().hex[:8]}"
    secret = f"as_{uuid.uuid4().hex[:12]}"
    
    # Store token
    oauth_tokens['access_tokens'][token] = {
        'secret': secret,
        'created_at': time.time()
    }
    
    logger.info(f"Created access token: {token}")
    return f"oauth_token={token}&oauth_token_secret={secret}"

# Health check
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'service': 'mock-external-apis'})

# ===== OGGO API ROUTES =====

# Contacts endpoints
@app.route('/contacts', methods=['GET'])
def get_contacts():
    """Get all contacts"""
    logger.info('Oggo API: GET /contacts')
    return jsonify(contacts)

@app.route('/contacts', methods=['POST'])
def create_contact():
    """Create a new contact"""
    logger.info('Oggo API: POST /contacts')
    new_contact = request.json
    new_contact['id'] = str(len(contacts) + 1)
    contacts.append(new_contact)
    return jsonify(new_contact), 201

@app.route('/contacts/<contact_id>', methods=['GET'])
def get_contact(contact_id):
    """Get a specific contact by ID"""
    contact = next((c for c in contacts if c['id'] == contact_id), None)
    if contact:
        return jsonify(contact)
    else:
        return jsonify({'error': 'Contact not found'}), 404

@app.route('/contacts/<contact_id>', methods=['PUT'])
def update_contact(contact_id):
    """Update an existing contact"""
    logger.info(f'Oggo API: PUT /contacts/{contact_id}')
    contact_index = next((i for i, c in enumerate(contacts) if c['id'] == contact_id), None)
    
    if contact_index is None:
        return jsonify({'error': 'Contact not found'}), 404
        
    # Update contact
    updated_data = request.json
    updated_contact = {**contacts[contact_index], **updated_data}
    updated_contact['updated_at'] = time.strftime('%Y-%m-%dT%H:%M:%SZ')
    contacts[contact_index] = updated_contact
    
    return jsonify(updated_contact)

# Projects endpoints
@app.route('/projects', methods=['GET'])
def get_projects():
    """Get all projects"""
    logger.info('Oggo API: GET /projects')
    return jsonify(projects)

@app.route('/projects', methods=['POST'])
def create_project():
    """Create a new project"""
    logger.info('Oggo API: POST /projects')
    new_project = request.json
    new_project['id'] = f"proj_{len(projects) + 1}"
    new_project['created_at'] = time.strftime('%Y-%m-%dT%H:%M:%SZ')
    new_project['updated_at'] = time.strftime('%Y-%m-%dT%H:%M:%SZ')
    projects.append(new_project)
    return jsonify(new_project), 201

@app.route('/projects/<project_id>', methods=['GET'])
def get_project(project_id):
    """Get a specific project by ID"""
    project = next((p for p in projects if p['id'] == project_id), None)
    if project:
        return jsonify(project)
    else:
        return jsonify({'error': 'Project not found'}), 404

@app.route('/projects/<project_id>', methods=['PUT'])
def update_project(project_id):
    """Update an existing project"""
    logger.info(f'Oggo API: PUT /projects/{project_id}')
    project_index = next((i for i, p in enumerate(projects) if p['id'] == project_id), None)
    
    if project_index is None:
        return jsonify({'error': 'Project not found'}), 404
        
    # Update project
    updated_data = request.json
    updated_project = {**projects[project_index], **updated_data}
    updated_project['updated_at'] = time.strftime('%Y-%m-%dT%H:%M:%SZ')
    projects[project_index] = updated_project
    
    return jsonify(updated_project)

# ===== HUBSPOT API ROUTES =====

# Contacts (HubSpot format)
@app.route('/crm/v3/objects/contacts/batch/create', methods=['POST'])
def create_hubspot_contacts():
    """Create contacts in HubSpot format"""
    logger.info('HubSpot API: POST /crm/v3/objects/contacts/batch/create')
    
    try:
        # Get the input data
        inputs = request.json.get('inputs', [])
        results = []

        # Process each contact
        for i, contact_data in enumerate(inputs):
            properties = contact_data.get('properties', {})
            result = {
                'id': f"1000{i}",
                'properties': properties,
                'createdAt': '2025-01-30T10:00:00.000Z',
                'updatedAt': '2025-01-30T10:00:00.000Z'
            }
            results.append(result)
        
        logger.info(f"✅ Successfully created {len(results)} contacts in HubSpot")
        
        return jsonify({
            'results': results,
            'status': 'COMPLETE'
        })
        
    except Exception as e:
        logger.error(f"Error in HubSpot contacts mock: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Deals (Projects in HubSpot format)
@app.route('/crm/v3/objects/deals/batch/create', methods=['POST'])
def create_hubspot_deals():
    """Create deals (projects) in HubSpot format"""
    logger.info('HubSpot API: POST /crm/v3/objects/deals/batch/create')
    
    try:
        # Get the input data
        inputs = request.json.get('inputs', [])
        results = []

        # Process each project/deal
        for i, deal_data in enumerate(inputs):
            properties = deal_data.get('properties', {})
            result = {
                'id': f"2000{i}",  # Deal IDs start with 2000
                'properties': properties,
                'createdAt': '2025-01-30T10:00:00.000Z',
                'updatedAt': '2025-01-30T10:00:00.000Z'
            }
            results.append(result)
        
        logger.info(f"✅ Successfully created {len(results)} deals in HubSpot")
        
        return jsonify({
            'results': results,
            'status': 'COMPLETE'
        })
        
    except Exception as e:
        logger.error(f"Error in HubSpot deals mock: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/crm/v3/objects/contacts', methods=['GET'])
def get_oggo_contacts():
    """Get contacts in HubSpot format"""
    logger.info('HubSpot API: GET /crm/v3/objects/contacts')
    
    # Transform local contacts to HubSpot format
    hubspot_contacts = []
    for contact in contacts:
        # Handle different formats of contacts (from Oggo vs from HubSpot)
        if 'properties' in contact:
            # Already in HubSpot format
            hubspot_contacts.append(contact)
        else:
            # Convert from Oggo format to HubSpot format
            hubspot_contact = {
                'id': contact['id'],
                'properties': {
                    'firstname': contact.get('first_name', ''),
                    'lastname': contact.get('last_name', ''),
                    'email': contact.get('email', ''),
                    'phone': contact.get('phone', ''),
                    'company': contact.get('company', ''),
                    'created_date': contact.get('created_at', ''),
                    'last_modified_date': contact.get('updated_at', '')
                }
            }
            hubspot_contacts.append(hubspot_contact)
    
    return jsonify({
        'results': hubspot_contacts
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    
    # Print available endpoints
    logger.info('Mock API server running at http://localhost:%s', port)
    logger.info('Available endpoints:')
    logger.info('  - GET /health')
    logger.info('  - GET /contacts')
    logger.info('  - POST /contacts')
    logger.info('  - GET /contacts/<id>')
    logger.info('  - PUT /contacts/<id>')
    logger.info('  - GET /projects')
    logger.info('  - POST /projects')
    logger.info('  - GET /projects/<id>')
    logger.info('  - PUT /projects/<id>')
    logger.info('  - GET /crm/v3/objects/contacts')
    logger.info('  - POST /crm/v3/objects/contacts/batch/create')
    logger.info('  - POST /crm/v3/objects/deals/batch/create')
    logger.info('  - POST /oauth/request_token')
    logger.info('  - GET /oauth/authorize')
    logger.info('  - POST /oauth/access_token')
    
    app.run(host='0.0.0.0', port=port, debug=True)