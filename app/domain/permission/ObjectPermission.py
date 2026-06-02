from dataclasses import dataclass
from datetime import datetime

from app.common.constants.Capability import Capability
from app.common.constants.Role import Role


# Maps each role to the set of capabilities it grants
# Module-level constant — shared across all ObjectPermission instances
ROLE_CAPABILITIES: dict[Role, frozenset[Capability]] = {
    Role.OWNER: frozenset({
        Capability.READ, Capability.WRITE, Capability.DELETE,
        Capability.SHARE, Capability.DOWNLOAD, Capability.COMMENT,
    }),
    Role.EDITOR: frozenset({
        Capability.READ, Capability.WRITE,
        Capability.DOWNLOAD, Capability.COMMENT,
    }),
    Role.CONTRIBUTOR: frozenset({
        Capability.READ, Capability.WRITE, Capability.COMMENT,
    }),
    Role.VIEWER: frozenset({
        Capability.READ, Capability.DOWNLOAD,
    }),
}


@dataclass(frozen=True)
class ObjectPermission:
    permission_id: bytes        # KSUID 24 bytes
    object_id: bytes            # KSUID 24 bytes
    subject_identity_id: bytes  # KSUID 24 bytes
    role: Role
    created_at: datetime

    def has_capability(self, capability: Capability) -> bool:
        return capability in ROLE_CAPABILITIES.get(self.role, frozenset())
