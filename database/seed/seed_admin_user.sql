-- Step 1: Insert admin user only if not exists
INSERT OR IGNORE INTO Users (Id, Username, HashedPassword)
VALUES (1, 'admin', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f'); 
-- "Weigh@2025" hashed with SHA-256

-- Step 2: Assign all permissions (avoids duplicates)
INSERT OR IGNORE INTO UserPermissions (UserId, PermissionId)
SELECT 1, Id FROM Permissions;
