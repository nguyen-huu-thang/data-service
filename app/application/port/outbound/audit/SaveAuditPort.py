from typing import Protocol


class SaveAuditPort(Protocol):
    async def record(
        self,
        object_id: bytes,
        actor_identity_id: bytes,
        action: str,
    ) -> None: ...
