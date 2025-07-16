# clavis_event_inventory/bookings/utils.py

import io
from django.http import HttpResponse
from django.utils import timezone
from django.conf import settings
import os
from datetime import date, datetime
import calendar

# ReportLab Imports
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, HRFlowable, PageBreak, KeepInFrame
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER, TA_JUSTIFY

# Import models
from clients.models import Client
from .models import Event, Rental
from inventory.models import Item

from reportlab.platypus import Frame

# ... (Keep your COMPANY DETAILS and get_pdf_styles, get_base_table_style, apply_zebra_striping functions as they are) ...
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
    
    # Waybill Specific
    styles.add(ParagraphStyle(name='WaybillDetailLabel', parent=styles['Normal'], fontName=base_font_bold, fontSize=8, alignment=TA_LEFT, spaceAfter=1, leading=10))
    styles.add(ParagraphStyle(name='WaybillDetailText', parent=styles['Normal'], fontName=base_font, fontSize=8, alignment=TA_LEFT, leftIndent=10, spaceAfter=4, leading=10))

    # Disclaimer & Signature Styles
    styles.add(ParagraphStyle(name='DisclaimerText', parent=styles['Normal'], fontName=base_font, fontSize=6.5, leading=8, textColor=colors.HexColor("#546E7A"), alignment=TA_JUSTIFY))
    styles.add(ParagraphStyle(name='SignatureLine', parent=styles['Normal'], fontName=base_font, fontSize=8, spaceBefore=12, textColor=colors.HexColor("#2C3E50"), leading=10))
    styles.add(ParagraphStyle(name='SignatureLabel', parent=styles['Normal'], fontName=base_font_bold, fontSize=8, spaceBefore=0, textColor=colors.HexColor("#2C3E50"), leading=10))
    
    styles.add(ParagraphStyle(name='NoDataMessage', parent=styles['Normal'], fontSize=9, textColor=colors.grey, alignment=TA_CENTER, spaceBefore=6, spaceAfter=6))
    return styles

def build_pdf_header_letterhead(story_list, styles, logo_el, doc_title_text, booking_ref, 
                                company_name_main, company_address_l1, company_address_l2, company_contact_reg, 
                                show_company_info=True):
    left_col_content = []
    if logo_el:
        logo_el.hAlign = 'LEFT' 
        left_col_content.append(logo_el)
        if show_company_info:
            left_col_content.append(Spacer(1,0.05*inch))
    
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
        Paragraph(f"No: {booking_ref}", styles['DocumentReference'])
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


