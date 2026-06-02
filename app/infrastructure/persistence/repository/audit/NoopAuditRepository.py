class NoopAuditRepository:
    """
    Placeholder until Phase 12 creates SqlAlchemyAuditRepository.
    Phase 12: delete this file, create SqlAlchemyAuditRepository,
    and re-bind SaveAuditPort in config/dependency.py.
    """

    async def record(
        self,
        object_id: bytes,
        actor_identity_id: bytes,
        action: str,
    ) -> None:
        pass
