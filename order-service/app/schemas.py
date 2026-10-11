from pydantic import BaseModel, Field


class OrderCreate(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)
    customer_name: str = Field(min_length=2, max_length=120)


class OrderResponse(OrderCreate):
    id: int
    total_price: float

    class Config:
        from_attributes = True