def build_addressee_date_section_letterhead(story_list, styles, booking, doc_date_label, doc_date_value, service_type_label="Event Name:"):
    client = booking.client
    addressee_info_style = styles['AddresseeInfo']
    addressee_label_style = styles['AddresseeToLabel']
    addressee_name_style = styles['AddresseeName']
    right_detail_line_style = styles['RightDetailLine']

    # --- Client Details (Left Column) ---
    left_col_elements = [Paragraph("To:", addressee_label_style)]
    if client:
        left_col_elements.append(Paragraph(client.name or "N/A", addressee_name_style))
        if client.company_name:
            left_col_elements.append(Paragraph(client.company_name, addressee_info_style))
        
        contact_parts = []
        if client.phone: contact_parts.append(f"Tel: {client.phone}")
        if client.email: contact_parts.append(f"Email: {client.email}")
        if contact_parts:
            left_col_elements.append(Paragraph(" / ".join(filter(None, contact_parts)), addressee_info_style))
        
        if client.address: 
            address_text = client.address.replace('\n', '<br/>')
            left_col_elements.append(Spacer(1, 0.02*inch)) 
            left_col_elements.append(Paragraph(address_text, addressee_info_style))
    else:
        left_col_elements.append(Paragraph("N/A", addressee_name_style))

    # --- Booking Details (Right Column) ---
    right_col_elements = [
        Paragraph(f"<b>{doc_date_label}</b> {doc_date_value}", right_detail_line_style),
    ]

    # ** THIS IS THE FIX **
    # Check if the booking is an Event and has an event_name
    if isinstance(booking, Event) and booking.event_name:
        right_col_elements.append(Paragraph(f"<b>{service_type_label}</b> {booking.event_name}", right_detail_line_style))
    elif isinstance(booking, Rental):
        # For rentals, we don't have a name, so just show the label and the client name again or ref#
        right_col_elements.append(Paragraph(f"<b>{service_type_label}</b> {str(booking.client)}", right_detail_line_style))


    right_col_elements.append(Paragraph(f"<b>Status:</b> {booking.get_status_display()}", right_detail_line_style))
    
    # Add location details
    if isinstance(booking, Event):
        location_label = "Primary Site:" if booking.is_logistics_only_service else "Location:"
        location_value = booking.delivery_address_override or booking.event_location
        if location_value:
            location_text = f"<b>{location_label}</b> {str(location_value).replace(chr(10), '<br/>').replace(chr(13), '')}"
            right_col_elements.append(Paragraph(location_text, right_detail_line_style))
    elif isinstance(booking, Rental) and booking.delivery_location:
        delivery_loc_text = str(booking.delivery_location).replace('\n', '<br/>')
        right_col_elements.append(Paragraph(f"<b>Delivery Location:</b> {delivery_loc_text}", right_detail_line_style))

    if booking.project_manager_name:
        right_col_elements.append(Paragraph(f"<b>Project Manager:</b> {booking.project_manager_name}", right_detail_line_style))
    if booking.subcontractor_name:
        right_col_elements.append(Paragraph(f"<b>Subcontractor:</b> {booking.subcontractor_name}", right_detail_line_style))

    # Assemble the table
    addressee_table_data = [[left_col_elements, right_col_elements]]
    addressee_table = Table(addressee_table_data, colWidths=[3.75*inch, 3.25*inch])
    addressee_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (0,0), 0),
        ('RIGHTPADDING', (1,0), (1,0), 0), 
        ('ALIGN', (1,0), (1,-1), 'RIGHT'), 
    ]))
    story_list.append(addressee_table)
    story_list.append(Spacer(1, 0.15*inch))
    
# --- The rest of your utils.py file (build_items_table_letterhead, generate_delivery_note_pdf, etc.) remains the same ---
# ... (include the rest of the functions from your previous version here) ...

def build_items_table_letterhead(story_list, styles, booking_items):
    table_header_style = styles['ItemsTableHeader']
    cell_text_style = styles['ItemsTableCellText']
    cell_number_style = styles['ItemsTableCellNumber']
    section_title_style = styles['SectionTitle']
    no_data_style = styles['NoDataMessage']

    story_list.append(Paragraph("Items Delivered / Received", section_title_style)) 
    story_list.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#BDC3C7"), spaceBefore=1, spaceAfter=3))
    
    if booking_items and booking_items.exists():
        table_data = [
            [Paragraph("#", table_header_style), 
             Paragraph("ITEM & DESCRIPTION", table_header_style), 
             Paragraph("QTY", table_header_style)]
        ]
        for i, booking_item in enumerate(booking_items, 1):
            item = booking_item.item
            item_name_text = item.name if item else "N/A Item"
            item_desc_text_formatted = ""
            
            if item and item.description:
                desc_str = str(item.description)
                desc_snippet = (desc_str[:50] + '...') if len(desc_str) > 50 else desc_str 
                desc_snippet_html = desc_snippet.replace('\n', '<br/>')
                item_desc_text_formatted = f"<br/><font size='-2' color='#546E7A'><i>- {desc_snippet_html}</i></font>"
            
            full_item_text = f"<b>{item_name_text}</b>{item_desc_text_formatted}"
            
            table_data.append([ 
                Paragraph(str(i), cell_number_style), 
                Paragraph(full_item_text, cell_text_style), 
                Paragraph(str(booking_item.quantity), cell_number_style), 
            ])
        
        item_table = Table(table_data, colWidths=[0.4*inch, 5.9*inch, 0.7*inch]) 
        item_table.setStyle(TableStyle([ 
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4A5568")), 
            ('TEXTCOLOR',(0,0),(-1,0),colors.white), 
            ('ALIGN', (0,0), (-1,0), 'CENTER'), 
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), 
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), 
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#BDC3C7")), 
            ('ALIGN', (0,1), (0,-1), 'CENTER'), 
            ('ALIGN', (2,1), (2,-1), 'CENTER'), 
            ('LEFTPADDING', (1,0), (1,-1), 4), 
            ('RIGHTPADDING', (1,0), (1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,0), 3), 
            ('TOPPADDING', (0,0), (-1,0), 3),   
            ('BOTTOMPADDING', (0,1), (-1,-1), 2),
            ('TOPPADDING', (0,1), (-1,-1), 2),   
        ]))
        story_list.append(item_table)
    else: 
        story_list.append(Paragraph("No items from our inventory are listed for this booking.", no_data_style))
    story_list.append(Spacer(1, 0.05*inch))

