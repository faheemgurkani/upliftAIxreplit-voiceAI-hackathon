from __future__ import annotations

import io
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.models.statement import StatementRecord, StructuredStatement


class PDFService:
    """Generate printable FIR-style witness statement PDFs."""

    def generate_statement_pdf(self, statement: StatementRecord) -> bytes:
        structured = statement.structured_statement
        if isinstance(structured, dict):
            structured = StructuredStatement.model_validate(structured)

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=18 * mm,
            rightMargin=18 * mm,
            topMargin=16 * mm,
            bottomMargin=16 * mm,
            title=f"Gawah Statement {statement.case_id}",
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
                name="SubCenter",
                parent=styles["Normal"],
                alignment=TA_CENTER,
                fontSize=10,
                textColor=colors.HexColor("#333333"),
                spaceAfter=12,
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
                name="Small",
                parent=styles["Normal"],
                fontSize=8,
                textColor=colors.HexColor("#555555"),
            )
        )

        story = []
        story.append(Paragraph("GAWAH — Witness Statement", styles["CenterTitle"]))
        story.append(
            Paragraph(
                "First Information / Witness Record (Hackathon MVP Format)",
                styles["SubCenter"],
            )
        )

        meta = [
            ["Case Reference", statement.case_id],
            ["Statement ID", statement.id],
            ["Call SID", statement.call_sid or "—"],
            ["Witness Language", statement.witness_language],
            ["Witness Confirmed", "Yes" if statement.confirmed else "No"],
            ["Officer Confirmed", "Yes" if statement.officer_confirmed else "No"],
            ["Created At", str(statement.created_at)],
        ]
        meta_table = Table(meta, colWidths=[45 * mm, 120 * mm])
        meta_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F2F2F2")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(meta_table)
        story.append(Spacer(1, 10))

        story.append(Paragraph("English Legal Summary", styles["Section"]))
        story.append(
            Paragraph(
                f"<b>Witness:</b> {self._esc(structured.witness_name or 'unknown')}<br/>"
                f"<b>Date:</b> {self._esc(structured.incident_date or 'unknown')} &nbsp; "
                f"<b>Time:</b> {self._esc(structured.incident_time or 'unknown')}<br/>"
                f"<b>Location:</b> {self._esc(structured.incident_location or 'unknown')}",
                styles["BodyLeft"],
            )
        )

        story.append(Paragraph("Persons Involved", styles["Section"]))
        if structured.persons_involved:
            for person in structured.persons_involved:
                story.append(Paragraph(f"• {self._esc(person)}", styles["BodyLeft"]))
        else:
            story.append(Paragraph("• None recorded", styles["BodyLeft"]))

        story.append(Paragraph("Sequence of Events", styles["Section"]))
        if structured.sequence_of_events:
            for idx, event in enumerate(structured.sequence_of_events, start=1):
                story.append(Paragraph(f"{idx}. {self._esc(event)}", styles["BodyLeft"]))
        else:
            story.append(Paragraph("1. No events recorded", styles["BodyLeft"]))

        story.append(Paragraph("Flagged Inconsistencies", styles["Section"]))
        inconsistencies = statement.inconsistencies or structured.inconsistencies
        if inconsistencies:
            for item in inconsistencies:
                story.append(Paragraph(f"• {self._esc(item)}", styles["BodyLeft"]))
        else:
            story.append(Paragraph("• None flagged", styles["BodyLeft"]))

        story.append(Paragraph("Raw Transcript / Vernacular Account", styles["Section"]))
        transcript = statement.raw_transcript or "—"
        # Keep RTL-ish presentation for Urdu/Pashto/Punjabi by right-aligning.
        body_style = (
            styles["BodyRight"]
            if statement.witness_language in {"urdu", "punjabi", "pashto"}
            else styles["BodyLeft"]
        )
        story.append(Paragraph(self._esc(transcript), body_style))

        story.append(Spacer(1, 18))
        story.append(Paragraph("Verification", styles["Section"]))
        thumb = Table(
            [
                ["Witness Signature / Thumbprint", "Recording Officer"],
                ["\n\n\n\n", "\n\n\n\n"],
                ["Name: ____________________", "Name: ____________________"],
                ["Date: ____________________", "Date: ____________________"],
            ],
            colWidths=[82 * mm, 82 * mm],
        )
        thumb.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (0, -1), 0.8, colors.black),
                    ("BOX", (1, 0), (1, -1), 0.8, colors.black),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEEEEE")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(thumb)
        story.append(Spacer(1, 10))
        story.append(
            Paragraph(
                "Generated by Gawah Voice AI — for hackathon demonstration use.",
                styles["Small"],
            )
        )

        doc.build(story)
        return buffer.getvalue()

    @staticmethod
    def _esc(value: Optional[str]) -> str:
        text = value or ""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )


_pdf_service: PDFService | None = None


def get_pdf_service() -> PDFService:
    global _pdf_service
    if _pdf_service is None:
        _pdf_service = PDFService()
    return _pdf_service
