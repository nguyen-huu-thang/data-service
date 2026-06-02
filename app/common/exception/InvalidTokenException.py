class InvalidTokenException(Exception):
    def __init__(self, reason: str = "Invalid token") -> None:
        super().__init__(reason)