def draw_signature_footer(canvas, doc):
    canvas.saveState()
    width, height = letter

    # Set margins
    left_margin = doc.leftMargin
    right_margin = doc.rightMargin
    usable_width = width - left_margin - right_margin

    # Calculate space for 3 equal sections with padding
    col_width = usable_width / 3
    padding = 15  # Extra padding between columns

    x1 = left_margin
    x2 = x1 + col_width + padding
    x3 = x2 + col_width + padding
    y = 0.5 * inch

    canvas.setFont("Helvetica-Bold", 7)
    canvas.drawString(x1, y + 30, "Received By (Client/Representative):")
    canvas.drawString(x2, y + 30, "Warehouse:")
    canvas.drawString(x3, y + 30, "Project Manager:")

    canvas.setFont("Helvetica", 7)
    canvas.drawString(x1, y + 15, "Name & Signature: ________________________")
    canvas.drawString(x2, y + 15, "Name & Signature: ________________________")
    canvas.drawString(x3, y + 15, "Name & Signature: ________________________")

    canvas.drawString(x1, y, "Date: _______________   Time: __________")
    canvas.drawString(x2, y, "Date: _______________   Time: __________")
    canvas.drawString(x3, y, "Date: _______________   Time: __________")

    canvas.restoreState()

# --- Delivery Note Function ---
def generate_delivery_note_pdf(booking):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.4*inch,
        bottomMargin=1.2*inch  # 👈 Reserve enough space for the footer!
    )
    styles = get_pdf_styles() 
    story = []

    logo_path = os.path.join(settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else settings.STATIC_ROOT or '', 'images', 'clavis_logo.png')
    logo_el = None
    if os.path.exists(logo_path):
        try:
            logo = Image(logo_path, width=1.5*inch, height=0.6*inch, kind='proportional') 
            logo_el = logo
        except Exception as e:
            print(f"--- ERROR: Error loading logo image for Delivery Note: {e}")

    build_pdf_header_letterhead(story, styles, logo_el, "DELIVERY NOTE", booking.reference_number,
                                COMPANY_NAME_FOR_PDF, 
                                COMPANY_ADDRESS_PDF_LINE1, 
                                COMPANY_ADDRESS_PDF_LINE2,
                                COMPANY_CONTACT_DETAILS_PDF + " | " + COMPANY_REGISTRATION_PDF,
                                show_company_info=False) # Hides company info
    
    delivery_date_str = timezone.localtime(booking.start_date).strftime('%d %B %Y, %H:%M') if booking.start_date else "N/A"
    
    if isinstance(booking, Event):
        build_addressee_date_section_letterhead(story, styles, booking, "Event Date:", delivery_date_str, service_type_label="Event Name:")
    elif isinstance(booking, Rental):
        build_addressee_date_section_letterhead(story, styles, booking, "Pickup Date:", delivery_date_str, service_type_label="Rental For:")


    booking_items_qs = booking.items.all().select_related('item', 'item__category') 
    build_items_table_letterhead(story, styles, booking_items_qs)
    
    story.append(Spacer(1, 0.15*inch))
    disclaimer1_text = "<b>Condition on Dispatch:</b> All items listed above were checked at the time of dispatch and confirmed to be in good working condition and free from damage unless otherwise noted. Any discrepancies must be reported to Clavis Events <b>immediately</b> upon receipt."
    story.append(Paragraph(disclaimer1_text, styles['DisclaimerText']))
    story.append(Spacer(1, 0.05*inch)) 
    disclaimer2_text = "<b>Care of Items:</b> You are requested to handle all items with care, especially electronic and fragile equipment."
    story.append(Paragraph(disclaimer2_text, styles['DisclaimerText']))
    story.append(Spacer(1, 0.25*inch)) 

    # sig_data = [
    #     [Paragraph("Received By (Client/Representative):", styles['SignatureLabel']), Paragraph("Clavis Events Staff:", styles['SignatureLabel'])],
    #     [Spacer(1, 0.5*inch), Spacer(1, 0.5*inch)], 
    #     [Paragraph("Name & Signature:________________________", styles['SignatureLine']), Paragraph("Name & Signature:________________________", styles['SignatureLine'])],
    #     [Paragraph("Date: _______________ Time: __________", styles['SignatureLine']), Paragraph("Date: _______________ Time: __________", styles['SignatureLine'])],
    # ]
    # sig_table = Table(sig_data, colWidths=[3.5*inch, 3.5*inch])
    # sig_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    # story.append(sig_table)

    doc.build(story, onFirstPage=draw_signature_footer, onLaterPages=draw_signature_footer)

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    filename = f"Delivery-Note-{booking.reference_number}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


