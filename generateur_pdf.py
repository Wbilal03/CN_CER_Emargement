from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4, landscape
from io import BytesIO
from PIL import Image as PILImage

def generate_pdf(meeting_name, participants_data):
    """
    Génère un PDF en mémoire pour la feuille d'émargement avec 2 jours et signatures.
    """
    buffer = BytesIO()
    # Orientation paysage pour mieux tenir les colonnes
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
    elements = []
    styles = getSampleStyleSheet()

    # Titre
    elements.append(Paragraph(f"Feuille d'émargement - {meeting_name}", styles["Heading1"]))
    elements.append(Spacer(1, 0.2*inch))

    # En-têtes tableau
    table_data = [["Nom", "Poste", "Entreprise", "Jour1", "Signature J1", "Jour2", "Signature J2"]]

    for p in participants_data:
        # Signature Jour 1
        sig_j1 = ""
        if p.get("Signature_Jour1") is not None:
            sig_buf = BytesIO()
            p["Signature_Jour1"].save(sig_buf, format="PNG")
            sig_buf.seek(0)
            sig_j1 = Image(sig_buf, width=0.8*inch, height=0.3*inch)

        # Signature Jour 2
        sig_j2 = ""
        if p.get("Signature_Jour2") is not None:
            sig_buf = BytesIO()
            p["Signature_Jour2"].save(sig_buf, format="PNG")
            sig_buf.seek(0)
            sig_j2 = Image(sig_buf, width=0.8*inch, height=0.3*inch)

        row = [
            p["Nom"],
            p["Poste"],
            Paragraph(str(p["Entreprise"]), styles["BodyText"]),
            p["Jour1"],
            sig_j1,
            p["Jour2"],
            sig_j2
        ]
        table_data.append(row)

    # Largeurs de colonnes ajustées
    col_widths = [1.3*inch, 1.2*inch, 2.5*inch, 0.7*inch, 0.8*inch, 0.7*inch, 0.8*inch]

    table = Table(table_data, colWidths=col_widths, hAlign="LEFT")
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(table)

    # Construire le PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer
