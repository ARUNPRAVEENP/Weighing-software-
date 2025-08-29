CREATE TABLE IF NOT EXISTS AuditLog (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    UserId INTEGER,
    ActionType TEXT NOT NULL,
    Description TEXT NOT NULL,
    Timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    AffectedRecordId INTEGER,
    TableName TEXT,
    OldValue TEXT,
    NewValue TEXT,
    IpAddress TEXT,
    FOREIGN KEY (UserId) REFERENCES Users(Id)
);