# --- Receipt / Return Confirmation Function ---
def generate_receipt_pdf(booking):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, 
                            rightMargin=0.5*inch, leftMargin=0.5*inch, 
                            topMargin=0.4*inch, bottomMargin=0.4*inch)
    styles = get_pdf_styles()
    story = []

    logo_path = os.path.join(settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else settings.STATIC_ROOT or '', 'images', 'clavis_logo.png')
    logo_el = None
    if os.path.exists(logo_path):
        try:
            logo = Image(logo_path, width=1.5*inch, height=0.6*inch, kind='proportional')
            logo_el = logo
        except Exception as e:
            print(f"--- ERROR: Error loading logo image for Receipt: {e}")

    is_event = isinstance(booking, Event)
    receipt_title_text = "EVENT COMPLETION RECEIPT" if is_event else "RENTAL RETURN RECEIPT"
    
    build_pdf_header_letterhead(story, styles, logo_el, receipt_title_text, booking.reference_number,
                                COMPANY_NAME_FOR_PDF, 
                                COMPANY_ADDRESS_PDF_LINE1, 
                                COMPANY_ADDRESS_PDF_LINE2, 
                                COMPANY_CONTACT_DETAILS_PDF + " | " + COMPANY_REGISTRATION_PDF,
                                show_company_info=True) # Explicitly show for receipts
    
    completion_date_str = timezone.localtime(booking.updated_at).strftime('%d %B %Y') if booking.updated_at else "N/A"
    
    if is_event:
        build_addressee_date_section_letterhead(story, styles, booking, "Completion Date:", completion_date_str, service_type_label="Event Name:" if not booking.is_logistics_only_service else "Service Title:")
    else: # It's a Rental
        build_addressee_date_section_letterhead(story, styles, booking, "Return Date:", completion_date_str, service_type_label="Rental For:")


    booking_items_qs = booking.items.all().select_related('item', 'item__category')
    
    if not (is_event and getattr(booking, 'is_logistics_only_service', False)):
        story.append(Paragraph("Items Returned/Accounted For", styles['SectionTitle']))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#BDC3C7"), spaceBefore=1, spaceAfter=3))
        
        if booking_items_qs.exists():
            table_data = [
                [Paragraph("#", styles['ItemsTableHeader']), 
                 Paragraph("ITEM & DESCRIPTION", styles['ItemsTableHeader']), 
                 Paragraph("QTY", styles['ItemsTableHeader'])]
            ]
            for i, booking_item in enumerate(booking_items_qs, 1):
                item = booking_item.item
                item_name_text = item.name if item else "N/A Item"
                item_desc_text_formatted = ""
                item_source_note = "" 
                if item and hasattr(item, 'item_source') and item.item_source == Item.ItemSourceType.CLIENT_SUPPLIED:
                     item_source_note = " <font size='-2' color='#D35400'><i>(Client Supplied)</i></font>"

                if item and item.description:
                    desc_str = str(item.description)
                    desc_snippet = (desc_str[:50] + '...') if len(desc_str) > 50 else desc_str
                    desc_snippet_html = desc_snippet.replace('\n', '<br/>')
                    item_desc_text_formatted = f"<br/><font size='-2' color='#546E7A'><i>- {desc_snippet_html}</i></font>"
                
                full_item_text = f"<b>{item_name_text}</b>{item_source_note}{item_desc_text_formatted}"

                table_data.append([ 
                    Paragraph(str(i), styles['ItemsTableCellNumber']), 
                    Paragraph(full_item_text, styles['ItemsTableCellText']), 
                    Paragraph(str(booking_item.quantity), styles['ItemsTableCellNumber']), 
                ])
            
            item_table = Table(table_data, colWidths=[0.4*inch, 5.9*inch, 0.7*inch])
            item_table.setStyle(TableStyle([ 
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4A5568")), 
                ('TEXTCOLOR',(0,0),(-1,0),colors.white), 
                ('ALIGN', (0,0), (-1,0), 'CENTER'), 
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), 
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), 
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#D1D5DB")), 
                ('ALIGN', (0,1), (0,-1), 'CENTER'), 
                ('ALIGN', (2,1), (2,-1), 'CENTER'), 
                ('LEFTPADDING', (1,0), (1,-1), 4), 
                ('RIGHTPADDING', (1,0), (1,-1), 4),
                ('BOTTOMPADDING', (0,0), (-1,0), 3), 
                ('TOPPADDING', (0,0), (-1,0), 3),   
                ('BOTTOMPADDING', (0,1), (-1,-1), 2),
                ('TOPPADDING', (0,1), (-1,-1), 2),   
            ]))
            story.append(item_table)
        else:
            story.append(Paragraph("No items were part of this booking.", styles['NoDataMessage']))
    elif is_event and getattr(booking, 'is_logistics_only_service', False):
        story.append(Paragraph("This was a logistics-only service.", styles['NoDataMessage']))


    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("Confirmed By (Client/Representative):", styles['SignatureLabel']))
    story.append(Spacer(1, 0.3*inch)) 
    story.append(Paragraph("Name: _______________________________ Signature: _________________________ Date: _______________", styles['SignatureLine']))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("Clavis Events Staff:", styles['SignatureLabel']))
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph("Name: _______________________________ Signature: _________________________ Date: _______________", styles['SignatureLine']))

    doc.build(story)
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    filename = f"Receipt-{booking.reference_number}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

