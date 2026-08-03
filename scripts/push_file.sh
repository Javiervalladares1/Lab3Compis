#!/bin/bash
set -euo pipefail

# Fail early (without printing the value) if the token is missing.
: "${GITHUB_TOKEN:?GITHUB_TOKEN is not set. Add it to program/.env}"

if [ ! -f repo_full_name.txt ]; then
  echo "Error: repo_full_name.txt not found. Run create_repo.sh first."
  exit 1
fi

FULL_NAME=$(cat repo_full_name.txt)

# Write the HTML to a temp file so we can base64 it cleanly
cat > /tmp/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Hello from the GitHub API</title>
  <style>
    body { font-family: sans-serif; background: #0f172a; color: #e2e8f0;
           display: flex; align-items: center; justify-content: center;
           height: 100vh; margin: 0; text-align: center; }
    h1 { color: #4ade80; }
    p  { opacity: .7; max-width: 500px; }
  </style>
</head>
<body>
  <div>
    <h1>Pushed via the GitHub API</h1>
    <p>This file was created using <code>curl</code> — no git clone, no GUI, just a REST call to the GitHub Contents API.</p>
  </div>
</body>
</html>
EOF

CONTENT_B64=$(base64 -w 0 /tmp/index.html)

echo "[*] Pushing index.html to $FULL_NAME via GitHub Contents API..."

RESPONSE=$(curl -s -X PUT "https://api.github.com/repos/$FULL_NAME/contents/index.html" \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  -d "$(jq -n \
    --arg msg "Add index.html via GitHub API" \
    --arg content "$CONTENT_B64" \
    '{message: $msg, content: $content}')")

FILE_URL=$(echo "$RESPONSE" | jq -r '.content.html_url')
echo "[✓] File pushed: $FILE_URL"
echo ""
echo "[*] Next step: run deploy_to_vercel.sh"
