class VehicleType:
    def __init__(self, id, name, default_tare_weight=None, max_weight_capacity=None):
        if not name:
            raise ValueError("Vehicle type name is required.")
        
        self.id = id
        self.name = name
        self.default_tare_weight = default_tare_weight
        self.max_weight_capacity = max_weight_capacity
