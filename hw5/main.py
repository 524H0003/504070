from fastapi import FastAPI, HTTPException, Path, Query
from pydantic import BaseModel, Field
from typing import Annotated, List, Optional

app = FastAPI(
    title="Order Management Service",
)

# In-memory storage
orders: List[dict] = []
next_order_id = 1


class OrderItem(BaseModel):
    product_id: int = Field(gt=0)
    product_name: str = Field(min_length=1)
    quantity: int = Field(gt=0)
    unit_price: float = Field(gt=0)


class Address(BaseModel):
    street: str = Field(min_length=1)
    city: str = Field(min_length=1)
    postal_code: str = Field(min_length=1)


class OrderCreate(BaseModel):
    customer_name: str = Field(min_length=1)
    shipping_address: Address
    items: List[OrderItem] = Field(
        min_length=1, description="At least one item required"
    )


class OrderUpdate(BaseModel):
    status: str = Field(min_length=1)
    note: Optional[str] = None


class Order(BaseModel):
    order_id: int
    customer_name: str
    shipping_address: Address
    items: List[OrderItem]
    total_amount: float
    status: str
    note: Optional[str] = None


def calculate_total(items: List[OrderItem]) -> float:
    return sum(item.quantity * item.unit_price for item in items)


def find_order(order_id: int) -> Optional[dict]:
    for order in orders:
        if order["order_id"] == order_id:
            return order
    return None


@app.get("/orders")
def get_orders():
    return orders


@app.get("/orders/{order_id}")
def get_order(order_id: int = Path(gt=0)):
    order = find_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@app.post("/orders")
def create_order(order_create: OrderCreate):
    global next_order_id
    total = calculate_total(order_create.items)
    order = {
        "order_id": next_order_id,
        "customer_name": order_create.customer_name,
        "shipping_address": order_create.shipping_address.model_dump(),
        "items": [item.model_dump() for item in order_create.items],
        "total_amount": round(total, 2),
        "status": "pending",
        "note": None,
    }
    orders.append(order)
    next_order_id += 1
    return order


@app.put("/orders/{order_id}")
def update_order(
    order_id: Annotated[int | None, Query(gt=0)] = None,
    notify_customer: Optional[bool] = Query(
        None, description="Whether to notify customer"
    ),
    priority: Optional[str] = Query(None, description="Processing priority"),
    update: OrderUpdate = None,
):
    order = find_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Update order using request body
    order["status"] = update.status
    order["note"] = update.note

    # Return updated order together with query parameter information
    response = {
        "order": order,
        "notify_customer": notify_customer,
        "priority": priority,
    }
    return response
