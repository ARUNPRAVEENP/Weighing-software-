import sqlite3
from typing import Optional, Dict
from resource_utils import resource_path


class PrinterViewModel:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def get_transaction_by_id(self, transaction_id: int) -> Optional[Dict]:
        query = """
        SELECT wt.*, 
           c.Name AS CustomerName, 
           mt.Name AS MaterialName
        FROM WeighingTransactions wt
        LEFT JOIN Customers c ON wt.CustomerId = c.Id
        LEFT JOIN MaterialTypes mt ON wt.MaterialTypeId = mt.Id
        WHERE wt.Id = ?
        """
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, (transaction_id,))
            row = cursor.fetchone()
            return dict(row) if row else None


    def get_last_transaction(self) -> Optional[Dict]:
        query = """
        SELECT wt.*, mt.Name AS MaterialName, c.Name AS CustomerName
        FROM WeighingTransactions wt
        LEFT JOIN MaterialTypes mt ON wt.MaterialTypeId = mt.Id
        LEFT JOIN Customers c ON wt.CustomerId = c.Id
        ORDER BY wt.CreatedAt DESC
        LIMIT 1

        """
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query)
            row = cursor.fetchone()
            return dict(row) if row else None
