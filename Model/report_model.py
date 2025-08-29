import sqlite3
from resource_utils import resource_path

class ReportRepository:
    def __init__(self, db_path="weighbridge.db"):
        self.db_path = resource_path(db_path)
        print(f"DEBUG: ReportRepository initialized. Using DB at: {self.db_path}")

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def fetch_daily_summary(self):
        query = '''
            SELECT DATE(FirstWeightTimestamp) AS TransactionDate,
                   COUNT(*) AS TotalTransactions,
                   SUM(NetWeight) AS TotalNetWeight,
                   SUM(Charges) AS TotalCharges
            FROM WeighingTransactions
            GROUP BY DATE(FirstWeightTimestamp)
            ORDER BY TransactionDate DESC;
        '''
        with self._connect() as conn:
            return conn.execute(query).fetchall()

    def fetch_available_dates(self):
        # --- START MODIFICATION ---
        query = '''
            SELECT DISTINCT DATE(FirstWeightTimestamp) AS TransactionDate
            FROM WeighingTransactions
            WHERE FirstWeightTimestamp IS NOT NULL -- ADDED: Exclude NULL timestamps
            ORDER BY TransactionDate DESC;
        '''
        # --- END MODIFICATION ---
        with self._connect() as conn:
            return [row["TransactionDate"] for row in conn.execute(query)]

    def fetch_transactions_by_date(self, date):
        query = '''
            SELECT WT.VehicleNumber, NetWeight, Charges, Status,
                   VT.Name AS VehicleTypeName,
                   U.Username AS OperatorName
            FROM WeighingTransactions WT
            LEFT JOIN VehicleTypes VT ON WT.VehicleTypeId = VT.Id
            LEFT JOIN Users U ON WT.OperatorId = U.Id
            WHERE DATE(FirstWeightTimestamp) = ?
            ORDER BY FirstWeightTimestamp;
        '''
        with self._connect() as conn:
            return conn.execute(query, (date,)).fetchall()

    def search_transactions(self, column, keyword):
        allowed_columns = {
            "VehicleNumber": "WT.VehicleNumber",
            "CustomerName": "C.Name",
            "MaterialName": "MT.name",
            "Status": "WT.Status",
            "VehicleTypeName": "VT.Name",
            "OperatorName": "U.Username"
        }

        if column not in allowed_columns:
            raise ValueError(f"Invalid column selected for search: {column}. Allowed are {list(allowed_columns.keys())}")

        safe_column = allowed_columns[column]
        
        base_query = '''
            SELECT WT.Id, WT.TransactionGuid, WT.VehicleNumber,
                   VT.Name AS VehicleTypeName,
                   MT.name AS MaterialName, C.Name AS CustomerName,
                   WT.FirstWeight, WT.FirstWeightTimestamp, WT.SecondWeight,
                   WT.SecondWeightTimestamp, WT.NetWeight, WT.Charges,
                   WT.Status, U.Username AS OperatorName, WT.Remarks,
                   WT.CreatedAt, WT.LastUpdatedAt
            FROM WeighingTransactions WT
            LEFT JOIN MaterialTypes MT ON WT.MaterialTypeId = MT.Id
            LEFT JOIN Customers C ON WT.CustomerId = C.Id
            LEFT JOIN Users U ON WT.OperatorId = U.Id
            LEFT JOIN VehicleTypes VT ON WT.VehicleTypeId = VT.Id
        '''
        
        query = f"{base_query} WHERE {safe_column} LIKE ? ORDER BY WT.FirstWeightTimestamp DESC;"

        with self._connect() as conn:
            return conn.execute(query, (f"%{keyword}%",)).fetchall()

    def fetch_all_transactions(self):
        query = '''
            SELECT WT.Id,
                   WT.TransactionGuid,
                   WT.VehicleNumber,
                   VT.Name AS VehicleTypeName,
                   MT.name AS MaterialName,
                   C.Name AS CustomerName,
                   WT.FirstWeight,
                   WT.FirstWeightTimestamp,
                   WT.SecondWeight,
                   WT.SecondWeightTimestamp,
                   WT.NetWeight,
                   WT.Charges,
                   WT.Status,
                   U.Username AS OperatorName,
                   WT.Remarks,
                   WT.CreatedAt,
                   WT.LastUpdatedAt
            FROM WeighingTransactions WT
            LEFT JOIN MaterialTypes MT ON WT.MaterialTypeId = MT.Id
            LEFT JOIN Customers C ON WT.CustomerId = C.Id
            LEFT JOIN Users U ON WT.OperatorId = U.Id
            LEFT JOIN VehicleTypes VT ON WT.VehicleTypeId = VT.Id
            ORDER BY WT.FirstWeightTimestamp DESC;
        '''
        with self._connect() as conn:
            return conn.execute(query).fetchall()

    def fetch_raw_transactions(self):
        with self._connect() as conn:
            query = "SELECT * FROM WeighingTransactions ORDER BY FirstWeightTimestamp DESC"
            return conn.execute(query).fetchall()

    def fetch_combined_filtered_transactions(self, column=None, keyword=None, date=None):
        """
        Fetches transactions applying both text search and date filter.
        """
        base_query = '''
            SELECT WT.Id, WT.TransactionGuid, WT.VehicleNumber,
                   VT.Name AS VehicleTypeName,
                   MT.name AS MaterialName, C.Name AS CustomerName,
                   WT.FirstWeight, WT.FirstWeightTimestamp, WT.SecondWeight,
                   WT.SecondWeightTimestamp, WT.NetWeight, WT.Charges,
                   WT.Status, U.Username AS OperatorName, WT.Remarks,
                   WT.CreatedAt, WT.LastUpdatedAt
            FROM WeighingTransactions WT
            LEFT JOIN MaterialTypes MT ON WT.MaterialTypeId = MT.Id
            LEFT JOIN Customers C ON WT.CustomerId = C.Id
            LEFT JOIN Users U ON WT.OperatorId = U.Id
            LEFT JOIN VehicleTypes VT ON WT.VehicleTypeId = VT.Id
        '''
        conditions = []
        params = []
        
        allowed_search_columns = {
            "VehicleNumber": "WT.VehicleNumber",
            "CustomerName": "C.Name",
            "MaterialName": "MT.name",
            "Status": "WT.Status",
            "VehicleTypeName": "VT.Name",
            "OperatorName": "U.Username"
        }

        if keyword and column:
            if column not in allowed_search_columns:
                raise ValueError(f"Invalid column selected for search: {column}.")
            
            conditions.append(f"{allowed_search_columns[column]} LIKE ?")
            params.append(f"%{keyword}%")

        if date and date != "All Dates":
            conditions.append("DATE(FirstWeightTimestamp) = ?")
            params.append(date)

        if conditions:
            query = f"{base_query} WHERE {' AND '.join(conditions)} ORDER BY WT.FirstWeightTimestamp DESC;"
        else:
            query = f"{base_query} ORDER BY WT.FirstWeightTimestamp DESC;"
            
        with self._connect() as conn:
            return conn.execute(query, params).fetchall()

