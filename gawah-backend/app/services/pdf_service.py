from __future__ import annotations

import io
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.models.statement import StatementRecord


class PDFService:
    def generate_statement_pdf(self, statement: StatementRecord) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=18 * mm,
            rightMargin=18 * mm,
            topMargin=16 * mm,
            bottomMargin=16 * mm,
            title=f"Gawah Statement {statement.ref_code}",
        )
        styles = getSampleStyleSheet()
        styles.add(
            ParagraphStyle(
                name="CenterTitle",
                parent=styles["Heading1"],
                alignment=TA_CENTER,
                fontSize=16,
                spaceAfter=6,
            )
        )
        styles.add(
            ParagraphStyle(
                name="BodyLeft",
                parent=styles["Normal"],
                alignment=TA_LEFT,
                fontSize=10,
                leading=14,
            )
        )
        styles.add(
            ParagraphStyle(
                name="BodyRight",
                parent=styles["Normal"],
                alignment=TA_RIGHT,
                fontSize=10,
                leading=14,
            )
        )
        styles.add(
            ParagraphStyle(
                name="Section",
                parent=styles["Heading2"],
                fontSize=12,
                spaceBefore=10,
                spaceAfter=6,
            )
        )
        styles.add(
            ParagraphStyle(
                name="Small",
                parent=styles["Normal"],
                fontSize=8,
                textColor=colors.HexColor("#555555"),
            )
        )

        story = []
        story.append(Paragraph("GAWAH — CrPC §161 Witness Statement", styles["CenterTitle"]))
        story.append(
            Paragraph(
                "Voice-confirmed record — no signature / thumbprint (CrPC §162 reliability).",
                styles["Small"],
            )
        )
        story.append(Spacer(1, 8))

        meta = [
            ["Reference Code", statement.ref_code],
            ["Status", statement.status],
            ["Language", statement.language_of_call],
            ["Witness Type", statement.witness_type],
            ["Privacy Mode", "Yes" if statement.privacy_mode else "No"],
            ["Witness Confirmed", "Yes" if statement.confirmed_by_witness else "No"],
            ["Intimidation Flag", "Yes" if statement.intimidation_flag else "No"],
            ["Created At", str(statement.created_at)],
        ]
        table = Table(meta, colWidths=[50 * mm, 115 * mm])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F2F2F2")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(table)

        story.append(Paragraph("Five Legal Fields", styles["Section"]))
        story.append(
            Paragraph(
                f"<b>Time:</b> {self._esc(statement.time_of_incident)}<br/>"
                f"<b>Location:</b> {self._esc(statement.location)}<br/>"
                f"<b>Persons:</b> {self._esc(', '.join(statement.persons_present))}<br/>"
                f"<b>Relationship:</b> {self._esc(statement.relationship_to_accused)}",
                styles["BodyLeft"],
            )
        )
        story.append(Paragraph("Sequence of Events (verbatim)", styles["Section"]))
        body_style = (
            styles["BodyRight"]
            if statement.language_of_call in {"ur", "pa", "ps"}
            else styles["BodyLeft"]
        )
        story.append(Paragraph(self._esc(statement.sequence_of_events), body_style))

        if statement.inconsistency_flags:
            story.append(Paragraph("Inconsistency Flags", styles["Section"]))
            for flag in statement.inconsistency_flags:
                data = flag.model_dump() if hasattr(flag, "model_dump") else flag
                story.append(
                    Paragraph(
                        f"• [{data.get('contradiction_type') or data.get('category')}] "
                        f"{self._esc(data.get('contradiction_description') or data.get('analysis'))}",
                        styles["BodyLeft"],
                    )
                )

        if statement.corroboration_score is not None:
            story.append(Paragraph("Corroboration (pre-litigation only)", styles["Section"]))
            story.append(
                Paragraph(
                    f"Score: {statement.corroboration_score}. "
                    "Disclaimer: Pre-litigation intelligence only — not admissible "
                    "corroboration under CrPC Section 162.",
                    styles["BodyLeft"],
                )
            )

        story.append(Spacer(1, 16))
        story.append(
            Paragraph(
                "Voice confirmation replaces thumbprint. Generated by Gawah.",
                styles["Small"],
            )
        )
        doc.build(story)
        return buffer.getvalue()

    @staticmethod
    def _esc(value: Optional[str]) -> str:
        text = value or "—"
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )


_pdf: PDFService | None = None


def get_pdf_service() -> PDFService:
    global _pdf
    if _pdf is None:
        _pdf = PDFService()
    return _pdf
