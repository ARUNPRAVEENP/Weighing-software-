from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class WeighingTransaction:
    id: Optional[int] = None
    transaction_guid: str = ""
    vehicle_number: str = ""
    vehicle_type_id: Optional[int] = None
    material_type_id: Optional[int] = None
    customer_id: Optional[int] = None
    first_weight: Optional[float] = None
    first_weight_timestamp: Optional[datetime] = None
    second_weight: Optional[float] = None
    second_weight_timestamp: Optional[datetime] = None
    net_weight: Optional[float] = None
    charges: Optional[float] = None
    status: str = "Pending"
    operator_id: Optional[int] = None
    remarks: Optional[str] = None
    created_at: datetime = datetime.now()
    last_updated_at: datetime = datetime.now()
