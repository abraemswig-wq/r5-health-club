#!/usr/bin/env bash
# REHAB FIVE HEALTH CLUB · Wöchentlicher Pipeline-Run
#
# Generiert den nächsten Artikel und versendet die Vorschau-Mail an Aric.
# Aufruf:
#   ./weekly-run.sh
#
# Für wöchentliche Automation via launchd: siehe README.md

set -euo pipefail

# ============================================================================
# Konfiguration
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${SCRIPT_DIR}/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="${LOG_DIR}/run-$(date +%Y-%m-%d_%H%M%S).log"

# Falls .env-Datei vorhanden, laden
if [ -f "${SCRIPT_DIR}/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  source "${SCRIPT_DIR}/.env"
  set +a
fi

# ============================================================================
# Vorab-Check
# ============================================================================

cd "$SCRIPT_DIR"

if [ -z "${GEMINI_API_KEY:-}" ]; then
  echo "FEHLER: GEMINI_API_KEY nicht gesetzt."
  echo "  Trage ihn in automation/.env ein (siehe README.md)."
  exit 1
fi

if [ -z "${RESEND_API_KEY:-}" ]; then
  echo "FEHLER: RESEND_API_KEY nicht gesetzt."
  echo "  Trage ihn in automation/.env ein (siehe README.md)."
  exit 1
fi

# ============================================================================
# Run
# ============================================================================

{
  echo "==============================================================="
  echo "REHAB FIVE HEALTH CLUB · Wöchentlicher Run · $(date)"
  echo "==============================================================="
  echo

  echo "[1/2] Artikel generieren …"
  python3 generate.py
  echo

  echo "[2/2] Vorschau-Mail senden …"
  python3 send-preview.py
  echo

  echo "==============================================================="
  echo "✓ Pipeline-Run erfolgreich."
  echo "  Aric bekommt jetzt eine Mail mit dem Vorschau-Artikel."
  echo "  Sobald er 'go' antwortet, läuft publish.py."
  echo "==============================================================="
} 2>&1 | tee "$LOG_FILE"
