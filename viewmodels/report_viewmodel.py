from Model.report_model import ReportRepository
# REMOVED: No longer needed, as ReportRepository now handles VehicleTypeName via join
# from repositories.vehicle_repository import VehicleRepository 

class ReportViewModel:
    def __init__(self):
        self.repo = ReportRepository()
        self.daily_summary_data = []
        self.available_dates = []
        self.transactions_for_date = []
        self.filtered_transactions = []
        
    def load_daily_summary(self):
        rows = self.repo.fetch_daily_summary()
        self.daily_summary_data = [dict(row) for row in rows]

    def load_available_dates(self):
        # Ensure "All Dates" is always the first option
        self.available_dates = ["All Dates"] + self.repo.fetch_available_dates() 

    def load_transactions_by_date(self, selected_date):
        rows = self.repo.fetch_transactions_by_date(selected_date)
        self.transactions_for_date = [dict(row) for row in rows]

    def search_transactions(self, column, keyword):
        rows = self.repo.search_transactions(column, keyword)
        self.filtered_transactions = [dict(row) for row in rows]

    def load_all_transactions(self):
        rows = self.repo.fetch_all_transactions()
        self.filtered_transactions = [dict(row) for row in rows]

    def load_raw_transactions(self):
        rows = self.repo.fetch_raw_transactions()
        self.filtered_transactions = [dict(row) for row in rows]
    
    def load_combined_filtered_transactions(self, column=None, keyword=None, date=None):
        rows = self.repo.fetch_combined_filtered_transactions(column, keyword, date)
        self.filtered_transactions = [dict(row) for row in rows]

