from datetime import datetime
from io import BytesIO
from pathlib import Path

try:
    from pypdf import PdfReader, PdfWriter
    HAS_PYPDF = True
except Exception:
    PdfReader = None
    PdfWriter = None
    HAS_PYPDF = False
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import Image, Paragraph, Table, TableStyle

TEMPLATE_PDF = Path(__file__).with_name("Doc1.pdf")


def _build_table(participants_data, include_day2, styles):
    if include_day2:
        table_data = [["Nom", "Poste", "Entreprise", "Jour1", "Signature J1", "Jour2", "Signature J2"]]
        col_widths = [1.0 * inch, 1.0 * inch, 2.0 * inch, 0.7 * inch, 1.0 * inch, 0.7 * inch, 1.0 * inch]
    else:
        table_data = [["Nom", "Poste", "Entreprise", "Jour1", "Signature J1"]]
        col_widths = [1.3 * inch, 1.3 * inch, 2.3 * inch, 0.9 * inch, 1.4 * inch]

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

    table = Table(table_data, colWidths=col_widths, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return table


def _create_overlay_pdf(meeting_name, participants_data, include_day2, page_width, page_height):
    overlay_buffer = BytesIO()
    c = canvas.Canvas(overlay_buffer, pagesize=(page_width, page_height))
    styles = getSampleStyleSheet()
    date_du_jour = datetime.today().strftime("%d/%m/%Y")

    title = Paragraph(f"Feuille d'emargement - {meeting_name} - {date_du_jour}", styles["Heading2"])
    title_w, title_h = title.wrap(page_width - (0.9 * inch), page_height)
    title.drawOn(c, 0.45 * inch, page_height - title_h - 0.45 * inch)

    table = _build_table(participants_data, include_day2, styles)
    max_table_width = page_width - (0.9 * inch)
    table_w, table_h = table.wrap(max_table_width, page_height)
    table_x = 0.45 * inch
    table_y = page_height - title_h - table_h - 0.75 * inch
    table.drawOn(c, table_x, max(table_y, 0.45 * inch))

    c.save()
    overlay_buffer.seek(0)
    return overlay_buffer


def _build_without_template(meeting_name, participants_data, include_day2):
    page_width, page_height = A4
    overlay_buffer = _create_overlay_pdf(meeting_name, participants_data, include_day2, page_width, page_height)
    return overlay_buffer


def generate_pdf(meeting_name, participants_data, include_day2=True):
    """
    Genere un PDF en memoire.
    Si Doc1.pdf existe, le contenu est ecrit par-dessus pour conserver le logo.
    Sinon, generation standard sans template.
    """
    if not HAS_PYPDF:
        return _build_without_template(meeting_name, participants_data, include_day2)

    if not TEMPLATE_PDF.exists():
        return _build_without_template(meeting_name, participants_data, include_day2)

    template_reader = PdfReader(str(TEMPLATE_PDF))
    if len(template_reader.pages) == 0:
        return _build_without_template(meeting_name, participants_data, include_day2)

    first_page = template_reader.pages[0]
    page_width = float(first_page.mediabox.width)
    page_height = float(first_page.mediabox.height)

    overlay_buffer = _create_overlay_pdf(meeting_name, participants_data, include_day2, page_width, page_height)
    overlay_reader = PdfReader(overlay_buffer)
    overlay_page = overlay_reader.pages[0]

    output_writer = PdfWriter()
    merged_page = first_page
    merged_page.merge_page(overlay_page)
    output_writer.add_page(merged_page)

    output_buffer = BytesIO()
    output_writer.write(output_buffer)
    output_buffer.seek(0)
    return output_buffer
