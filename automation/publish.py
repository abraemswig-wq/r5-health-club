#!/usr/bin/env python3
"""
REHAB FIVE HEALTH CLUB · Artikel-Publish

Kopiert einen Entwurf von drafts/ ins finale /wissen/<slug>/index.html,
ergänzt die Sitemap und aktualisiert den Status in topics.md.

Aufruf:
    python3 publish.py <draft-dateiname>
    python3 publish.py 2026-05-22-homeoffice-rueckenuebungen.html
    python3 publish.py --latest    # jüngsten Entwurf publishen
    python3 publish.py --check     # nur prüfen, was passieren würde
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
import sys
from pathlib import Path

# ============================================================================
# Pfade
# ============================================================================

ROOT = Path(__file__).resolve().parent
DRAFTS_DIR = ROOT / "drafts"
PUBLISHED_DIR = ROOT / "published"  # Archiv der versendeten Entwürfe
SITE_ROOT = ROOT.parent
WISSEN_DIR = SITE_ROOT / "wissen"
SITEMAP_FILE = SITE_ROOT / "sitemap.xml"
TOPICS_FILE = ROOT / "topics.md"

PUBLISHED_DIR.mkdir(exist_ok=True)


# ============================================================================
# Meta + Sitemap
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


def add_to_sitemap(slug: str, today: dt.date):
    """Fügt den neuen Artikel zur sitemap.xml hinzu (falls noch nicht da)."""
    if not SITEMAP_FILE.exists():
        print(f"  ⚠️  {SITEMAP_FILE} existiert nicht — überspringe Sitemap-Update.")
        return False

    text = SITEMAP_FILE.read_text(encoding="utf-8")
    url = f"https://rehab-five-health-club.com/wissen/{slug}/"

    if url in text:
        print(f"  → Sitemap enthält bereits {url}, überspringe.")
        return False

    new_entry = f"""  <url>
    <loc>{url}</loc>
    <lastmod>{today.isoformat()}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>
