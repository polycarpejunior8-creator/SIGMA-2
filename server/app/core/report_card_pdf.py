"""
Génération du bulletin au format PDF (cf §23).
Utilise reportlab (pure Python, sans dépendance système), ce qui garde le déploiement
du serveur simple (cf §55 - objectif d'installation en un clic, §29 du document
architecture).
"""
import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer


def generate_report_card_pdf(
    school_name: str,
    student_name: str,
    matricule: str,
    class_name: str,
    period_label: str,
    subject_rows: list[dict],
    overall_average: float | None,
    rank: int | None,
    class_size: int,
) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1.5 * cm, bottomMargin=1.5 * cm)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle("SigmaTitle", parent=styles["Title"], fontSize=16, spaceAfter=4)
    subtitle_style = ParagraphStyle("SigmaSubtitle", parent=styles["Normal"], fontSize=11, textColor=colors.grey)

    elements = [
        Paragraph(school_name, title_style),
        Paragraph(f"Bulletin — {period_label}", subtitle_style),
        Spacer(1, 12),
        Paragraph(f"<b>Élève :</b> {student_name} &nbsp;&nbsp; <b>Matricule :</b> {matricule}", styles["Normal"]),
        Paragraph(f"<b>Classe :</b> {class_name}", styles["Normal"]),
        Spacer(1, 16),
    ]

    table_data = [["Matière", "Coefficient", "Moyenne / 20"]]
    for row in subject_rows:
        avg_text = f"{row['average']:.2f}" if row["average"] is not None else "—"
        table_data.append([row["subject"].name, str(row["coefficient"]), avg_text])

    table = Table(table_data, colWidths=[8 * cm, 4 * cm, 4 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dfe4ea")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f6f9")]),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 20))

    overall_text = f"{overall_average:.2f} / 20" if overall_average is not None else "Non calculable (pas assez de notes validées)"
    rank_text = f"{rank} / {class_size}" if rank is not None else "—"

    elements.append(Paragraph(f"<b>Moyenne générale :</b> {overall_text}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Rang dans la classe :</b> {rank_text}", styles["Normal"]))
    elements.append(Spacer(1, 40))

    elements.append(Paragraph("Signature du responsable pédagogique : ____________________", styles["Normal"]))

    doc.build(elements)
    return buffer.getvalue()
