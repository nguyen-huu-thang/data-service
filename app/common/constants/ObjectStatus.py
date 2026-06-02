from enum import StrEnum


class ObjectStatus(StrEnum):
    ACTIVE       = "ACTIVE"
    ARCHIVED     = "ARCHIVED"
    SOFT_DELETED = "SOFT_DELETED"
    PURGED       = "PURGED"
