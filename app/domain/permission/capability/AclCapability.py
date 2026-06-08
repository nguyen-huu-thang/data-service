from enum import StrEnum


class AclCapability(StrEnum):
    READ = "READ"
    WRITE = "WRITE"
    DELETE = "DELETE"
    SHARE = "SHARE"
    DOWNLOAD = "DOWNLOAD"
