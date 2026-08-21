import datetime
from typing import Optional, Dict, List
from pydantic import BaseModel, Field

class StrikeBase(BaseModel):
    distance: int = Field(..., ge=0, le=40, description="Distance in km (0 to 40)")
    intensity: int = Field(..., ge=0, description="Raw intensity value (energy)")

class StrikeCreate(StrikeBase):
    pass

class StrikeResponse(StrikeBase):
    id: int
    timestamp: datetime.datetime

    class Config:
        from_attributes = True

class StatsResponse(BaseModel):
    amount_24h: int
    amount_7d: int
    avg_distance: float
    avg_intensity: float
    closest_distance: Optional[int] = None

class SensorConfigResponse(BaseModel):
    capacitance: int
    location: int  # 0: Indoors, 1: Outdoors
    disturber: int  # 0: Disabled, 1: Enabled
    noise_floor: int  # 0 - 7
    watchdog: int  # 0 - 7
    spike_rejection: int  # 0 - 7
    display_active_start: int  # Hour (e.g. 8)
    display_active_end: int  # Hour (e.g. 20)
    telegram_enabled: bool
    telegram_token: str
    telegram_chat_id: str
    is_mock_as3935: bool
    is_mock_lcd: bool

class SensorConfigUpdate(BaseModel):
    capacitance: int = Field(96, ge=8, le=120)
    location: int = Field(0, ge=0, le=1)
    disturber: int = Field(1, ge=0, le=1)
    noise_floor: int = Field(2, ge=0, le=7)
    watchdog: int = Field(2, ge=0, le=7)
    spike_rejection: int = Field(2, ge=0, le=7)
    display_active_start: int = Field(8, ge=0, le=23)
    display_active_end: int = Field(20, ge=0, le=23)
    telegram_enabled: bool = False
    telegram_token: str = ""
    telegram_chat_id: str = ""

class TelegramTestRequest(BaseModel):
    token: str
    chat_id: str

class DiagnosticDetails(BaseModel):
    is_mock: bool
    i2c_connected: bool
    error_message: Optional[str] = None
    
    capacitance_read: Optional[int] = None
    capacitance_config: int
    capacitance_match: bool
    
    location_read: Optional[str] = None
    location_config: str
    location_match: bool
    
    disturber_read: Optional[str] = None
    disturber_config: str
    disturber_match: bool
    
    noise_floor_read: Optional[int] = None
    noise_floor_config: int
    noise_floor_match: bool
    
    watchdog_read: Optional[int] = None
    watchdog_config: int
    watchdog_match: bool
    
    spike_rejection_read: Optional[int] = None
    spike_rejection_config: int
    spike_rejection_match: bool

class DiagnosticResponse(BaseModel):
    status: str  # "healthy", "warning", "error"
    message: str
    details: DiagnosticDetails
    recommendations: List[str]

class ToggleMockErrorRequest(BaseModel):
    enable_error: bool
