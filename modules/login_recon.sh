#!/usr/bin/env bash
# modules/login_recon.sh - auto-discover login form on a target
#
# Usage:
#   ./modules/login_recon.sh <base_url_or_path>
#   ./modules/login_recon.sh <base_url> <explicit_login_url>
#
# Output: structured findings on stdout (one finding per line)
# Format: [INFO] key=value pairs, [HIGH] warnings, [LOW] notes
#
# Side effect: writes $RAW/login_page.html and $RAW/login_recon.json with
# the discovered form details.

set -uo pipefail

TARGET="${1:-}"
EXPLICIT_URL="${2:-}"

if [ -z "$TARGET" ]; then
  echo "[CRITICAL] usage: $0 <target> [explicit_login_url]"
  exit 1
fi

# strip scheme + path -> base host
if [[ "$TARGET" =~ ^https?:// ]]; then
  base_no_scheme="${TARGET#http://}"
  base_no_scheme="${base_no_scheme#https://}"
  base_no_scheme="${base_no_scheme%%/*}"
  if [[ "$TARGET" =~ ^https:// ]]; then
    BASE_URL="https://$base_no_scheme"
  else
    BASE_URL="http://$base_no_scheme"
  fi
else
  base_no_scheme="${TARGET%%/*}"
  # localhost / 127.x / ::1 / 0.0.0.0 → http, otherwise https
  if [[ "$base_no_scheme" =~ ^(localhost(:[0-9]+)?$|127\.[0-9]+\.[0-9]+\.[0-9]+(:[0-9]+)?$|::1(:[0-9]+)?$|0\.0\.0\.0(:[0-9]+)?$) ]]; then
    BASE_URL="http://$base_no_scheme"
  else
    BASE_URL="https://$base_no_scheme"
  fi
fi
base="$base_no_scheme"

RAW="${RAW:-.}"
mkdir -p "$RAW"

# Candidate login paths to try (in order of likelihood)
CANDIDATE_PATHS=(
  "/login"
  "/signin"
  "/auth/login"
  "/user/login"
  "/users/sign_in"
  "/wp-login.php"
  "/account/login"
  "/log-in"
  "/session/new"
  "/login.php"
)

# If user gave an explicit URL, try that first
if [ -n "$EXPLICIT_URL" ]; then
  CANDIDATE_PATHS=("$EXPLICIT_URL" "${CANDIDATE_PATHS[@]}")
fi

echo "[INFO] recon: scanning ${BASE_URL} for login forms"

# ----- 1. find login page -----
FOUND_URL=""
FOUND_HTML=""
FOUND_STATUS=""
CANDIDATES_200=""     # URLs that returned 200 but had no form (likely JS SPAs)
CANDIDATES_NOTFOUND="" # URLs that returned 404 or other non-200
TRIES=0

for path in "${CANDIDATE_PATHS[@]}"; do
  # If path is full URL (explicit), use as-is; otherwise join with base
  if [[ "$path" =~ ^https?:// ]]; then
    url="$path"
  else
    url="${BASE_URL}${path}"
  fi

  TRIES=$((TRIES + 1))

  response=$(curl -s -L -o "$RAW/login_page.html" -w "%{http_code}|%{url_effective}|%{content_type}" \
    --max-time 5 --connect-timeout 3 "$url" 2>/dev/null)
  status=$(echo "$response" | cut -d'|' -f1)
  final_url=$(echo "$response" | cut -d'|' -f2)
  ctype=$(echo "$response" | cut -d'|' -f3)

  # Skip non-200 responses quickly
  if [ "$status" != "200" ]; then
    CANDIDATES_NOTFOUND="$CANDIDATES_NOTFOUND $url($status)"
    continue
  fi

  # Require an ACTUAL <form> tag with an input - this is a real HTML login form.
  # Just having the words "sign in" or "login" in the body is not enough
  # (JS SPAs have those in their JS bundles even without a real form).
  if grep -Eqi "<form[^>]*>" "$RAW/login_page.html" && \
     grep -Eqi "<input[^>]*" "$RAW/login_page.html"; then
    FOUND_URL="$url"
    FOUND_HTML="$RAW/login_page.html"
    FOUND_STATUS="$status"
    echo "[INFO] recon: found HTML login form at $url (HTTP $status)"
    break
  fi

  # 200 OK but no form - likely a JS SPA / framework stub page
  CANDIDATES_200="$CANDIDATES_200 $url"
  echo "[INFO] recon: $url returned 200 but no HTML <form> (likely JS SPA)"
done

if [ -z "$FOUND_URL" ]; then
  echo "[HIGH] recon: no HTML login form found after $TRIES attempts"
  if [ -n "$CANDIDATES_200" ]; then
    echo "[LOW] recon: these paths returned HTTP 200 but have no <form> tag (likely JS SPAs):"
    for u in $CANDIDATES_200; do
      echo "[LOW]   - $u"
    done
    echo "[LOW] recon: the site is probably a React/Vue/Angular app that renders the login form client-side."
    echo "[LOW] recon: gray-box HTTP login won't work — use --mode white and paste a cookie."
  else
    echo "[LOW] recon: tried paths: ${CANDIDATE_PATHS[*]}"
    echo "[LOW] recon: provide the login URL manually with --login-url"
  fi

  # persist what we tried for the orchestrator to act on
  cat > "$RAW/login_recon.json" <<EOF
{
  "login_url": "",
  "form_action": "",
  "form_method": "POST",
  "user_field": "",
  "pass_field": "",
  "csrf_field": "",
  "captcha_field": "",
  "twofa_detected": false,
  "spa_candidates": "$CANDIDATES_200",
  "is_spa": $([ -n "$CANDIDATES_200" ] && echo true || echo false)
}
EOF
  exit 2
fi

# ----- 2. parse the form -----
HTML=$(cat "$FOUND_HTML")

# Is there even a <form>?
if ! echo "$HTML" | grep -qi "<form"; then
  echo "[HIGH] recon: page at $FOUND_URL does not contain a <form> element"
  echo "[LOW] recon: may be a JS-rendered SPA - consider --mode white"
  exit 2
fi

# Find form action
form_action=$(echo "$HTML" | grep -oiE '<form[^>]*action=["'\'']?[^"'\'' >]+' | head -1 | sed -E 's/.*action=["'\'']?//')
# form method
form_method=$(echo "$HTML" | grep -oiE '<form[^>]*method=["'\'']?[^"'\'' >]+' | head -1 | sed -E 's/.*method=["'\'']?//I')
[ -z "$form_method" ] && form_method="GET"
[ -z "$form_action" ] && form_action="$FOUND_URL"
# If action is relative, resolve
if [[ ! "$form_action" =~ ^https?:// ]]; then
  if [[ "$form_action" == /* ]]; then
    form_action="${BASE_URL}${form_action}"
  else
    # relative to the login URL directory
    dir="${FOUND_URL%/*}/"
    form_action="${dir}${form_action}"
  fi
fi

echo "[INFO] recon: form action → $form_action"
echo "[INFO] recon: form method → $form_method"

# Find input fields
echo "[INFO] recon: input fields detected:"
echo "$HTML" | grep -oiE '<input[^>]*>' | while IFS= read -r inp; do
  name=$(echo "$inp" | grep -oiE 'name=["'\'']?[^"'\'' >]+' | sed -E 's/.*name=["'\'']?//;s/["'\'' ]*$//' | head -1)
  type=$(echo "$inp" | grep -oiE 'type=["'\'']?[^"'\'' >]+' | sed -E 's/.*type=["'\'']?//;s/["'\'' ]*$//' | head -1)
  [ -z "$name" ] && continue
  echo "[INFO] field: name='$name' type='$type'"
done

# Heuristic field detection
USER_FIELD=""
PASS_FIELD=""
CSRF_FIELD=""
CAPTCHA_FIELD=""

while IFS= read -r inp; do
  name=$(echo "$inp" | grep -oiE 'name=["'\'']?[^"'\'' >]+' | sed -E 's/.*name=["'\'']?//;s/["'\'' ]*$//' | head -1)
  type=$(echo "$inp" | grep -oiE 'type=["'\'']?[^"'\'' >]+' | sed -E 's/.*type=["'\'']?//;s/["'\'' ]*$//' | head -1)
  [ -z "$name" ] && continue

  # password field
  if [ "$type" = "password" ] && [ -z "$PASS_FIELD" ]; then
    PASS_FIELD="$name"
  # csrf token
  elif echo "$name" | grep -Eqi '(csrf|xsrf|authenticity|_token|antiforgery)'; then
    CSRF_FIELD="$name"
  # captcha
  elif echo "$name" | grep -Eqi '(captcha|recaptcha|hcaptcha|turnstile|cf-turnstile|challenge)'; then
    CAPTCHA_FIELD="$name"
  # username/email field (must be text-like, not a button)
  elif [ -z "$USER_FIELD" ] && [ "$type" != "submit" ] && [ "$type" != "button" ] && [ "$type" != "hidden" ]; then
    if echo "$name" | grep -Eqi '(user|email|login|account|phone|mobile|handle)'; then
      USER_FIELD="$name"
    fi
  fi
done < <(echo "$HTML" | grep -oiE '<input[^>]*>')

# Detect external captcha scripts
if [ -z "$CAPTCHA_FIELD" ]; then
  if echo "$HTML" | grep -Eqi '(google\.com/recaptcha|hcaptcha\.com|challenges\.cloudflare|turnstile)'; then
    CAPTCHA_FIELD="g-recaptcha-response"
    echo "[INFO] recon: external CAPTCHA detected (reCAPTCHA/hCaptcha/Turnstile)"
    echo "[INFO] recon: will use field name '$CAPTCHA_FIELD'"
  fi
fi

# Detect JSON content-type or JS-only login
if echo "$HTML" | grep -Eqi 'application/json|content-type.*json'; then
  echo "[INFO] recon: JSON content-type detected"
fi
if echo "$HTML" | grep -Eqi '(react|vue|angular|next-data|__NEXT_DATA__)'; then
  echo "[LOW] recon: page appears to be a JS SPA - form may be rendered client-side"
  echo "[LOW] recon: if recon fails, use --mode white and paste a cookie"
fi

# Detect 2FA markers in the form
TWOFA_DETECTED=0
if echo "$HTML" | grep -Eqi '(2fa|two[- ]?factor|otp|verification[ -]?code|authenticator|mfa|totp)'; then
  echo "[LOW] recon: page mentions 2FA/OTP - login may need a second step"
  TWOFA_DETECTED=1
fi

# Detect OAuth/SSO markers
if echo "$HTML" | grep -Eqi '(oauth|sso|sign[ -]?in with|continue with|google.*signin|github.*signin)'; then
  echo "[LOW] recon: OAuth/SSO detected - consider --mode cookie if form is hidden behind SSO"
fi

# Summary
echo "[INFO] recon: login_url=$FOUND_URL"
echo "[INFO] recon: form_action=$form_action"
echo "[INFO] recon: form_method=$form_method"
echo "[INFO] recon: user_field=$USER_FIELD"
echo "[INFO] recon: pass_field=$PASS_FIELD"
echo "[INFO] recon: csrf_field=$CSRF_FIELD"
echo "[INFO] recon: captcha_field=$CAPTCHA_FIELD"
echo "[INFO] recon: twofa_detected=$TWOFA_DETECTED"

# Persist to JSON for the orchestrator to read
cat > "$RAW/login_recon.json" <<EOF
{
  "login_url": "$FOUND_URL",
  "form_action": "$form_action",
  "form_method": "$form_method",
  "user_field": "$USER_FIELD",
  "pass_field": "$PASS_FIELD",
  "csrf_field": "$CSRF_FIELD",
  "captcha_field": "$CAPTCHA_FIELD",
  "twofa_detected": $TWOFA_DETECTED
}
EOF
