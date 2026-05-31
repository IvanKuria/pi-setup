#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${PI_BOB_PROXY_URL:-http://127.0.0.1:${PI_BOB_PROXY_PORT:-4010}}"
LOCAL_KEY="${PI_BOB_PROXY_KEY:-pi-bob-local}"
MODEL="${1:-bob-best}"
PROMPT="${2:-Say hello in one sentence.}"
TIMEOUT="${PI_BOB_TEST_TIMEOUT:-60}"

need() {
  command -v "$1" >/dev/null 2>&1 || { echo "Missing required command: $1" >&2; exit 2; }
}
need curl

if command -v python3 >/dev/null 2>&1; then
  JSON_PRETTY=(python3 -m json.tool)
else
  JSON_PRETTY=(cat)
fi

echo "== pi IBM Bob connector smoke test =="
echo "Base URL: $BASE_URL"
echo "Model:    $MODEL"
echo

echo "[1/4] Health"
if ! curl -fsS --max-time 5 "$BASE_URL/health" | "${JSON_PRETTY[@]}"; then
  cat >&2 <<EOF

Health check failed. Is the connector running?

  export BOBSHELL_API_KEY='<your_bob_api_key>'
  ~/.pi/ibm-bob/start.sh
EOF
  exit 1
fi

echo
echo "[2/4] Local OpenAI-compatible model list"
curl -fsS --max-time 10 \
  -H "Authorization: Bearer $LOCAL_KEY" \
  "$BASE_URL/v1/models" | "${JSON_PRETTY[@]}" || {
    echo "Model list failed. Check PI_BOB_PROXY_KEY/local auth." >&2
    exit 1
  }

echo
echo "[3/4] Native Bob model-info diagnostic"
MODEL_INFO_TMP="$(mktemp)"
HTTP_CODE="$({ curl -sS --max-time 30 \
  -H "Authorization: Bearer $LOCAL_KEY" \
  -o "$MODEL_INFO_TMP" \
  -w '%{http_code}' \
  "$BASE_URL/bob/model-info" || true; } 2>/tmp/pi-bob-test-model-info.err)"
echo "HTTP $HTTP_CODE"
if [[ "$HTTP_CODE" == 2* ]]; then
  "${JSON_PRETTY[@]}" < "$MODEL_INFO_TMP" || cat "$MODEL_INFO_TMP"
else
  echo "Native model-info failed; this usually means Bob rejected auth/profile/model-info."
  echo "Response body:"
  cat "$MODEL_INFO_TMP" || true
  echo
  echo "curl stderr:"
  cat /tmp/pi-bob-test-model-info.err || true
fi
rm -f "$MODEL_INFO_TMP"

echo
echo "[4/4] Chat completion"
CHAT_BODY="$(mktemp)"
python3 - "$MODEL" "$PROMPT" > "$CHAT_BODY" <<'PY'
import json, sys
model, prompt = sys.argv[1], sys.argv[2]
print(json.dumps({
    "model": model,
    "messages": [{"role": "user", "content": prompt}],
}))
PY
CHAT_OUT="$(mktemp)"
CHAT_ERR="$(mktemp)"
HTTP_CODE="$({ curl -sS --max-time "$TIMEOUT" \
  -H "Authorization: Bearer $LOCAL_KEY" \
  -H 'Content-Type: application/json' \
  -o "$CHAT_OUT" \
  -w '%{http_code}' \
  -d @"$CHAT_BODY" \
  "$BASE_URL/v1/chat/completions" || true; } 2>"$CHAT_ERR")"
echo "HTTP $HTTP_CODE"
if [[ "$HTTP_CODE" == 2* ]]; then
  "${JSON_PRETTY[@]}" < "$CHAT_OUT" || cat "$CHAT_OUT"
  echo
  echo "[5/5] Streaming chat compatibility"
  STREAM_BODY="$(mktemp)"
  python3 - "$MODEL" "$PROMPT" > "$STREAM_BODY" <<'PY'
import json, sys
model, prompt = sys.argv[1], sys.argv[2]
print(json.dumps({
    "model": model,
    "stream": True,
    "messages": [{"role": "user", "content": prompt}],
}))
PY
  if curl -fsS --max-time "$TIMEOUT" \
    -H "Authorization: Bearer $LOCAL_KEY" \
    -H 'Content-Type: application/json' \
    -d @"$STREAM_BODY" \
    "$BASE_URL/v1/chat/completions" | tee /tmp/pi-bob-test-stream.out | grep -q 'data: \[DONE\]'; then
    echo
    echo "PASS: connector can complete non-streaming and streaming chat requests."
  else
    echo "FAIL: streaming compatibility check failed." >&2
    cat /tmp/pi-bob-test-stream.out 2>/dev/null || true
    rm -f "$STREAM_BODY"
    exit 1
  fi
  rm -f "$STREAM_BODY"
else
  echo "FAIL: chat completion failed or timed out."
  echo "Response body:"
  cat "$CHAT_OUT" || true
  echo
  echo "curl stderr:"
  cat "$CHAT_ERR" || true
  echo
  cat >&2 <<EOF
Next checks:
- Confirm start.sh terminal exported BOBSHELL_API_KEY before starting.
- Prefer an IBM Bob Inference API key.
- Look at the connector terminal logs for the matching POST /v1/chat/completions request.
EOF
  rm -f "$CHAT_BODY" "$CHAT_OUT" "$CHAT_ERR"
  exit 1
fi
rm -f "$CHAT_BODY" "$CHAT_OUT" "$CHAT_ERR"
