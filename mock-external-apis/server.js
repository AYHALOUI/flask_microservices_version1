const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const morgan = require('morgan');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(bodyParser.json());
app.use(morgan('dev'));

// Mock API keys
const API_KEYS = {
  'mock-oggo-key': 'valid',
  'mock-hubspot-key': 'valid'
};

// Authorization middleware
function checkApiKey(req, res, next) {
  // Skip auth check for OPTIONS requests (preflight CORS)
  if (req.method === 'OPTIONS') {
    return next();
  }

  // Skip auth for health check
  if (req.path === '/health') {
    return next();
  }

  // Extract the authorization header
  const authHeader = req.headers.authorization || '';
  const apiKeyHeader = req.headers['x-api-key'] || '';
  
  // Check Bearer token
  if (authHeader.startsWith('Bearer ')) {
    const token = authHeader.substring(7);
    if (API_KEYS[token] === 'valid') {
      return next();
    }
  }
  
  // Check API key
  if (API_KEYS[apiKeyHeader] === 'valid') {
    return next();
  }
  
  // If no valid authorization found
  console.log('Unauthorized request:', {
    path: req.path,
    method: req.method,
    authHeader,
    apiKeyHeader
  });
  
  res.status(401).json({ 
    error: 'Unauthorized', 
    message: 'Invalid API key or token',
    timestamp: new Date().toISOString()
  });
}

// Apply authorization to all routes except health check
app.use(checkApiKey);

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'mock-external-apis' });
});

// Mock data
const contacts = [
  { 
    id: '1', 
    first_name: 'aymene01', 
    last_name: 'haloui01', 
    email: 'john@example.com',
    phone: '+1234567890',
    company: 'Acme Inc',
  },
  { 
    id: '2', 
    first_name: 'haloui1', 
    last_name: 'rabiai', 
    email: 'jane@example.com',
    phone: '+1987654321',
    company: 'XYZ Corp',
  },
  // { 
  //   id: '3', 
  //   first_name: 'haloui2', 
  //   last_name: 'sabr', 
  //   email: 'alice@example.com',
  //   phone: '+1122334455',
  //   company: 'Tech Solutions',
  // }
];

// Mock Oggo API
app.get('/contacts', (req, res) => {
  console.log('Oggo API: GET /contacts');
  res.json(contacts);
});

app.get('/contacts/:id', (req, res) => {
  const contact = contacts.find(c => c.id === req.params.id);
  if (contact) {
    res.json(contact);
  } else {
    res.status(404).json({ error: 'Contact not found' });
  }
});

app.post('/contacts', (req, res) => {
  console.log('Oggo API: POST /contacts', req.body);
  const newContact = req.body;
  newContact.id = String(contacts.length + 1);
  newContact.created_at = new Date().toISOString();
  newContact.updated_at = new Date().toISOString();
  contacts.push(newContact);
  res.status(201).json(newContact);
});

app.put('/contacts/:id', (req, res) => {
  const contactIndex = contacts.findIndex(c => c.id === req.params.id);
  if (contactIndex >= 0) {
    const updatedContact = { ...contacts[contactIndex], ...req.body };
    updatedContact.updated_at = new Date().toISOString();
    contacts[contactIndex] = updatedContact;
    res.json(updatedContact);
  } else {
    res.status(404).json({ error: 'Contact not found' });
  }
});

app.post('/crm/v3/objects/contacts/batch/create', (req, res) => {
  console.log('HubSpot API: POST /crm/v3/objects/contacts/batch/create', req.body);
  
  // Store the contacts with their original property names
  const newContacts = req.body.inputs.map((input, index) => {
    // Generate a new contact with the properties as provided
    return {
      id: String(contacts.length + index + 1),
      properties: input.properties  // Keep exact same property structure
    };
  });
  
  // Add these to our stored contacts for retrieval later
  // You'd need to modify your contacts storage to handle this format
  newContacts.forEach(contact => {
    // Add to your stored contacts with the exact same properties structure
    contacts.push(contact);
  });
  
  res.json({
    status: 'success',
    results: newContacts
  });
});

// For retrieving contacts - return them exactly as stored
app.get('/crm/v3/objects/contacts', (req, res) => {
  console.log('HubSpot API: GET /crm/v3/objects/contacts');
  
  res.json({
    results: contacts
  });
});

// Start the server
app.listen(PORT, () => {
  console.log(`Mock API server running at http://localhost:${PORT}`);
  console.log('Available endpoints:');
  console.log('  - GET /health');
  console.log('  - GET /contacts');
  console.log('  - GET /contacts/:id');
  console.log('  - POST /contacts');
  console.log('  - PUT /contacts/:id');
  console.log('  - GET /crm/v3/objects/contacts');
  console.log('  - POST /crm/v3/objects/contacts/batch/create');
});