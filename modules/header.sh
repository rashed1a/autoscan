#!/usr/bin/env bash
# modules/header.sh - HTTP security headers + CSP analysis
# Prints one line per check in a structured format that report_gen.py parses.
# Format:
#   [SEVERITY] HEADER: VALUE_OR_MISSING
#   [INFO] note: free-form context

set -uo pipefail

TARGET="${1:-}"
if [ -z "$TARGET" ]; then echo "Usage: $0 <domain>"; exit 1; fi
URL="https://$TARGET"

HEADERS=(
  "Strict-Transport-Security"
  "X-Frame-Options"
  "X-Content-Type-Options"
  "Referrer-Policy"
  "Content-Security-Policy"
  "Permissions-Policy"
)

# Normalize, default to https
RESPONSE=$(curl -s -I -L --max-time 15 "$URL" 2>/dev/null)
[ -z "$RESPONSE" ] && RESPONSE=$(curl -s -I -L --max-time 15 "http://$TARGET" 2>/dev/null)

if [ -z "$RESPONSE" ]; then
  echo "[CRITICAL] connectivity: cannot reach $TARGET"
  exit 1
fi

echo "=== Security Headers ==="
echo "Target: $TARGET"

for H in "${HEADERS[@]}"; do
  VAL=$(echo "$RESPONSE" | grep -i "^${H}:" | tail -1 | sed -E "s/^[^:]+:[ \t]*//" | tr -d '\r')
  if [ -z "$VAL" ]; then
    case "$H" in
      "Strict-Transport-Security") echo "[HIGH] $H: MISSING - HTTPS downgrade / session hijack risk" ;;
      "Content-Security-Policy")   echo "[HIGH] $H: MISSING - no XSS mitigation via CSP" ;;
      "X-Frame-Options")           echo "[MEDIUM] $H: MISSING - clickjacking risk" ;;
      "X-Content-Type-Options")    echo "[MEDIUM] $H: MISSING - MIME sniffing attacks possible" ;;
      "Referrer-Policy")           echo "[LOW] $H: MISSING - referrer leaks to third parties" ;;
      "Permissions-Policy")        echo "[LOW] $H: MISSING - browser feature abuse possible" ;;
    esac
  else
    echo "[INFO] $H: $VAL"
    # Specific CSP weakness checks
    if [ "$H" = "Content-Security-Policy" ]; then
      echo "$VAL" | grep -qi "'unsafe-inline'" && \
        echo "[CRITICAL] CSP unsafe-inline: allows inline script execution, defeats XSS protection"
      echo "$VAL" | grep -qi "'unsafe-eval'" && \
        echo "[CRITICAL] CSP unsafe-eval: allows eval()/Function() on attacker strings"
      echo "$VAL" | grep -Eqi "(^| )\*( |\$)" && \
        echo "[HIGH] CSP wildcard source: any host can serve allowed content"
      echo "$VAL" | grep -Eqi "(^| )https?:( |\$)" && \
        echo "[MEDIUM] CSP bare scheme: allows content from any HTTPS/HTTP host"
      echo "$VAL" | grep -qi "default-src" || echo "[LOW] CSP default-src: missing - directives fall back permissively"
      echo "$VAL" | grep -qi "frame-ancestors" || echo "[MEDIUM] CSP frame-ancestors: missing - clickjacking via framing"
    fi
    if [ "$H" = "Strict-Transport-Security" ]; then
      echo "$VAL" | grep -qi "includeSubDomains" || \
        echo "[LOW] HSTS includeSubDomains: missing - subdomains not protected"
      echo "$VAL" | grep -Eqi "max-age=[0-9]+" | head -1
    fi
  fi
done

# Bonus checks: server disclosure
SERVER=$(echo "$RESPONSE" | grep -i "^server:" | tail -1 | sed -E "s/^[^:]+:[ \t]*//" | tr -d '\r')
[ -n "$SERVER" ] && echo "[INFO] server: $SERVER"

XPOWERED=$(echo "$RESPONSE" | grep -i "^x-powered-by:" | tail -1 | sed -E "s/^[^:]+:[ \t]*//" | tr -d '\r')
[ -n "$XPOWERED" ] && echo "[LOW] x-powered-by: $XPOWERED - tech stack disclosure"
