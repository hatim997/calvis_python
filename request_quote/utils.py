# clavis_event_inventory/request_quote/utils.py

import io
from django.http import HttpResponse
from django.utils import timezone
from django.conf import settings
import os

# ReportLab Imports
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER, TA_JUSTIFY

# Import models
from .models import QuoteRequest, QuoteRequestItem
from inventory.models import Item

# --- COMPANY DETAILS ---
COMPANY_NAME_FOR_PDF = "Clavis Events & Promotions W.L.L"
COMPANY_ADDRESS_PDF_LINE1 = "Office 123, Building 456, Road 789"
COMPANY_ADDRESS_PDF_LINE2 = "Manama, Kingdom of Bahrain"
COMPANY_CONTACT_DETAILS_PDF = "Tel: +973 1700 0000 | Email: info@clavisevents.com"
COMPANY_REGISTRATION_PDF = "CR: XXXXXX-X | VAT: XXXXXXXXXXXXXXX"

# --- PDF STYLES ---
def get_pdf_styles():
    styles = getSampleStyleSheet()
    base_font = 'Helvetica'
    base_font_bold = 'Helvetica-Bold'

    # Company Header Styles
    styles.add(ParagraphStyle(name='CompanyNameLarge', parent=styles['h1'], fontName=base_font_bold, fontSize=16, leading=18, alignment=TA_LEFT, textColor=colors.HexColor("#2C3E50")))
    styles.add(ParagraphStyle(name='CompanyAddressSmall', parent=styles['Normal'], fontName=base_font, fontSize=7, leading=8, alignment=TA_LEFT, textColor=colors.HexColor("#34495E")))

    # Document Title & Reference Styles
    styles.add(ParagraphStyle(name='DocumentTitleMain', parent=styles['h1'], fontName=base_font_bold, fontSize=18, alignment=TA_RIGHT, textColor=colors.HexColor("#4A4A4A"), spaceBefore=0, spaceAfter=1))
    styles.add(ParagraphStyle(name='DocumentReference', parent=styles['Normal'], fontName=base_font_bold, fontSize=8, alignment=TA_RIGHT, textColor=colors.HexColor("#2C3E50"), spaceBefore=3))

    # Addressee & Date Section Styles
    styles.add(ParagraphStyle(name='AddresseeToLabel', parent=styles['Normal'], fontName=base_font, fontSize=7.5, alignment=TA_LEFT, textColor=colors.HexColor("#7F8C8D"), spaceBefore=0, spaceAfter=1, leading=9))
    styles.add(ParagraphStyle(name='AddresseeName', parent=styles['Normal'], fontName=base_font_bold, fontSize=9, alignment=TA_LEFT, textColor=colors.HexColor("#2C3E50"), spaceBefore=0, spaceAfter=0, leading=11))
    styles.add(ParagraphStyle(name='AddresseeInfo', parent=styles['Normal'], fontName=base_font, fontSize=7.5, alignment=TA_LEFT, textColor=colors.HexColor("#34495E"), leading=9))
    styles.add(ParagraphStyle(name='RightDetailLine', parent=styles['Normal'], fontName=base_font, fontSize=8, alignment=TA_RIGHT, textColor=colors.HexColor("#2C3E50"), spaceBefore=0, spaceAfter=0, leading=10))
    styles.add(ParagraphStyle(name='RightDetailLineBold', parent=styles['RightDetailLine'], fontName=base_font_bold))

    # Item Table Styles
    styles.add(ParagraphStyle(name='ItemsTableHeader', parent=styles['Normal'], fontName=base_font_bold, fontSize=7.5, alignment=TA_CENTER, textColor=colors.white, spaceBefore=2, spaceAfter=2))
    styles.add(ParagraphStyle(name='ItemsTableCellText', parent=styles['Normal'], fontName=base_font, fontSize=7.5, leading=9, alignment=TA_LEFT))
    styles.add(ParagraphStyle(name='ItemsTableCellNumber', parent=styles['Normal'], fontName=base_font, fontSize=7.5, leading=9, alignment=TA_CENTER))

    # Section Title
    styles.add(ParagraphStyle(name='SectionTitle', parent=styles['h2'], fontName=base_font_bold, fontSize=10, alignment=TA_LEFT, textColor=colors.HexColor("#2C3E50"), spaceBefore=10, spaceAfter=2, borderPadding=1, bottomPadding=1))

    # Disclaimer & Signature Styles
    styles.add(ParagraphStyle(name='DisclaimerText', parent=styles['Normal'], fontName=base_font, fontSize=6.5, leading=8, textColor=colors.HexColor("#546E7A"), alignment=TA_JUSTIFY))
    styles.add(ParagraphStyle(name='SignatureLine', parent=styles['Normal'], fontName=base_font, fontSize=8, spaceBefore=12, textColor=colors.HexColor("#2C3E50"), leading=10))
    styles.add(ParagraphStyle(name='SignatureLabel', parent=styles['Normal'], fontName=base_font_bold, fontSize=8, spaceBefore=0, textColor=colors.HexColor("#2C3E50"), leading=10))
    
    styles.add(ParagraphStyle(name='NoDataMessage', parent=styles['Normal'], fontSize=9, textColor=colors.grey, alignment=TA_CENTER, spaceBefore=6, spaceAfter=6))
    return styles

