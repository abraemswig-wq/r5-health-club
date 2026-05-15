#!/usr/bin/env python3
"""
REHAB FIVE HEALTH CLUB · Mail-Versand

Sendet eine HTML-Vorschau-Mail mit dem Artikel-Entwurf an
a.braemswig@rehab-five.com via Resend.com.

Voraussetzungen:
- pip install requests
- Env-Variablen:
    RESEND_API_KEY    = re_xxxxxxxx (von https://resend.com/api-keys)
    REVIEWER_EMAIL    = a.braemswig@rehab-five.com (Default)
    FROM_EMAIL        = onboarding@resend.dev (Default, Test-Sender)
                      = später: noreply@rehab-five-health-club.com
                        nachdem Domain in Resend verifiziert wurde

Aufruf:
    python3 send-preview.py <draft-dateiname>
    python3 send-preview.py 2026-05-22-homeoffice-rueckenuebungen.html
    python3 send-preview.py  # nimmt automatisch jüngsten Entwurf
"""
from __future__ import annotations

import os
import re
import sys
from html.parser import HTMLParser
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
DRAFTS_DIR = ROOT / "drafts"
TEMPLATE_FILE = ROOT / "preview-template.html"

RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
REVIEWER_EMAIL = os.environ.get("REVIEWER_EMAIL", "a.braemswig@rehab-five.com")
FROM_EMAIL = os.environ.get("FROM_EMAIL", "onboarding@resend.dev")
FROM_NAME = "REHAB FIVE HEALTH CLUB · Auto-Drafts"

if not RESEND_API_KEY:
    print("FEHLER: RESEND_API_KEY nicht gesetzt.")
    print("  export RESEND_API_KEY=re_...")
    print("  Schlüssel besorgen: https://resend.com/api-keys")
    sys.exit(1)


# ============================================================================
# HTML-Inhalts-Parser (extrahiert Titel, Lead, Quick-Answer, H2, FAQ)
# ============================================================================

class ArticleExtractor(HTMLParser):
    """Sehr einfacher HTML-Parser, der die nötigen Strings aus dem Artikel zieht."""

    def __init__(self):
        super().__init__()
        self.title = ""
        self.lead = ""
        self.quick_answer = ""
        self.h2_titles: list[str] = []
        self.faq_questions: list[str] = []

        # State
        self._in_title = False
        self._in_h1 = False
        self._in_lead_p = False
        self._after_h1 = False
        self._in_h2 = False
        self._in_quick_answer_p = False
        self._in_summary = False
        self._after_quick_h2 = False
        self._text_buffer = ""
        self._quick_buffer = ""
        self._h2_buffer = ""
        self._h1_seen = False
        self._faq_seen_h2 = False

    def handle_starttag(self, tag, attrs):
        attrs_d = dict(attrs)

        if tag == "title":
            self._in_title = True
            self._text_buffer = ""
        elif tag == "h1":
            self._in_h1 = True
            self._text_buffer = ""
        elif tag == "h2":
            self._in_h2 = True
            self._h2_buffer = ""
        elif tag == "summary":
            self._in_summary = True
            self._text_buffer = ""
        elif tag == "p":
            cls = attrs_d.get("class", "")
            # Lead = das <p> direkt nach <h1>
            if self._after_h1:
                self._in_lead_p = True
                self._text_buffer = ""
                self._after_h1 = False
            # Quick-Answer: <p> nach H2 in aside
            if self._after_quick_h2:
                self._in_quick_answer_p = True
                self._quick_buffer = ""
                self._after_quick_h2 = False

    def handle_endtag(self, tag):
        if tag == "title" and self._in_title:
            self.title = self._text_buffer.strip()
            self._in_title = False
        elif tag == "h1" and self._in_h1:
            self._in_h1 = False
            self._after_h1 = True
            self._h1_seen = True
        elif tag == "h2" and self._in_h2:
            self._in_h2 = False
            h2_text = self._h2_buffer.strip()
            # Quick-Answer-H2 nicht als regulärer H2 zählen
            if h2_text.lower() in {"was ist funktionelles training?", "wie viel zahlt die kasse?",
                                   "was ist der unterschied zwischen mobility und stretching?",
                                   "pilates vs. yoga — der kurze unterschied",
                                   "warum krafttraining ab 50?", "was hilft wirklich?",
                                   "kurz erklärt"}:
                self._after_quick_h2 = True
            elif self._h1_seen:
                # FAQ-H2 erkennen: enthält "FAQ" oder "Häufige Fragen"
                if "faq" in h2_text.lower() or "häufige fragen" in h2_text.lower():
                    self._faq_seen_h2 = True
                else:
                    self.h2_titles.append(h2_text)
        elif tag == "p" and self._in_lead_p:
            self.lead = self._text_buffer.strip()
            self._in_lead_p = False
        elif tag == "p" and self._in_quick_answer_p:
            self.quick_answer = self._quick_buffer.strip()
            self._in_quick_answer_p = False
        elif tag == "summary" and self._in_summary:
            self._in_summary = False
            # Bereinigen: trailing chevron entfernen
            q = re.sub(r"▾$", "", self._text_buffer.strip()).strip()
            if q:
                self.faq_questions.append(q)

    def handle_data(self, data):
        if self._in_title:
            self._text_buffer += data
        elif self._in_h1:
            self._text_buffer += data
        elif self._in_h2:
            self._h2_buffer += data
        elif self._in_lead_p:
            self._text_buffer += data
        elif self._in_quick_answer_p:
            self._quick_buffer += data
        elif self._in_summary:
            self._text_buffer += data


def strip_html_tags(html: str) -> str:
    """Entfernt HTML-Tags und gibt Plain-Text zurück."""
    return re.sub(r"<[^>]+>", "", html)


