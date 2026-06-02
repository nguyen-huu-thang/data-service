from enum import StrEnum


class ObjectType(StrEnum):
    IMAGE    = "IMAGE"
    VIDEO    = "VIDEO"
    DOCUMENT = "DOCUMENT"
    ARCHIVE  = "ARCHIVE"
    DATASET  = "DATASET"
    AUDIO    = "AUDIO"
    OTHER    = "OTHER"
