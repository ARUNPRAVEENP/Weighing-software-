import json
import logging
import tempfile
import subprocess
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from num2words import num2words
from viewmodels.printerviewmodel import PrinterViewModel
from resource_utils import resource_path


def load_config():
    config_path = resource_path("config.json")
    if not os.path.exists(config_path):
        raise FileNotFoundError("❌ Missing config.json file.")
    with open(config_path, "r") as f:
        config = json.load(f)

    config["database_path"] = resource_path(config.get("database_path", "weighbridge.db"))
    config["sumatra_path"] = resource_path(config.get("sumatra_path", "SumatraPDFcopy/SumatraPDF.exe"))
    return config

class ReceiptPrinter:
    def __init__(self):
        config = load_config()
        self.db_path = config["database_path"]
        self.sumatra_path = config["sumatra_path"]
        self.viewmodel = PrinterViewModel(self.db_path)

        logging.basicConfig(
            filename="print_log.txt",
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )

    def generate_receipt_pdf(self, transaction: dict) -> str:
        page_width, page_height = A4
        half_height = page_height / 2
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        c = canvas.Canvas(temp_file.name, pagesize=A4)

        def draw_receipt(y_offset: float):
            left_x = 60
            label_font = "Helvetica"
            label_size = 10
            line_y = y_offset + 260

            c.setFont("Helvetica-Bold", 14)
            c.drawCentredString(page_width / 2, line_y, "AGM BLUE METALS")
            c.setFont(label_font, label_size)
            for text in [
                "GST NO: 33AARFA8461G1Z9",
                "144/1-C, Karanampettai,",
                "COIMBATORE, TAMILNADU, 641401."
            ]:
                line_y -= 15
                c.drawCentredString(page_width / 2, line_y, text)

            line_y -= 30
            c.drawString(left_x, line_y, f"SL NO       : {transaction['Id']}")
            c.drawString(left_x, line_y - 15, f"MATERIAL    : {transaction.get('MaterialName', '-')}")
            c.drawRightString(page_width - 60, line_y, f"VEHICLE NO : {transaction['VehicleNumber']}")
            c.drawRightString(page_width - 60, line_y - 15, f"CUSTOMER     : {transaction.get('CustomerName', '-')}")

            line_y -= 30
            c.line(left_x, line_y, page_width - 60, line_y)

            line_y -= 20
            c.drawString(left_x, line_y, f"GROSS WEIGHT : {transaction['FirstWeight']} Tons")
            c.drawString(left_x, line_y - 15, f"TARE WEIGHT  : {transaction['SecondWeight']} Tons")
            c.drawString(left_x, line_y - 30, f"NET WEIGHT   : {transaction['NetWeight']} Tons")

            c.drawRightString(page_width - 60, line_y, f"DATE TIME (Gross): {transaction['FirstWeightTimestamp']}")
            c.drawRightString(page_width - 60, line_y - 15, f"DATE TIME (Tare) : {transaction['SecondWeightTimestamp']}")
            charges = transaction.get("Charges")
            charges_str = f"{charges:.2f}" if charges is not None else "0.00"
            c.drawRightString(page_width - 60, line_y - 30, f"CHARGES         : Rs. {charges_str}")

            line_y -= 50
            c.line(left_x, line_y, page_width - 60, line_y)
            net_words = num2words(int(transaction["NetWeight"] or 0)).upper()
            c.drawString(left_x, line_y - 20, f"NET WT (in words): {net_words} TONS")
            c.drawString(left_x, line_y - 50, "OPERATOR SIGNATURE ___________________________")

        draw_receipt(half_height)
        draw_receipt(0)
        c.showPage()
        c.save()
        return temp_file.name

    def print_last_transaction(self):
        transaction = self.viewmodel.get_last_transaction()
        if not transaction:
            logging.warning("❌ No transaction found for printing.")
            print("❌ No transaction found.")
            return

        try:
            pdf_path = self.generate_receipt_pdf(transaction)
            print(f"📄 PDF saved at: {pdf_path}")
            if not os.path.exists(self.sumatra_path):
                raise FileNotFoundError("❌ SumatraPDF executable not found.")

            command = [self.sumatra_path, "-print-to-default", "-silent", pdf_path]
            exit_code = subprocess.call(command)

            if exit_code == 0:
                logging.info(f"🖨️ Successfully printed transaction ID {transaction['Id']}")
                print("✅ Print successful.")
            else:
                logging.error(f"⚠️ Print failed with exit code {exit_code}")
                print(f"❌ Print command failed (exit code {exit_code}).")

        except Exception as e:
            logging.exception(f"❌ Exception during printing: {e}")
            print(f"❌ Exception occurred: {e}")

        finally:
            if os.path.exists(pdf_path):
                try:
                    os.remove(pdf_path)
                    print("🧹 Temporary PDF cleaned up.")
                except Exception as cleanup_error:
                    logging.warning(f"Could not delete temp file: {cleanup_error}")