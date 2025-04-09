from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO


def generateCibilReportPDF(personal_info, credit_score, credit_summary, account_details, enquiries):
    """
    Generate a PDF report using Python's ReportLab

    Returns:
        BytesIO object containing the PDF data
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    # Add header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(30, 750, "CIBIL REPORT")

    # Add personal info
    c.setFont("Helvetica", 12)
    c.drawString(30, 720, f"Name: {personal_info.get('name', 'N/A')}")
    c.drawString(30, 700, f"PAN: {personal_info.get('panNumber', 'N/A')}")
    c.drawString(30, 680, f"Phone: {personal_info.get('phone', 'N/A')}")

    # Add credit score
    c.setFont("Helvetica-Bold", 14)
    c.drawString(30, 640, f"Credit Score: {credit_score}")

    # Add more content as needed

    c.save()
    buffer.seek(0)
    return buffer
