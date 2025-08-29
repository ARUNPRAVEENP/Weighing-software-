import re

class Customer:
    def __init__(self, id, name, address=None, city=None, pincode=None,
                 contact_number=None, email=None, gst_id=None):
        if not name:
            raise ValueError("Customer name is required.")
        if contact_number and not re.fullmatch(r"\d{10}", contact_number):
            raise ValueError("Contact number must be a 10-digit number without country code.")
        if email and not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email):
            raise ValueError("Invalid email format.")
        
        self.id = id
        self.name = name
        self.address = address
        self.city = city
        self.pincode = pincode
        self.contact_number = contact_number
        self.email = email
        self.gst_id = gst_id
