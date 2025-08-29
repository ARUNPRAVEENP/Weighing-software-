CREATE TABLE IF NOT EXISTS VehicleTypes (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    Name TEXT NOT NULL UNIQUE,
    DefaultTareWeight REAL,
    MaxWeightCapacity REAL
);
