from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    category: str = Field(min_length=2, max_length=80)
    quantity: int = Field(ge=0)
    price: float = Field(gt=0)


class ProductResponse(ProductCreate):
    id: int

    class Config:
        from_attributes = True
