from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime, date

# 用户相关
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=80)
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        orm_mode = True

# 婴儿相关
class BabyCreate(BaseModel):
    print("创建婴儿数据:")
    name: str = Field(..., min_length=1, max_length=100)
    birth_date: date
    gender: Optional[str] = Field(None, regex='^(male|female|other)$')
    # class Config:
    #     orm_mode = True

class BabyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    birth_date: Optional[date] = None
    gender: Optional[str] = Field(None, regex='^(male|female|other)$')

class BabyResponse(BaseModel):
    id: int
    name: str
    birth_date: date
    gender: Optional[str] = None
    user_id: int

    class Config:
        # from_attributes = True
        orm_mode = True 
        # json_encoders = {
        #     datetime: lambda v: v.isoformat()  # 将 datetime 转换为 ISO 格式字符串
        # }

# 体重身长记录相关
class MeasurementCreate(BaseModel):
    weight_kg: Optional[float] = Field(None, gt=0)
    height_cm: Optional[float] = Field(None, gt=0)
    measurement_date: date
    notes: Optional[str] = None
    baby_id: int

class MeasurementUpdate(BaseModel):
    weight_kg: Optional[float] = Field(None, gt=0)
    height_cm: Optional[float] = Field(None, gt=0)
    measurement_date: Optional[date] = None
    notes: Optional[str] = None

class MeasurementResponse(BaseModel):
    id: int
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    measurement_date: date
    notes: Optional[str] = None
    baby_id: int

    class Config:
        # from_attributes = True
        orm_mode = True 

# 哺乳记录相关
class FeedingCreate(BaseModel):
    feeding_type: str = Field(..., regex='^(breast|bottle)$')  # 'breast' 或 'bottle'
    start_time: Optional[datetime] = None
    bottle_ml: Optional[int] = None
    baby_id: int

class BottleFeedingCreate(BaseModel):
    bottle_ml: int
    timestamp: Optional[datetime] = None
    baby_id: int

class BreastFeedingStart(BaseModel):
    start_time: datetime
    baby_id: int

class BreastFeedingEnd(BaseModel):
    end_time: datetime
    notes: Optional[str] = None

class FeedingUpdate(BaseModel):
    feeding_type: Optional[str] = Field(None, regex='^(breast|bottle)$')
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    bottle_ml: Optional[int] = None
    breast_ml: Optional[int] = None
    notes: Optional[str] = None

class FeedingResponse(BaseModel):
    id: int
    feeding_type: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    bottle_ml: int
    breast_ml: int
    total_ml: int
    duration_minutes: Optional[float] = None
    notes: Optional[str] = None
    baby_id: int

    class Config:
        # from_attributes = True
        orm_mode = True 

# 大小便记录相关
class DiaperCreate(BaseModel):
    diaper_type: str = Field(..., regex='^(wet|dirty)$')  # 只能是 wet 或 dirty
    baby_id: int
    timestamp: Optional[datetime] = None

class DiaperUpdate(BaseModel):
    diaper_type: Optional[str] = Field(None, regex='^(wet|dirty)$')
    timestamp: Optional[datetime] = None
    notes: Optional[str] = None

class DiaperResponse(BaseModel):
    id: int
    diaper_type: str
    timestamp: datetime
    notes: Optional[str] = None
    baby_id: int

    class Config:
        # from_attributes = True
        orm_mode = True 

# 睡眠记录相关
class SleepCreate(BaseModel):
    start_time: datetime
    baby_id: int

class SleepUpdate(BaseModel):
    end_time: Optional[datetime] = None
    notes: Optional[str] = None

class SleepResponse(BaseModel):
    id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: Optional[float] = None
    notes: Optional[str] = None
    baby_id: int

    class Config:
        # from_attributes = True
        orm_mode = True 

# 统计相关
class StatsRequest(BaseModel):
    baby_id: int
    start_date: datetime
    end_date: datetime

class FeedingStats(BaseModel):
    date: str
    total_bottle_ml: int
    total_breastfeeding_minutes: float

class DiaperStats(BaseModel):
    date: str
    wet_count: int
    dirty_count: int

class SleepStats(BaseModel):
    date: str
    total_sleep_minutes: float

# 母乳余量与吸奶相关
class MilkPumpCreate(BaseModel):
    baby_id: int
    volume_ml: int
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    notes: Optional[str] = None

class BottleBreastCreate(BaseModel):
    baby_id: int
    volume_ml: int
    timestamp: Optional[datetime] = None
    notes: Optional[str] = None

class MilkInventoryResponse(BaseModel):
    baby_id: int
    remaining_ml: int
    updated_at: datetime

    class Config:
        orm_mode = True

# 亲喂（独立）
class DirectBreastStart(BaseModel):
    baby_id: int
    start_time: datetime
    side: Optional[str] = Field(None, regex='^(left|right|both)$')
    notes: Optional[str] = None

class DirectBreastEnd(BaseModel):
    end_time: datetime
    notes: Optional[str] = None

class DirectBreastResponse(BaseModel):
    id: int
    baby_id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: Optional[float] = None
    side: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        orm_mode = True

# 瓶喂母乳（独立）
class BottleBreastCreate(BaseModel):
    baby_id: int
    volume_ml: int
    timestamp: Optional[datetime] = None
    notes: Optional[str] = None

class BottleBreastResponse(BaseModel):
    id: int
    baby_id: int
    volume_ml: int
    timestamp: datetime
    notes: Optional[str] = None

    class Config:
        orm_mode = True

# 配方奶粉（独立）
class FormulaFeedingCreate(BaseModel):
    baby_id: int
    volume_ml: int
    timestamp: Optional[datetime] = None
    brand: Optional[str] = None
    notes: Optional[str] = None

class FormulaFeedingResponse(BaseModel):
    id: int
    baby_id: int
    volume_ml: int
    timestamp: datetime
    brand: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        orm_mode = True