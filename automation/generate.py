#!/usr/bin/env python3
"""
REHAB FIVE HEALTH CLUB · Artikel-Generator (Google Gemini)

Wählt das nächste Thema aus topics.md aus, generiert einen kompletten
Artikel im etablierten AI-SEO-Pattern (Quick-Answer + 5 H2 + 6 FAQ +
Quellen + Article/FAQPage-Schema) und speichert ihn als HTML-Datei in
./drafts/.

Voraussetzungen:
- Python 3.10+
- pip install google-generativeai
- GEMINI_API_KEY als Env-Variable gesetzt
  (kostenlos auf https://aistudio.google.com/app/apikey)

Aufruf:
    python3 generate.py                # nächstes passendes Thema
    python3 generate.py --topic T-007  # bestimmtes Thema erzwingen
    python3 generate.py --dry-run      # nur zeigen, was generiert würde
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import sys
from pathlib import Path
from typing import Optional

try:
    import google.generativeai as genai
except ImportError:
    print("FEHLER: 'google-generativeai' nicht installiert. Bitte ausführen:")
    print("  pip install google-generativeai")
    sys.exit(1)

# ============================================================================
# Pfade
# ============================================================================

ROOT = Path(__file__).resolve().parent
TOPICS_FILE = ROOT / "topics.md"
DRAFTS_DIR = ROOT / "drafts"
SITE_ROOT = ROOT.parent  # /Users/.../rehab-five-gym/
EXISTING_ARTICLE = SITE_ROOT / "wissen" / "funktionelles-training-was-ist-das" / "index.html"

DRAFTS_DIR.mkdir(exist_ok=True)

# ============================================================================
# API-Konfiguration
# ============================================================================

API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    print("FEHLER: GEMINI_API_KEY nicht gesetzt.")
    print("  export GEMINI_API_KEY=...")
    print("  Schlüssel besorgen: https://aistudio.google.com/app/apikey")
    sys.exit(1)

genai.configure(api_key=API_KEY)

# gemini-1.5-pro: kostenloses Tier, 8192 Output-Tokens, gut für lange strukturierte Artikel
# Alternative: gemini-2.0-flash-exp (schneller, neuer) oder gemini-1.5-flash (am schnellsten)
MODEL = os.environ.get("GEMINI_MODEL", "gemini-1.5-pro")


# ============================================================================
# Themen-Auswahl
# ============================================================================

def parse_topics(text: str) -> list[dict]:
    """Parst das topics.md Markdown in eine Liste von Themen-Dicts."""
    topics = []
    # Pattern: ### T-001 · Titel ... bis zum nächsten ### oder ---
    blocks = re.split(r"\n### (T-\d+) · ", text)[1:]
    # blocks ist jetzt [id1, body1, id2, body2, ...]
    for i in range(0, len(blocks), 2):
        topic_id = blocks[i].strip()
        body = blocks[i + 1] if i + 1 < len(blocks) else ""
        # Title ist die erste Zeile
        title_line, *rest_lines = body.strip().split("\n", 1)
        rest = rest_lines[0] if rest_lines else ""
        # Felder per Regex extrahieren
        def find(pattern):
            m = re.search(pattern, rest, re.IGNORECASE)
            return m.group(1).strip() if m else ""
        topics.append({
            "id": topic_id,
            "title": title_line.strip(),
            "slug": find(r"\*\*Slug\*\*:\s*`([^`]+)`"),
            "priority": find(r"\*\*P\*\*:\s*(\d)"),
            "season": find(r"\*\*Saison\*\*:\s*([^·\n]+)"),
            "status": find(r"\*\*Status\*\*:\s*([^\n]+)"),
            "keywords": find(r"\*\*Keywords\*\*:\s*([^\n]+)"),
            "icd": find(r"\*\*ICD\*\*:\s*([^\n]+)"),
            "target": find(r"\*\*Zielgruppe\*\*:\s*([^\n]+)"),
            "pitch": find(r"\*\*Quick-Answer-Pitch\*\*:\s*([^\n]+)"),
            "cross_links": find(r"\*\*Cross-Links\*\*:\s*([^\n]+)"),
        })
    return topics


SEASON_MONTHS = {
    "januar": 1, "februar": 2, "märz": 3, "maerz": 3, "april": 4, "mai": 5,
    "juni": 6, "juli": 7, "august": 8, "september": 9, "oktober": 10,
    "november": 11, "dezember": 12,
}


def select_next_topic(topics: list[dict], today: dt.date) -> Optional[dict]:
    """Wählt das nächste zu generierende Thema."""
    # Nur Themen im Status `idea`
    eligible = [t for t in topics if t.get("status", "").lower() == "idea"]
    if not eligible:
        return None

    current_month = today.month

    def season_score(topic):
        season = topic.get("season", "").lower()
        if "evergreen" in season or "ganzjährig" in season:
            return 0
        # Saison parsen: "Januar" oder "Februar/März"
        months = []
        for token in re.split(r"[/,]", season):
            tok = token.strip().lower()
            if tok in SEASON_MONTHS:
                months.append(SEASON_MONTHS[tok])
        if not months:
            return 0
        # Score = 10 wenn current_month dabei, sonst Distanz
        if current_month in months:
            return 10
        nearest = min(abs((current_month - m) % 12) for m in months)
        return -nearest

    def priority_score(topic):
        try:
            return 4 - int(topic.get("priority", "3"))
        except ValueError:
            return 0

    eligible.sort(key=lambda t: (season_score(t), priority_score(t)), reverse=True)
    return eligible[0]


# ============================================================================
# Existierenden Artikel als Style-Referenz lesen
# ============================================================================

def load_reference_article() -> str:
    """Lädt einen bestehenden Artikel als Style-Vorlage."""
    if not EXISTING_ARTICLE.exists():
        return ""
    return EXISTING_ARTICLE.read_text(encoding="utf-8")


# ============================================================================
# Claude-Prompt
# ============================================================================

SYSTEM_PROMPT = """Du bist Content-Lead beim REHAB FIVE HEALTH CLUB in Münster. \
Du schreibst Artikel für rehab-five-health-club.com/wissen/ — eine standalone Domain \
des physiotherapeutisch geführten Health Clubs.

