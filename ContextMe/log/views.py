from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
import json
from login.models import User
from log.models import ActivityLog
import csv
from datetime import datetime
from io import BytesIO, StringIO
from django.http import HttpResponse
from django.db.models import Q
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

def activity_log_list(request):
    # Step 1: Get Supabase session data
    supabase_user_raw = request.session.get('supabase_user')
    if not supabase_user_raw:
        return redirect('login')

    # Step 2: Parse session JSON if needed
    if isinstance(supabase_user_raw, str):
        try:
            supabase_user_data = json.loads(supabase_user_raw)
        except json.JSONDecodeError:
            return redirect('login')
    elif isinstance(supabase_user_raw, dict):
        supabase_user_data = supabase_user_raw
    else:
        return redirect('login')

    # Step 3: Extract email
    email = supabase_user_data.get('email')
    if not email:
        return redirect('login')

    # Step 4: Get matching user
    user = get_object_or_404(User, email=email)

    # Step 5: Fetch logs for that user
    logs_qs = ActivityLog.objects.filter(user=user).order_by('-created_at')

    # Step 6: Paginate results
    paginator = Paginator(logs_qs, 10)  # 10 logs per page
    page_number = request.GET.get('page')
    logs = paginator.get_page(page_number)

    # Step 7: Render template
    return render(request, 'activity_log_list.html', {'logs': logs})

def download_activity_log_txt(request):
    """
    Download activity logs as TXT file
    """
    # Get filtered queryset
    logs = get_filtered_logs(request)
    
    # Create the HttpResponse object with the appropriate TXT header
    response = HttpResponse(content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="activity_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt"'
    
    # Create content
    content = StringIO()
    
    # Write header
    content.write("ACTIVITY LOG REPORT\n")
    content.write("=" * 50 + "\n")
    content.write(f"Generated on: {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}\n")
    content.write(f"Total entries: {logs.count()}\n\n")
    
    # Apply filters info
    action_filter = request.GET.get('action')
    persona_filter = request.GET.get('persona')
    
    if action_filter or persona_filter:
        content.write("APPLIED FILTERS:\n")
        content.write("-" * 20 + "\n")
        if action_filter:
            content.write(f"Action: {action_filter}\n")
        if persona_filter:
            content.write(f"Persona: {persona_filter}\n")
        content.write("\n")
    
    # Write data
    content.write("ACTIVITY ENTRIES:\n")
    content.write("-" * 20 + "\n\n")
    
    for i, log in enumerate(logs, 1):
        content.write(f"Entry #{i}\n")
        content.write(f"Action: {log.action_type}\n")
        content.write(f"Description: {log.description or 'N/A'}\n")
        content.write(f"Persona: {log.persona.persona_name if log.persona else 'N/A'}\n")
        content.write(f"IP Address: {log.ip_address or 'N/A'}\n")
        content.write(f"Date & Time: {log.created_at.strftime('%B %d, %Y at %H:%M:%S')}\n")
        content.write("-" * 40 + "\n\n")
    
    response.write(content.getvalue())
    content.close()
    
    return response

def download_activity_log_pdf(request):
    """
    Download activity logs as PDF file
    """
    # Get filtered queryset
    logs = get_filtered_logs(request)
    
    # Create the HttpResponse object with the appropriate PDF header
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="activity_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
    
    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*inch)
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        textColor=colors.darkblue
    )
    
    # Build PDF content
    elements = []
    
    # Title
    elements.append(Paragraph("Activity Log Report", title_style))
    elements.append(Spacer(1, 12))
    
    # Header info
    header_info = [
        f"Generated on: {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}",
        f"Total entries: {logs.count()}"
    ]
    
    # Add filter info
    action_filter = request.GET.get('action')
    persona_filter = request.GET.get('persona')
    
    if action_filter or persona_filter:
        header_info.append("Applied Filters:")
        if action_filter:
            header_info.append(f"  • Action: {action_filter}")
        if persona_filter:
            header_info.append(f"  • Persona: {persona_filter}")
    
    for info in header_info:
        elements.append(Paragraph(info, styles['Normal']))
    
    elements.append(Spacer(1, 20))
    
    # Create table data
    table_data = [
        ['Action', 'Description', 'Persona', 'IP Address', 'Date & Time']
    ]
    
    for log in logs:
        table_data.append([
            log.action_type,
            log.description or 'N/A',
            log.persona.persona_name if log.persona else 'N/A',
            log.ip_address or 'N/A',
            log.created_at.strftime('%m/%d/%Y %H:%M')
        ])
    
    # Create table
    table = Table(table_data, colWidths=[1*inch, 2*inch, 1.5*inch, 1.2*inch, 1.3*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
    ]))
    
    elements.append(table)
    
    # Build PDF
    doc.build(elements)
    
    # Get the value of the BytesIO buffer and write it to the response
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    
    return response

def get_filtered_logs(request):
    """
    Helper function to get filtered logs based on request parameters
    """
    logs = ActivityLog.objects.select_related('persona').order_by('-created_at')
    
    action_filter = request.GET.get('action')
    persona_filter = request.GET.get('persona')
    
    if action_filter:
        logs = logs.filter(action_type=action_filter)
    
    if persona_filter:
        logs = logs.filter(persona__persona_name=persona_filter)
    
    return logs
