CREATE TABLE IF NOT EXISTS Customers (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    Name TEXT NOT NULL,
    Address TEXT,
    City TEXT,
    Pincode TEXT,
    ContactNumber TEXT,
    Email TEXT,
    GSTId TEXT
);
