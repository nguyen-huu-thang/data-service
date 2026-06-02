class ObjectNotFoundException(Exception):
    def __init__(self, object_id: bytes) -> None:
        super().__init__(f"Object not found: {object_id.hex()}")
        self.object_id = object_id