# --- Logistics Waybill PDF Generation ---
def generate_logistics_waybill_pdf(event_instance): 
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, 
                            rightMargin=0.75*inch, leftMargin=0.75*inch, 
                            topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = get_pdf_styles()
    story = []

    logo_path = os.path.join(settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else settings.STATIC_ROOT or '', 'images', 'clavis_logo.png')
    logo_el = None
    if os.path.exists(logo_path):
        try:
            logo = Image(logo_path, width=1.5*inch, height=0.6*inch, kind='proportional')
            logo_el = logo
        except Exception as e:
            print(f"Error loading logo for Waybill: {e}")

    # For Waybill, we want to show company info, so show_company_info=True (or omit, as it defaults to True)
    build_pdf_header_letterhead(story, styles, logo_el, "LOGISTICS WAYBILL", event_instance.reference_number,
                                COMPANY_NAME_FOR_PDF, 
                                COMPANY_ADDRESS_PDF_LINE1, 
                                COMPANY_ADDRESS_PDF_LINE2, 
                                COMPANY_CONTACT_DETAILS_PDF + " | " + COMPANY_REGISTRATION_PDF,
                                show_company_info=True) 
    
    service_date_str = timezone.localtime(event_instance.start_date).strftime('%d %B %Y, %H:%M') if event_instance.start_date else "N/A"
    build_addressee_date_section_letterhead(story, styles, event_instance, "Service Date:", service_date_str, service_type_label="Service Title:")
    
    story.append(Spacer(1, 0.1*inch))
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.black, spaceBefore=5, spaceAfter=8))

    story.append(Paragraph("<b>Description of Goods:</b>", styles['WaybillDetailLabel']))
    story.append(Paragraph(event_instance.description_of_goods.replace('\n', '<br/>') if event_instance.description_of_goods else "N/A", styles['WaybillDetailText']))
    story.append(Spacer(1, 0.15*inch))

    # Logistics Details Table
    story.append(Paragraph("<b>Logistics Movements:</b>", styles['SectionTitle']))
    logistics_details_table_data = [
        [Paragraph("<b><u>Leg 1: Client to Site</u></b>", styles['WaybillDetailLabel']), None],
        [Paragraph("Pickup From (Client):", styles['WaybillDetailLabel']), Paragraph(event_instance.pickup_address.replace('\n', '<br/>') if event_instance.pickup_address else "N/A", styles['WaybillDetailText'])],
        [Paragraph("Pickup Contact:", styles['WaybillDetailLabel']), Paragraph(event_instance.pickup_contact_details.replace('\n', '<br/>') if event_instance.pickup_contact_details else "N/A", styles['WaybillDetailText'])],
        [Paragraph("Deliver To (Site):", styles['WaybillDetailLabel']), Paragraph((event_instance.delivery_address_override or event_instance.event_location or "N/A").replace('\n', '<br/>'), styles['WaybillDetailText'])],
        [Paragraph("Delivery Contact (Site):", styles['WaybillDetailLabel']), Paragraph(event_instance.delivery_contact_details.replace('\n', '<br/>') if event_instance.delivery_contact_details else "N/A", styles['WaybillDetailText'])],
        
        [Spacer(1,0.05*inch), None], # Small spacer
        
        [Paragraph("<b><u>Leg 2: Site to Client/Warehouse</u></b>", styles['WaybillDetailLabel']), None],
        [Paragraph("Return Pickup From (Site):", styles['WaybillDetailLabel']), Paragraph(event_instance.return_pickup_address.replace('\n', '<br/>') if event_instance.return_pickup_address else "(As per Delivery Site)", styles['WaybillDetailText'])],
        [Paragraph("Return Pickup Contact:", styles['WaybillDetailLabel']), Paragraph(event_instance.return_pickup_contact_details.replace('\n', '<br/>') if event_instance.return_pickup_contact_details else "N/A", styles['WaybillDetailText'])],
        [Paragraph("Return Delivery To:", styles['WaybillDetailLabel']), Paragraph(event_instance.return_delivery_address.replace('\n', '<br/>') if event_instance.return_delivery_address else "(As per Client Pickup Address)", styles['WaybillDetailText'])],
        [Paragraph("Return Delivery Contact:", styles['WaybillDetailLabel']), Paragraph(event_instance.return_delivery_contact_details.replace('\n', '<br/>') if event_instance.return_delivery_contact_details else "N/A", styles['WaybillDetailText'])],
    ]

    logistics_table = Table(logistics_details_table_data, colWidths=[2.3*inch, 4.7*inch])
    logistics_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4), 
        # SPAN and LINE for Leg 1 header
        ('SPAN', (0,0), (1,0)),      
        ('LINEBELOW', (0,0), (1,0), 0.5, colors.grey, None, None, 2, 4),
        # SPAN for spacer
        ('SPAN', (0,5), (1,5)), 
        # SPAN and LINE for Leg 2 header
        ('SPAN', (0,6), (1,6)),      
        ('LINEBELOW', (0,6), (1,6), 0.5, colors.grey, None, None, 2, 4),
    ]))
    story.append(logistics_table)
    story.append(Spacer(1, 0.3*inch))

    # --- Signatures for Waybill ---
    sig_data = [
        [Paragraph("Received By (Client/Site Representative):", styles['SignatureLabel']), Paragraph("Delivered By (Clavis Representative):", styles['SignatureLabel'])],
        [Spacer(1, 0.5*inch), Spacer(1, 0.5*inch)], 
        [Paragraph("Name & Signature:________________________", styles['SignatureLine']), Paragraph("Name & Signature:________________________", styles['SignatureLine'])],
        [Paragraph("Date: _______________ Time: __________", styles['SignatureLine']), Paragraph("Date: _______________ Time: __________", styles['SignatureLine'])],
    ]
    sig_table = Table(sig_data, colWidths=[3.5*inch, 3.5*inch]) 
    sig_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(sig_table)

    doc.build(story)
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    filename = f"Waybill-{event_instance.reference_number}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


