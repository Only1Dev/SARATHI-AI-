"""
Sarathi AI (Cascade India) - PDF Blueprint Generator
Generates a publication-quality SIH Hackathon PDF blueprint for team sharing.
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to add headers and 'Page X of Y' footers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 800, "SARATHI AI (CASCADE INDIA) — SIH PROTOTYPE BLUEPRINT")
            self.setStrokeColor(colors.HexColor("#e2e8f0"))
            self.setLineWidth(0.5)
            self.line(54, 792, 541, 792)

        # Footer (all pages)
        footer_text = f"Smart India Hackathon (SIH) Technical Guide  |  Page {self._pageNumber} of {page_count}"
        self.drawRightString(541, 36, footer_text)
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(54, 48, 541, 48)
        
        self.restoreState()

def create_blueprint_pdf(filename="Sarathi_AI_SIH_Prototype_Blueprint.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom Color Palette
    PRIMARY = colors.HexColor("#0f172a")     # Slate 900
    ACCENT_GREEN = colors.HexColor("#059669")# Emerald 600
    ACCENT_BLUE = colors.HexColor("#2563eb") # Blue 600
    AMBER = colors.HexColor("#d97706")       # Amber 600
    TEXT_DARK = colors.HexColor("#1e293b")   # Slate 800
    TEXT_MUTED = colors.HexColor("#475569")  # Slate 600
    BG_LIGHT = colors.HexColor("#f8fafc")    # Slate 50

    # Custom Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=PRIMARY,
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=ACCENT_GREEN,
        spaceAfter=15
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=PRIMARY,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=ACCENT_BLUE,
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=TEXT_DARK,
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )

    code_style = ParagraphStyle(
        'Code_Custom',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#0f172a"),
        backColor=colors.HexColor("#f1f5f9"),
        borderColor=colors.HexColor("#cbd5e1"),
        borderWidth=0.5,
        borderPadding=6,
        spaceAfter=8
    )

    story = []

    # Title Banner Block
    story.append(Paragraph("⚡ SARATHI AI (CASCADE INDIA)", title_style))
    story.append(Paragraph("<b>SIH Prototype Blueprint & Teammate Building Guide</b><br/><i>Telegram Task Triage · UPI Escrow Hold · Worker Web Portal · AI Automated Proof Verification</i>", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT_GREEN, spaceAfter=12))

    # Executive Overview Box
    exec_summary_text = (
        "<b>Executive Vision:</b> Sarathi AI brings the exact architecture of <b>Cascade</b> to India. "
        "Users communicate strictly over <b>Telegram</b> (or WhatsApp). Informational queries are answered instantly by AI for <b>₹0</b>. "
        "Tasks requiring real human labor (store calls, app testing, local errands, CA/legal advice) generate a price quote. "
        "Upon user acceptance, funds are locked in a <b>Dummy UPI Escrow</b>. When a worker submits proof on the <b>Worker Web Dashboard</b>, "
        "an <b>AI Proof Verification Engine</b> automatically inspects the proof against task requirements. Once verified, escrow funds are instantly released to the worker's UPI ID."
    )
    
    summary_table = Table(
        [[Paragraph(exec_summary_text, body_style)]],
        colWidths=[487]
    )
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#ecfdf5")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#a7f3d0")),
        ('PADDING', (0,0), (-1,-1), 10),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 10))

    # Section 1: End-to-End Judge Presentation Demo Flow
    story.append(Paragraph("1. End-to-End Judge Presentation Demo Flow", h1_style))
    story.append(Paragraph("To win at Smart India Hackathon (SIH), present this exact 6-step live workflow to the judges:", body_style))

    flow_data = [
        ["Step", "Actor", "Action / Screen", "System Mechanics & Status"],
        ["1", "User (Phone)", "Sends task in Telegram: <i>'Call Om Stationary Koramangala & check A3 drafting board stock'</i>", "Triage Engine classifies query as Tier 2 (Gig Network). Calculates quote (₹120) & ~15m turnaround."],
        ["2", "Telegram Bot", "Bot replies with Quote Card: <b>'Price: ₹120 (Held in UPI Escrow)'</b> + Inline Button", "User sees button: <code>[ ✅ Approve & Pre-Auth ₹120 ]</code>"],
        ["3", "User (Phone)", "Taps <b>'Approve & Pre-Auth ₹120'</b> button in Telegram", "<b>UPI Pre-Auth Escrow Locked!</b> Status: <code>ESCROW_HOLD</code>. Task dispatches to Worker Web Dashboard."],
        ["4", "Worker (Web)", "Worker opens <code>/worker</code> portal, views live task, & clicks <b>'Claim Task'</b>", "Status transitions to <code>IN_PROGRESS</code>. Assigned to worker (e.g. Aarav - Bangalore)."],
        ["5", "Worker (Web)", "Worker completes task & uploads proof: <i>'Spoke with store. 4 units A3 board available @ ₹680'</i>", "Status transitions to <code>PROOF_SUBMITTED</code>. AI Verification Engine triggers automatically."],
        ["6", "AI & Engine", "<b>AI Proof Verification Engine</b> validates proof against prompt & releases payout!", "AI Score: 98% Verified. Status: <code>SETTLED</code>. ₹120 released to worker UPI. Notification sent in Telegram!"]
    ]

    flow_table = Table(flow_data, colWidths=[32, 70, 185, 200])
    flow_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 8.5),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('FONTSIZE', (0,1), (-1,-1), 8),
        ('PADDING', (0,1), (-1,-1), 5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_LIGHT])
    ]))
    story.append(flow_table)
    story.append(Spacer(1, 12))

    # Section 2: Technical Architecture & System Modules
    story.append(Paragraph("2. System Architecture & Component Responsibilities", h1_style))
    
    arch_data = [
        ["Module Name", "Tech Stack", "Key Responsibilities"],
        ["1. Cascade Landing Page", "HTML5, CSS3, JS (Vanilla)", "Serves marketing UI at <code>/</code> matching Cascade aesthetic. Features Hero thread preview, Stack, Pricing, FAQ, and <b>'Open App'</b> button leading to Telegram."],
        ["2. Worker Web Dashboard", "HTML5, JS, REST APIs", "Standalone portal at <code>/worker</code> for gig workers/experts to view escrow-backed tasks, claim jobs, submit proof notes, & track UPI earnings."],
        ["3. Backend API Server", "Python (Flask / FastAPI)", "Central engine handling state persistence, worker feeds, escrow Virtual Account ledger, & endpoint routing."],
        ["4. Telegram Bot Bridge", "python-telegram-bot / HTTP", "Polls Telegram API, sends Markdown quote cards with inline buttons, & delivers completion notifications to phone."],
        ["5. AI Triage & Proof Engine", "Google Gemini / Groq API", "1. Classifies task (AI ₹0 vs Gig/Expert ₹).<br/>2. Performs <b>Automated AI Verification</b> comparing submitted proof vs initial prompt requirements."]
    ]

    arch_table = Table(arch_data, colWidths=[110, 110, 267])
    arch_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e293b")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 8.5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('FONTSIZE', (0,1), (-1,-1), 8),
        ('PADDING', (0,1), (-1,-1), 5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_LIGHT])
    ]))
    story.append(arch_table)
    story.append(Spacer(1, 12))

    # Page Break for clean layout
    story.append(PageBreak())

    # Section 3: AI Proof Verification Mechanism
    story.append(Paragraph("3. AI Proof Verification Engine (Key Innovation)", h1_style))
    story.append(Paragraph(
        "A critical feature judges will love is <b>Automated AI Verification</b>. When a worker submits a deliverable on the web portal, "
        "the backend calls Gemini / Groq with the initial task prompt and the worker's submitted proof to verify accuracy before releasing payment.",
        body_style
    ))

    verification_code = (
        "def verify_deliverable_with_ai(prompt: str, proof_text: str, proof_type: str):\n"
        "    system_prompt = '''You are an AI Verification Auditor for Sarathi AI.\n"
        "    Compare the User's Original Task against the Worker's Submitted Proof.\n"
        "    Evaluate if the worker answered the core request accurately.\n"
        "    Return JSON: {\"is_verified\": true|false, \"confidence_score\": 0-100, \"feedback\": \"...\"}'''\n\n"
        "    user_payload = f\"Task: {prompt}\\nProof ({proof_type}): {proof_text}\"\n"
        "    # Calls Gemini Flash API -> returns JSON evaluation\n"
        "    # If is_verified == true -> Auto-release UPI Escrow!"
    )
    story.append(Paragraph(verification_code.replace("\n", "<br/>").replace(" ", "&nbsp;"), code_style))

    # Section 4: Dummy UPI Escrow State Machine
    story.append(Paragraph("4. Dummy UPI Escrow State Machine", h1_style))
    story.append(Paragraph("The ledger tracks tasks through a strict financial state machine in memory / database:", body_style))

    state_data = [
        ["State Code", "Trigger Event", "Financial Action"],
        ["UNPAID_QUOTE", "User sends task in Telegram", "AI calculates quote. No money moved."],
        ["ESCROW_HOLD", "User taps 'Approve & Pre-Auth' in TG", "Pre-auth simulation: ₹X locked in user escrow ledger."],
        ["CLAIMED", "Worker clicks 'Claim' on Web Portal", "Task locked to worker ID. Countdown timer starts."],
        ["PROOF_SUBMITTED", "Worker submits proof on Web", "AI Verification Engine checks proof accuracy."],
        ["SETTLED", "AI verifies proof (or User approves)", "₹X transferred from Escrow to Worker UPI ID. Tx ID generated."]
    ]

    state_table = Table(state_data, colWidths=[110, 170, 207])
    state_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), ACCENT_BLUE),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 8.5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('FONTSIZE', (0,1), (-1,-1), 8),
        ('PADDING', (0,1), (-1,-1), 5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_LIGHT])
    ]))
    story.append(state_table)
    story.append(Spacer(1, 12))

    # Section 5: Teammate Setup & Task Allocation Checklist
    story.append(Paragraph("5. Teammate Setup & Task Allocation Checklist", h1_style))
    story.append(Paragraph("Share this section with your teammates to divide and conquer:", body_style))

    story.append(Paragraph("<b>A. 2-Minute Free Key Setup (For any teammate running the bot):</b>", h2_style))
    story.append(Paragraph("• <b>Telegram Token</b>: Message <code>@BotFather</code> on Telegram $\\to$ Send <code>/newbot</code> $\\to$ Copy token.", bullet_style))
    story.append(Paragraph("• <b>Gemini API Key</b>: Go to <font color='#2563eb'><u>aistudio.google.com</u></font> $\\to$ Sign in $\\to$ Click <i>Get API Key</i>.", bullet_style))

    story.append(Paragraph("<b>B. Task Division for Team Members:</b>", h2_style))
    
    tasks_div_data = [
        ["Team Role", "Assigned Tasks & Deliverables"],
        ["Frontend Dev 1 (Marketing)", "Build Cascade-styled landing page at <code>/</code> (Hero, Stack, Pricing, FAQ, 'Open App' link)."],
        ["Frontend Dev 2 (Worker Portal)", "Build Worker Dashboard at <code>/worker</code> (Job Feed, Claim button, Deliverable Upload modal)."],
        ["Backend Dev (API & Bot)", "Build Flask REST endpoints + Telegram Bot handler + AI Proof Verification function."],
        ["Presenter / Pitcher", "Prepare SIH slide deck & practice live 6-step phone-to-website demo flow for judges."]
    ]

    tasks_table = Table(tasks_div_data, colWidths=[120, 367])
    tasks_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#334155")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 8.5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('FONTSIZE', (0,1), (-1,-1), 8),
        ('PADDING', (0,1), (-1,-1), 5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_LIGHT])
    ]))
    story.append(tasks_table)
    story.append(Spacer(1, 14))

    # Footer Notice Box
    final_note = (
        "<b>Summary for SIH Presentation:</b> Sarathi AI demonstrates a seamless real-world problem solution: "
        "no app downloads required for users, zero cost for free AI answers, pre-authorized UPI escrow for trust, "
        "and automated AI proof verification to protect both users and gig workers."
    )
    final_table = Table([[Paragraph(final_note, body_style)]], colWidths=[487])
    final_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f0f9ff")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#bae6fd")),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(final_table)

    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[OK] Blueprint PDF successfully generated at: {os.path.abspath(filename)}")

if __name__ == "__main__":
    create_blueprint_pdf()
