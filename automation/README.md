# REHAB FIVE HEALTH CLUB · Auto-Artikel-Pipeline

Wöchentlich neuen Wissens-Artikel generieren → per Mail an `a.braemswig@rehab-five.com` → nach Lesefreigabe live stellen.

## Was passiert?

```
Montag 8:00 Uhr            Dienstag (du)              Mittwoch (du)
─────────────────────       ─────────────────         ─────────────────
1. generate.py wählt        4. Mail in Posteingang    6. python3 publish.py
   nächstes Thema aus          „Artikel zur            → Datei in
   topics.md                    Freigabe"               /wissen/<slug>/
                                                       → Sitemap update
2. Claude schreibt          5. Du liest die           → topic Status auf
   den Artikel im              Vorschau                 'published'
   AI-SEO-Pattern             → antwortest 'go'
                              (oder 'fix' / 'skip')
3. send-preview.py
   schickt Vorschau
   per Resend
```

## Setup · einmalig, ca. 15 Minuten

### 1. Google Gemini API-Key (5 Min., gratis)

1. Gehe zu **https://aistudio.google.com/app/apikey**
2. Mit deinem Google-Account einloggen (bestehender Firmen-Account funktioniert)
3. **Create API Key** → wähle ein Google-Cloud-Projekt (oder „Create API Key in new project")
4. Schlüssel kopieren
5. **Free Tier**: 1.500 Anfragen/Tag bei Gemini 1.5 Pro — wir brauchen ~4/Monat → komplett kostenlos

### 2. Resend Account (5 Min.)

1. Gehe zu **https://resend.com/signup**
2. Mit Google oder Mail-Adresse anmelden (kostenlos, 100 Mails/Tag inklusive)
3. Links im Menü: **API Keys** → **Create API Key**
4. Name: `rehab-five-health-club`
5. Permission: **Sending access**
6. Schlüssel kopieren (beginnt mit `re_...`)

**Optional (später)**: Eigene Domain `rehab-five-health-club.com` verifizieren, damit Mails von `noreply@rehab-five-health-club.com` kommen statt `onboarding@resend.dev`. → **Domains → Add Domain** in Resend, dann DNS-Eintrag bei deinem Domain-Hoster.

### 3. Lokales Setup (5 Min.)

Terminal öffnen:

```bash
cd /Users/aricbramswig/Downloads/rehab-five-gym/automation

# Python-Pakete installieren (einmalig)
pip3 install google-generativeai requests

# .env-Datei anlegen
cat > .env <<EOF
GEMINI_API_KEY=DEINSCHLUESSEL
RESEND_API_KEY=re_DEINSCHLUESSEL
REVIEWER_EMAIL=a.braemswig@rehab-five.com
FROM_EMAIL=onboarding@resend.dev
EOF

# Test-Run
./weekly-run.sh
```

Wenn alles klappt: in 30 Sekunden landet eine Vorschau-Mail in deinem Posteingang.

## Tägliche / wöchentliche Nutzung

### Manueller Run (jederzeit)

```bash
cd /Users/aricbramswig/Downloads/rehab-five-gym/automation
./weekly-run.sh
```

### Wöchentlicher Auto-Run (Empfehlung: Montag 8 Uhr)

macOS `launchd` ist die richtige Stelle. Lege folgende Datei an:

```bash
nano ~/Library/LaunchAgents/com.rehab-five.weekly-article.plist
```

Inhalt (Pfade anpassen falls nötig):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.rehab-five.weekly-article</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/aricbramswig/Downloads/rehab-five-gym/automation/weekly-run.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Weekday</key>
        <integer>1</integer>
        <key>Hour</key>
        <integer>8</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/aricbramswig/Downloads/rehab-five-gym/automation/logs/launchd.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/aricbramswig/Downloads/rehab-five-gym/automation/logs/launchd-error.log</string>
</dict>
</plist>
```

Aktivieren:

```bash
launchctl load ~/Library/LaunchAgents/com.rehab-five.weekly-article.plist
```

→ Jeden Montag 8:00 Uhr generiert dein Mac automatisch den nächsten Artikel und schickt ihn an dich.

**Wichtig**: Mac muss zu der Uhrzeit an sein (nicht im Standby). Falls Mac über Nacht aus ist: einfach Mittag-Termin wählen (Hour=12).

### Wenn du eine Antwort gibst

Du bekommst die Vorschau-Mail. Du antwortest mit:

| Antwort | Was passiert |
|---|---|
| `go` | Artikel publishen — du musst das Skript nur einmal selber starten |
| `fix` + Kommentar | Status zurück auf `idea`, neu schreiben nächste Woche (mit deinem Feedback) |
| `skip` | Thema verwerfen, beim nächsten Run ein anderes |

**Ein-Befehl-Publish**:

```bash
cd /Users/aricbramswig/Downloads/rehab-five-gym/automation
python3 publish.py --latest
```

Das war's. Datei landet automatisch in `/wissen/<slug>/index.html` + Sitemap wird aktualisiert.

**Online stellen**: Nach dem Publish lädst du den Ordner-Inhalt auf dein Hosting:
- Falls Netlify: einfach den ganzen `rehab-five-gym/` Ordner auf [app.netlify.com/drop](https://app.netlify.com/drop) neu ziehen (er erkennt was sich geändert hat)
- Falls eigener Server: FTP-Upload der neuen Dateien

## Themen-Backlog pflegen

In `topics.md` kannst du:

- **Neue Themen hinzufügen**: Format wie die bestehenden (T-028, T-029, ...)
- **Prioritäten ändern**: P1/P2/P3 anpassen
- **Themen überspringen**: Status auf `skip` setzen
- **Themen erneut versuchen**: Status zurück auf `idea`

Status-Zustände:

- `idea` → bereit zum Generieren
- `pending-review` → wartet auf Lesefreigabe von dir
- `published` → live
- `skip` → verworfen

## Was kostet das?

| Dienst | Kosten |
|---|---|
| Google Gemini API (1.5 Pro) | **0 €** im Free Tier (1.500 Anfragen/Tag) |
| Resend (E-Mail-Versand) | **0 €** bis 100 Mails/Tag |
| **Total** | **0 €** pro Monat |

## Fehlersuche

### „GEMINI_API_KEY nicht gesetzt"

→ `.env`-Datei prüfen. Pfad: `automation/.env`. Inhalt siehe Setup oben.

### Mail kommt nicht an

1. Schau in den Spam-Ordner
2. Bei Resend → **Logs** → siehst du, ob die Mail versendet wurde
3. Falls Resend „Delivered" zeigt, aber nichts ankommt: SPF/DKIM für deine Mail-Domain prüfen

### Artikel-Qualität schlecht

→ In `topics.md` einen besseren `Quick-Answer-Pitch` schreiben. Claude orientiert sich daran.

→ Oder das `SYSTEM_PROMPT` in `generate.py` schärfen (z.B. „Vermeide das Wort 'optimal'").

### Status hängt auf `pending-review`

→ Manuell setzen: in `topics.md` den Status zurück auf `idea` schreiben.

### Generator nimmt das „falsche" Thema

→ Erzwingen mit: `python3 generate.py --topic T-007`

## Dateien

```
automation/
├── README.md              ← du bist hier
├── .env                   ← deine API-Keys (NIE in Git pushen!)
├── topics.md              ← Themen-Backlog (27 Ideen)
├── generate.py            ← Artikel-Generator
├── preview-template.html  ← Mail-Template
├── send-preview.py        ← Mail-Versand
├── publish.py             ← Artikel ins /wissen/ kopieren
├── weekly-run.sh          ← Wrapper für launchd
├── drafts/                ← aktuelle Entwürfe (wartet auf Freigabe)
├── published/             ← Archiv aller versendeten Entwürfe
└── logs/                  ← Run-Logs
```

## Sicherheits-Hinweis

`.env` enthält API-Keys. Falls du den `rehab-five-gym/` Ordner irgendwann mit jemandem teilst oder auf GitHub hochlädst:

```bash
# .gitignore anlegen (falls noch nicht da)
echo "automation/.env" >> .gitignore
echo "automation/drafts/*.html" >> .gitignore
echo "automation/drafts/*.meta" >> .gitignore
echo "automation/published/" >> .gitignore
echo "automation/logs/" >> .gitignore
```
