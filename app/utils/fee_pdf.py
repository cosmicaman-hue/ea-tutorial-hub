import os
import json
import hashlib
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """Custom canvas that draws elegant headers and footers on every page, with dynamic page numbering."""
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#475569"))
        
        # Draw Header
        self.drawString(54, 750, "PROJECT EA — MONTHLY FEE COLLECTION REPORT")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 742, 558, 742)
        
        # Draw Footer
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 36, page_text)
        self.drawString(54, 36, f"DURABLE LEDGER EVIDENCE · Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.line(54, 48, 558, 48)
        self.restoreState()


def compute_ledger_hash(transactions):
    """Generate a SHA-256 digest of stable fields in the monthly transaction logs."""
    if not transactions:
        return "N/A - No transactions recorded"
    
    # Sort transactions stably by txn_id to guarantee consistency
    sorted_txns = sorted(transactions, key=lambda t: str(t.get('txn_id', '')))
    stable_list = []
    for t in sorted_txns:
        stable_list.append({
            'txn_id': str(t.get('txn_id', '')),
            'student_id': int(t.get('student_id', 0) or 0),
            'date': str(t.get('date', '')),
            'amount': float(t.get('amount', 0) or 0),
            'mode': str(t.get('mode', 'cash')),
            'status': str(t.get('status', 'confirmed')),
            'is_reversal': bool(t.get('is_reversal', False))
        })
    
    serialized = json.dumps(stable_list, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def generate_monthly_fee_report(month_key, db_data, output_path):
    """
    Compile student roster and payment transactions for a given month into a professional PDF report.
    Saves the PDF to output_path.
    """
    # ── 1. Gather & Process Data ─────────────────────────────────────────────
    students = db_data.get('students', [])
    fee_records = db_data.get('fee_records', [])
    fee_map = {str(r.get('studentId')): r for r in fee_records}
    
    # Filter active/inactive students for the selected month
    active_students = [s for s in students if s.get('active') is not False]
    active_students.sort(key=lambda s: (str(s.get('class', '')), str(s.get('roll', ''))))
    
    # Extract transactions recorded in this month
    all_txns = []
    month_txns = []
    
    for r in fee_records:
        history = r.get('payment_history') or []
        for h in history:
            # Match transaction date or payment cycle to the report month
            txn_date = h.get('date') or h.get('paid_on') or ''
            if txn_date.startswith(month_key):
                # Attach student info for ease of formatting
                sid = r.get('studentId')
                student = next((s for s in students if s.get('id') == sid), None)
                h_copy = dict(h)
                h_copy['studentId'] = sid
                h_copy['student_name'] = student.get('name') if student else f"Student #{sid}"
                h_copy['roll'] = student.get('roll') if student else '-'
                h_copy['class'] = student.get('class') if student else '-'
                month_txns.append(h_copy)
            
            # Keep all for absolute total calculations
            h_copy = dict(h)
            h_copy['studentId'] = r.get('studentId')
            all_txns.append(h_copy)

    # Re-calculate statistics for the month
    total_students = len(active_students)
    total_expected = 0
    total_collected_in_month = 0
    total_pending = 0
    
    student_rows_data = []
    for s in active_students:
        sid_str = str(s.get('id'))
        record = fee_map.get(sid_str) or {}
        
        # Expected monthly amount
        base_fee = record.get('amount')
        if base_fee is None:
            base_fee = s.get('fees', 0)
        try:
            base_fee = float(base_fee)
        except (ValueError, TypeError):
            base_fee = 0.0
            
        total_expected += base_fee
        
        # Pending dues
        pending = record.get('pending_amount')
        if pending is None:
            pending = base_fee
        try:
            pending = float(pending)
        except (ValueError, TypeError):
            pending = 0.0
            
        total_pending += pending

        # Paid in this specific month
        paid_in_month = 0.0
        for h in record.get('payment_history', []):
            t_date = h.get('date') or h.get('paid_on') or ''
            if t_date.startswith(month_key) and not h.get('is_reversal') and h.get('status') != 'reversed':
                paid_in_month += float(h.get('amount', 0) or 0)
        
        total_collected_in_month += paid_in_month
        
        # Status Label
        last_paid = record.get('last_paid_date', '-')
        due_date = record.get('due_date', '-')
        
        # Quick status check
        if pending <= 0:
            status = "Paid"
        elif base_fee > 0 and pending >= base_fee * 2:
            status = "Overdue"
        else:
            status = "Due"
            
        student_rows_data.append([
            s.get('roll', '-'),
            s.get('name', 'Unknown'),
            str(s.get('class', '-')),
            f"₹{int(base_fee)}",
            status,
            f"₹{int(paid_in_month)}",
            f"₹{int(pending)}",
            last_paid
        ])

    # Compute secure checksum over the transactions
    ledger_checksum = compute_ledger_hash(month_txns)

    # ── 2. ReportLab Document Design ─────────────────────────────────────────
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=72,
        bottomMargin=72
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#475569"),
        spaceAfter=20
    )
    
    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=14,
        spaceAfter=10
    )
    
    body_bold = ParagraphStyle(
        'BodyBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#1e293b")
    )
    
    body_normal = ParagraphStyle(
        'BodyNormal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155")
    )
    
    table_text_header = ParagraphStyle(
        'TableHeaderText',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.white
    )

    story = []

    # Title & Subtitle
    story.append(Paragraph(f"Monthly Fee Collection Report", title_style))
    story.append(Paragraph(f"Digital Ledger Summary & Transactions for Cycle: <b>{month_key}</b>", subtitle_style))

    # ── Summary Stat Cards Table ─────────────────────────────────────────────
    summary_data = [
        [
            Paragraph("<b>Total Active Roster</b>", body_normal),
            Paragraph("<b>Target Expected Fees</b>", body_normal),
            Paragraph("<b>Fees Collected (This Month)</b>", body_normal),
            Paragraph("<b>Outstanding Balance Dues</b>", body_normal)
        ],
        [
            Paragraph(f"<font size=14 color='#0f172a'><b>{total_students}</b></font>", body_bold),
            Paragraph(f"<font size=14 color='#0f172a'><b>₹{int(total_expected):,}</b></font>", body_bold),
            Paragraph(f"<font size=14 color='#16a34a'><b>₹{int(total_collected_in_month):,}</b></font>", body_bold),
            Paragraph(f"<font size=14 color='#dc2626'><b>₹{int(total_pending):,}</b></font>", body_bold)
        ]
    ]
    summary_table = Table(summary_data, colWidths=[126, 126, 126, 126])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f8fafc")),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor("#f1f5f9")),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor("#0f172a")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 20))

    # ── Section 1: Roster Status Ledger ──────────────────────────────────────
    story.append(Paragraph("1. Monthly Student Fee Ledger", section_title_style))
    
    ledger_headers = ["Roll No.", "Student Name", "Class", "Expected", "Status", "Paid", "Pending", "Last Paid On"]
    ledger_rows = [[Paragraph(f"<b>{h}</b>", table_text_header) for h in ledger_headers]]
    
    for row in student_rows_data:
        status_color = "#16a34a" if row[4] == "Paid" else ("#dc2626" if row[4] == "Overdue" else "#ea580c")
        ledger_rows.append([
            Paragraph(row[0], body_normal),
            Paragraph(row[1], body_normal),
            Paragraph(row[2], body_normal),
            Paragraph(row[3], body_normal),
            Paragraph(f"<font color='{status_color}'><b>{row[4]}</b></font>", body_bold),
            Paragraph(row[5], body_normal),
            Paragraph(row[6], body_normal),
            Paragraph(row[7], body_normal),
        ])
        
    ledger_table = Table(ledger_rows, colWidths=[65, 120, 45, 55, 55, 50, 50, 68])
    ledger_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(ledger_table)
    story.append(Spacer(1, 20))

    # ── Section 2: Transaction History for the Month ─────────────────────────
    story.append(Paragraph(f"2. Payments Recorded in {month_key}", section_title_style))
    
    if not month_txns:
        story.append(Paragraph("<i>No fee collection transactions recorded during this month cycle.</i>", body_normal))
    else:
        txn_headers = ["Date", "Roll", "Name", "Amount", "Mode", "Category", "Transaction ID / Ref", "Recorder"]
        txn_rows = [[Paragraph(f"<b>{h}</b>", table_text_header) for h in txn_headers]]
        
        for t in sorted(month_txns, key=lambda tx: str(tx.get('date', ''))):
            ref_str = t.get('ref_no') or '-'
            is_rev = t.get('is_reversal') or t.get('status') == 'reversed'
            amt_text = f"₹{int(float(t.get('amount', 0)))}"
            if is_rev:
                amt_text = f"-{amt_text} (Reversal)"
                amt_color = "#dc2626"
            else:
                amt_color = "#16a34a"
                
            txn_rows.append([
                Paragraph(t.get('date', '-'), body_normal),
                Paragraph(t.get('roll', '-'), body_normal),
                Paragraph(t.get('student_name', 'Unknown'), body_normal),
                Paragraph(f"<font color='{amt_color}'><b>{amt_text}</b></font>", body_bold),
                Paragraph(str(t.get('mode', 'cash')).upper(), body_normal),
                Paragraph(str(t.get('category', 'tuition')).capitalize(), body_normal),
                Paragraph(f"ID: {t.get('txn_id', '-')}<br/><font color='#64748b'>Ref: {ref_str}</font>", body_normal),
                Paragraph(t.get('recorded_by', 'Admin'), body_normal),
            ])
            
        txn_table = Table(txn_rows, colWidths=[60, 50, 95, 75, 45, 50, 110, 68])
        txn_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#475569")),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(txn_table)

    story.append(Spacer(1, 25))

    # ── Section 3: Digital Forensic Verification Signature ────────────────────
    verify_block = []
    verify_block.append(Paragraph("3. Cryptographic Forensic Audit Ledger Hash", section_title_style))
    verify_block.append(Paragraph(
        "To guarantee the authenticity of this digital report and prove that no transaction records have been "
        "altered, added, or deleted after the fact, the system has generated an immutable SHA-256 digital signature of this "
        "month's fee ledger. Any manual database tampering or retrospective modification of transactions will invalidate this hash.",
        body_normal
    ))
    verify_block.append(Spacer(1, 6))
    verify_block.append(Paragraph(
        f"<b>IMMUTABLE SHA-256 LEDGER SIGNATURE:</b><br/>"
        f"<font size=10 face='Courier' color='#1e293b'><b>{ledger_checksum}</b></font>",
        body_bold
    ))
    story.append(KeepTogether(verify_block))

    # ── 3. Build Document ────────────────────────────────────────────────────
    doc.build(story, canvasmaker=NumberedCanvas)
