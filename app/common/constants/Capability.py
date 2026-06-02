from enum import StrEnum


class Capability(StrEnum):
    READ     = "READ"
    WRITE    = "WRITE"
    DELETE   = "DELETE"
    SHARE    = "SHARE"
    DOWNLOAD = "DOWNLOAD"
    COMMENT  = "COMMENT"