Tonalität:
- Du-Form, konsequent
- Therapeut:innen-Stimme — wissenschaftlich fundiert, aber nicht überheblich
- Keine Marketing-Floskeln, keine Übertreibungen, keine Werbe-Adjektive
- Klar, konkret, mit echten Zahlen und Studien wo möglich
- Setze Hervorhebungen sparsam mit <strong> für die wichtigsten 2–3 Begriffe pro Sektion

Markenwelt:
- REHAB FIVE HEALTH CLUB ist Tochter von REHAB FIVE (Physiotherapie, 10+ Jahre Münster)
- Standort: Friedrich-Ebert-Straße 122, 48153 Münster
- 6 Kurse: Funktionelles Training (15 €), Pilates Mat (14 €), Rückenfit §20 (149 € / 8 Einheiten), Athletik-Bootcamp (15 €), Mobility & Stretch (15 €), Fit ab 50 §20 (149 € / 8 Einheiten)
- Mitgliedschaft: Probestunde gratis, 10er-Karte 130 € (13 €/Kurs), Flat 79 €/Monat
- Telefon: 0251 74788 200, E-Mail: info@rehab-five.com
- USP: kleine Gruppen (10–12), physiotherapeutisch geplant, ZPP-zertifizierte Präventionskurse

Struktur (zwingend):
1. Quick-Answer-Box (40–60 Wörter, AI-Overview-tauglich)
2. 4–6 H2-Hauptsektionen
3. Inline-CTA-Block mittendrin (zum passenden Kurs)
4. 6 FAQ-Einträge (jede Antwort 40–80 Wörter)
5. Quellen-Sektion (3–5 Quellen, jeweils Autor/Jahr + Titel)

