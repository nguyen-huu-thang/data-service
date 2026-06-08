from enum import StrEnum


class Role(StrEnum):
    OWNER = "OWNER"

    EDITOR = "EDITOR"

    VIEWER = "VIEWER"