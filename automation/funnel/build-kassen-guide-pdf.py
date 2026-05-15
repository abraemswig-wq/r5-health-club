#!/usr/bin/env python3
"""
Erstellt die Kassen-Guide-PDF, die als Lead-Magnet versendet wird.

Aufruf:
    python3 build-kassen-guide-pdf.py

Output: ../../downloads/kassen-guide.pdf
"""
from __future__ import annotations

import os
from pathlib import Path

from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether,
)

# ============================================================================
# Pfade & Farben
# ============================================================================

ROOT = Path(__file__).resolve().parents[2]  # /Users/.../rehab-five-gym/
OUT_PATH = ROOT / "downloads" / "kassen-guide.pdf"
OUT_PATH.parent.mkdir(exist_ok=True)

# CI-Farben
FOREST = HexColor("#1F342D")
FOREST_DARK = HexColor("#172620")
BRAND = HexColor("#D99129")
BRAND_DARK = HexColor("#A66819")
INK = HexColor("#1A1A1A")
INK_700 = HexColor("#4A4A4A")
INK_50 = HexColor("#FAFAFA")
INK_100 = HexColor("#F5F5F5")
LINE = HexColor("#E6E3DC")

PAGE_W, PAGE_H = A4

# ============================================================================
# Stile
# ============================================================================

ss = getSampleStyleSheet()

h1_style = ParagraphStyle(
    "h1", parent=ss["Heading1"],
    fontName="Helvetica-Bold", fontSize=26, leading=30,
    textColor=FOREST, spaceAfter=14, spaceBefore=0,
)
h2_style = ParagraphStyle(
    "h2", parent=ss["Heading2"],
    fontName="Helvetica-Bold", fontSize=16, leading=20,
    textColor=FOREST, spaceAfter=8, spaceBefore=14,
)
h3_style = ParagraphStyle(
    "h3", parent=ss["Heading3"],
    fontName="Helvetica-Bold", fontSize=12, leading=16,
    textColor=FOREST, spaceAfter=4, spaceBefore=10,
)
body_style = ParagraphStyle(
    "body", parent=ss["BodyText"],
    fontName="Helvetica", fontSize=10.5, leading=15,
    textColor=INK, spaceAfter=6, alignment=TA_LEFT,
)
small_style = ParagraphStyle(
    "small", parent=body_style,
    fontSize=9, leading=12, textColor=INK_700,
)
eyebrow_style = ParagraphStyle(
    "eyebrow", parent=ss["BodyText"],
    fontName="Helvetica-Bold", fontSize=8, leading=11,
    textColor=BRAND_DARK, spaceAfter=3, letterSpacing=2,
)
quick_style = ParagraphStyle(
    "quick", parent=body_style,
    fontSize=11, leading=16, textColor=INK,
    backColor=HexColor("#FBF1E0"),
    borderColor=HexColor("#F4D9A9"),
    borderWidth=0.5, borderPadding=12, borderRadius=4,
    spaceAfter=10, spaceBefore=4,
)

# ============================================================================
# Page-Template mit Header/Footer
# ============================================================================

def draw_page_chrome(canv: canvas.Canvas, doc):
    canv.saveState()
    page_num = canv.getPageNumber()

    # Header-Streifen (forest, schmal)
    canv.setFillColor(FOREST)
    canv.rect(0, PAGE_H - 1.0 * cm, PAGE_W, 1.0 * cm, fill=1, stroke=0)
    canv.setFillColor(white)
    canv.setFont("Helvetica-Bold", 9)
    canv.drawString(2 * cm, PAGE_H - 0.65 * cm, "REHAB FIVE HEALTH CLUB · Krankenkassen-Guide")
    canv.setFont("Helvetica", 8)
    canv.setFillColor(HexColor("#D99129"))
    canv.drawRightString(PAGE_W - 2 * cm, PAGE_H - 0.65 * cm, "rehab-five-health-club.com")

    # Footer
    canv.setFillColor(INK_700)
    canv.setFont("Helvetica", 8)
    if page_num > 1:
        canv.drawString(2 * cm, 1.0 * cm, f"Seite {page_num}")
    canv.drawCentredString(PAGE_W / 2, 1.0 * cm, "© REHAB FIVE · Friedrich-Ebert-Straße 122 · 48153 Münster")
    canv.drawRightString(PAGE_W - 2 * cm, 1.0 * cm, "0251 74788 200")

    # Brand-Strich am unteren Footer
    canv.setStrokeColor(BRAND)
    canv.setLineWidth(2)
    canv.line(2 * cm, 1.5 * cm, 4 * cm, 1.5 * cm)

    canv.restoreState()


