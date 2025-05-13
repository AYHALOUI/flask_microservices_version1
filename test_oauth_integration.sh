#!/bin/bash

# Step 1: Get request token
echo "Getting request token..."
REQUEST_TOKEN_RESPONSE=$(curl -s -X POST http://localhost:3000/oauth/request_token)
echo $REQUEST_TOKEN_RESPONSE

# Extract token from response (debug print)
echo "Attempting to extract from: $REQUEST_TOKEN_RESPONSE"
REQUEST_TOKEN=$(echo $REQUEST_TOKEN_RESPONSE | grep -o 'oauth_token=[^&]*' | cut -d= -f2)
echo "Request token: $REQUEST_TOKEN"

# Step 2: Authorize token
echo -e "\nAuthorizing token..."
AUTH_RESPONSE=$(curl -s "http://localhost:3000/oauth/authorize?oauth_token=$REQUEST_TOKEN")
echo "Authorization response: $AUTH_RESPONSE"

# Extract verifier from response (updated to match "Your verifier is:")
VERIFIER=$(echo $AUTH_RESPONSE | grep -o 'Your verifier is: [^<]*' | cut -d: -f2 | xargs)
echo "Verifier: $VERIFIER"

# Step 3: Get access token
echo -e "\nGetting access token..."
ACCESS_TOKEN_RESPONSE=$(curl -s -X POST "http://localhost:3000/oauth/access_token")
echo "Access token response: $ACCESS_TOKEN_RESPONSE"

# Extract access token
ACCESS_TOKEN=$(echo $ACCESS_TOKEN_RESPONSE | grep -o 'oauth_token=[^&]*' | cut -d= -f2)
echo "Access token: $ACCESS_TOKEN"

# Step 4: Use token for API requests
echo -e "\nTesting API endpoints with OAuth token..."

echo -e "\n1. Get all contacts:"
curl -s -H "Authorization: OAuth oauth_token=\"$ACCESS_TOKEN\"" http://localhost:3000/contacts

echo -e "\n2. Get contact with ID 1:"
curl -s -H "Authorization: OAuth oauth_token=\"$ACCESS_TOKEN\"" http://localhost:3000/contacts/1

echo -e "\n3. Get HubSpot contacts:"
curl -s -H "Authorization: OAuth oauth_token=\"$ACCESS_TOKEN\"" http://localhost:3000/crm/v3/objects/contacts

echo -e "\n4. Create HubSpot contact:"
curl -s -X POST \
  -H "Authorization: OAuth oauth_token=\"$ACCESS_TOKEN\"" \
  -H "Content-Type: application/json" \
  -d '{"inputs":[{"properties":{"firstname":"OAuth","lastname":"Test"}}]}' \
  http://localhost:3000/crm/v3/objects/contacts/batch/create

echo -e "\nOAuth flow test completed!"