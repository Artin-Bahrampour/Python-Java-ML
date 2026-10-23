from pydantic import BaseModel, Field, field_validator

class Ticket(BaseModel):
    ticket_id: str = Field(min_length=1, max_length=80)
    priority: str
    channel: str
    age_minutes: int = Field(ge=0, le=43200)
    messages_count: int = Field(ge=0, le=10000)
    customer_tier: str
    agent_queue_depth: int = Field(ge=0, le=10000)

    @field_validator("priority")
    @classmethod
    def priority_ok(cls, value):
        if value not in {"low", "normal", "high", "urgent"}: raise ValueError("invalid priority")
        return value
    @field_validator("channel")
    @classmethod
    def channel_ok(cls, value):
        if value not in {"email", "chat", "phone"}: raise ValueError("invalid channel")
        return value
    @field_validator("customer_tier")
    @classmethod
    def tier_ok(cls, value):
        if value not in {"standard", "business", "enterprise"}: raise ValueError("invalid customer_tier")
        return value

class Risk(BaseModel):
    ticket_id: str
    breach_probability: float
    threshold: float
    prioritize: bool
    model_version: str
