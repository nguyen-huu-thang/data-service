from enum import StrEnum


class Visibility(StrEnum):
    PRIVATE  = "PRIVATE"
    INTERNAL = "INTERNAL"   # accessible within the same tenant
    PUBLIC   = "PUBLIC"
