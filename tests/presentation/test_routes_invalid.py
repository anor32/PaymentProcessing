from fastapi.testclient import TestClient


class TestCreatePaymentInvalidData:
    def test_negative_amount_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/payments",
            json={
                "amount": -100.00,
                "currency": "RUB",
                "description": "Test",
            },
            headers={
                "X-API-Key": "secret-api-key",
                "Idempotency-Key": "idem-neg",
            },
        )
        assert (
            response.status_code == 422
        ), f"Expected 422, got {response.status_code}: {response.text}"
        data = response.json()
        assert "detail" in data

    def test_zero_amount_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/payments",
            json={
                "amount": 0,
                "currency": "RUB",
                "description": "Test",
            },
            headers={
                "X-API-Key": "secret-api-key",
                "Idempotency-Key": "idem-zero",
            },
        )
        assert (
            response.status_code == 422
        ), f"Expected 422, got {response.status_code}: {response.text}"

    def test_empty_description_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/payments",
            json={
                "amount": 100.00,
                "currency": "RUB",
                "description": "   ",
            },
            headers={
                "X-API-Key": "secret-api-key",
                "Idempotency-Key": "idem-empty-desc",
            },
        )
        assert (
            response.status_code == 422
        ), f"Expected 422, got {response.status_code}: {response.text}"

    def test_missing_idempotency_key_header_returns_422(
        self,
        client: TestClient,
    ) -> None:
        response = client.post(
            "/api/v1/payments",
            json={
                "amount": 100.00,
                "currency": "RUB",
                "description": "Test",
            },
            headers={
                "X-API-Key": "secret-api-key",
            },
        )
        assert (
            response.status_code == 422
        ), f"Expected 422, got {response.status_code}: {response.text}"

    def test_empty_idempotency_key_returns_400(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/payments",
            json={
                "amount": 100.00,
                "currency": "RUB",
                "description": "Test",
            },
            headers={
                "X-API-Key": "secret-api-key",
                "Idempotency-Key": "",
            },
        )
        assert (
            response.status_code == 400
        ), f"Expected 400, got {response.status_code}: {response.text}"

    def test_invalid_currency_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/payments",
            json={
                "amount": 100.00,
                "currency": "XXX",
                "description": "Test",
            },
            headers={
                "X-API-Key": "secret-api-key",
                "Idempotency-Key": "idem-bad-curr",
            },
        )
        assert (
            response.status_code == 422
        ), f"Expected 422, got {response.status_code}: {response.text}"

    def test_no_500_for_invalid_data(
        self,
        client: TestClient,
    ) -> None:
        """Общая проверка: ни один невалидный запрос не должен возвращать 500."""
        invalid_cases = [
            {"amount": -50, "currency": "RUB", "description": "Test"},
            {"amount": 0, "currency": "RUB", "description": "Test"},
            {"amount": 100, "currency": "RUB", "description": ""},
        ]
        for case in invalid_cases:
            response = client.post(
                "/api/v1/payments",
                json=case,
                headers={
                    "X-API-Key": "secret-api-key",
                    "Idempotency-Key": f"idem-{case.get('amount', 'x')}",
                },
            )
            assert response.status_code != 500, f"Got 500 for {case}: {response.text}"
            assert response.status_code in (
                400,
                422,
            ), f"Unexpected status {response.status_code} for {case}: {response.text}"
