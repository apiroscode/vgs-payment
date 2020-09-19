import base64

import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import asyncio

cred = credentials.Certificate("vgs.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins="*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SERVER_KEY = "Mid-server-KJHthD0IwbSgfGNe_CHPbydj"
AUTH_STRING = base64.b64encode(f"{SERVER_KEY}:".encode("ascii"))
END_POINT = "https://app.midtrans.com/snap/v1/transactions"


class Transaction(BaseModel):
    order_id: str
    gross_amount: int
    email: str
    phone: str


@app.post("/midtrans")
async def get_midtrans_token(transaction: Transaction):
    transaction_dict = transaction.dict()
    midtrans_payload = {
        "transaction_details": {
            "gross_amount": transaction_dict["gross_amount"],
            "order_id": transaction_dict["order_id"],
        },
        "customer_details": {
            "email": transaction_dict["email"],
            "phone": transaction_dict["phone"],
        },
        "credit_card": {"secure": False,},
    }
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Basic {AUTH_STRING.decode('utf-8')}",
    }
    result = requests.post(END_POINT, json=midtrans_payload, headers=headers,)
    return result.json()


class MidtransTransaction(BaseModel):
    order_id: str
    transaction_status: str


async def change_order_status(order_id, status):
    order_ref = db.collection("orders").document(order_id)
    order = order_ref.get()

    if order.exists:
        order_ref.update({"status": status})


@app.post("/midtrans/notify")
async def check_midtrans_notify(transaction: MidtransTransaction):
    transaction_dict = transaction.dict()
    asyncio.create_task(
        change_order_status(transaction_dict["order_id"], transaction_dict["transaction_status"])
    )
    return {"status": "OK"}
