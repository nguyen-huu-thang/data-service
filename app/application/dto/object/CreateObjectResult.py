from dataclasses import dataclass


@dataclass(frozen=True)
class CreateObjectResult:
    object_id: bytes
    shard_id: str
    storage_pointer: str
