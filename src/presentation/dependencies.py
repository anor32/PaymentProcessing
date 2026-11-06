from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.application.usecases import CreatePaymentUseCase, GetPaymentUseCase
from src.config import settings
from src.domain.interfaces import IUnitOfWork
from src.infrastructure.database.db import engine
from src.infrastructure.database.uow import SQLAlchemyUnitOfWork

session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession]:
    async with session_factory() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_uow() -> IUnitOfWork:
    return SQLAlchemyUnitOfWork(session_factory)


UowDep = Annotated[IUnitOfWork, Depends(get_uow)]


def get_create_payment_usecase(uow: UowDep) -> CreatePaymentUseCase:
    return CreatePaymentUseCase(uow)


def get_get_payment_usecase(uow: UowDep) -> GetPaymentUseCase:
    return GetPaymentUseCase(uow)


CreatePaymentDep = Annotated[CreatePaymentUseCase, Depends(get_create_payment_usecase)]
GetPaymentDep = Annotated[GetPaymentUseCase, Depends(get_get_payment_usecase)]


api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_api_key(api_key: Annotated[str | None, Depends(api_key_header)]) -> str:
    if api_key is None:
        raise HTTPException(status_code=403, detail="Not authenticated")

    if api_key != settings.API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")

    return api_key
