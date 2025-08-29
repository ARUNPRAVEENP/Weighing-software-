import datetime
import uuid # Import uuid for TransactionGuid

class WeighingTransaction:
    def __init__(self, id=None, transaction_guid=None, vehicle_number=None, vehicle_type_id=None,
                 material_type_id=None, customer_id=None,
                 first_weight=None, first_weight_timestamp=None,
                 second_weight=None, second_weight_timestamp=None,
                 net_weight=None, status='Pending', # 'Pending', 'Completed', 'Canceled'
                 operator_id=None, # New field: ID of the operator/user
                 remarks=None,
                 charges=None, # ADDED: New field for charges
                 created_at=None, last_updated_at=None): # Renamed updated_at to last_updated_at
        
        self.id = id
        self.transaction_guid = transaction_guid if transaction_guid else str(uuid.uuid4()) # Generate UUID if not provided
        self.vehicle_number = vehicle_number
        self.vehicle_type_id = vehicle_type_id
        self.material_type_id = material_type_id
        self.customer_id = customer_id
        
        self.first_weight = first_weight
        self.first_weight_timestamp = first_weight_timestamp
        self.second_weight = second_weight
        self.second_weight_timestamp = second_weight_timestamp
        
        self.net_weight = net_weight
        self.status = status
        self.operator_id = operator_id
        self.remarks = remarks
        self.charges = charges # Assign the new charges field
        
        self.created_at = created_at if created_at else datetime.datetime.now()
        self.last_updated_at = last_updated_at if last_updated_at else datetime.datetime.now()

    def to_dict(self):
        return {
            "id": self.id,
            "transaction_guid": self.transaction_guid,
            "vehicle_number": self.vehicle_number,
            "vehicle_type_id": self.vehicle_type_id,
            "material_type_id": self.material_type_id,
            "customer_id": self.customer_id,
            "first_weight": self.first_weight,
            "first_weight_timestamp": self.first_weight_timestamp.isoformat() if isinstance(self.first_weight_timestamp, datetime.datetime) else self.first_weight_timestamp,
            "second_weight": self.second_weight,
            "second_weight_timestamp": self.second_weight_timestamp.isoformat() if isinstance(self.second_weight_timestamp, datetime.datetime) else self.second_weight_timestamp,
            "net_weight": self.net_weight,
            "status": self.status,
            "operator_id": self.operator_id,
            "remarks": self.remarks,
            "charges": self.charges, # Include charges in dict
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime.datetime) else self.created_at,
            "last_updated_at": self.last_updated_at.isoformat() if isinstance(self.last_updated_at, datetime.datetime) else self.last_updated_at
        }

    @staticmethod
    def from_dict(data):
        # Helper to parse datetime strings
        def parse_datetime(dt_str):
            return datetime.datetime.fromisoformat(dt_str) if dt_str and isinstance(dt_str, str) else dt_str

        return WeighingTransaction(
            id=data.get("id"),
            transaction_guid=data.get("transaction_guid"),
            vehicle_number=data.get("vehicle_number"),
            vehicle_type_id=data.get("vehicle_type_id"),
            material_type_id=data.get("material_type_id"),
            customer_id=data.get("customer_id"),
            first_weight=data.get("first_weight"),
            first_weight_timestamp=parse_datetime(data.get("first_weight_timestamp")),
            second_weight=data.get("second_weight"),
            second_weight_timestamp=parse_datetime(data.get("second_weight_timestamp")),
            net_weight=data.get("net_weight"),
            status=data.get("status"),
            operator_id=data.get("operator_id"),
            remarks=data.get("remarks"),
            charges=data.get("charges"), # Include charges when creating from dict
            created_at=parse_datetime(data.get("created_at")),
            last_updated_at=parse_datetime(data.get("last_updated_at"))
        )