def draw_cover_page(canv: canvas.Canvas, doc):
    """Cover-Seite: ganzseitig grün mit Headline."""
    canv.saveState()
    # forest Hintergrund
    canv.setFillColor(FOREST)
    canv.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    # Brand-Akzent
    canv.setFillColor(BRAND)
    canv.rect(0, 0, PAGE_W, 1 * cm, fill=1, stroke=0)

    # Eyebrow
    canv.setFillColor(BRAND)
    canv.setFont("Helvetica-Bold", 10)
    canv.drawString(2.5 * cm, PAGE_H - 4 * cm, "REHAB FIVE HEALTH CLUB · GRATIS-GUIDE")

    # Hauptüberschrift
    canv.setFillColor(white)
    canv.setFont("Helvetica-Bold", 32)
    canv.drawString(2.5 * cm, PAGE_H - 6.5 * cm, "100 % von der")
    canv.setFillColor(BRAND)
    canv.drawString(2.5 * cm, PAGE_H - 8.3 * cm, "Kasse zurück.")

    canv.setFillColor(white)
    canv.setFont("Helvetica", 13)
    canv.drawString(2.5 * cm, PAGE_H - 10.5 * cm, "Wie du die volle Erstattung für deinen")
    canv.drawString(2.5 * cm, PAGE_H - 11.3 * cm, "Präventionskurs bekommst. Schritt für Schritt.")

    # Stichpunkte
    canv.setFillColor(HexColor("#FBF1E0"))
    canv.setFont("Helvetica", 10)
    bullets = [
        "§20 SGB V erklärt — was die Kasse zahlen muss",
        "Vergleich: TK · AOK · Barmer · DAK · IKK · BKK",
        "4-Schritte-Ablauf — von Anmeldung bis Auszahlung",
        "Antrags-Vorlage für jede gesetzliche Krankenkasse",
        "Auch für Privatpatient:innen — was geht und wann",
    ]
    y = PAGE_H - 13.5 * cm
    for b in bullets:
        canv.setFillColor(BRAND)
        canv.drawString(2.5 * cm, y, "›")
        canv.setFillColor(white)
        canv.drawString(3.2 * cm, y, b)
        y -= 0.7 * cm

    # Foot-Info
    canv.setFillColor(HexColor("#D99129"))
    canv.setFont("Helvetica-Bold", 9)
    canv.drawString(2.5 * cm, 3.5 * cm, "12 SEITEN  ·  10 MIN LESEZEIT")
    canv.setFillColor(white)
    canv.setFont("Helvetica", 9)
    canv.drawString(2.5 * cm, 3.0 * cm, "Stand: Mai 2026 · Geschrieben vom REHAB FIVE Therapie-Team")
    canv.drawString(2.5 * cm, 2.5 * cm, "rehab-five-health-club.com  ·  Friedrich-Ebert-Straße 122, 48153 Münster")

    canv.restoreState()


# ============================================================================
# Inhalt
# ============================================================================

