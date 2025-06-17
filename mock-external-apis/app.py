from flask import Flask, request, jsonify
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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


# Contacts endpoints
@app.route('/contacts', methods=['GET'])
def get_contacts():
    """Get all contacts"""
    logger.info('Oggo API: GET /contacts')
    return jsonify(contacts)



# Projects endpoints
@app.route('/projects', methods=['GET'])
def get_projects():
    """Get all projects"""
    logger.info('Oggo API: GET /projects')
    return jsonify(projects)


# ===== HUBSPOT API ROUTES =====
# Contacts (HubSpot format)
@app.route('/crm/v3/objects/contacts/batch/create', methods=['POST'])
def create_hubspot_contacts():
    """Create contacts in HubSpot format""" 
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
        return jsonify({
            'results': results,
            'status': 'COMPLETE'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Projects in HubSpot
@app.route('/crm/v3/objects/deals/batch/create', methods=['POST'])
def create_hubspot_deals():
    """Create deals (projects) in HubSpot format"""
    logger.info('HubSpot API: POST /crm/v3/objects/deals/batch/create')
    
    try:
        # Get the input data
        inputs = request.json.get('inputs', [])
        results = []

        for i, deal_data in enumerate(inputs):
            properties = deal_data.get('properties', {})
            result = {
                'id': f"2000{i}",  # Deal IDs start with 2000
                'properties': properties,
                'createdAt': '2025-01-30T10:00:00.000Z',
                'updatedAt': '2025-01-30T10:00:00.000Z'
            }
            results.append(result)        
        return jsonify({
            'results': results,
            'status': 'COMPLETE'
        })
        
    except Exception as e:
        logger.error(f"Error in HubSpot deals mock: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)