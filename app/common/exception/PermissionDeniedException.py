class PermissionDeniedException(Exception):
    def __init__(self, message: str = "Permission denied") -> None:
        super().__init__(message)
