# pdf_generator.py
import io
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, Rect, Line, String, Circle, Group, Path
from reportlab.lib.utils import ImageReader


# ============================
# CUSTOM CANVAS WITH WATERMARK AND HEADER LOGO
# ============================
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

        # --- Try to locate logo.png in several likely places ---
        self.logo_image = None
        script_dir = os.path.dirname(os.path.abspath(__file__))
        cwd = os.getcwd()

        possible_paths = [
            os.path.join(script_dir, "logo.png"),
            os.path.join(script_dir, "assets", "logo.png"),
            os.path.join(cwd, "logo.png"),
            os.path.join(cwd, "assets", "logo.png"),
            "logo.png",  # fallback relative to current dir
        ]
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    self.logo_image = ImageReader(path)
                    # Optionally, print debug info (disabled by default)
                    # print(f"[PDF] Logo loaded from {path}")
                    break
                except Exception:
                    continue

        # If still no logo, we will skip drawing it (or use fallback text)

    def beginPage(self):
        """Called at the start of every new page – draws the watermark behind everything."""
        super().beginPage()
        if self.logo_image is not None:
            self._draw_watermark()
        else:
            # Fallback: draw a text watermark if logo not found
            self._draw_text_watermark()

    def _draw_watermark(self):
        """Draw a centred, semi‑transparent logo as a watermark."""
        page_width, page_height = letter
        wm_width = 200
        img_width, img_height = self.logo_image.getSize()
        aspect = img_height / img_width
        wm_height = wm_width * aspect

        x = (page_width - wm_width) / 2
        y = (page_height - wm_height) / 2

        self.saveState()
        self.setAlpha(0.15)   # transparency
        self.drawImage(
            self.logo_image,
            x, y,
            width=wm_width,
            height=wm_height,
            preserveAspectRatio=True
        )
        self.restoreState()

    def _draw_text_watermark(self):
        """Fallback watermark if no image is available."""
        self.saveState()
        self.setFont("Helvetica-Bold", 48)
        self.setFillColor(colors.HexColor("#CBD5E1"))
        self.setAlpha(0.12)
        self.drawCentredString(306, 400, "PYMUDCEMENT")
        self.restoreState()

    def _draw_header_logo(self):
        """Draw an opaque logo in the top‑right corner of every page."""
        if self.logo_image is None:
            return
        page_width, page_height = letter
        logo_width = 55
        img_width, img_height = self.logo_image.getSize()
        aspect = img_height / img_width
        logo_height = logo_width * aspect

        # Position: 54 pt from right edge, 54 pt from top (inside margin)
        x = page_width - 54 - logo_width
        y = page_height - 54 - logo_height

        self.saveState()
        self.drawImage(
            self.logo_image,
            x, y,
            width=logo_width,
            height=logo_height,
            preserveAspectRatio=True
        )
        self.restoreState()

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def _draw_page_decorations(self, page_count):
        """Draw header (logo + text) and footer on top of content."""
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#64748B"))

        # ---- Header: logo always appears, text only on pages > 1 ----
        self._draw_header_logo()   # draws logo on every page

        if self._pageNumber > 1:
            self.drawString(54, 750, "PYMUDCEMENT OPTIMA PRO v5.0 — TECHNICAL COMPLIANCE REPORT")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, 742, 558, 742)

        # ---- Footer ----
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(1)
        self.line(54, 45, 558, 45)

        self.drawString(54, 32, "Generated by: PyMudCement Optima Pro v5.0")
        self.drawCentredString(306, 32, "CONFIDENTIAL — DRILLING ENGINEERING DIVISION")
        self.drawRightString(558, 32, f"Page {self._pageNumber} of {page_count}")

        self.restoreState()


