from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status

from src.application.dtos.payment_create_dto import PaymentCreateDto
from src.presentation.api.dependencies import CreatePaymentDep, GetPaymentDep
from src.presentation.dependencies import get_api_key
from src.presentation.schemas import PaymentCreateRequest, PaymentResponse

router = APIRouter(prefix="/api/v1")


@router.post("/payments", response_model=PaymentResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_payment(
    request: PaymentCreateRequest,
    api_key: Annotated[str, Depends(get_api_key)],
    usecase: CreatePaymentDep,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
) -> PaymentResponse:
    """Creates a new payment."""
    create_dto = PaymentCreateDto.from_request(request, idempotency_key)
    payment = await usecase.execute(create_dto)
    return PaymentResponse.create_response(payment)


@router.get("/payments/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: str,
    api_key: Annotated[str, Depends(get_api_key)],
    usecase: GetPaymentDep,
) -> PaymentResponse:
    payment = await usecase.execute(payment_id)

    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    return PaymentResponse.get_response(payment)