def estimate_wordcount(html: str) -> int:
    """Grobe Wortzählung im Article-Body."""
    text = strip_html_tags(html)
    words = re.findall(r"\w+", text)
    return len(words)


# ============================================================================
# Template-Befüllung
# ============================================================================

def build_preview_html(article_path: Path, meta: dict) -> str:
    """Liest den Artikel + Template und füllt die Platzhalter."""
    article_html = article_path.read_text(encoding="utf-8")
    template = TEMPLATE_FILE.read_text(encoding="utf-8")

    extractor = ArticleExtractor()
    extractor.feed(article_html)

    title = extractor.title.split(" · ")[0].split(" | ")[0].strip() or meta.get("title", "")
    lead = extractor.lead or "(Lead konnte nicht extrahiert werden — bitte HTML-Datei prüfen.)"
    quick = extractor.quick_answer or "(Quick-Answer-Box konnte nicht extrahiert werden.)"

    # Outline aus H2-Sektionen
    h2s = [h for h in extractor.h2_titles if h.lower() not in {"weitere kurse", "mehr aus dem wissen-bereich", "lies dich tiefer ein", "worauf wir uns stützen", "quellen & weiterführend"}]
    outline_items = "\n              ".join(f"<li>{h}</li>" for h in h2s) or "<li>(keine H2-Sektionen gefunden)</li>"

    # FAQ
    faq_q = extractor.faq_questions
    faq_items = "\n              ".join(f"<li>{q}</li>" for q in faq_q) or "<li>(keine FAQ-Fragen gefunden)</li>"

    wc = estimate_wordcount(article_html)
    readtime = max(3, round(wc / 200))

    rendered = template
    replacements = {
        "{{TITLE}}": title,
        "{{TOPIC_ID}}": meta.get("topic_id", "—"),
        "{{SLUG}}": meta.get("slug", ""),
        "{{DATE}}": meta.get("date", ""),
        "{{WORDCOUNT}}": str(wc),
        "{{READTIME}}": str(readtime),
        "{{LEAD}}": lead,
        "{{QUICK_ANSWER}}": quick,
        "{{OUTLINE_ITEMS}}": outline_items,
        "{{FAQ_COUNT}}": str(len(faq_q)),
        "{{FAQ_ITEMS}}": faq_items,
        "{{DRAFT_FILENAME}}": article_path.name,
    }
    for k, v in replacements.items():
        rendered = rendered.replace(k, v)

    return rendered, title, wc, readtime


# ============================================================================
# Resend API
# ============================================================================

def send_via_resend(html_body: str, subject: str, attachment_path: Path) -> dict:
    """Sendet Mail mit Anhang via Resend."""
    import base64

    with open(attachment_path, "rb") as f:
        attachment_data = base64.b64encode(f.read()).decode("ascii")

    payload = {
        "from": f"{FROM_NAME} <{FROM_EMAIL}>",
        "to": [REVIEWER_EMAIL],
        "subject": subject,
        "html": html_body,
        "attachments": [
            {
                "filename": attachment_path.name,
                "content": attachment_data,
            }
        ],
        "reply_to": REVIEWER_EMAIL,  # Antworten gehen an dich selbst, damit du "go"/"fix"/"skip" replyen kannst
    }

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
        print(f"FEHLER: Resend-Versand fehlgeschlagen ({response.status_code})")
        print(f"  Response: {response.text}")
        sys.exit(1)

    return response.json()


# ============================================================================
# Meta-Sidecar lesen
# ============================================================================

def read_meta(path: Path) -> dict:
    if not path.exists():
        return {}
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


# ============================================================================
# Main
# ============================================================================

def find_latest_draft() -> Path | None:
    """Findet den jüngsten Entwurf."""
    drafts = sorted(DRAFTS_DIR.glob("*.html"), key=lambda p: p.stat().st_mtime, reverse=True)
    return drafts[0] if drafts else None


def main():
    print(f"REHAB FIVE HEALTH CLUB · Mail-Versand")
    print("=" * 60)

    # Entwurf wählen
    if len(sys.argv) > 1:
        draft_path = DRAFTS_DIR / sys.argv[1]
        if not draft_path.exists():
            print(f"FEHLER: {draft_path} nicht gefunden.")
            sys.exit(1)
    else:
        draft_path = find_latest_draft()
        if not draft_path:
            print("FEHLER: Kein Entwurf in drafts/ vorhanden.")
            print("  Erst Generator laufen lassen: python3 generate.py")
            sys.exit(1)
        print(f"  → Jüngster Entwurf: {draft_path.name}")

    meta_path = draft_path.with_suffix(".meta")
    meta = read_meta(meta_path)
    print(f"  → Meta: {meta.get('topic_id', '?')} · {meta.get('slug', '?')}")

    # Preview-HTML aufbauen
    print("  → Baue HTML-Vorschau …")
    preview_html, title, wc, readtime = build_preview_html(draft_path, meta)

    # Mail senden
    print(f"  → Sende an {REVIEWER_EMAIL} …")
    print(f"    From: {FROM_EMAIL}")
    print(f"    Subject: {title}")

    subject = f"[Health Club Artikel] {title} · {wc} Wörter · ~{readtime} Min."
    result = send_via_resend(preview_html, subject, draft_path)

    print(f"  ✓ Mail versendet. ID: {result.get('id', '?')}")
    print()
    print("Nächster Schritt:")
    print("  1. Öffne deine Mail in Outlook/Apple Mail/Gmail")
    print("  2. Lies die Vorschau")
    print("  3. Antworte mit `go` (publish), `fix` (neu schreiben) oder `skip` (verwerfen)")
    print("  4. Oder manuell: python3 publish.py", draft_path.name)


if __name__ == "__main__":
    main()
