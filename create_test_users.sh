#!/bin/bash

# Get port from environment variable or default to 8000
PORT=${PORT:-8000}

# Function to check HTTP status and handle errors
check_status() {
  local status=$1
  local operation=$2
  local exit_on_error=${3:-true}
  
  if [[ $status -lt 200 || $status -ge 300 ]]; then
    echo "Error: $operation failed with HTTP status $status"
    if [[ "$exit_on_error" == "true" ]]; then
      echo "Exiting script due to critical error."
      exit 1
    fi
    return 1
  fi
  return 0
}

# Create first user
echo "Creating first user..."
RESPONSE=$(curl -s -w "\n%{http_code}" -X 'POST' \
  "http://localhost:$PORT/users/" \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "name": "Billy Herrington",
  "email": "billy@example.com",
  "password": "12345678"
}')

HTTP_STATUS=$(echo "$RESPONSE" | tail -n1)
BILLY_RESPONSE=$(echo "$RESPONSE" | sed '$ d')

check_status "$HTTP_STATUS" "Creating Billy user"

# Extract Billy's ID
BILLY_ID=$(echo $BILLY_RESPONSE | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
echo "Created user Billy with ID: $BILLY_ID"

echo -e "\n"

# Create second user
echo "Creating second user..."
RESPONSE=$(curl -s -w "\n%{http_code}" -X 'POST' \
  "http://localhost:$PORT/users/" \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "name": "Van Darkholme",
  "email": "van@example.com",
  "password": "12345678"
}')

HTTP_STATUS=$(echo "$RESPONSE" | tail -n1)
VAN_RESPONSE=$(echo "$RESPONSE" | sed '$ d')

check_status "$HTTP_STATUS" "Creating Van user"

# Extract Van's ID
VAN_ID=$(echo $VAN_RESPONSE | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
echo "Created user Van with ID: $VAN_ID"

echo -e "\n\nUsers creation completed."

# Authorize first user
echo -e "\nAuthorizing first user..."
RESPONSE=$(curl -s -w "\n%{http_code}" -X 'POST' \
  "http://localhost:$PORT/users/login" \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "email": "billy@example.com",
  "password": "12345678"
}')

HTTP_STATUS=$(echo "$RESPONSE" | tail -n1)
AUTH_RESPONSE=$(echo "$RESPONSE" | sed '$ d')

check_status "$HTTP_STATUS" "Authorizing Billy"

BILLY_TOKEN=$(echo $AUTH_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
echo "Billy's token: $BILLY_TOKEN"

# Authorize second user
echo -e "\nAuthorizing second user..."
RESPONSE=$(curl -s -w "\n%{http_code}" -X 'POST' \
  "http://localhost:$PORT/users/login" \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "email": "van@example.com",
  "password": "12345678"
}')

HTTP_STATUS=$(echo "$RESPONSE" | tail -n1)
AUTH_RESPONSE=$(echo "$RESPONSE" | sed '$ d')

check_status "$HTTP_STATUS" "Authorizing Van"

VAN_TOKEN=$(echo $AUTH_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
echo "Van's token: $VAN_TOKEN"

echo -e "\nAuthorization completed."

# Create a chat between Billy and Van
echo -e "\nCreating a chat between Billy and Van..."
RESPONSE=$(curl -s -w "\n%{http_code}" -X 'POST' \
  "http://localhost:$PORT/chats/" \
  -H 'accept: application/json' \
  -H "Authorization: Bearer $BILLY_TOKEN" \
  -H 'Content-Type: application/json' \
  -d "{
  \"name\": \"Gachi Discussion\",
  \"type\": \"personal\",
  \"participant_ids\": [
    $BILLY_ID,
    $VAN_ID
  ],
  \"creator_id\": $BILLY_ID
}")

HTTP_STATUS=$(echo "$RESPONSE" | tail -n1)
CHAT_RESPONSE=$(echo "$RESPONSE" | sed '$ d')

check_status "$HTTP_STATUS" "Creating chat"

# Extract chat ID
CHAT_ID=$(echo $CHAT_RESPONSE | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
echo "Created chat with ID: $CHAT_ID"
echo "Chat details: $CHAT_RESPONSE"

echo -e "\nSetup completed successfully!"

# Test chat history endpoint (optional)
echo -e "\nTesting chat history endpoint..."
RESPONSE=$(curl -s -w "\n%{http_code}" -X 'GET' \
  "http://localhost:$PORT/chats/history/$CHAT_ID?limit=10&offset=0" \
  -H 'accept: application/json' \
  -H "Authorization: Bearer $BILLY_TOKEN")

HTTP_STATUS=$(echo "$RESPONSE" | tail -n1)
HISTORY_RESPONSE=$(echo "$RESPONSE" | sed '$ d')

if check_status "$HTTP_STATUS" "Retrieving chat history" "false"; then
  echo "Chat history: $HISTORY_RESPONSE"
else
  echo "Chat history retrieval failed, but continuing with script."
fi

echo -e "\n----------------------------------------"
echo -e "WEBSOCKET CONNECTION INFORMATION"
echo -e "----------------------------------------"
echo -e "WebSocket URL: ws://localhost:$PORT/ws/chat/$CHAT_ID"
echo -e "\nAuthorization tokens:"
echo -e "Billy's token: $BILLY_TOKEN"
echo -e "Van's token: $VAN_TOKEN"
echo -e "\nConnect to the WebSocket with one of these tokens in the header:"
echo -e "Authorization: Bearer TOKEN"
echo -e "----------------------------------------"
echo -e "\nChat History API:"
echo -e "GET http://localhost:$PORT/chats/history/$CHAT_ID?limit=10&offset=0"
echo -e "Authorization: Bearer TOKEN"
echo -e "----------------------------------------"
