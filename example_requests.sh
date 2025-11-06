#!/bin/bash

# Example API requests for PNJ Jewelry AI Designer
# Make sure the API is running at http://localhost:8000
# Requires: curl, jq (for JSON parsing)

API_URL="http://localhost:8000"

echo "================================"
echo "PNJ Jewelry AI Designer API Examples"
echo "================================"
echo ""

# 1. Health Check
echo "1. Health Check (no auth required)"
curl -X GET "$API_URL/health" | jq
echo -e "\n"

# 2. Register a new user
echo "2. Register a new user"
TIMESTAMP=$(date +%s)
USER_EMAIL="test_user_${TIMESTAMP}@example.com"

REGISTER_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/users/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$USER_EMAIL\",
    \"password\": \"SecurePassword123!\",
    \"name\": \"Test User\",
    \"gender\": \"female\",
    \"age\": 28,
    \"marital_status\": \"single\",
    \"segment\": \"middle\",
    \"region\": \"south\",
    \"nationality\": \"Vietnamese\"
  }")
echo $REGISTER_RESPONSE | jq
USER_ID=$(echo $REGISTER_RESPONSE | jq -r '.id')
echo "Created user with ID: $USER_ID"
echo -e "\n"

# 3. Login to get access token
echo "3. Login to get access token"
LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/users/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$USER_EMAIL\",
    \"password\": \"SecurePassword123!\"
  }")
echo $LOGIN_RESPONSE | jq
ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')
echo "Access token: ${ACCESS_TOKEN:0:20}..."
echo -e "\n"

# 4. Get current user info
echo "4. Get current user info"
curl -s -X GET "$API_URL/api/v1/users/me" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq
echo -e "\n"

# 5. Create a new conversation
echo "5. Create a new conversation"
CONVERSATION=$(curl -s -X POST "$API_URL/api/v1/conversations" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Custom Engagement Ring Design",
    "description": "Designing a unique engagement ring for proposal"
  }')
echo $CONVERSATION | jq
CONVERSATION_ID=$(echo $CONVERSATION | jq -r '.id')
echo "Created conversation with ID: $CONVERSATION_ID"
echo -e "\n"

# 6. List all conversations
echo "6. List all conversations"
curl -s -X GET "$API_URL/api/v1/conversations" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq
echo -e "\n"

# 7. Chat with the AI assistant
echo "7. Chat with AI assistant"
curl -s -X POST "$API_URL/api/v1/chat" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"conversation_id\": \"$CONVERSATION_ID\",
    \"message\": \"I want to design a modern solitaire engagement ring with a round diamond on white gold. The style should be elegant and timeless. Can you show me some designs?\"
  }" | jq
echo -e "\n"

# 8. Upload an image (if you have an image file)
echo "8. Upload an image (example - will fail if file doesn't exist)"
if [ -f "test_image.jpg" ]; then
  IMAGE_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/images/upload" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -F "file=@test_image.jpg" \
    -F "conversation_id=$CONVERSATION_ID")
  echo $IMAGE_RESPONSE | jq
  IMAGE_ID=$(echo $IMAGE_RESPONSE | jq -r '.id')
  echo "Uploaded image with ID: $IMAGE_ID"
else
  echo "Skipped - test_image.jpg not found"
  IMAGE_ID=""
fi
echo -e "\n"

# 9. Get conversation with messages
echo "9. Get conversation details"
curl -s -X GET "$API_URL/api/v1/conversations/$CONVERSATION_ID" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.id, .title, .messages | length'
echo -e "\n"

# 10. Another chat example - refining design
echo "10. Refine design through chat"
curl -s -X POST "$API_URL/api/v1/chat" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"conversation_id\": \"$CONVERSATION_ID\",
    \"message\": \"I like the design but can you make it more minimalist? Also, I prefer rose gold instead of white gold.\"
  }" | jq '.assistant_message.content'
echo -e "\n"

echo "================================"
echo "Examples completed!"
echo "Visit http://localhost:8000/docs for interactive API documentation"
echo "================================"