def build_pdf_header_letterhead(story_list, styles, logo_el, doc_title_text, quote_ref, 
                                company_name_main, company_address_l1, company_address_l2, company_contact_reg, 
                                show_company_info=True):
    left_col_content = []
    if logo_el:
        logo_el.hAlign = 'LEFT'
        left_col_content.append(logo_el)
        if show_company_info:
            left_col_content.append(Spacer(1, 0.05*inch))
    
    if show_company_info:
        if company_name_main:
            left_col_content.append(Paragraph(company_name_main, styles['CompanyNameLarge']))
        if company_address_l1:
            left_col_content.append(Paragraph(company_address_l1.replace('<br/>', '\n'), styles['CompanyAddressSmall']))
        if company_address_l2:
            left_col_content.append(Paragraph(company_address_l2.replace('\n', '<br/>'), styles['CompanyAddressSmall']))
        if company_contact_reg:
            left_col_content.append(Paragraph(company_contact_reg, styles['CompanyAddressSmall']))
    
    right_col_content = [
        Paragraph(doc_title_text.upper(), styles['DocumentTitleMain']),
        Paragraph(f"No: {quote_ref}", styles['DocumentReference'])
    ]
    
    if not left_col_content:
        left_col_content = [Spacer(1, 0.1*inch)]

    header_table_data = [[left_col_content, right_col_content]]
    header_table = Table(header_table_data, colWidths=[3.75*inch, 3.75*inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (0,0), (0,0), 'LEFT'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),       
        ('RIGHTPADDING', (0,0), (-1,-1), 0),       
    ]))
    story_list.append(header_table)
    story_list.append(Spacer(1, 0.2*inch))

def build_addressee_date_section_letterhead(story_list, styles, quote, doc_date_label, doc_date_value):
    left_info = []
    right_info = []

    def right(label, value):
        return Paragraph(f"<b>{label}</b> {value or 'N/A'}", styles['RightDetailLine'])

    def left(label, value):
        return Paragraph(f"<b>{label}:</b> {value or 'N/A'}", styles['AddresseeInfo'])

    # LEFT COLUMN
    left_info.append(left("Client Name", quote.client.name))
    left_info.append(left("Event Start Date", quote.event_start_date.strftime('%d %B %Y') if quote.event_start_date else 'N/A'))
    left_info.append(left("Setup Installation Date & Time", quote.setup_installation_datetime.strftime('%d %B %Y, %I:%M %p') if quote.setup_installation_datetime else 'N/A'))

    # Highlight Project Manager line
    pm_name = quote.project_manager.get_full_name() or quote.project_manager.username if quote.project_manager else "N/A"
    project_manager_line = f"<b>Project Manager Name</b> <font>{pm_name}</font>"
    left_info.append(Paragraph(project_manager_line, styles['AddresseeInfo']))
    left_info.append(left("Subcontractors if Involved", quote.subcontractors))

    # RIGHT COLUMN
    right_info.append(right("Date:", doc_date_value))
    right_info.append(right("Reference Number:", quote.reference_number))
    right_info.append(right("Event Title:", quote.event_title))
    right_info.append(right("Event End Date:", quote.event_end_date.strftime('%d %B %Y') if quote.event_end_date else 'N/A'))
    right_info.append(right("Setup Removal Date & Time:", quote.setup_removal_datetime.strftime('%d %B %Y, %I:%M %p') if quote.setup_removal_datetime else 'N/A'))
    right_info.append(right("Delivery Note to be signed from", "?????"))

    # Assemble the table
    table_data = [[left_info, right_info]]
    table = Table(table_data, colWidths=[3.75*inch, 3.25*inch])
    table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
    ]))

    story_list.append(table)
    story_list.append(Spacer(1, 0.2*inch))
    
