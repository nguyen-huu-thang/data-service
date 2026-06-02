from dataclasses import dataclass


@dataclass(frozen=True)
class ShardInfo:
    shard_id: str
    host: str
    port: int
    is_local: bool

    def address(self) -> str:
        return f"{self.host}:{self.port}"
