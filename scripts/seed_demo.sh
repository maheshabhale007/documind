#!/usr/bin/env bash
set -e

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"

echo "Seeding demo documents into DocuMind..."

for f in sample_docs/*; do
    if [ -f "$f" ]; then
        echo "Uploading $f..."
        curl -s -X POST "$BACKEND_URL/api/v1/documents/upload" \
            -F "file=@$f" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"  -> {data.get('filename')} ({data.get('total_chunks')} chunks)\")
"
    fi
done

echo ""
echo "Seed complete. Open http://localhost:8501 and start asking questions!"
