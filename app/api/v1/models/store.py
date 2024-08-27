from pydantic import BaseModel
from typing import Optional

class StoreData(BaseModel):
    store_id: str
    timestamp_utc: str
    status: str

class BusinessHours(BaseModel):
    store_id: str
    dayOfWeek: int
    start_time_local: str
    end_time_local: str

class Timezone(BaseModel):
    store_id: str
    timezone_str: str
