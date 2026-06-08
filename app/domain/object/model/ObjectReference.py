from datetime import datetime

from app.domain.object.valueobject.ResourceType import ResourceType


class ObjectReference:

    def __init__(
        self,
        reference_id: bytes,
        object_id: bytes,
        application_identity_id: bytes,
        application_name: str,
        resource_type: ResourceType,
        resource_id: str,
        created_at: datetime,
    ) -> None:
        self._reference_id = reference_id

        self._object_id = object_id

        self._application_identity_id = application_identity_id
        self._application_name = application_name

        self._resource_type = resource_type
        self._resource_id = resource_id

        self._created_at = created_at

    @property
    def reference_id(self) -> bytes:
        return self._reference_id

    @property
    def object_id(self) -> bytes:
        return self._object_id

    @property
    def application_identity_id(self) -> bytes:
        return self._application_identity_id

    @property
    def application_name(self) -> str:
        return self._application_name

    @property
    def resource_type(self) -> ResourceType:
        return self._resource_type

    @property
    def resource_id(self) -> str:
        return self._resource_id

    @property
    def created_at(self) -> datetime:
        return self._created_at