def build_story():
    story = []

    # =========================
    # Cover-Seite (leere Platzhalter, wird via PageTemplate gezeichnet)
    # =========================
    # Wir fügen einen Spacer hinzu, damit die Seite voll bleibt
    story.append(Spacer(1, PAGE_H - 3 * cm))
    story.append(PageBreak())

    # =========================
    # Seite 2 · Intro
    # =========================
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("KAPITEL 1", eyebrow_style))
    story.append(Paragraph("§20 SGB V – was das Gesetz wirklich sagt", h1_style))
    story.append(Paragraph(
        "§20 SGB V ist der Paragraph im Sozialgesetzbuch, der gesetzliche Krankenkassen "
        "verpflichtet, <b>Maßnahmen zur primären Prävention</b> zu fördern. Vereinfacht: "
        "deine Kasse darf — und soll — dich dabei unterstützen, gar nicht erst krank zu werden.",
        body_style
    ))
    story.append(Paragraph(
        "Konkret: bei einem ZPP-zertifizierten Präventionskurs (z.B. Rückenfit, Fit ab 50) "
        "erstattet die Kasse <b>bis zu 100 % der Kursgebühr</b> — bei zwei Kursen pro Jahr.",
        body_style
    ))

    story.append(Paragraph("Quick-Answer", h3_style))
    story.append(Paragraph(
        "<b>Wie viel zahlt die Kasse?</b> Gesetzliche Krankenkassen erstatten gemäß §20 SGB V "
        "in der Regel <b>bis zu 100 % der Kursgebühr</b> für zwei zertifizierte Kurse pro Jahr. "
        "Voraussetzung: ZPP-Zertifizierung des Kurses und mindestens 80 % Anwesenheit. "
        "Du zahlst zuerst selbst, reichst die Teilnahmebescheinigung ein, und bekommst das Geld "
        "direkt aufs Konto.",
        quick_style
    ))

    story.append(Paragraph("Wer wird gefördert?", h3_style))
    story.append(Paragraph(
        "Alle gesetzlich Versicherten ab dem 18. Lebensjahr. Familien-Versicherte und "
        "Studierende eingeschlossen. Privat-Versicherte: je nach Tarif (siehe Kapitel 5).",
        body_style
    ))

    story.append(Paragraph("Welche Kurse zählen?", h3_style))
    story.append(Paragraph(
        "Nur Kurse, die durch die <b>Zentrale Prüfstelle Prävention (ZPP)</b> zertifiziert sind. "
        "Die ZPP prüft Konzept, Qualifikation der Kursleitung, Inhalte und Dauer. Unser "
        "Rückenfit- und Fit-ab-50-Kurs sind ZPP-zertifiziert.",
        body_style
    ))

    story.append(PageBreak())

    # =========================
    # Seite 3 · 4 Schritte
    # =========================
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("KAPITEL 2", eyebrow_style))
    story.append(Paragraph("So funktioniert die Erstattung in 4 Schritten", h1_style))

    steps = [
        ("01", "Kurs auswählen und anmelden",
         "Du buchst online oder telefonisch deinen Kurs. Wir senden dir eine Bestätigung "
         "mit der ZPP-Kursnummer — die brauchst du später für deine Kasse."),
        ("02", "Mindestens 80 % teilnehmen",
         "Bei einem 8-Wochen-Kurs darfst du also 1–2 Mal fehlen. Wir führen eine Anwesenheitsliste."),
        ("03", "Teilnahmebescheinigung erhalten",
         "Nach der letzten Einheit bekommst du automatisch eine Bescheinigung mit Kursnummer, "
         "Datum, Anwesenheit und Stempel der Kursleitung."),
        ("04", "Bei der Kasse einreichen",
         "Per Post, E-Mail oder über die Kassen-App. Die Erstattung kommt meist innerhalb "
         "von 2–4 Wochen direkt aufs Konto."),
    ]
    for num, title, desc in steps:
        cell = Table(
            [[Paragraph(f'<font color="#D99129"><b>{num}</b></font>', h2_style),
              Paragraph(f'<b>{title}</b><br/>{desc}', body_style)]],
            colWidths=[1.5 * cm, 14 * cm], style=TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
            ])
        )
        story.append(cell)

    story.append(PageBreak())

    # =========================
    # Seite 4 · Kassen-Vergleich Tabelle
    # =========================
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("KAPITEL 3", eyebrow_style))
    story.append(Paragraph("Kassen-Vergleich (Stand 2026)", h1_style))
    story.append(Paragraph(
        "Die genaue Höhe der Erstattung variiert je nach Kasse und Tarif. "
        "Diese Tabelle zeigt typische Werte — bitte vor Buchung bei deiner Kasse bestätigen.",
        body_style
    ))
    story.append(Spacer(1, 0.5 * cm))

    table_data = [
        ["Kasse", "Erstattung pro Kurs", "Bonus-Programm?", "Anträge digital?"],
        ["Techniker Krankenkasse (TK)", "bis 100 %, max. 150 €", "Ja (TK-Bonus)", "Ja, TK-App"],
        ["AOK (regional)", "bis 100 %, 100–150 €", "Teilweise", "Meine AOK-App"],
        ["Barmer", "bis 100 %, max. 200 €", "Barmer-Bonus", "Barmer-App"],
        ["DAK-Gesundheit", "bis 100 %, max. 150 €", "Aktiv-Bonus", "DAK-App"],
        ["IKK / BKK", "Tarif-abhängig, 80–100 %", "Variabel", "Variabel"],
        ["KKH", "bis 100 %, max. 100 €", "KKH-Bonus", "Ja"],
        ["HKK", "bis 90 %, max. 150 €", "Ja", "Ja"],
    ]

    tbl = Table(table_data, colWidths=[5.5 * cm, 4.5 * cm, 3.5 * cm, 3 * cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), FOREST),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, INK_50]),
        ("GRID", (0, 0), (-1, -1), 0.3, LINE),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(
        "<b>Faustregel:</b> Bei unseren Kursen (149 €) ist 100 % Erstattung in fast allen "
        "Fällen drin. Du zahlst effektiv 0 €.",
        body_style
    ))

    story.append(PageBreak())

    # =========================
    # Seite 5 · Antrags-Vorlage
    # =========================
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("KAPITEL 4", eyebrow_style))
    story.append(Paragraph("Antrags-Vorlage zum Kopieren", h1_style))
    story.append(Paragraph(
        "Die meisten Kassen brauchen keinen formellen Antrag — nur die Teilnahmebescheinigung. "
        "Falls deine Kasse einen Anschreiben fordert, hier eine Vorlage:",
        body_style
    ))

    template_text = """
<b>Betreff:</b> Erstattung Präventionskurs nach §20 SGB V – Mitgliedsnummer [ID]<br/><br/>

Sehr geehrte Damen und Herren,<br/><br/>

als Mitglied der [KASSENNAME] (Mitgliedsnummer [DEINE ID]) reiche ich hiermit
die Bescheinigung über die erfolgreiche Teilnahme am ZPP-zertifizierten
Präventionskurs „[KURSNAME]" der REHAB FIVE GmbH ein.<br/><br/>

<b>Kursdaten:</b><br/>
· Kurs: [Rückenfit § 20 SGB V / Fit ab 50 § 20 SGB V]<br/>
· Anbieter: REHAB FIVE GmbH, Friedrich-Ebert-Straße 122, 48153 Münster<br/>
· ZPP-Kursnummer: [siehe Bescheinigung]<br/>
· Kursdauer: 8 Einheiten à 60 Minuten<br/>
· Teilnahmequote: über 80 % (siehe Bescheinigung)<br/>
· Kursgebühr: 149,00 €<br/><br/>

Ich bitte um Erstattung gemäß §20 SGB V auf folgendes Konto:<br/>
IBAN: [DEINE IBAN]<br/>
Inhaber: [DEIN NAME]<br/><br/>

Mit freundlichen Grüßen<br/>
[DEIN NAME]<br/>
[DATUM]
    """

    box_table = Table([[Paragraph(template_text, small_style)]],
                      colWidths=[16 * cm],
                      style=TableStyle([
                          ("BACKGROUND", (0, 0), (-1, -1), INK_50),
                          ("BOX", (0, 0), (-1, -1), 0.5, LINE),
                          ("LEFTPADDING", (0, 0), (-1, -1), 16),
                          ("RIGHTPADDING", (0, 0), (-1, -1), 16),
                          ("TOPPADDING", (0, 0), (-1, -1), 12),
                          ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                      ]))
    story.append(box_table)

    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(
        "<b>Tipp:</b> Viele Kassen haben Apps mit Beleg-einreichen-Funktion (TK, AOK, Barmer, "
        "DAK, IKK). Schneller als Post — meist Erstattung in 1–2 Wochen.",
        small_style
    ))

    story.append(PageBreak())

    # =========================
    # Seite 6 · Privat-Versicherte
    # =========================
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("KAPITEL 5", eyebrow_style))
    story.append(Paragraph("Was Privatpatient:innen wissen müssen", h1_style))

    story.append(Paragraph(
        "Auch private Krankenversicherungen (PKV) bezuschussen viele Präventionskurse — "
        "die Bedingungen unterscheiden sich aber je nach Tarif erheblich.",
        body_style
    ))

    story.append(Paragraph("Was die PKV typischerweise erstattet", h3_style))
    story.append(Paragraph(
        "· Tarife mit Gesundheitsförderung/Vorsorge-Modul: bis 100 % Erstattung<br/>"
        "· Basis-Tarife: oft 50–80 %, manchmal mit Eigenanteil<br/>"
        "· Heilfürsorge (Beamte): in der Regel anteilig",
        body_style
    ))

    story.append(Paragraph("Was du tun solltest", h3_style))
    story.append(Paragraph(
        "1. <b>Vor der Buchung</b> bei deiner PKV nachfragen — meist per Mail oder App.<br/>"
        "2. Frage konkret: Wird ein ZPP-zertifizierter Präventionskurs nach §20 SGB V erstattet?<br/>"
        "3. Falls ja: lass dir die Bedingungen schriftlich geben.",
        body_style
    ))

    story.append(Paragraph("Beihilfe (Beamte)", h3_style))
    story.append(Paragraph(
        "Für Beamte und ihre Familien zahlt die Beihilfe normalerweise einen Anteil "
        "(meist 50–70 %). Die PKV übernimmt den Rest. Genaue Sätze hängen vom Bundesland ab.",
        body_style
    ))

    story.append(PageBreak())

    # =========================
    # Seite 7 · 7 Stolperfallen
    # =========================
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("KAPITEL 6", eyebrow_style))
    story.append(Paragraph("Die 7 häufigsten Stolperfallen", h1_style))

    pitfalls = [
        ("Du verlierst die ZPP-Kursnummer", "Sicherheits-Tipp: Bestätigungs-Mail in einem Ordner Krankenkasse archivieren."),
        ("Anwesenheit unter 80 %", "Bei einem 8-Wochen-Kurs darfst du max. 2x fehlen — ab dem dritten Mal entfällt der Erstattungs-Anspruch."),
        ("Bescheinigung wird verspätet eingereicht", "Manche Kassen haben 1-Jahres-Frist. Direkt nach Kurs-Ende einreichen."),
        ("Falsche Kurs-Kategorie angegeben", "Bei Bewegungs-Kursen exakt Bewegungsgewohnheiten als Handlungsfeld nennen — nicht Stress oder Ernährung."),
        ("Zweiter Kurs vor Ablauf des Kalenderjahres", "Maximal 2 Kurse/Jahr — Ablauf orientiert sich am Kalender-Jahr, nicht am Mitgliedsjahr."),
        ("Selbstbeteiligung übersehen", "Einige Kassen verlangen eine Selbstbeteiligung von 10–25 %. Steht in der Erstattungs-Bestätigung."),
        ("Bonus-Programm vergessen", "Viele Kassen geben zusätzlich 100–200 € Bonus, wenn du Präventionskurse als aktive Maßnahme ins Bonusheft einträgst."),
    ]

    for i, (title, text) in enumerate(pitfalls, 1):
        story.append(Paragraph(f"<b>{i:02d}. {title}</b>", h3_style))
        story.append(Paragraph(text, small_style))
        story.append(Spacer(1, 0.3 * cm))

    story.append(PageBreak())

    # =========================
    # Seite 8 · FAQ
    # =========================
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("KAPITEL 7", eyebrow_style))
    story.append(Paragraph("FAQ — die häufigsten Fragen", h1_style))

    faqs = [
        ("Wie viel zahlt die Kasse für einen Präventionskurs?",
         "Gesetzliche Krankenkassen erstatten gemäß §20 SGB V <b>bis zu 100 % der Kursgebühr</b> — zweimal pro Jahr."),
        ("Welche Voraussetzungen muss ich erfüllen?",
         "Du musst gesetzlich versichert sein, an mindestens <b>80 % der Einheiten</b> teilnehmen und den Kurs vollständig abschließen. Eine ärztliche Verordnung ist nicht nötig."),
        ("Brauche ich eine ärztliche Verordnung?",
         "Nein. Präventionskurse nach §20 SGB V sind <b>ohne Rezept</b> buchbar — das ist der Unterschied zur klassischen Heilmittel-Verordnung."),
        ("Was kostet der Kurs bei euch?",
         "Unsere ZPP-Kurse (Rückenfit, Fit ab 50) kosten 149 € für 8 Einheiten à 60 Minuten. Bei voller Kassen-Erstattung zahlst du effektiv 0 €."),
        ("Kann ich auch als Privatpatient teilnehmen?",
         "Ja. Privat Versicherte können je nach Tarif eine Erstattung beantragen — viele PKVs bezuschussen Präventionskurse anteilig."),
        ("Was, wenn ich einen Termin verpasse?",
         "Für die Erstattung müssen <b>80 % der Einheiten</b> besucht werden — bei 8 Wochen darfst du bis zu 2× fehlen."),
    ]

    for q, a in faqs:
        story.append(Paragraph(q, h3_style))
        story.append(Paragraph(a, small_style))
        story.append(Spacer(1, 0.25 * cm))

    story.append(PageBreak())

    # =========================
    # Seite 9 · Nächste Schritte
    # =========================
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("DEIN NÄCHSTER SCHRITT", eyebrow_style))
    story.append(Paragraph("So geht's bei uns los", h1_style))

    story.append(Paragraph(
        "Du hast den Guide gelesen — jetzt geht's um die Praxis. Bei uns im REHAB FIVE "
        "HEALTH CLUB läuft es so:",
        body_style
    ))

    next_steps_table = Table(
        [
            ["1.", "Probestunde buchen",
             "Kostenfrei, unverbindlich. Online oder telefonisch unter 0251 74788 200."],
            ["2.", "Vorgespräch + Bewegungsanamnese",
             "15 Minuten vor Ort, damit wir wissen, wo du stehst und was sicher ist."],
            ["3.", "Erste Kursstunde mitmachen",
             "Du lernst Methode, Trainer:in und Gruppe kennen. Keine Verpflichtung."],
            ["4.", "Kurs buchen",
             "Bei §20-Kursen (Rückenfit / Fit ab 50): 149 €, von der Kasse erstattet."],
        ],
        colWidths=[1 * cm, 4 * cm, 11 * cm],
        style=TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("TEXTCOLOR", (0, 0), (0, -1), BRAND),
            ("FONTSIZE", (0, 0), (0, -1), 12),
            ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (1, 0), (1, -1), 11),
            ("FONTSIZE", (2, 0), (2, -1), 10),
            ("TEXTCOLOR", (2, 0), (2, -1), INK_700),
        ])
    )
    story.append(next_steps_table)

    story.append(Spacer(1, 1 * cm))

    # CTA-Box
    cta_para = Paragraph(
        '<font color="#FBF1E0" size="10"><b>PROBESTUNDE SICHERN</b></font><br/>'
        '<font color="white" size="16"><b>Komm vorbei. Kostenlos.</b></font><br/><br/>'
        '<font color="white" size="10">Online: rehab-five-health-club.com<br/>'
        'Telefon: 0251 74788 200<br/>'
        'E-Mail: info@rehab-five.com</font>',
        ParagraphStyle("cta", parent=body_style, alignment=TA_LEFT, leading=14)
    )
    cta_box = Table([[cta_para]], colWidths=[16 * cm],
                    style=TableStyle([
                        ("BACKGROUND", (0, 0), (-1, -1), FOREST),
                        ("LEFTPADDING", (0, 0), (-1, -1), 22),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 22),
                        ("TOPPADDING", (0, 0), (-1, -1), 22),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 22),
                    ]))
    story.append(cta_box)

    story.append(Spacer(1, 1 * cm))

    # Impressum-Block
    story.append(Paragraph("Über REHAB FIVE", h3_style))
    story.append(Paragraph(
        "REHAB FIVE ist seit über 10 Jahren in Münster aktiv — mit Physiotherapie an drei "
        "Standorten und dem Health Club an der Friedrich-Ebert-Straße 122. 5,0 Sterne bei "
        "über 100 Google-Bewertungen. Mehr unter <b>rehab-five.com</b>.",
        small_style
    ))

    return story


