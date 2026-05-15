#!/usr/bin/env python3
"""
REHAB FIVE HEALTH CLUB · Lead-Magnet-Funnel

Triggert die 3-Mail-Sequence für neue Kassen-Guide-Anfragen.
- Mail 1: sofort (mit PDF-Anhang)
- Mail 2: +3 Tage (Kassen-spezifischer Tipp)
- Mail 3: +7 Tage (Soft-CTA Kaffee)

Resend bietet "scheduled emails" über das `scheduled_at` Parameter
(ISO-8601 UTC). Damit reicht ein einziger Skript-Aufruf — der Versand
wird automatisch zum richtigen Zeitpunkt ausgelöst.

Voraussetzungen:
- pip install requests
- Env-Variablen (siehe .env oder shell):
    RESEND_API_KEY = re_xxxxxxxx
    FROM_EMAIL     = onboarding@resend.dev (Default — funktioniert sofort
                     ohne Domain-Verifizierung. Später noreply@rehab-...)

Aufruf:
    python3 send-kassen-funnel.py <email> [<vorname>]
    python3 send-kassen-funnel.py max@example.com Maximilian
    python3 send-kassen-funnel.py max@example.com  # Vorname ist optional
    python3 send-kassen-funnel.py --test            # Test-Mode (an Aric)
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import os
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("FEHLER: 'requests' nicht installiert. Bitte ausführen:")
    print("  pip install requests")
    sys.exit(1)

# ============================================================================
# Pfade & Konfiguration
# ============================================================================

ROOT = Path(__file__).resolve().parent
SITE_ROOT = ROOT.parents[1]  # /Users/.../rehab-five-gym/
PDF_PATH = SITE_ROOT / "downloads" / "kassen-guide.pdf"
LEADS_LOG = ROOT / "leads.jsonl"  # Audit-Log aller Funnel-Trigger

MAIL_1 = ROOT / "mail-1-welcome.html"
MAIL_2 = ROOT / "mail-2-kassen.html"
MAIL_3 = ROOT / "mail-3-coffee.html"

RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
FROM_EMAIL = os.environ.get("FROM_EMAIL", "onboarding@resend.dev")
FROM_NAME = "REHAB FIVE HEALTH CLUB"
REPLY_TO = os.environ.get("REPLY_TO", "a.braemswig@rehab-five.com")

# Funnel-Zeitpunkte (in Tagen ab jetzt)
DELAYS = {
    "mail-1-welcome": 0,
    "mail-2-kassen": 3,
    "mail-3-coffee": 7,
}

MAIL_FILES = {
    "mail-1-welcome": MAIL_1,
    "mail-2-kassen": MAIL_2,
    "mail-3-coffee": MAIL_3,
}

SUBJECTS = {
    "mail-1-welcome": "Dein Krankenkassen-Guide ist da · REHAB FIVE",
    "mail-2-kassen": "{firstname}, eine Sache zur Krankenkasse · REHAB FIVE",
    "mail-3-coffee": "{firstname}, komm auf einen Kaffee vorbei · REHAB FIVE",
}


# ============================================================================
# Helpers
# ============================================================================

def check_env():
    if not RESEND_API_KEY:
        print("FEHLER: RESEND_API_KEY nicht gesetzt.")
        print("  export RESEND_API_KEY=re_...")
        print("  Schlüssel besorgen: https://resend.com/api-keys")
        sys.exit(1)
    for name, path in MAIL_FILES.items():
        if not path.exists():
            print(f"FEHLER: Mail-Template fehlt: {path}")
            sys.exit(1)
    if not PDF_PATH.exists():
        print(f"WARNUNG: PDF fehlt unter {PDF_PATH}")
        print("  Erst PDF generieren: python3 build-kassen-guide-pdf.py")


def render_template(path: Path, firstname: str) -> str:
    """Lädt HTML-Template und ersetzt {{FIRSTNAME}}."""
    html = path.read_text(encoding="utf-8")
    return html.replace("{{FIRSTNAME}}", firstname or "")


def load_pdf_base64() -> str:
    with open(PDF_PATH, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


def schedule_time_iso(days_from_now: int) -> str:
    """Berechnet ISO-8601 UTC für scheduled_at."""
    if days_from_now == 0:
        return ""  # sofort senden, kein scheduled_at
    when = dt.datetime.utcnow() + dt.timedelta(days=days_from_now)
    # Resend erwartet "in 3 days" zum Beispiel — wir nutzen ISO 8601
    return when.replace(microsecond=0).isoformat() + "Z"


def log_lead(email: str, firstname: str, results: list[dict]):
    """Schreibt einen Audit-Eintrag in leads.jsonl."""
    entry = {
        "timestamp": dt.datetime.utcnow().isoformat() + "Z",
        "email": email,
        "firstname": firstname,
        "results": results,
    }
    with open(LEADS_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ============================================================================
# Resend-Versand
# ============================================================================

def send_mail(slug: str, to_email: str, firstname: str, attach_pdf: bool = False) -> dict:
    """Sendet eine einzelne Mail via Resend (sofort oder scheduled)."""
    html = render_template(MAIL_FILES[slug], firstname)
    subject = SUBJECTS[slug].format(firstname=firstname or "")
    # Bereinige leere Anrede
    subject = subject.replace(", ,", ",").replace("  ", " ")

    payload = {
        "from": f"{FROM_NAME} <{FROM_EMAIL}>",
        "to": [to_email],
        "subject": subject,
        "html": html,
        "reply_to": REPLY_TO,
        "tags": [
            {"name": "campaign", "value": "kassen-guide-funnel"},
            {"name": "step", "value": slug},
        ],
    }

    # Scheduled-Versand (Resend akzeptiert ISO 8601 oder Natural-Language)
    delay_days = DELAYS[slug]
    if delay_days > 0:
        payload["scheduled_at"] = schedule_time_iso(delay_days)

    # PDF-Anhang nur in Mail 1
    if attach_pdf and PDF_PATH.exists():
        payload["attachments"] = [{
            "filename": "kassen-guide.pdf",
            "content": load_pdf_base64(),
        }]

    response = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=30,
    )

    if response.status_code >= 400:
        print(f"  ✗ {slug}: HTTP {response.status_code} — {response.text}")
        return {"slug": slug, "ok": False, "error": response.text}

    result = response.json()
    schedule_info = f" · scheduled für +{delay_days} Tage" if delay_days > 0 else " · sofort"
    print(f"  ✓ {slug}: id={result.get('id', '?')}{schedule_info}")
    return {"slug": slug, "ok": True, "id": result.get("id"), "scheduled_days": delay_days}


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="REHAB FIVE Kassen-Funnel triggern")
    parser.add_argument("email", nargs="?", help="Email-Adresse des Leads")
    parser.add_argument("firstname", nargs="?", default="", help="Vorname (optional)")
    parser.add_argument("--test", action="store_true",
                        help="Test-Mode: sendet alle 3 Mails an Aric (REPLY_TO)")
    args = parser.parse_args()

    if args.test:
        target_email = REPLY_TO
        target_name = "Aric"
    else:
        if not args.email:
            parser.error("Email-Adresse oder --test erforderlich")
        target_email = args.email
        target_name = args.firstname or ""

    check_env()

    print(f"REHAB FIVE Kassen-Guide-Funnel")
    print("=" * 60)
    print(f"  Empfänger: {target_email}")
    print(f"  Vorname:   {target_name or '(leer)'}")
    print(f"  Absender:  {FROM_NAME} <{FROM_EMAIL}>")
    print(f"  Reply-To:  {REPLY_TO}")
    print()

    results = []
    # Mail 1 sofort (mit PDF-Anhang)
    results.append(send_mail("mail-1-welcome", target_email, target_name, attach_pdf=True))
    # Mail 2 in 3 Tagen
    results.append(send_mail("mail-2-kassen", target_email, target_name))
    # Mail 3 in 7 Tagen
    results.append(send_mail("mail-3-coffee", target_email, target_name))

    log_lead(target_email, target_name, results)

    success = sum(1 for r in results if r.get("ok"))
    print()
    print(f"  {success}/3 Mails erfolgreich abgesetzt.")
    print(f"  Log: {LEADS_LOG.relative_to(SITE_ROOT)}")

    if success < 3:
        sys.exit(1)


if __name__ == "__main__":
    main()
