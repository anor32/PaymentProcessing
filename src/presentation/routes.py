from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status

from src.application.dtos.payment_create_dto import PaymentCreateDto
from src.domain.exceptions import (
    IdempotencyError,
    InvalidPaymentError,
    ObjectNotFoundError,
)
from src.presentation.dependencies import CreatePaymentDep, GetPaymentDep, get_api_key
from src.presentation.schemas.payment_schemas import PaymentCreateRequest, PaymentResponse

router = APIRouter(prefix="/api/v1")


def _map_domain_error_to_http(exc: Exception) -> HTTPException:
    if isinstance(exc, InvalidPaymentError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message)
    if isinstance(exc, ObjectNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    if isinstance(exc, IdempotencyError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message)
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="internal server error"
    )


@router.post("/payments", response_model=PaymentResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_payment(
    request: PaymentCreateRequest,
    api_key: Annotated[str, Depends(get_api_key)],
    usecase: CreatePaymentDep,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
) -> PaymentResponse:
    create_dto = PaymentCreateDto.from_request(request, idempotency_key)
    try:
        payment = await usecase.execute(create_dto)
    except Exception as e:
        raise _map_domain_error_to_http(e) from e

    return PaymentResponse(**asdict(payment))


@router.get("/payments/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: str,
    api_key: Annotated[str, Depends(get_api_key)],
    usecase: GetPaymentDep,
) -> PaymentResponse:
    try:
        payment = await usecase.execute(payment_id)
    except ObjectNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message) from None

    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    return PaymentResponse(**asdict(payment))
