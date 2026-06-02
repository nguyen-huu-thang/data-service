class InvalidShardException(Exception):
    def __init__(self, shard_id: str) -> None:
        super().__init__(f"Invalid or unknown shard: {shard_id}")
        self.shard_id = shard_id
