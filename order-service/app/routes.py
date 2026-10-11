import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .database import get_db, settings
from .models import Order
from .schemas import OrderCreate, OrderResponse

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("", response_model=list[OrderResponse])
def list_orders(db: Session = Depends(get_db)):
    return db.query(Order).order_by(Order.id).all()


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.post("", response_model=OrderResponse, status_code=201)
def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
    try:
        response = httpx.get(
            f"{settings.product_service_url}/products/{payload.product_id}",
            timeout=5,
        )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=503,
            detail="Product service unavailable",
        ) from exc

    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="Product not found")

    if response.status_code != 200:
        raise HTTPException(status_code=503, detail="Unable to validate product")

    product = response.json()

    if product["quantity"] < payload.quantity:
        raise HTTPException(status_code=400, detail="Insufficient product quantity")

    total_price = product["price"] * payload.quantity

    updated_product = {
        "name": product["name"],
        "category": product["category"],
        "quantity": product["quantity"] - payload.quantity,
        "price": product["price"],
    }
    try:
        stock_response = httpx.put(
            f"{settings.product_service_url}/products/{payload.product_id}",
            json=updated_product,
            timeout=5,
        )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=503,
            detail="Product service unavailable",
        ) from exc

    if stock_response.status_code != 200:
        raise HTTPException(status_code=503, detail="Unable to update product stock")

    order = Order(
        product_id=payload.product_id,
        quantity=payload.quantity,
        customer_name=payload.customer_name,
        total_price=total_price,
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    return order


@router.delete("/{order_id}", status_code=204)
def delete_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    db.delete(order)
    db.commit()