# ============================================================================
# Build
# ============================================================================

def build_pdf():
    # Erste Seite hat das Cover-Layout, danach Standard-Chrome
    frame_cover = Frame(0, 0, PAGE_W, PAGE_H, leftPadding=0, rightPadding=0,
                        topPadding=0, bottomPadding=0, id="cover")
    cover_template = PageTemplate(id="cover", frames=frame_cover,
                                  onPage=draw_cover_page)

    frame_content = Frame(2 * cm, 2 * cm,
                          PAGE_W - 4 * cm, PAGE_H - 4 * cm,
                          leftPadding=0, rightPadding=0,
                          topPadding=0, bottomPadding=0, id="content")
    content_template = PageTemplate(id="content", frames=frame_content,
                                    onPage=draw_page_chrome)

    doc = BaseDocTemplate(
        str(OUT_PATH),
        pagesize=A4,
        title="REHAB FIVE HEALTH CLUB · Krankenkassen-Guide",
        author="REHAB FIVE Therapie-Team",
        subject="100 % Krankenkassen-Erstattung für Präventionskurse",
        keywords="§20 SGB V, ZPP, Krankenkasse, Präventionskurs, REHAB FIVE",
    )
    doc.addPageTemplates([cover_template, content_template])

    story = build_story()
    doc.build(story)

    print(f"✓ PDF erstellt: {OUT_PATH}")
    print(f"  Größe: {OUT_PATH.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    build_pdf()
