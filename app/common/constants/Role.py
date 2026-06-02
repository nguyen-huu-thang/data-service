from enum import StrEnum


class Role(StrEnum):
    OWNER       = "OWNER"
    EDITOR      = "EDITOR"
    CONTRIBUTOR = "CONTRIBUTOR"
    VIEWER      = "VIEWER"
