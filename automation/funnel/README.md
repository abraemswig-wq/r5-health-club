# Lead-Magnet-Funnel · Kassen-Guide

3-Mail-Sequence für jeden Lead, der den Krankenkassen-Guide auf rehab-five-health-club.com/kassen-guide/ angefordert hat.

## Wie es läuft

```
Jemand füllt das Formular aus
      ↓
FormSubmit forwarded an a.braemswig@rehab-five.com
      ↓
Du kopierst die E-Mail-Adresse + Vorname
      ↓
Du startest 1 Befehl im Terminal
      ↓
Resend versendet alle 3 Mails automatisch
   · Mail 1 sofort (mit PDF-Anhang)
   · Mail 2 in 3 Tagen
   · Mail 3 in 7 Tagen
      ↓
Du musst nichts mehr tun
```

## Der eine Befehl

```bash
cd /Users/aricbramswig/Downloads/rehab-five-gym/automation/funnel
python3 send-kassen-funnel.py max@example.com Maximilian
```

Das war's. **Resend's Scheduled-Versand** kümmert sich um den Rest — auch wenn dein Mac in der Zwischenzeit aus ist.

## Setup · einmalig

### 1. Resend API-Key (falls noch nicht da)

Brauchst du eh für die Wissens-Artikel-Pipeline:

```bash
export RESEND_API_KEY=re_DEINSCHLÜSSEL
```

Oder besser dauerhaft in `~/.zshrc` oder `~/.bashrc` ablegen. Oder in `automation/.env` (wird von der Sister-Pipeline geladen).

### 2. PDF einmal bauen

```bash
python3 build-kassen-guide-pdf.py
```

Erstellt `downloads/kassen-guide.pdf` (12 Seiten, ~20 KB). Wird automatisch in Mail 1 angehängt.

### 3. Test-Run

```bash
python3 send-kassen-funnel.py --test
```

Sendet alle 3 Mails an dich selbst (`a.braemswig@rehab-five.com`).

Du bekommst:
- **Sofort**: Mail 1 mit PDF-Anhang
- **In 3 Tagen**: Mail 2 (Kassen-spezifischer Tipp)
- **In 7 Tagen**: Mail 3 (Soft-CTA Kaffee)

## Wie du echte Leads einspielst

Du bekommst eine FormSubmit-Mail mit den Daten so:

```
Vorname:  Maximilian
Email:    max.muster@gmail.com
Krankenkasse: Techniker Krankenkasse (TK)
```

Im Terminal:

```bash
cd ~/Downloads/rehab-five-gym/automation/funnel
python3 send-kassen-funnel.py max.muster@gmail.com Maximilian
```

**Fertig.** Maximilian bekommt jetzt automatisch die 3 Mails in den nächsten 7 Tagen.

## Audit-Log

Jeder Funnel-Trigger wird in `leads.jsonl` protokolliert (eine Zeile pro Lead).

```bash
cat leads.jsonl | tail -5
```

So siehst du, wer wann durch den Funnel ging.

## Erwartete Conversion-Rate

Industry-Benchmark für Lead-Magnet-Funnel im B2C-Gesundheitsbereich:

| Stelle | Typische Rate | Bei dir realistisch |
|---|---|---|
| LP-Conversion (Form-Abschluss) | 8–15 % der Besucher | 10–20 % (klares Versprechen) |
| Mail 1 Open-Rate | 60–80 % | 70–85 % (eigene Anfrage) |
| Mail 2 Open-Rate | 35–50 % | 40–55 % |
| Mail 3 Open-Rate | 25–40 % | 30–45 % |
| Probestunden-Buchung aus Funnel | 5–15 % der Leads | 10–20 % |

**Konkret**: 100 Guide-Anfragen → ~15 Probestunden → ~5–8 Neumitglieder. Bei Flat-Mitgliedschaft (79 €) sind das ~400 € MRR (Monatlich wiederkehrender Umsatz) **pro Wave**.

## Dateien

```
automation/funnel/
├── README.md                     ← du bist hier
├── build-kassen-guide-pdf.py     ← PDF-Generator (einmalig)
├── send-kassen-funnel.py         ← Funnel-Trigger (pro Lead)
├── mail-1-welcome.html           ← Mail 1 Template
├── mail-2-kassen.html            ← Mail 2 Template
├── mail-3-coffee.html            ← Mail 3 Template
└── leads.jsonl                   ← Audit-Log

downloads/
└── kassen-guide.pdf              ← der eigentliche Guide
```

## Anpassung der Templates

Wenn du Texte oder Designs anpassen willst:

1. Öffne `mail-1-welcome.html` / `mail-2-kassen.html` / `mail-3-coffee.html`
2. Ändere was du willst — `{{FIRSTNAME}}` ist der einzige Platzhalter
3. Speichern, fertig — beim nächsten Funnel-Trigger ist die Änderung live

## Anpassung der Versand-Verzögerung

In `send-kassen-funnel.py` ganz oben:

```python
DELAYS = {
    "mail-1-welcome": 0,    # Sofort
    "mail-2-kassen": 3,     # +3 Tage
    "mail-3-coffee": 7,     # +7 Tage
}
```

Anpassen wenn andere Intervalle gewünscht.

## Voll-automatisieren (später, optional)

Aktuell musst du jeden Lead **manuell** auslösen. Wenn du das später vollautomatisch willst (Form-Submit → Auto-Funnel ohne Terminal), bauen wir eine Cloudflare-Worker-Integration. Dauert ~30 Min. Setup, dann läuft alles dauerhaft.

Bis dahin: der manuelle Workflow ist 30 Sekunden Aufwand pro Lead und behält dir die Kontrolle.

## Was im PDF steht

Der `kassen-guide.pdf` enthält 12 Seiten:

1. **Cover** (forest, branded)
2. **§20 SGB V einfach erklärt**
3. **4-Schritte-Erstattungs-Ablauf**
4. **Kassen-Vergleich** (TK · AOK · Barmer · DAK · IKK · BKK · KKH · HKK)
5. **Antrags-Vorlage** (zum Kopieren)
6. **Privatpatient:innen-Spezial**
7. **7 häufigste Stolperfallen**
8. **FAQ**
9. **Nächste Schritte** (CTA zu uns)

Wenn du den Guide aktualisieren willst: `build-kassen-guide-pdf.py` öffnen, Inhalt anpassen, neu bauen.

## DSGVO-Compliance

Das Formular auf der LP hat ein Pflicht-Häkchen für die Datenschutzerklärung. Die `leads.jsonl` darf nur lokal liegen (nicht auf GitHub gepusht). Im Footer jeder Mail ist ein Abmelde-Link:

```html
<a href="mailto:info@rehab-five.com?subject=Bitte%20austragen">Hier abmelden</a>
```

Wenn jemand abmelden möchte: Lead in `leads.jsonl` markieren und keine weiteren manuellen Funnel-Trigger mehr. Bei einem voll-automatisierten Setup (Cloudflare Worker) müsste eine Suppression-Liste implementiert werden.
