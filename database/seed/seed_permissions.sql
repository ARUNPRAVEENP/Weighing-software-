INSERT INTO Permissions (Name, Description) VALUES
-- Material Master
("CanViewMaterial", "View materials"),
("CanAddMaterial", "Add new materials"),
("CanEditMaterial", "Edit existing materials"),
("CanDeleteMaterial", "Delete materials"),

-- Customer Master
("CanViewCustomer", "View customers"),
("CanAddCustomer", "Add new customers"),
("CanEditCustomer", "Edit customer information"),
("CanDeleteCustomer", "Delete customers"),

-- Vehicle Type Master
("CanViewVehicle", "View vehicle types"),
("CanAddVehicle", "Add new vehicle types"),
("CanEditVehicle", "Edit vehicle types"),
("CanDeleteVehicle", "Delete vehicle types"),

-- Weighing Transactions
("CanWeighEntry", "Create new weighing record"),
("CanOverrideWeight", "Manually override weight"),
("CanPrintWeighSlip", "Print weighment ticket"),
("CanApplyWeighCharges", "Apply extra charges"),
("CanEditWeighTransaction", "Edit existing weighing record"),
("CanDeleteWeighTransaction", "Delete weighment record"),

-- User Management
("CanAddUser", "Add new users"),
("CanEditUser", "Edit user details"),
("CanDeleteUser", "Remove users"),
("CanManageUserPermissions", "Assign or remove user permissions"),

-- Reports (Optional but ready)
("CanViewReports", "Access reporting dashboard"),
("CanExportReports", "Export report data");
