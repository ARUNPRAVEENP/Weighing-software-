import sqlite3
import datetime
import uuid # Import uuid for TransactionGuid

from Model.WeighingTransactionModel import WeighingTransaction
from resource_utils import resource_path



class WeighingTransactionRepository:
    def __init__(self, db_path="weighbridge.db"):
        
        actual_path = resource_path(db_path)
        self.conn = sqlite3.connect(actual_path)
        # Enable row_factory to access columns by name
        self.conn.row_factory = sqlite3.Row
        self._create_table()

    def _create_table(self):
        """Creates the WeighingTransactions table if it doesn't exist, matching the new schema."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS WeighingTransactions (
                Id INTEGER PRIMARY KEY AUTOINCREMENT,
                TransactionGuid TEXT NOT NULL UNIQUE,
                VehicleNumber TEXT NOT NULL,
                VehicleTypeId INTEGER,
                MaterialTypeId INTEGER,
                CustomerId INTEGER,
                FirstWeight REAL,
                FirstWeightTimestamp DATETIME,
                SecondWeight REAL,
                SecondWeightTimestamp DATETIME,
                NetWeight REAL,
                Status TEXT NOT NULL, -- 'Pending', 'Completed', 'Canceled'
                OperatorId INTEGER,
                Remarks TEXT,
                Charges REAL, -- Added charges field
                CreatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                LastUpdatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (VehicleTypeId) REFERENCES VehicleTypes(Id),
                FOREIGN KEY (MaterialTypeId) REFERENCES MaterialTypes(Id),
                FOREIGN KEY (CustomerId) REFERENCES Customers(Id)
                -- FOREIGN KEY (OperatorId) REFERENCES Users(Id) -- Re-add if Users table exists and has an Id column
            )
        """)
        self.conn.commit()
        print("[DEBUG] WeighingTransactionRepository: WeighingTransactions table ensured/created with new schema.")

    def _row_to_model(self, row):
        """Converts a database row to a WeighingTransaction model object."""
        if row is None:
            return None
        
        # Helper to parse datetime strings from DB
        def parse_db_datetime(dt_str):
            # Handle cases where datetime string might be empty or invalid
            if dt_str:
                try:
                    return datetime.datetime.fromisoformat(dt_str)
                except ValueError:
                    return None # Or raise an error, depending on desired strictness
            return None

        return WeighingTransaction(
            id=row["Id"],
            transaction_guid=row["TransactionGuid"],
            vehicle_number=row["VehicleNumber"],
            vehicle_type_id=row["VehicleTypeId"],
            material_type_id=row["MaterialTypeId"],
            customer_id=row["CustomerId"],
            first_weight=row["FirstWeight"],
            first_weight_timestamp=parse_db_datetime(row["FirstWeightTimestamp"]),
            second_weight=row["SecondWeight"],
            second_weight_timestamp=parse_db_datetime(row["SecondWeightTimestamp"]),
            net_weight=row["NetWeight"],
            status=row["Status"],
            operator_id=row["OperatorId"],
            remarks=row["Remarks"],
            charges=row["Charges"], # Include charges
            created_at=parse_db_datetime(row["CreatedAt"]),
            last_updated_at=parse_db_datetime(row["LastUpdatedAt"])
        )

    def add(self, transaction: WeighingTransaction): # Renamed from add_transaction
        """Adds a new weighing transaction to the database."""
        if not isinstance(transaction, WeighingTransaction):
            raise TypeError("Expected a WeighingTransaction object.")

        cursor = self.conn.cursor()
        current_time = datetime.datetime.now().isoformat()
        
        # Ensure TransactionGuid is set
        if not transaction.transaction_guid:
            transaction.transaction_guid = str(uuid.uuid4())

        cursor.execute("""
            INSERT INTO WeighingTransactions (
                TransactionGuid, VehicleNumber, VehicleTypeId, MaterialTypeId, CustomerId,
                FirstWeight, FirstWeightTimestamp, SecondWeight, SecondWeightTimestamp,
                NetWeight, Status, OperatorId, Remarks, Charges, CreatedAt, LastUpdatedAt
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            transaction.transaction_guid,
            transaction.vehicle_number,
            transaction.vehicle_type_id,
            transaction.material_type_id,
            transaction.customer_id,
            transaction.first_weight,
            transaction.first_weight_timestamp.isoformat() if transaction.first_weight_timestamp else None,
            transaction.second_weight,
            transaction.second_weight_timestamp.isoformat() if transaction.second_weight_timestamp else None,
            transaction.net_weight,
            transaction.status,
            transaction.operator_id,
            transaction.remarks,
            transaction.charges, # Include charges
            current_time,
            current_time
        ))
        self.conn.commit()
        transaction.id = cursor.lastrowid
        transaction.created_at = datetime.datetime.fromisoformat(current_time)
        transaction.last_updated_at = datetime.datetime.fromisoformat(current_time)
        print(f"[DEBUG] WeighingTransactionRepository: Added new transaction with ID: {transaction.id}, GUID: {transaction.transaction_guid}")
        return transaction

    def update(self, transaction: WeighingTransaction): # Renamed from update_transaction
        """Updates an existing weighing transaction in the database."""
        if not isinstance(transaction, WeighingTransaction) or transaction.id is None:
            raise ValueError("Invalid WeighingTransaction object for update.")

        current_time = datetime.datetime.now().isoformat()
        self.conn.execute("""
            UPDATE WeighingTransactions SET
                VehicleNumber = ?, VehicleTypeId = ?, MaterialTypeId = ?, CustomerId = ?,
                FirstWeight = ?, FirstWeightTimestamp = ?, SecondWeight = ?, SecondWeightTimestamp = ?,
                NetWeight = ?, Status = ?, OperatorId = ?, Remarks = ?, Charges = ?, LastUpdatedAt = ?
            WHERE Id = ?
        """, (
            transaction.vehicle_number,
            transaction.vehicle_type_id,
            transaction.material_type_id,
            transaction.customer_id,
            transaction.first_weight,
            transaction.first_weight_timestamp.isoformat() if transaction.first_weight_timestamp else None,
            transaction.second_weight,
            transaction.second_weight_timestamp.isoformat() if transaction.second_weight_timestamp else None,
            transaction.net_weight,
            transaction.status,
            transaction.operator_id,
            transaction.remarks,
            transaction.charges, # Include charges
            current_time,
            transaction.id
        ))
        self.conn.commit()
        transaction.last_updated_at = datetime.datetime.fromisoformat(current_time)
        print(f"[DEBUG] WeighingTransactionRepository: Updated transaction with ID: {transaction.id}")

    def get_by_id(self, transaction_id): # Renamed from get_transaction_by_id
        """Retrieves a single transaction by its ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM WeighingTransactions WHERE Id = ?", (transaction_id,))
        row = cursor.fetchone()
        return self._row_to_model(row)

    def get_all(self): # Renamed from get_all_weighing_transactions
        """Retrieves all weighing transactions."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM WeighingTransactions ORDER BY CreatedAt DESC")
        rows = cursor.fetchall()
        return [self._row_to_model(row) for row in rows]

    def get_last_transaction_by_vehicle_number(self, vehicle_number):
        """Retrieves the very last transaction (any status) for a given vehicle number."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM WeighingTransactions
            WHERE VehicleNumber = ?
            ORDER BY CreatedAt DESC
            LIMIT 1
        """, (vehicle_number,))
        row = cursor.fetchone()
        return self._row_to_model(row)

    # Removed the get_pending_transaction_by_vehicle method as it's no longer
    # needed with the flexible weighing flow and the use of get_all_pending_by_vehicle_number
    # in the ViewModel.

    def get_all_pending_by_vehicle_number(self, vehicle_number): # Added this method
        """Retrieves all pending transactions for a given vehicle number."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM WeighingTransactions
            WHERE VehicleNumber = ? AND Status = 'Pending'
            ORDER BY CreatedAt DESC
        """, (vehicle_number,))
        rows = cursor.fetchall()
        return [self._row_to_model(row) for row in rows]

    def get_latest_completed_transaction(self, vehicle_number):
        """Retrieves the latest completed transaction for a given vehicle number."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM WeighingTransactions
            WHERE VehicleNumber = ? AND Status = 'Completed'
            ORDER BY CreatedAt DESC
            LIMIT 1
        """, (vehicle_number,))
        row = cursor.fetchone()
        return self._row_to_model(row)

    def get_max_transaction_id(self):
        """Retrieves the maximum transaction ID from the database."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT MAX(Id) FROM WeighingTransactions")
        max_id = cursor.fetchone()[0]
        return max_id if max_id is not None else 0 # Return 0 if no records exist

    def delete_transaction(self, transaction_id): # Renamed from delete
        """Deletes a transaction by ID."""
        self.conn.execute("DELETE FROM WeighingTransactions WHERE Id = ?", (transaction_id,))
        self.conn.commit()
        print(f"[DEBUG] WeighingTransactionRepository: Deleted transaction with ID: {transaction_id}")

    def delete_by_guid(self, transaction_guid): # Added this method
        """Deletes a transaction by its GUID."""
        self.conn.execute("DELETE FROM WeighingTransactions WHERE TransactionGuid = ?", (transaction_guid,))
        self.conn.commit()
        print(f"[DEBUG] WeighingTransactionRepository: Deleted transaction with GUID: {transaction_guid}")
    
    def get_by_guid(self, transaction_guid):
        """Fetch a transaction by its GUID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM WeighingTransactions WHERE TransactionGuid = ?", (transaction_guid,))
        row = cursor.fetchone()
        return self._row_to_model(row) if row else None