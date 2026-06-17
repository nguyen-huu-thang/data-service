from xime.core.config.runtime import RuntimeConfig

from app.domain.sharedkernel.model.Id import Id
from app.domain.sharedkernel.routing.ShardRouter import ShardRouter


class ShardRoutingService:
    def __init__(self, config: RuntimeConfig, shard_router: ShardRouter) -> None:
        # MVP: single local shard from config. Future: full shard table here.
        # MVP: một shard cục bộ từ config. Tương lai: bảng shard đầy đủ ở đây.
        self._shard_ids: list[str] = [config.get("shard.id", "DATA_SHARD_01")]
        self._router = shard_router

    def compute_shard(self, identity_id: Id) -> str:
        # Application owns config; domain ShardRouter owns the placement rule.
        # Application giữ config; ShardRouter (domain) giữ quy tắc đặt chỗ.
        return self._router.route(identity_id, self._shard_ids)
