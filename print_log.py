import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer, Paragraph, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
import os

# Assuming your WeighingTransactionModel is accessible
from Model.WeighingTransactionModel import WeighingTransaction

class WeighbridgeSlipGenerator:
    """
    Generates a PDF weighbridge slip with company letterhead and transaction details.
    """
    def __init__(self, company_name: str, company_address: str, company_phone: str, company_email: str, output_dir: str = "receipts"):
        self.company_name = company_name
        self.company_address = company_address
        self.company_phone = company_phone
        self.company_email = company_email
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        self.styles = getSampleStyleSheet()
        self._setup_styles()

    def _setup_styles(self):
        """Sets up custom paragraph styles for the slip."""
        self.styles.add(ParagraphStyle(name='CompanyName',
                                       fontName='Helvetica-Bold',
                                       fontSize=20,
                                       alignment=1, # TA_CENTER
                                       spaceAfter=6))
        self.styles.add(ParagraphStyle(name='CompanyAddress',
                                       fontName='Helvetica',
                                       fontSize=10,
                                       alignment=1, # TA_CENTER
                                       spaceAfter=1))
        self.styles.add(ParagraphStyle(name='SlipTitle',
                                       fontName='Helvetica-Bold',
                                       fontSize=16,
                                       alignment=1, # TA_CENTER
                                       spaceBefore=12,
                                       spaceAfter=12))
        self.styles.add(ParagraphStyle(name='FieldLabel',
                                       fontName='Helvetica-Bold',
                                       fontSize=9,
                                       alignment=0)) # TA_LEFT
        self.styles.add(ParagraphStyle(name='FieldValue',
                                       fontName='Helvetica',
                                       fontSize=9,
                                       alignment=0)) # TA_LEFT
        self.styles.add(ParagraphStyle(name='TableHeading',
                                       fontName='Helvetica-Bold',
                                       fontSize=8,
                                       alignment=1)) # TA_CENTER
        self.styles.add(ParagraphStyle(name='TableCell',
                                       fontName='Helvetica',
                                       fontSize=8,
                                       alignment=1)) # TA_CENTER
        self.styles.add(ParagraphStyle(name='FooterText',
                                       fontName='Helvetica-Oblique',
                                       fontSize=7,
                                       alignment=1,
                                       spaceBefore=20))
        self.styles.add(ParagraphStyle(name='SignatureLine',
                                       fontName='Helvetica',
                                       fontSize=9,
                                       alignment=0, # TA_LEFT
                                       spaceBefore=20,
                                       spaceAfter=5))
        self.styles.add(ParagraphStyle(name='SignatureLabel',
                                       fontName='Helvetica-Bold',
                                       fontSize=9,
                                       alignment=0)) # TA_LEFT


    def _get_header_elements(self):
        """Generates the header (letterhead) elements."""
        elements = []
        elements.append(Paragraph(self.company_name, self.styles['CompanyName']))
        elements.append(Paragraph(self.company_address, self.styles['CompanyAddress']))
        elements.append(Paragraph(f"Phone: {self.company_phone} | Email: {self.company_email}", self.styles['CompanyAddress']))
        elements.append(Spacer(1, 8*mm))
        elements.append(Paragraph("WEIGHBRIDGE SLIP", self.styles['SlipTitle']))
        elements.append(Spacer(1, 5*mm))
        return elements

    def generate_slip_pdf(self, transaction: WeighingTransaction, output_filename: str = None) -> str:
        """
        Generates a PDF weighbridge slip for a given transaction.

        Args:
            transaction: The WeighingTransaction object containing the details.
            output_filename: Optional. The name of the output PDF file. If None,
                             a default name based on GUID will be used.

        Returns:
            The absolute path to the generated PDF file.
        """
        if not isinstance(transaction, WeighingTransaction):
            raise TypeError("Expected a WeighingTransaction object.")

        if output_filename is None:
            # Ensure transaction_guid is treated as a string for slicing
            guid_prefix = str(transaction.transaction_guid)[:8] if transaction.transaction_guid else "N/A"
            output_filename = f"weighbridge_slip_{guid_prefix}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        
        pdf_path = os.path.join(self.output_dir, output_filename)
        doc = SimpleDocTemplate(pdf_path, pagesize=A4,
                                rightMargin=15*mm, leftMargin=15*mm,
                                topMargin=15*mm, bottomMargin=15*mm)
        
        story = []
        story.extend(self._get_header_elements())

        # Transaction Details Table
        # Explicitly convert all potentially non-string values to string before Paragraph
        data = [
            [Paragraph("Slip No:", self.styles['FieldLabel']), Paragraph(str(transaction.id), self.styles['FieldValue']),
             Paragraph("Date:", self.styles['FieldLabel']), Paragraph(datetime.datetime.now().strftime('%Y-%m-%d'), self.styles['FieldValue'])],
            
            [Paragraph("Vehicle No:", self.styles['FieldLabel']), Paragraph(str(transaction.vehicle_number), self.styles['FieldValue']),
             Paragraph("Time:", self.styles['FieldLabel']), Paragraph(datetime.datetime.now().strftime('%H:%M:%S'), self.styles['FieldValue'])],

            # Removed Status and Operator fields from here
            [Paragraph("Vehicle Type:", self.styles['FieldLabel']), Paragraph(str(transaction.vehicle_type_id) if transaction.vehicle_type_id else '-', self.styles['FieldValue']),
             Paragraph("Customer Name:", self.styles['FieldLabel']), Paragraph(str(transaction.customer_id) if transaction.customer_id else '-', self.styles['FieldValue'])],
            
            [Paragraph("Material Type:", self.styles['FieldLabel']), Paragraph(str(transaction.material_type_id) if transaction.material_type_id else '-', self.styles['FieldValue']),
             Paragraph("Remarks:", self.styles['FieldLabel']), Paragraph(str(transaction.remarks) if transaction.remarks else '-', self.styles['FieldValue'])]
        ]

        # Dynamic weight rows
        if transaction.first_weight is not None:
            data.append([
                Paragraph("First Weight (Tare):", self.styles['FieldLabel']),
                Paragraph(f"{transaction.first_weight:.2f} kg", self.styles['FieldValue']),
                Paragraph("Timestamp:", self.styles['FieldLabel']),
                Paragraph(transaction.first_weight_timestamp.strftime('%Y-%m-%d %H:%M:%S') if transaction.first_weight_timestamp else '-', self.styles['FieldValue'])
            ])
        
        if transaction.second_weight is not None:
            data.append([
                Paragraph("Second Weight (Gross):", self.styles['FieldLabel']),
                Paragraph(f"{transaction.second_weight:.2f} kg", self.styles['FieldValue']),
                Paragraph("Timestamp:", self.styles['FieldLabel']),
                Paragraph(transaction.second_weight_timestamp.strftime('%Y-%m-%d %H:%M:%S') if transaction.second_weight_timestamp else '-', self.styles['FieldValue'])
            ])

        if transaction.net_weight is not None:
            data.append([
                Paragraph("Net Weight:", self.styles['FieldLabel']),
                Paragraph(f"{transaction.net_weight:.2f} kg", self.styles['FieldValue']),
                Paragraph("Charges:", self.styles['FieldLabel']),
                Paragraph(f"₹ {transaction.charges:.2f}" if transaction.charges is not None else '-', self.styles['FieldValue'])
            ])


        table = Table(data, colWidths=[30*mm, 60*mm, 30*mm, 60*mm])
        table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            # Add borders for visual separation
            ('GRID', (0,0), (-1,-1), 0.25, colors.lightgrey),
            ('BOX', (0,0), (-1,-1), 0.5, colors.black),
        ]))
        story.append(table)
        story.append(Spacer(1, 15*mm))

        # Add Operator Signature section
        story.append(Spacer(1, 20*mm)) # More space before signature
        story.append(Paragraph("---------------------------------", self.styles['SignatureLine']))
        story.append(Paragraph("Operator Signature", self.styles['SignatureLabel']))
        story.append(Spacer(1, 10*mm)) # Space after signature line

        # Footer
        story.append(Paragraph("Thank you for your business!", self.styles['FooterText']))
        story.append(Paragraph(f"Generated on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", self.styles['FooterText']))

        try:
            doc.build(story)
            print(f"PDF slip generated at: {pdf_path}")
            return pdf_path
        except Exception as e:
            print(f"Error generating PDF: {e}")
            raise