# --- Master Inventory Report Utils ---
# Note: These functions use 'initial_quantity' and 'available_quantity', 
# which is correct for your current backup project's model state.
def get_month_year_str_for_master(year, month): 
    try:
        month_int = int(month) 
        month_name = calendar.month_name[month_int]
        return f"{month_name} {year}"
    except (ValueError, IndexError):
        return f"Month {month} {year}" 

def generate_master_inventory_excel(items):
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="clavis_master_inventory_{date.today()}.xlsx"'
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = 'Master Inventory'
    
    headers = [ 
        "SKU", "Item Name", "Category", "Description", "Location", 
        "Initial Qty", "Available Qty",
        "Purchase Price (BHD)", "Rent Price/Day (BHD)", "Supplier", 
        "Depth", "Width", "Height", "Unit", "Created", "Updated" 
    ]
    sheet.append(headers)
    header_font = Font(bold=True)
    for cell in sheet[1]: 
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center')

    for item_obj in items: 
        row_values = [ 
            item_obj.sku, item_obj.name, item_obj.category.name if item_obj.category else '-', 
            item_obj.description, item_obj.storage_location, 
            item_obj.initial_quantity,
            item_obj.available_quantity,
            item_obj.purchase_price, item_obj.rent_price_per_day, 
            item_obj.supplier.name if item_obj.supplier else '-', 
            item_obj.depth, item_obj.width, item_obj.height, 
            item_obj.get_dimension_unit_display(), 
            timezone.localtime(item_obj.created_at).strftime('%Y-%m-%d %H:%M') if item_obj.created_at else '-', 
            timezone.localtime(item_obj.updated_at).strftime('%Y-%m-%d %H:%M') if item_obj.updated_at else '-', 
        ]
        sheet.append(row_values)
    
    for column_cells in sheet.columns:
        max_length = 0
        try: # Use openpyxl.utils.get_column_letter to be safe
            column_letter = openpyxl.utils.get_column_letter(column_cells[0].column)
        except AttributeError: # Fallback for older versions or different structures
            column_letter = column_cells[0].column
            
        for cell in column_cells:
            try:
                if cell.value:
                    cell_value_str = str(cell.value)
                    if len(cell_value_str) > max_length:
                        max_length = len(cell_value_str)
            except:
                pass
        adjusted_width = (max_length + 2) if max_length > 0 else 12
        sheet.column_dimensions[column_letter].width = adjusted_width
        
    workbook.save(response)
    return response

