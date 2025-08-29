import sqlite3
from Model.material_type_model import MaterialType
from resource_utils import resource_path


class MaterialRepository:
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
                CREATE TABLE IF NOT EXISTS MaterialTypes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    charges REAL,
                    unit TEXT
                )
            """)
            conn.commit()

    def add(self, name, charges=None, unit=None):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO MaterialTypes (name, charges, unit) VALUES (?, ?, ?)",
                (name, charges, unit)
            )
            conn.commit()
            return cur.lastrowid

    def update(self, material_id, name, charges=None, unit=None):
        with self._connect() as conn:
            conn.execute(
                "UPDATE MaterialTypes SET name = ?, charges = ?, unit = ? WHERE id = ?",
                (name, charges, unit, material_id)
            )
            conn.commit()

    def delete(self, material_id):
        with self._connect() as conn:
            conn.execute("DELETE FROM MaterialTypes WHERE id = ?", (material_id,))
            conn.commit()

    def get_all(self):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM MaterialTypes")
            rows = cur.fetchall()
            return [MaterialType(
                id=row["id"],
                name=row["name"],
                charges=row["charges"],
                unit=row["unit"]
            ) for row in rows]

    def get_by_id(self, material_id):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM MaterialTypes WHERE id = ?", (material_id,))
            row = cur.fetchone()
            return MaterialType(
                id=row["id"],
                name=row["name"],
                charges=row["charges"],
                unit=row["unit"]
            ) if row else None