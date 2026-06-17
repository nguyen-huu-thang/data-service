"""
Unit tests — tag use cases (set / list). Ports mocked; no DB.
"""
from unittest.mock import AsyncMock, MagicMock

import pytest

from test._app_errors import raises_app

from app.application.dto.tag.ListObjectTagsQuery import ListObjectTagsQuery
from app.application.dto.tag.SetObjectTagsCommand import SetObjectTagsCommand
from app.application.usecase.tag.ListObjectTagsUseCase import ListObjectTagsUseCase
from app.application.usecase.tag.SetObjectTagsUseCase import SetObjectTagsUseCase
from app.domain.object.valueobject.ObjectTag import ObjectTag
from app.domain.sharedkernel.model.Id import Id
from test.conftest import OBJECT_ID, OTHER_ID, OWNER_ID, make_object, mock_audit, mock_auth, mock_tx

pytestmark = pytest.mark.asyncio


def _set_uc(*, obj=None, auth_allow=True):
    load = MagicMock(); load.find_by_id = AsyncMock(return_value=obj)
    repo = MagicMock(); repo.replace_tags = AsyncMock()
    uc = SetObjectTagsUseCase(mock_tx(), load, repo, mock_auth(allow=auth_allow), mock_audit())
    return uc, repo


def _cmd(tags, requester=OWNER_ID):
    return SetObjectTagsCommand(Id(requester), "HUMAN", "t", Id(OBJECT_ID), tags)


async def test_set_tags_replaces_deduped():
    uc, repo = _set_uc(obj=make_object())
    await uc.execute(_cmd(["a", "b", "a", " b "]))
    repo.replace_tags.assert_called_once()
    passed = repo.replace_tags.call_args.args[1]
    assert [t.value for t in passed] == ["a", "b"]


async def test_set_tags_empty_clears():
    uc, repo = _set_uc(obj=make_object())
    await uc.execute(_cmd([]))
    passed = repo.replace_tags.call_args.args[1]
    assert passed == []


async def test_set_tags_invalid_raises():
    uc, repo = _set_uc(obj=make_object())
    with raises_app("E007001"):
        await uc.execute(_cmd(["   "]))  # blank tag invalid
    repo.replace_tags.assert_not_called()


async def test_set_tags_not_found():
    uc, _ = _set_uc(obj=None)
    with raises_app("E067000"):
        await uc.execute(_cmd(["a"]))


async def test_set_tags_permission_denied():
    uc, _ = _set_uc(obj=make_object(), auth_allow=False)
    with raises_app("E007004"):
        await uc.execute(_cmd(["a"], requester=OTHER_ID))


async def test_list_tags_returns_repo_result():
    load = MagicMock(); load.find_by_id = AsyncMock(return_value=make_object())
    repo = MagicMock(); repo.find_tags = AsyncMock(return_value=[ObjectTag("x")])
    uc = ListObjectTagsUseCase(load, repo, mock_auth())
    result = await uc.execute(ListObjectTagsQuery(Id(OWNER_ID), "HUMAN", "t", Id(OBJECT_ID)))
    assert [t.value for t in result] == ["x"]