# ============================
# PRESSURE WINDOW CHART (unchanged)
# ============================
def create_pressure_window_chart() -> Drawing:
    d = Drawing(450, 140)
    d.add(Rect(0, 0, 450, 140, fillColor=colors.HexColor("#F8FAFC"), strokeColor=colors.HexColor("#E2E8F0")))
    for x in range(50, 450, 50):
        d.add(Line(x, 10, x, 130, strokeColor=colors.HexColor("#E2E8F0"), strokeWidth=0.5))
    d.add(Rect(60, 10, 100, 120, fillColor=colors.HexColor("#FEE2E2"), strokeColor=colors.transparent))
    d.add(Rect(320, 10, 100, 120, fillColor=colors.HexColor("#FEE2E2"), strokeColor=colors.transparent))
    d.add(Rect(160, 10, 160, 120, fillColor=colors.HexColor("#DCFCE7"), strokeColor=colors.transparent))
    d.add(Line(200, 130, 220, 90, strokeColor=colors.HexColor("#2563EB"), strokeWidth=2))
    d.add(Line(220, 90, 210, 50, strokeColor=colors.HexColor("#2563EB"), strokeWidth=2))
    d.add(Line(210, 50, 235, 10, strokeColor=colors.HexColor("#2563EB"), strokeWidth=2))
    d.add(String(70, 115, "Pore Pressure", fontName="Helvetica-Bold", fontSize=8, fillColor=colors.HexColor("#991B1B")))
    d.add(String(190, 115, "ECD Operating Window", fontName="Helvetica-Bold", fontSize=8, fillColor=colors.HexColor("#166534")))
    d.add(String(330, 115, "Fracture Limit", fontName="Helvetica-Bold", fontSize=8, fillColor=colors.HexColor("#991B1B")))
    return d


