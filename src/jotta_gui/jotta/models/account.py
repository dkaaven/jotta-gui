from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AccountStatus:
    email: str | None
    fullname: str | None
    hostname: str | None
    brand: str | None

    capacity: int | None
    usage: int | None
    subscription_code: int | None
    subscription_name: str | None
    product_name: str | None

    device_name: str | None
    device_type: int | None