def generate_master_inventory_pdf(items):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=0.5*inch, leftMargin=0.5*inch, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = get_report_pdf_styles()
    story = []
    
    title = f"Clavis Master Inventory Report - {date.today()}"
    story.append(Paragraph(title, styles['ReportMainTitle']))
    story.append(Spacer(1, 0.2*inch))
    
    headers = [ "SKU", "Item Name", "Category", "Loc", "Init Qty", "Avail Qty", "Purch Price", "Rent/Day", "D", "W", "H", "Unit", "Supplier"]
    data = [ [Paragraph(h, styles['ReportTableHeader']) for h in headers] ]

    for item_obj in items: 
        purch_price_str = f"{item_obj.purchase_price} BHD" if item_obj.purchase_price is not None else '-'
        rent_price_str = f"{item_obj.rent_price_per_day} BHD" if item_obj.rent_price_per_day is not None else '-'
        
        row_data = [
            Paragraph(item_obj.sku or '-', styles['ReportTableCell']), 
            Paragraph(item_obj.name or '-', styles['ReportTableCell']), 
            Paragraph(item_obj.category.name if item_obj.category else '-', styles['ReportTableCell']), 
            Paragraph(item_obj.storage_location or '-', styles['ReportTableCell']), 
            Paragraph(str(item_obj.initial_quantity), styles['ReportTableCellCenter']),
            Paragraph(str(item_obj.available_quantity), styles['ReportTableCellCenter']), 
            Paragraph(purch_price_str, styles['ReportTableCellRight']),
            Paragraph(rent_price_str, styles['ReportTableCellRight']), 
            Paragraph(str(item_obj.depth or '-'), styles['ReportTableCellCenter']), 
            Paragraph(str(item_obj.width or '-'), styles['ReportTableCellCenter']), 
            Paragraph(str(item_obj.height or '-'), styles['ReportTableCellCenter']), 
            Paragraph(item_obj.get_dimension_unit_display(), styles['ReportTableCellCenter']), 
            Paragraph(item_obj.supplier.name if item_obj.supplier else '-', styles['ReportTableCell']), 
        ]
        data.append(row_data)
        
    if len(data) > 1 : 
        col_widths_master = [0.7*inch, 1.3*inch, 0.8*inch, 0.8*inch, 0.6*inch, 0.6*inch, 0.8*inch, 0.8*inch, 0.4*inch, 0.4*inch, 0.4*inch, 0.5*inch, 1.0*inch]
        table = Table(data, colWidths=col_widths_master)
        table_style_cmds = get_base_table_style(header_bg_color=colors.darkslategray, grid_color=colors.black) 
        apply_zebra_striping(table_style_cmds, len(data)-1, even_row_bg_color=colors.lightgrey, odd_row_bg_color=colors.whitesmoke)
        table.setStyle(TableStyle(table_style_cmds))
        story.append(table)
    else: 
        story.append(Paragraph("No inventory items found.", styles['NoDataMessage']))
        
    doc.build(story)
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="clavis_master_inventory_{date.today()}.pdf"'
    return response

