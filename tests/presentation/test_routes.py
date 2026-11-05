from unittest.mock import AsyncMock

from fastapi.testclient import TestClient


class TestRoutes:
    def test_create_payment_endpoint(
        self,
        client: TestClient,
        mock_create_usecase: AsyncMock,
    ) -> None:
        response = client.post(
            "/api/v1/payments",
            json={
                "amount": 100.50,
                "currency": "RUB",
                "description": "Test",
                "metadata": {},
                "webhook_url": None,
            },
            headers={
                "X-API-Key": "secret-api-key",
                "Idempotency-Key": "idem-1",
            },
        )

        assert response.status_code == 202
        data = response.json()
        assert data["id"] == "pay-1"
        assert data["status"] == "pending"

    def test_create_payment_missing_api_key(
        self,
        client: TestClient,
    ) -> None:
        response = client.post(
            "/api/v1/payments",
            json={"amount": 100.00, "currency": "RUB", "description": "Test"},
        )

        assert response.status_code == 403

    def test_get_payment_endpoint(
        self,
        client: TestClient,
        mock_get_usecase: AsyncMock,
    ) -> None:
        response = client.get(
            "/api/v1/payments/pay-1",
            headers={"X-API-Key": "secret-api-key"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "pay-1"
        assert data["status"] == "succeeded"

    def test_get_payment_not_found(
        self,
        client: TestClient,
        mock_get_usecase: AsyncMock,
    ) -> None:
        mock_get_usecase.execute.return_value = None

        response = client.get(
            "/api/v1/payments/non-existent",
            headers={"X-API-Key": "secret-api-key"},
        )

        assert response.status_code == 404
