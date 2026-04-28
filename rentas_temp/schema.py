from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class VehicleBase(BaseModel):
    plate: str
    brand: str
    model: str
    year: int
    color: Optional[str] = None
    vin: Optional[str] = None
    device_id: Optional[str] = None


class VehicleCreate(VehicleBase):
    pass


class VehicleUpdate(BaseModel):
    plate: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    color: Optional[str] = None
    vin: Optional[str] = None
    device_id: Optional[str] = None
    status: Optional[str] = None


class VehicleResponse(VehicleBase):
    id: int
    status: str
    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None
    speed: Optional[float] = None
    battery_level: Optional[float] = None
    last_update: Optional[datetime] = None
    created_at: datetime

    class Config:
        orm_mode = True


class GPSLocationBase(BaseModel):
    latitude: float
    longitude: float
    altitude: Optional[float] = None
    speed: Optional[float] = None
    heading: Optional[float] = None
    accuracy: Optional[float] = None


class GPSLocationCreate(GPSLocationBase):
    vehicle_id: int


class GPSLocationResponse(GPSLocationBase):
    id: int
    vehicle_id: int
    timestamp: datetime
    source: Optional[str] = None

    class Config:
        orm_mode = True


class RentalBase(BaseModel):
    vehicle_id: int
    user_id: int
    start_latitude: float
    start_longitude: float


class RentalCreate(RentalBase):
    pass


class RentalUpdate(BaseModel):
    end_latitude: Optional[float] = None
    end_longitude: Optional[float] = None
    end_time: Optional[datetime] = None
    total_distance: Optional[float] = None
    total_cost: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class RentalResponse(RentalBase):
    id: int
    end_latitude: Optional[float] = None
    end_longitude: Optional[float] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    total_distance: Optional[float] = None
    total_cost: Optional[float] = None
    status: str
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True


class GeofenceBase(BaseModel):
    vehicle_id: int
    name: str
    center_latitude: float
    center_longitude: float
    radius_meters: float
    alert_on_entry: bool = True
    alert_on_exit: bool = True


class GeofenceCreate(GeofenceBase):
    pass


class GeofenceUpdate(BaseModel):
    name: Optional[str] = None
    center_latitude: Optional[float] = None
    center_longitude: Optional[float] = None
    radius_meters: Optional[float] = None
    is_active: Optional[bool] = None
    alert_on_entry: Optional[bool] = None
    alert_on_exit: Optional[bool] = None


class GeofenceResponse(GeofenceBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        orm_mode = True


class GeofenceAlertResponse(BaseModel):
    id: int
    geofence_id: int
    vehicle_id: int
    alert_type: str
    latitude: float
    longitude: float
    message: Optional[str] = None
    is_read: bool
    timestamp: datetime

    class Config:
        orm_mode = True


class TrackingUpdate(BaseModel):
    device_id: str
    latitude: float
    longitude: float
    altitude: Optional[float] = None
    speed: Optional[float] = None
    heading: Optional[float] = None
    accuracy: Optional[float] = None
    battery_level: Optional[float] = None


class TrackingResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    data: Optional[dict] = None