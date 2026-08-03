#!/bin/bash
set -euo pipefail

# Fail early (without printing the value) if the token is missing.
: "${VERCEL_TOKEN:?VERCEL_TOKEN is not set. Add it to program/.env}"

PROJECT_NAME="my-portfolio-api-test"

# Write HTML to a temp file
cat > /tmp/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Deployed via the Vercel API</title>
  <style>
    body { font-family: sans-serif; background: #0f172a; color: #e2e8f0;
           display: flex; align-items: center; justify-content: center;
           height: 100vh; margin: 0; text-align: center; }
    h1 { color: #4ade80; }
    p  { opacity: .7; max-width: 500px; }
    code { background: #1e293b; padding: 2px 6px; border-radius: 4px; }
  </style>
</head>
<body>
  <div>
    <h1>Deployed via the Vercel API</h1>
    <p>This page was deployed using <code>curl</code> — no Vercel CLI, no dashboard, just a REST call to the Vercel Deployments API.</p>
  </div>
</body>
</html>
EOF

HTML_CONTENT=$(cat /tmp/index.html)

echo "[*] Calling the Vercel Deployments API directly..."
echo "[*] Project name: $PROJECT_NAME"
echo ""

RESPONSE=$(curl -s -X POST "https://api.vercel.com/v13/deployments" \
  -H "Authorization: Bearer $VERCEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$(jq -n \
    --arg name "$PROJECT_NAME" \
    --arg html "$HTML_CONTENT" \
    '{name: $name, files: [{file: "index.html", data: $html}], projectSettings: {framework: null}, target: "production"}')")

URL=$(echo "$RESPONSE" | jq -r '.url')

if [ "$URL" = "null" ]; then
  echo "Error: $(echo "$RESPONSE" | jq -r '.error.message // .message')"
  exit 1
fi

echo "[✓] Deployed to: https://$URL"
echo ""
echo "[*] This is exactly the same API call your ANTLR compiler will automate in Parte 2."