def build_items_table_letterhead(story, styles, quote_items_qs):
    data = []

    # Table headers
    data.append([
        Paragraph("Sr.", styles['ItemsTableHeader']),
        Paragraph("List of Items", styles['ItemsTableHeader']),
        Paragraph("Quantity", styles['ItemsTableHeader']),
    ])

    # Table body
    for idx, quote_item in enumerate(quote_items_qs, 1):
        item_name = quote_item.item.name if hasattr(quote_item.item, 'name') else 'N/A'
        quantity = quote_item.quantity if quote_item.quantity else ''
        
        data.append([
            Paragraph(str(idx), styles['ItemsTableCellNumber']),
            Paragraph(item_name, styles['ItemsTableCellText']),
            Paragraph(str(quantity), styles['ItemsTableCellNumber']),
        ])

    # Create table
    table = Table(data, colWidths=[0.5*inch, 5.5*inch, 1.0*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2C3E50")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.25, colors.grey),
        ('FONTSIZE', (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('TOPPADDING', (0,0), (-1,0), 6),
    ]))

    story.append(table)



def draw_signature_footer(canvas, doc):
    canvas.saveState()
    width, height = letter

    # Set margins
    left_margin = doc.leftMargin
    right_margin = doc.rightMargin
    usable_width = width - left_margin - right_margin

    # Calculate space for 2 equal sections with padding
    col_width = usable_width / 2
    padding = 15  # Extra padding between columns

    x1 = left_margin
    x2 = x1 + col_width + padding
    y = 0.5 * inch

    canvas.setFont("Helvetica-Bold", 7)
    canvas.drawString(x1, y + 30, "Prepared By (Clavis Representative):")
    canvas.drawString(x2, y + 30, "Approved By (Client/Representative):")

    canvas.setFont("Helvetica", 7)
    canvas.drawString(x1, y + 15, "Name & Signature: ________________________")
    canvas.drawString(x2, y + 15, "Name & Signature: ________________________")
    canvas.drawString(x1, y, "Date: _______________   Time: __________")
    canvas.drawString(x2, y, "Date: _______________   Time: __________")

    canvas.restoreState()

# In request_quote/utils.py, within generate_quote_pdf
def generate_quote_pdf(quote):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.4*inch,
        bottomMargin=1.2*inch
    )
    styles = get_pdf_styles()
    story = []

    # Load logo
    logo_path = os.path.join(settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else settings.STATIC_ROOT or '', 'images', 'clavis_logo.png')
    logo_el = None
    if os.path.exists(logo_path):
        try:
            logo = Image(logo_path, width=1.5*inch, height=0.6*inch, kind='proportional')
            logo_el = logo
        except Exception as e:
            print(f"--- ERROR: Error loading logo image for Quote: {e}")

    # Build header
    build_pdf_header_letterhead(
        story, styles, logo_el, "QUOTE REQUEST",
        quote.reference_number, COMPANY_NAME_FOR_PDF,
        COMPANY_ADDRESS_PDF_LINE1, COMPANY_ADDRESS_PDF_LINE2,
        COMPANY_CONTACT_DETAILS_PDF + " | " + COMPANY_REGISTRATION_PDF,
        show_company_info=True
    )

    # Addressee and date section
    quote_date_str = quote.date_created.strftime('%d %B %Y') if quote.date_created else "N/A"  # Fixed: Removed timezone.localtime
    build_addressee_date_section_letterhead(story, styles, quote, "Quote Date:", quote_date_str)

    # ... (rest of the function remains unchanged) ...
    # Items table
    quote_items_qs = quote.items.all().select_related('item', 'item__category')
    build_items_table_letterhead(story, styles, quote_items_qs)

    # Additional details
    story.append(Spacer(1, 0.15*inch))
    if quote.project_manager_notes:
        story.append(Paragraph("Additional Notes", styles['SectionTitle']))
        story.append(Paragraph(quote.project_manager_notes.replace('\n', '<br/>'), styles['ItemsTableCellText']))
        story.append(Spacer(1, 0.15*inch))

    # Disclaimer
    disclaimer_text = "<b>Terms:</b> This quotation is valid for 30 days from the date of issue. All items are subject to availability at the time of confirmation. Please confirm acceptance in writing."
    story.append(Paragraph(disclaimer_text, styles['DisclaimerText']))
    story.append(Spacer(1, 0.25*inch))

    # Build PDF with signature footer
    doc.build(story, onFirstPage=draw_signature_footer, onLaterPages=draw_signature_footer)

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    filename = f"Quote-{quote.reference_number}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response