# Example Usage (for testing purposes, not part of the main app flow)
if __name__ == "__main__":
    # Create a dummy transaction model for testing
    from Model.WeighingTransactionModel import WeighingTransaction # Ensure model is importable

    # Dummy data for demonstration
    dummy_transaction = WeighingTransaction(
        id=123,
        transaction_guid="a1b2c3d4-e5f6-7890-1234-567890abcdef",
        vehicle_number="TN37AB1234",
        vehicle_type_id="Heavy Truck", # Changed to string for testing
        material_type_id="Sand", # Changed to string for testing
        customer_id="ABC Corp", # Changed to string for testing
        first_weight=15000.50,
        first_weight_timestamp=datetime.datetime(2025, 7, 11, 10, 30, 0),
        second_weight=35000.75,
        second_weight_timestamp=datetime.datetime(2025, 7, 11, 11, 0, 0),
        net_weight=20000.25,
        status="Completed",
        operator_id="Admin", # Changed to string for testing
        remarks="Delivered to site A",
        charges=1200.50,
        created_at=datetime.datetime(2025, 7, 11, 10, 0, 0),
        last_updated_at=datetime.datetime(2025, 7, 11, 11, 0, 0)
    )

    # Example Company Details
    company_details = {
        "name": "WEIGHMAX SOLUTIONS PVT. LTD.",
        "address": "123, Industrial Area, Coimbatore - 641001, Tamil Nadu",
        "phone": "+91 98765 43210",
        "email": "info@weighmax.com"
    }

    # Initialize the generator
    slip_generator = WeighbridgeSlipGenerator(
        company_name=company_details["name"],
        company_address=company_details["address"],
        company_phone=company_details["phone"],
        company_email=company_details["email"]
    )

    # Generate the slip
    try:
        generated_pdf_path = slip_generator.generate_slip_pdf(dummy_transaction)
        print(f"Successfully generated slip: {generated_pdf_path}")
        # You can open the PDF automatically for testing if needed
        # import subprocess
        # subprocess.Popen([generated_pdf_path], shell=True)
    except Exception as e:
        print(f"Failed to generate slip: {e}")