</urlset>"""
    text = text.replace("</urlset>", new_entry)
    SITEMAP_FILE.write_text(text, encoding="utf-8")
    print(f"  ✓ Sitemap aktualisiert.")
    return True


def update_topic_status(topic_id: str, new_status: str):
    """Setzt den Status eines Themas in topics.md."""
    if not topic_id:
        return
    text = TOPICS_FILE.read_text(encoding="utf-8")
    pattern = rf"(### {re.escape(topic_id)} · [^\n]+\n(?:- [^\n]+\n)*?- \*\*P\*\*: \d · \*\*Saison\*\*: [^·]+· \*\*Status\*\*: )([^\n]+)"
    new_text, count = re.subn(pattern, rf"\g<1>{new_status}", text)
    if count == 0:
        print(f"  ⚠️  Status für {topic_id} konnte nicht aktualisiert werden — bitte manuell.")
        return
    TOPICS_FILE.write_text(new_text, encoding="utf-8")
    print(f"  ✓ Status {topic_id} → '{new_status}'")


def update_wissen_hub(slug: str, title: str):
    """Hinweis: Wissen-Hub kann ebenfalls auto-aktualisiert werden — TODO."""
    # NOTE: aktuell ist /wissen/index.html statisch gepflegt.
    # Diese Funktion ist Platzhalter für späteres Auto-Update.
    print(f"  ℹ️  Wissen-Hub manuell pflegen: /wissen/index.html → neue Karte für {slug}")


def update_homepage_wissen_section(slug: str, title: str):
    """Hinweis: Homepage-Wissen-Sektion ebenfalls statisch — TODO."""
    print(f"  ℹ️  Homepage manuell prüfen: /index.html (Wissen-Sektion) → Karte für {slug}")


# ============================================================================
# Publish
# ============================================================================

def publish(draft_path: Path, dry_run: bool = False):
    meta_path = draft_path.with_suffix(".meta")
    meta = read_meta(meta_path)

    slug = meta.get("slug")
    title = meta.get("title", "")
    topic_id = meta.get("topic_id", "")
    today = dt.date.today()

    if not slug:
        # Versuch: Slug aus Dateinamen extrahieren
        # Format: YYYY-MM-DD-slug-name.html
        name_match = re.match(r"\d{4}-\d{2}-\d{2}-(.+)\.html$", draft_path.name)
        if name_match:
            slug = name_match.group(1)
            print(f"  → Slug aus Dateinamen extrahiert: {slug}")
        else:
            print(f"FEHLER: Slug konnte nicht ermittelt werden. Meta-Datei fehlt: {meta_path}")
            sys.exit(1)

    target_dir = WISSEN_DIR / slug
    target_file = target_dir / "index.html"

    print(f"Publish-Plan:")
    print(f"  Quelle:  {draft_path.relative_to(SITE_ROOT)}")
    print(f"  Ziel:    {target_file.relative_to(SITE_ROOT)}")
    print(f"  Slug:    {slug}")
    print(f"  Topic:   {topic_id or '?'}")
    print()

    if target_file.exists():
        print(f"  ⚠️  Zieldatei existiert bereits.")
        if not dry_run:
            response = input("  Überschreiben? (y/N): ").strip().lower()
            if response != "y":
                print("  Abgebrochen.")
                sys.exit(0)

    if dry_run:
        print("[DRY-RUN] Würde Datei kopieren, Sitemap erweitern, Topic-Status setzen.")
        return

    # 1. Verzeichnis anlegen
    target_dir.mkdir(parents=True, exist_ok=True)

    # 2. Datei kopieren
    shutil.copy2(draft_path, target_file)
    print(f"  ✓ Datei kopiert: {target_file.relative_to(SITE_ROOT)}")

    # 3. Sitemap erweitern
    add_to_sitemap(slug, today)

    # 4. Topic-Status auf 'published'
    if topic_id:
        update_topic_status(topic_id, "published")

    # 5. Manuelle Schritte hinweisen
    update_wissen_hub(slug, title)
    update_homepage_wissen_section(slug, title)

    # 6. Entwurf ins Archiv verschieben
    archive = PUBLISHED_DIR / draft_path.name
    shutil.move(str(draft_path), str(archive))
    print(f"  ✓ Entwurf ins Archiv verschoben: published/{draft_path.name}")
    if meta_path.exists():
        shutil.move(str(meta_path), str(PUBLISHED_DIR / meta_path.name))

    print()
    print(f"✓ Artikel ist live (lokal): {target_file.relative_to(SITE_ROOT)}")
    print(f"  URL nach Deploy: https://rehab-five-health-club.com/wissen/{slug}/")
    print()
    print("Nicht vergessen:")
    print("  - Datei auf Hosting hochladen (Netlify Drop oder FTP)")
    print("  - Wissen-Hub /wissen/index.html ergänzen (Karte hinzufügen)")
    print("  - Homepage Wissen-Sektion ergänzen (oder älteren Eintrag ersetzen)")


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="REHAB FIVE HEALTH CLUB Publish")
    parser.add_argument("filename", nargs="?", help="Entwurf-Dateiname")
    parser.add_argument("--latest", action="store_true", help="Jüngsten Entwurf publishen")
    parser.add_argument("--check", action="store_true", help="Nur Plan anzeigen, nicht ausführen")
    args = parser.parse_args()

    if args.latest or not args.filename:
        drafts = sorted(DRAFTS_DIR.glob("*.html"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not drafts:
            print("FEHLER: Keine Entwürfe in drafts/")
            sys.exit(1)
        draft_path = drafts[0]
        print(f"  → Jüngster Entwurf: {draft_path.name}")
    else:
        draft_path = DRAFTS_DIR / args.filename
        if not draft_path.exists():
            print(f"FEHLER: {draft_path} nicht gefunden.")
            sys.exit(1)

    print(f"REHAB FIVE HEALTH CLUB · Artikel publishen")
    print("=" * 60)
    publish(draft_path, dry_run=args.check)


if __name__ == "__main__":
    main()
