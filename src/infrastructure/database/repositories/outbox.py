from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.interfaces.outbox_repository import IOutboxRepository
from src.infrastructure.database.models import Outbox, OutboxStatus


class SQLAlchemyOutboxRepository(IOutboxRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_event(self, event_type: str, payload: dict[str, Any]) -> None:
        self._session.add(
            Outbox(
                event_type=event_type,
                payload=payload,
            )
        )
        await self._session.flush()

    async def get_pending_events(self, limit=100) -> list[dict[str, Any]]:
        stmt = (
            select(Outbox)
            .where(Outbox.status == OutboxStatus.PENDING)
            .with_for_update(skip_locked=True)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        rows = result.scalars().all()
        return [
            {"id": str(row.id), "event_type": row.event_type, "payload": row.payload}
            for row in rows
        ]

    async def mark_published(self, event_id: str) -> None:
        stmt = (
            update(Outbox)
            .where(Outbox.id == event_id)
            .values(status=OutboxStatus.PUBLISHED, published_at=datetime.now(UTC))
        )
        await self._session.execute(stmt)

    async def mark_failed(self, event_id: str, error_message: str | None = None) -> None:
        row = await self._session.get(Outbox, event_id)
        if row is None:
            return
        row.retry_count += 1
        row.error_message = error_message
        if row.retry_count >= 3:
            row.status = OutboxStatus.FAILED
        await self._session.flush()
