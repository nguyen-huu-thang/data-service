class InvalidObjectStateException(Exception):
    def __init__(self, current: str, target: str) -> None:
        super().__init__(f"Cannot transition from {current} to {target}")
        self.current = current
        self.target = target
