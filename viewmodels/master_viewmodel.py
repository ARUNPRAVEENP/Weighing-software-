class VehicleMasterViewModel:
    def __init__(self, repository):
        self.repository = repository  # VehicleRepository
        self.selected_entity = None
        self.entities = []  # List of VehicleType
        self.search_query = ""
        self.load_entities()

    def load_entities(self):
        self.entities = self.repository.get_all()

    def filter_entities(self):
        if not self.search_query:
            return self.entities
        return [v for v in self.entities if self.search_query.lower() in v.name.lower()]

    def add_entity(self, name, default_tare=None, max_capacity=None):
        if not name.strip():
            raise ValueError("Vehicle type name cannot be empty.")
        new_entity = self.repository.add(name, default_tare, max_capacity)
        self.load_entities()
        return new_entity

    def edit_entity(self, vehicle_id, name, default_tare=None, max_capacity=None):
        self.repository.update(vehicle_id, name, default_tare, max_capacity)
        self.load_entities()

    def delete_entity(self, vehicle_id):
        self.repository.delete(vehicle_id)
        self.load_entities()

    def select_entity(self, vehicle_id):
        self.selected_entity = self.repository.get_by_id(vehicle_id)

class MasterViewModel:
    def __init__(self, repository):
        self.repo = repository
        self.entities = self.repo.get_all()

    def add_entity(self, *args, **kwargs):
        self.repo.add(*args, **kwargs)
        self.refresh()

    def edit_entity(self, entity_id, *args, **kwargs):
        self.repo.update(entity_id, *args, **kwargs)
        self.refresh()

    def delete_entity(self, entity_id):
        self.repo.delete(entity_id)
        self.refresh()

    def refresh(self):
        self.entities = self.repo.get_all()

class CustomerMasterViewModel:
    def __init__(self, repository):
        self.repository = repository  # CustomerRepository
        self.selected_entity = None
        self.entities = []  # List of Customer
        self.search_query = ""
        self.load_entities()

    def load_entities(self):
        self.entities = self.repository.get_all()

    def filter_entities(self):
        if not self.search_query:
            return self.entities
        q = self.search_query.lower()
        return [
            c for c in self.entities
            if q in (c.name or "").lower()
            or q in (c.city or "").lower()
            or q in (c.contact_number or "")
            or q in (c.gst_id or "").lower()
        ]

    def add_entity(self, name, address=None, city=None, pincode=None, contact_number=None, email=None, gst_id=None):
        name = name.strip().upper()
        if not name:
            raise ValueError("Customer name cannot be empty.")
        return self.repository.add(name, address, city, pincode, contact_number, email, gst_id)

    def edit_entity(self, customer_id, name, address=None, city=None, pincode=None, contact_number=None, email=None, gst_id=None):
        name = name.strip().upper()
        return self.repository.update(customer_id, name, address, city, pincode, contact_number, email, gst_id)

    def delete_entity(self, customer_id):
        self.repository.delete(customer_id)
        self.load_entities()

    def select_entity(self, customer_id):
        self.selected_entity = self.repository.get_by_id(customer_id)
