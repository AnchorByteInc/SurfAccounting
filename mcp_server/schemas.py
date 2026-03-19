from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

class InvoiceLineSchema(BaseModel):
    item_id: Optional[int] = None
    description: Optional[str] = None
    quantity: float = Field(default=1.0, gt=0)
    unit_price: float = Field(default=0.0, ge=0)
    account_id: int
    tax_ids: List[int] = Field(default_factory=list)

class InvoiceCreateSchema(BaseModel):
    customer_id: int
    issue_date: date
    due_date: date
    lines: List[InvoiceLineSchema]
    invoice_number: Optional[str] = None

class BillLineSchema(BaseModel):
    item_id: Optional[int] = None
    description: Optional[str] = None
    quantity: float = Field(default=1.0, gt=0)
    unit_price: float = Field(default=0.0, ge=0)
    account_id: int
    tax_ids: List[int] = Field(default_factory=list)

class BillCreateSchema(BaseModel):
    vendor_id: int
    bill_number: str
    issue_date: date
    due_date: date
    lines: List[BillLineSchema]

class PaymentDetailsSchema(BaseModel):
    date: date
    payment_method: Optional[str] = "Cash"
    account_id: Optional[int] = None

class CustomerCreateSchema(BaseModel):
    name: str = Field(..., min_length=1)
    email: Optional[str] = None
    phone: Optional[str] = None
    primary_contact_name: Optional[str] = None
    website: Optional[str] = None
    billing_address: Optional[str] = None
    shipping_address: Optional[str] = None

class VendorCreateSchema(BaseModel):
    name: str = Field(..., min_length=1)
    email: Optional[str] = None
    phone: Optional[str] = None
    primary_contact_name: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None

class PaymentCreateSchema(BaseModel):
    customer_id: int
    amount: float = Field(..., gt=0)
    date: date
    payment_method: str = "Cash"
    invoice_id: Optional[int] = None
    account_id: Optional[int] = None

class VendorPaymentCreateSchema(BaseModel):
    vendor_id: int
    amount: float = Field(..., gt=0)
    date: date
    payment_method: str = "Cash"
    bill_id: Optional[int] = None
    account_id: Optional[int] = None

class ItemCreateSchema(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    price: float = Field(default=0.0, ge=0)
    sellable: bool = True
    income_account_id: Optional[int] = None
    purchaseable: bool = False
    expense_account_id: Optional[int] = None
    tax_ids: List[int] = Field(default_factory=list)
