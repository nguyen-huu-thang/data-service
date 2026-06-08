class ShareToken:

    def __init__(
        self,
        value: str,
    ) -> None:
        if not value:
            raise ValueError("Share token cannot be empty")

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
        if not isinstance(other, ShareToken):
            return False

        return self._value == other._value

    def __hash__(self) -> int:
        return hash(self._value)