Cross-Links zur Mutter-Marke rehab-five.com nur bei medizinischen Themen.
"""

USER_PROMPT_TEMPLATE = """Schreibe einen kompletten HTML-Artikel für das Thema:

**{title}**

- Slug: {slug}
- Quick-Answer-Pitch (als Ausgangspunkt): {pitch}
- Keywords: {keywords}
- Zielgruppe: {target}
- ICD-Code (falls relevant): {icd}
- Cross-Links (intern): {cross_links}

Verwende exakt die HTML-Struktur und das CI des Beispiel-Artikels unten. \
Tausche nur:
- `<title>`, Meta-Description, OG-Tags
- JSON-LD Article-Felder (headline, description, image, about, wordCount)
- JSON-LD FAQPage (6 Q&A)
- JSON-LD BreadcrumbList (URL, name)
- Breadcrumb-Text
- Eyebrow-Kategorie + Lesezeit
- H1
- Lead-Paragraph
- Quick-Answer-Box (H2 + Paragraph)
- Hero-Bild-Pfad (passend zum Thema, wähle aus: kraft-1200.jpg, senior-1200.jpg, \
  community-1200.jpg, barbell-1200.jpg, standorte/friedrich-ebert-122/hero-matten.jpg, \
  standorte/friedrich-ebert-122/gallery-01-kursraum.jpg, \
  standorte/friedrich-ebert-122/gallery-05-powerbar.jpg)
- Artikel-Body (4–6 H2-Sektionen mit Paragraphen/Listen)
- Inline-CTA-Block (forest-700, weiße Schrift)
- 6 FAQ-Details (Klapp-Blöcke)
- Quellen-Liste
- 3 Cross-Link-Kacheln am Ende

Footer, Header, Mobile-Menü, Scripts bleiben **identisch**.

Wichtig:
- Alle URLs auf `https://rehab-five-health-club.com/...`
- Bilder mit relativem Pfad `../../img/...`
- Logo-Pfad `../../R5-Logo-B-black_RZ.png`
- Datum heute: {today}
- Lesezeit-Angabe realistisch (5–7 Min.)

Antworte NUR mit dem fertigen HTML (kein Markdown-Wrapping, kein Kommentar).

Hier der Beispiel-Artikel als Style-Vorlage:

---STYLE-REFERENZ---

{reference}

