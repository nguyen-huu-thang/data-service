class ContentHash:

    def __init__(
        self,
        value: str,
    ) -> None:
        if not value:
            raise ValueError(
                "Content hash cannot be empty",
            )

        self._value = value.lower()

    @property
    def value(self) -> str:
        return self._value

    def __str__(self) -> str:
        return self._value

    def __eq__(
        self,
        other: object,
    ) -> bool:
        if not isinstance(other, ContentHash):
            return False

        return self._value == other._value

    def __hash__(self) -> int:
        return hash(self._value)