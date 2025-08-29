class MaterialType:
    def __init__(self, id, name, charges=None, unit=None):
        if not name:
            raise ValueError("Material name is required.")
        if charges is not None and not unit:
            raise ValueError("Unit is required when charges are provided.")
        
        self.id = id
        self.name = name
        self.charges = charges
        self.unit = unit