---ENDE STYLE-REFERENZ---
"""


# ============================================================================
# Generierung
# ============================================================================

def generate_article(topic: dict, reference_html: str) -> str:
    """Generiert den Artikel via Google Gemini."""
    prompt = USER_PROMPT_TEMPLATE.format(
        title=topic["title"],
        slug=topic["slug"],
        pitch=topic.get("pitch", ""),
        keywords=topic.get("keywords", ""),
        target=topic.get("target", "Allgemein"),
        icd=topic.get("icd", "—"),
        cross_links=topic.get("cross_links", ""),
        today=dt.date.today().isoformat(),
        reference=reference_html,
    )

    print(f"  → Generiere Artikel mit {MODEL} …")

    model = genai.GenerativeModel(
        MODEL,
        system_instruction=SYSTEM_PROMPT,
    )

    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            temperature=0.7,
            top_p=0.95,
            max_output_tokens=8192,
        ),
        safety_settings={
            # Medizinische Inhalte (z.B. Rückenschmerzen, Arthrose) sollen nicht
            # versehentlich von der Safety-Filter blockiert werden.
            "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
            "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
            "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
            "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
        },
    )

    text = response.text or ""

    # Falls Gemini doch Markdown-Wrapping nutzt, abschneiden
    if "```html" in text:
        text = text.split("```html", 1)[1]
        text = text.rsplit("```", 1)[0]
    elif text.startswith("```"):
        text = text.split("```", 1)[1]
        text = text.rsplit("```", 1)[0]
    text = text.strip()

    if not text.startswith("<!DOCTYPE") and not text.startswith("<html"):
        print("  ⚠️  Output beginnt nicht mit <!DOCTYPE — bitte manuell prüfen.")

    return text


# ============================================================================
# Topics-Status aktualisieren
# ============================================================================

def update_topic_status(topic_id: str, new_status: str):
    """Aktualisiert den Status eines Themas in topics.md."""
    text = TOPICS_FILE.read_text(encoding="utf-8")
    # Suche nach dem T-XXX-Block und ersetze nur den Status dort
    pattern = rf"(### {re.escape(topic_id)} · [^\n]+\n(?:- [^\n]+\n)*?- \*\*P\*\*: \d · \*\*Saison\*\*: [^·]+· \*\*Status\*\*: )([^\n]+)"
    new_text, count = re.subn(pattern, rf"\g<1>{new_status}", text)
    if count == 0:
        print(f"  ⚠️  Konnte Status für {topic_id} nicht aktualisieren — bitte manuell in topics.md.")
        return
    TOPICS_FILE.write_text(new_text, encoding="utf-8")
    print(f"  → Status von {topic_id} auf '{new_status}' gesetzt.")


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="REHAB FIVE HEALTH CLUB Artikel-Generator")
    parser.add_argument("--topic", help="Erzwinge bestimmtes Thema, z.B. T-007")
    parser.add_argument("--dry-run", action="store_true", help="Nur zeigen, was generiert würde")
    args = parser.parse_args()

    today = dt.date.today()
    print(f"REHAB FIVE HEALTH CLUB Artikel-Generator · {today}")
    print("=" * 60)

    # Topics laden
    if not TOPICS_FILE.exists():
        print(f"FEHLER: {TOPICS_FILE} nicht gefunden.")
        sys.exit(1)
    topics = parse_topics(TOPICS_FILE.read_text(encoding="utf-8"))
    print(f"  → {len(topics)} Themen aus topics.md geladen.")

    # Auswählen
    if args.topic:
        topic = next((t for t in topics if t["id"] == args.topic), None)
        if not topic:
            print(f"FEHLER: Thema {args.topic} nicht gefunden.")
            sys.exit(1)
    else:
        topic = select_next_topic(topics, today)
        if not topic:
            print("Keine Themen mit Status 'idea' verfügbar. Backlog ist leer.")
            sys.exit(0)

    print(f"  → Gewähltes Thema: {topic['id']} · {topic['title']}")
    print(f"    Slug: {topic['slug']}")
    print(f"    Status: {topic.get('status', '?')} → drafting → pending-review")

    if args.dry_run:
        print("\n[DRY-RUN] Kein API-Aufruf, keine Datei geschrieben.")
        sys.exit(0)

    # Reference laden
    reference_html = load_reference_article()
    if not reference_html:
        print("FEHLER: Referenz-Artikel nicht gefunden.")
        sys.exit(1)

    # Generieren
    html = generate_article(topic, reference_html)

    # Speichern
    draft_path = DRAFTS_DIR / f"{today.isoformat()}-{topic['slug']}.html"
    draft_path.write_text(html, encoding="utf-8")
    print(f"  ✓ Entwurf gespeichert: {draft_path.relative_to(SITE_ROOT)}")

    # Metadata-Sidecar für Versand
    meta_path = DRAFTS_DIR / f"{today.isoformat()}-{topic['slug']}.meta"
    meta_path.write_text(
        f"topic_id={topic['id']}\n"
        f"slug={topic['slug']}\n"
        f"title={topic['title']}\n"
        f"date={today.isoformat()}\n",
        encoding="utf-8",
    )

    # Status updaten
    update_topic_status(topic["id"], "pending-review")

    print()
    print("Nächster Schritt:")
    print(f"  python3 send-preview.py {draft_path.name}")


if __name__ == "__main__":
    main()
