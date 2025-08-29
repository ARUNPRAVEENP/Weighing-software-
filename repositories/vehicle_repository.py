import sqlite3
from Model.vehicle_type_model import VehicleType
from resource_utils import resource_path


class VehicleRepository:
    def __init__(self, db_path="weighbridge.db", auto_init=True): # Changed db_path here
        self.db_path = resource_path(db_path)
        if auto_init:
            self._ensure_table()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_table(self):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS VehicleTypes (
                    Id INTEGER PRIMARY KEY AUTOINCREMENT,
                    Name TEXT NOT NULL UNIQUE,
                    DefaultTareWeight REAL,
                    MaxWeightCapacity REAL
                )
            """)
            conn.commit()

    def get_all(self):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM VehicleTypes")
            rows = cur.fetchall()
            return [
                VehicleType(
                    id=row["Id"],
                    name=row["Name"],
                    default_tare_weight=row["DefaultTareWeight"], # Updated column name
                    max_weight_capacity=row["MaxWeightCapacity"] # Updated column name
                )
                for row in rows
            ]

    def get_by_id(self, vehicle_id):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM VehicleTypes WHERE Id = ?", (vehicle_id,))
            row = cur.fetchone()
            return VehicleType(
                id=row["Id"],
                name=row["Name"],
                default_tare_weight=row["DefaultTareWeight"], # Updated column name
                max_weight_capacity=row["MaxWeightCapacity"] # Updated column name
            ) if row else None

    def add(self, name, tare, capacity):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO VehicleTypes (Name, DefaultTareWeight, MaxWeightCapacity)
                VALUES (?, ?, ?)
            """, (name, tare, capacity)) # Updated column names in INSERT statement
            conn.commit()

    def update(self, vehicle_id, name, tare, capacity):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                UPDATE VehicleTypes
                SET Name = ?, DefaultTareWeight = ?, MaxWeightCapacity = ?
                WHERE Id = ?
            """, (name, tare, capacity, vehicle_id)) # Updated column names in UPDATE statement
            conn.commit()

    def delete(self, vehicle_id):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM VehicleTypes WHERE Id = ?", (vehicle_id,))
            conn.commit()