from app.domain.sharedkernel.model.Id import Id


class ShardRouter:
    """
    Pure domain rule that maps an owner identity to a data shard.

    Placement is immutable: the same identity always routes to the same shard
    for a given shard set. The application layer supplies the configured shard
    ids; the routing math lives here so it stays framework-neutral and testable.

    Quy tắc domain thuần ánh xạ identity chủ sở hữu -> data shard. Vị trí bất biến:
    cùng identity luôn route về cùng shard với một tập shard cho trước. Tầng
    application cấp danh sách shard từ config; phép tính route nằm ở đây để giữ
    domain trung lập framework và dễ test.
    """

    def route(self, identity_id: Id, shard_ids: list[str]) -> str:
        if not shard_ids:
            raise ValueError("shard_ids must not be empty")

        # Deterministic placement from the identity's leading bytes.
        # With a single shard this always returns that shard.
        # Đặt chỗ tất định từ các byte đầu của identity. Một shard -> luôn trả shard đó.
        index = int.from_bytes(identity_id.to_bytes()[:4], byteorder="big") % len(shard_ids)
        return shard_ids[index]
