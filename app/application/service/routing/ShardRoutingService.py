from core.config.runtime import RuntimeConfig


class ShardRoutingService:
    def __init__(self, config: RuntimeConfig) -> None:
        self._shard_id: str = config.get("shard.id", "DATA_SHARD_01")

    def compute_shard(self, identity_id: bytes) -> str:
        # MVP: single local shard — all objects placed here
        # Future: hash(identity_id[:4]) % partition_count → shard lookup table
        return self._shard_id
