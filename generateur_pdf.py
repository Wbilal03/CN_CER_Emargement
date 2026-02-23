from datetime import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def generate_pdf(meeting_name, participants_data, include_day2=True):
    """
    Genere un PDF en memoire pour la feuille d'emargement.
    Si include_day2=False, seules les colonnes Jour 1 sont affichees.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=0.45 * inch,
        rightMargin=0.45 * inch,
    )
    elements = []
    styles = getSampleStyleSheet()

    date_du_jour = datetime.today().strftime("%d/%m/%Y")
    elements.append(Paragraph(f"Feuille d'emargement - {meeting_name} - {date_du_jour}", styles["Heading1"]))
    elements.append(Spacer(1, 0.2 * inch))

    if include_day2:
        table_data = [["Nom", "Poste", "Entreprise", "Jour1", "Signature J1", "Jour2", "Signature J2"]]
    else:
        table_data = [["Nom", "Poste", "Entreprise", "Jour1", "Signature J1"]]

    for p in participants_data:
        sig_j1 = ""
        if p.get("Signature_Jour1") is not None:
            sig_buf = BytesIO()
            p["Signature_Jour1"].save(sig_buf, format="PNG")
            sig_buf.seek(0)
            sig_j1 = Image(sig_buf, width=0.8 * inch, height=0.3 * inch)

        row = [
            Paragraph(str(p["Nom"]), styles["BodyText"]),
            str(p["Poste"]).replace("\n", " "),
            Paragraph(str(p["Entreprise"]), styles["BodyText"]),
            p["Jour1"],
            sig_j1,
        ]

        if include_day2:
            sig_j2 = ""
            if p.get("Signature_Jour2") is not None:
                sig_buf = BytesIO()
                p["Signature_Jour2"].save(sig_buf, format="PNG")
                sig_buf.seek(0)
                sig_j2 = Image(sig_buf, width=0.8 * inch, height=0.3 * inch)
            row.extend([p["Jour2"], sig_j2])

        table_data.append(row)

    if include_day2:
        col_widths = [1.0 * inch, 1.0 * inch, 2.0 * inch, 0.7 * inch, 1.0 * inch, 0.7 * inch, 1.0 * inch]
    else:
        col_widths = [1.3 * inch, 1.3 * inch, 2.3 * inch, 0.9 * inch, 1.4 * inch]

    table = Table(table_data, colWidths=col_widths, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    elements.append(table)

    doc.build(elements)
    buffer.seek(0)
    return buffer
