###
# Simple restaurant order api.
# - create order
# - query sum of all of a user's order amounts.
###

from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select
from uuid import uuid4
from sqlalchemy import text
import uvicorn

# CAUTION: sqlite doesn't like tables named "order".
class CustomerOrder(SQLModel, table=True):
    order_id: str = Field(index=True, primary_key=True)
    shopper_id: str = Field(index=True)
    cart_id: str = Field(index=True)
    price_cents: int = Field()

sqlite_file_name = "database_02.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.post("/order/")
def new_order(order: CustomerOrder, session: SessionDep) -> CustomerOrder:
    order.order_id = uuid4().hex
    # do not validate order shopper_id or cart_id.
    session.add(order)
    session.commit()
    session.refresh(order)
    return order

@app.get("/order-totals/{user_id}")
def calculate_order_totals(user_id:str, session: SessionDep) -> str:
    # sql = text('select * from customerorder')
    sql = text('select sum(price_cents) as sum_price_cents from customerorder where order_id = "6ea88c2cc37f40b383039056e5435481";')
    rows = session.execute(sql)
    # return 10
    return str(rows.mappings().all())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)