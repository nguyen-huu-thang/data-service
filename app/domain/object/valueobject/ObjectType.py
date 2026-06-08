class ObjectType:

    def __init__(
        self,
        value: str,
    ) -> None:
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
        if not isinstance(other, ObjectType):
            return False

        return self._value == other._value