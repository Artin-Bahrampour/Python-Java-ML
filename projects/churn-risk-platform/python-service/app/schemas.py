from pydantic import BaseModel, Field, field_validator


class CustomerFeatures(BaseModel):
    customer_id: str = Field(min_length=1, max_length=64)
    tenure_months: int = Field(ge=0, le=600)
    monthly_charge: float = Field(ge=0, le=10000)
    support_tickets_90d: int = Field(ge=0, le=1000)
    login_days_30d: int = Field(ge=0, le=31)
    contract_type: str
    payment_method: str
    autopay_enabled: bool

    @field_validator("contract_type")
    @classmethod
    def valid_contract(cls, value: str) -> str:
        if value not in {"month_to_month", "one_year", "two_year"}:
            raise ValueError("contract_type must be month_to_month, one_year, or two_year")
        return value

    @field_validator("payment_method")
    @classmethod
    def valid_payment(cls, value: str) -> str:
        if value not in {"card", "bank_transfer", "invoice"}:
            raise ValueError("payment_method must be card, bank_transfer, or invoice")
        return value


class Prediction(BaseModel):
    customer_id: str
    churn_probability: float
    threshold: float
    requires_review: bool
    model_version: str
