from pydantic import BaseModel

from app.domain.object.valueobject.ObjectTag import ObjectTag


class SetTagsRequest(BaseModel):
    tags: list[str]


class TagListResponse(BaseModel):
    tags: list[str]


class TagRestMapper:
    def to_list_response(self, tags: list[ObjectTag]) -> TagListResponse:
        return TagListResponse(tags=[t.value for t in tags])
