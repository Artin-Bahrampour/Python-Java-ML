from pydantic import BaseModel, Field
class ForecastRequest(BaseModel):
    building_id:str=Field(min_length=1,max_length=64)
    hour:int=Field(ge=0,le=23)
    day_of_week:int=Field(ge=0,le=6)
    outside_temp_c:float=Field(ge=-50,le=60)
    occupancy_ratio:float=Field(ge=0,le=1)
    prior_hour_kwh:float=Field(ge=0,le=1_000_000)
class Forecast(BaseModel):
    building_id:str
    predicted_kwh:float
    model_version:str
