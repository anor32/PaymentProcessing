from src.domain.value_objects.payment_objects import Currency, PaymentStatus


class TestPaymentStatus:
    def test_values(self) -> None:
        assert PaymentStatus.PENDING.value == "pending"
        assert PaymentStatus.SUCCEEDED.value == "succeeded"
        assert PaymentStatus.FAILED.value == "failed"

    def test_str_enum(self) -> None:
        assert PaymentStatus.PENDING == "pending"


class TestCurrency:
    def test_values(self) -> None:
        assert Currency.RUB.value == "RUB"
        assert Currency.USD.value == "USD"
        assert Currency.EUR.value == "EUR"

    def test_str_enum(self) -> None:
        assert Currency.RUB == "RUB"
