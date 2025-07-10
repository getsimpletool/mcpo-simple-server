#!/bin/bash

# Test script for dynamic tools API endpoints
# This script tests both public and user-specific tools OpenAPI endpoints

# Configuration
BASE_URL="http://192.168.1.99:8000"
USERNAME="azdolinski"

# Test token - replace with a valid JWT token for testing
# In a real environment, you would get this from an authentication endpoint
TEST_TOKEN="st-ffffffff-eeee-dddd-cccc-bbbbbbbbbbbb-mniaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaam=="


# Test public tools endpoint (should be accessible without authentication)
echo "\n===== Testing Public Tools OpenAPI Endpoint ====="
echo "GET $BASE_URL/api/v1/public/tools/openapi.json"
curl -s "$BASE_URL/api/v1/public/tools/openapi.json" | jq '.'


# Test user-specific tools endpoint (requires authentication)
echo "\n===== Testing User-Specific Tools OpenAPI Endpoint ====="
echo "GET $BASE_URL/api/v1/user/tools/openapi.json"
curl -s -H "Authorization: Bearer $TEST_TOKEN" "$BASE_URL/api/v1/user/tools/openapi.json" | jq '.'

echo "\nTests completed."
