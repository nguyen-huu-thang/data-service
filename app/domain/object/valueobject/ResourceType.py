from enum import StrEnum


class ResourceType(StrEnum):
    USER = "USER"

    POST = "POST"

    COMMENT = "COMMENT"

    MESSAGE = "MESSAGE"

    PRODUCT = "PRODUCT"

    ORDER = "ORDER"

    PROFILE = "PROFILE"

    DOCUMENT = "DOCUMENT"