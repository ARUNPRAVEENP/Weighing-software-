import os
import json
import subprocess
from viewmodels.pri import ReceiptPrinter

def load_config():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, "config.json")
    with open(config_path, "r") as f:
        config = json.load(f)
    # Resolve relative paths
    config["database_path"] = os.path.join(base_dir, config.get("database_path", "weighbridge.db"))
    config["sumatra_path"] = os.path.join(base_dir, config.get("sumatra_path", "SumatraPDF/SumatraPDF.exe"))
    return config

def main():
    config = load_config()
    printer = ReceiptPrinter()  # now uses config internally — no args needed

    transaction_id = 7  # 👈 Change this to target a specific transaction

    transaction = printer.viewmodel.get_transaction_by_id(transaction_id)
    if transaction:
        pdf_path = printer.generate_receipt_pdf(transaction)
        print(f"📄 PDF saved at: {pdf_path}")
        command = [printer.sumatra_path, "-print-to-default", "-silent", pdf_path]
        exit_code = subprocess.call(command)

        if exit_code == 0:
            print(f"✅ Successfully printed transaction ID {transaction_id}")
        else:
            print(f"❌ Print failed with exit code {exit_code}")
    else:
        print(f"❌ No transaction found for ID {transaction_id}")

if __name__ == "__main__":
    main()
