class MasterService:
    def __init__(self, vehicle_repo, material_repo, customer_repo):
        self.vehicle_repo = vehicle_repo
        self.material_repo = material_repo
        self.customer_repo = customer_repo

    # ==== Vehicle Types ====
    def get_all_vehicle_types(self):
        return self.vehicle_repo.get_all()

    def get_vehicle_type_by_id(self, vehicle_id):
        return self.vehicle_repo.get_by_id(vehicle_id)

    def add_vehicle_type(self, name, tare=0.0, capacity=0.0):
        self.vehicle_repo.add(name, tare, capacity)
        # Return latest inserted (if needed)
        return self.vehicle_repo.get_all()[-1]

    # ==== Material Types ====
    def get_all_material_types(self):
        return self.material_repo.get_all()

    def get_material_type_by_id(self, material_id):
        return self.material_repo.get_by_id(material_id)

    def add_material_type(self, name, charges=0.0, unit=""):
        self.material_repo.add(name, charges, unit)
        return self.material_repo.get_all()[-1]

    # ==== Customers ====
    def get_all_customers(self):
        return self.customer_repo.get_all()

    def get_customer_by_id(self, customer_id):
        return self.customer_repo.get_by_id(customer_id)

    def add_customer(self, name):
        self.customer_repo.add(name)
        return self.customer_repo.get_all()[-1]
