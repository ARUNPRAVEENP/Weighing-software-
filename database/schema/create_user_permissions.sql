CREATE TABLE IF NOT EXISTS UserPermissions (
    UserId INTEGER NOT NULL,
    PermissionId INTEGER NOT NULL,
    PRIMARY KEY (UserId, PermissionId),
    FOREIGN KEY (UserId) REFERENCES Users(Id) ON DELETE CASCADE,
    FOREIGN KEY (PermissionId) REFERENCES Permissions(Id) ON DELETE CASCADE
);
