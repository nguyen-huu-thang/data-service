class ObjectTag:

    def __init__(
        self,
        value: str,
    ) -> None:
        value = value.strip()

        if not value:
            raise ValueError(
                "Object tag cannot be empty",
            )

        if len(value) > 100:
            raise ValueError(
                "Object tag is too long",
            )

        self._value = value

    @property
    def value(self) -> str:
        return self._value

    def __str__(self) -> str:
        return self._value

    def __eq__(
        self,
        other: object,
    ) -> bool:
        if not isinstance(
            other,
            ObjectTag,
        ):
            return False

        return self._value == other._value

    def __hash__(self) -> int:
        return hash(
            self._value,
        )