def generate_master_inventory_docx(items):
    document = Document()
    title_p = document.add_heading(f"Clavis Master Inventory Report - {date.today()}", level=0) 
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    document.add_paragraph() 

    headers = [ "SKU", "Item Name", "Category", "Location", "Initial Qty", "Available Qty", 
                "Purchase Price (BHD)", "Rent Price/Day (BHD)", "Depth", "Width", "Height", "Unit", "Supplier" ]
    
    if items: 
        table = document.add_table(rows=1, cols=len(headers))
        table.style = 'Table Grid'
        table.autofit = False 
        
        col_widths_cm_word = [2, 3.5, 2.5, 2.5, 1.5, 1.5, 2, 2, 1.2, 1.2, 1.2, 1.2, 2.5] 
        for i, width_cm in enumerate(col_widths_cm_word):
            if i < len(table.columns):
                table.columns[i].width = Inches(width_cm / 2.54) 

        hdr_cells = table.rows[0].cells
        for i, header_text in enumerate(headers): 
            cell_paragraph = hdr_cells[i].paragraphs[0]
            run = cell_paragraph.add_run(header_text)
            run.font.bold = True
            run.font.size = Pt(9)
            cell_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            hdr_cells[i].vertical_alignment = WD_ALIGN_PARAGRAPH.CENTER

        for item_obj in items: 
            row_cells = table.add_row().cells
            purch_price_str = f"{item_obj.purchase_price} BHD" if item_obj.purchase_price is not None else '-'
            rent_price_str = f"{item_obj.rent_price_per_day} BHD" if item_obj.rent_price_per_day is not None else '-'
            
            row_data_values = [
                item_obj.sku or '-', 
                item_obj.name or '-', 
                item_obj.category.name if item_obj.category else '-', 
                item_obj.storage_location or '-', 
                str(item_obj.initial_quantity), 
                str(item_obj.available_quantity), 
                purch_price_str, 
                rent_price_str, 
                str(item_obj.depth or '-'), 
                str(item_obj.width or '-'), 
                str(item_obj.height or '-'), 
                item_obj.get_dimension_unit_display(), 
                item_obj.supplier.name if item_obj.supplier else '-'
            ]
            for i, cell_text in enumerate(row_data_values):
                cell_run = row_cells[i].paragraphs[0].add_run(str(cell_text))
                row_cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
                cell_run.font.size = Pt(8)
                if headers[i] in ["Initial Qty", "Available Qty", "Depth", "Width", "Height", "Unit"]:
                     row_cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
                elif headers[i] in ["Purchase Price (BHD)", "Rent Price/Day (BHD)"]:
                     row_cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
    else: 
        document.add_paragraph("No inventory items found.")
    
    buffer = io.BytesIO()
    document.save(buffer)
    buffer.seek(0)
    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )
    response['Content-Disposition'] = f'attachment; filename="clavis_master_inventory_{date.today()}.docx"'
    return response