# ============================
# MAIN PDF GENERATION FUNCTION
# ============================
def generate_pdf_payload(
    project_metadata: Dict[str, Any],
    physics_results: Dict[str, Any],
    diagnostic_results: Dict[str, Any],
    engineer_name: str = "Peter Prempeh",
    cementing_results: Optional[Dict[str, Any]] = None
) -> io.BytesIO:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=64
    )

    styles = getSampleStyleSheet()

    # Custom paragraph styles
    title_style = ParagraphStyle(
        'CompTitle',
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=colors.HexColor('#0F172A')
    )
    subtitle_style = ParagraphStyle(
        'CompSub',
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#F97316'),
        spaceAfter=12
    )
    h1_style = ParagraphStyle(
        'SectH1',
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor('#0F172A'),
        spaceBefore=14,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'SectBody',
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#334155')
    )
    bold_body = ParagraphStyle(
        'SectBodyBold',
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#1E293B')
    )

    elements = []

    # ---- Title block ----
    elements.append(Paragraph("PYMUDCEMENT OPTIMA PRO v5.0", title_style))
    elements.append(Paragraph("Engineering Technical Compliance Field Report", subtitle_style))

    # ---- Metadata table ----
    meta_data = [
        [
            Paragraph("<b>Project Asset Base:</b>", body_style),
            Paragraph(str(project_metadata.get('name', 'N/A')), body_style),
            Paragraph("<b>Rig Identification:</b>", body_style),
            Paragraph(str(project_metadata.get('rig_name', 'Rig-05')), body_style)
        ],
        [
            Paragraph("<b>Wellbore Depth:</b>", body_style),
            Paragraph(f"{physics_results.get('total_depth_ft', 0.0)} ft MD", body_style),
            Paragraph("<b>Lead Field Engineer:</b>", body_style),
            Paragraph(engineer_name, body_style)
        ],
        [
            Paragraph("<b>Operating Client:</b>", body_style),
            Paragraph(str(project_metadata.get('company', 'Enterprise Hydrocarbons Corp')), body_style),
            Paragraph("<b>Report Identifier:</b>", body_style),
            Paragraph(f"PMC-{datetime.now().strftime('%M%S')}", body_style)
        ],
        [
            Paragraph("<b>Flow Rate:</b>", body_style),
            Paragraph(f"{physics_results.get('flow_rate_gpm', 0.0)} GPM", body_style),
            Paragraph("<b>Date / Local Time:</b>", body_style),
            Paragraph(datetime.now().strftime('%Y-%m-%d / %H:%M'), body_style)
        ],
    ]
    t_meta = Table(meta_data, colWidths=[110, 140, 110, 140])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#F1F5F9')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.extend([t_meta, Spacer(1, 10)])

    # ---- Executive Summary ----
    severity = diagnostic_results.get("severity", "GREEN")
    status_text = (
        "✔ STABLE OPERATIONAL GRADIENT"
        if severity == "GREEN"
        else ("⚠️ WARNING ELEVATED" if severity == "YELLOW" else "❌ CRITICAL BREACH")
    )

    summary_box = [
        [
            Paragraph("<b>Well Health Status:</b>", body_style),
            Paragraph(status_text, bold_body)
        ],
        [
            Paragraph("<b>Matched Hazard Vector:</b>", body_style),
            Paragraph(diagnostic_results.get("matched_hazard", "None"), body_style)
        ],
        [
            Paragraph("<b>AI Diagnosis:</b>", body_style),
            Paragraph(diagnostic_results.get("detailed_diagnosis", "Nominal"), body_style)
        ]
    ]
    t_summary = Table(summary_box, colWidths=[140, 360])
    t_summary.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#0F172A')),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F1F5F9')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.extend([Paragraph("EXECUTIVE SUMMARY", h1_style), t_summary, Spacer(1, 10)])

    # ---- Primary Hydraulics Table ----
    elements.append(Paragraph("1. Primary Mechanical Hydraulics Summary", h1_style))
    ecd = physics_results.get("equivalent_circulating_density_ecd_ppg", 0.0)
    spp = physics_results.get("standpipe_pressure_spp_psi", 0.0)

    comp_rows = [
        [
            Paragraph("<b>Metric Parameter</b>", bold_body),
            Paragraph("<b>Value Output</b>", bold_body),
            Paragraph("<b>Safe Limit</b>", bold_body),
            Paragraph("<b>Status</b>", bold_body)
        ],
        [
            Paragraph("Equivalent Circulating Density (ECD)", body_style),
            Paragraph(f"{ecd:.2f} ppg", body_style),
            Paragraph("< 15.5 ppg", body_style),
            Paragraph("PASS" if ecd < 15.5 else "FAIL", bold_body)
        ],
        [
            Paragraph("Standpipe Pressure (SPP)", body_style),
            Paragraph(f"{spp:.1f} psi", body_style),
            Paragraph("< 3500 psi", body_style),
            Paragraph("PASS" if spp < 3500 else "WARNING", bold_body)
        ],
        [
            Paragraph("Annular Pressure Loss", body_style),
            Paragraph(f"{physics_results.get('total_annular_pressure_loss_psi', 0.0):.1f} psi", body_style),
            Paragraph("Dynamic", body_style),
            Paragraph("PASS", bold_body)
        ],
        [
            Paragraph("Drillstring Pressure Loss", body_style),
            Paragraph(f"{physics_results.get('total_pipe_pressure_loss_psi', 0.0):.1f} psi", body_style),
            Paragraph("Dynamic", body_style),
            Paragraph("PASS", bold_body)
        ],
    ]
    t_comp = Table(comp_rows, colWidths=[160, 110, 130, 100])
    t_comp.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.extend([t_comp, Spacer(1, 10)])

    # ---- Pressure Profile Chart ----
    elements.append(Paragraph("2. Pressure Profile Visualization", h1_style))
    elements.append(create_pressure_window_chart())
    elements.append(Spacer(1, 15))

    # ---- Cementing Results (if provided) ----
    if cementing_results:
        elements.append(Paragraph("3. Cementing Job Summary", h1_style))
        c_data = [
            ["Lead Slurry Volume", f"{cementing_results.get('lead_slurry_volume_bbl', 0.0):.2f} bbl"],
            ["Tail Slurry Volume", f"{cementing_results.get('tail_slurry_volume_bbl', 0.0):.2f} bbl"],
            ["Spacer Volume", f"{cementing_results.get('spacer_volume_bbl', 0.0):.2f} bbl"],
            ["Displacement Volume", f"{cementing_results.get('displacement_volume_bbl', 0.0):.2f} bbl"],
            ["Plug Bumping Pressure", f"{cementing_results.get('recommended_plug_bumping_pressure_psi', 0.0):.1f} psi"],
        ]
        t_cement = Table(c_data, colWidths=[200, 200])
        t_cement.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(t_cement)
        elements.append(Spacer(1, 10))

        # Additives
        elements.append(Paragraph("Suggested Additives", h1_style))
        additives = cementing_results.get("suggested_additives", [])
        for add in additives:
            elements.append(Paragraph(f"• <b>{add['name']}</b> ({add['category']}) – {add['description']}", body_style))
        elements.append(Spacer(1, 10))

    # ---- AI Recommendations & Sign‑off ----
    elements.append(Paragraph("4. AI Action Blueprint & Engineering Sign-Off", h1_style))
    recs = diagnostic_results.get("actionable_recommendations", ["Maintain standard operations."])
    for rec in recs:
        elements.append(Paragraph(f"• {rec}", body_style))

    elements.append(Spacer(1, 20))
    sig_line = "_____________________________________"
    sig_data = [
        [
            Paragraph(
                f"<b>Prepared By:</b><br/><br/>{sig_line}<br/>Lead Engineer: {engineer_name}",
                body_style
            ),
            Paragraph(
                f"<b>Approved By:</b><br/><br/>{sig_line}<br/>Rig Superintendent",
                body_style
            )
        ]
    ]
    t_sig = Table(sig_data, colWidths=[250, 250])
    elements.append(t_sig)

    # ---- Build the PDF with our custom canvas ----
    doc.build(elements, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer