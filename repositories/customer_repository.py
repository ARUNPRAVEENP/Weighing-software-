import sqlite3
from Model.customer_model import Customer
from resource_utils import resource_path


class CustomerRepository:
    def __init__(self, db_path="weighbridge.db", auto_init=True):
        self.db_path = resource_path(db_path)
        if auto_init:
            self._create_table()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _create_table(self):
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS Customers (
                    Id INTEGER PRIMARY KEY AUTOINCREMENT,
                    Name TEXT NOT NULL,
                    Address TEXT,
                    City TEXT,
                    Pincode TEXT,
                    ContactNumber TEXT,
                    Email TEXT,
                    GSTId TEXT
                )
            """)
            conn.commit()

    def add(self, name, address=None, city=None, pincode=None,
            contact_number=None, email=None, gst_id=None):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO Customers (Name, Address, City, Pincode, ContactNumber, Email, GSTId)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (name, address, city, pincode, contact_number, email, gst_id))
            conn.commit()
            return cur.lastrowid

    def update(self, customer_id, name, address=None, city=None, pincode=None,
               contact_number=None, email=None, gst_id=None):
        with self._connect() as conn:
            conn.execute("""
                UPDATE Customers
                SET Name = ?, Address = ?, City = ?, Pincode = ?, ContactNumber = ?, Email = ?, GSTId = ?
                WHERE Id = ?
            """, (name, address, city, pincode, contact_number, email, gst_id, customer_id))
            conn.commit()

    def delete(self, customer_id):
        with self._connect() as conn:
            conn.execute("DELETE FROM Customers WHERE Id = ?", (customer_id,))
            conn.commit()

    def get_all(self):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM Customers")
            rows = cur.fetchall()
            return [Customer(
                id=row["Id"],
                name=row["Name"],
                address=row["Address"],
                city=row["City"],
                pincode=row["Pincode"],
                contact_number=row["ContactNumber"],
                email=row["Email"],
                gst_id=row["GSTId"]
            ) for row in rows]

    def get_by_id(self, customer_id):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM Customers WHERE Id = ?", (customer_id,))
            row = cur.fetchone()
            return Customer(
                id=row["Id"],
                name=row["Name"],
                address=row["Address"],
                city=row["City"],
                pincode=row["Pincode"],
                contact_number=row["ContactNumber"],
                email=row["Email"],
                gst_id=row["GSTId"]
            ) if row else None