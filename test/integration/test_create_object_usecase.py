"""
Integration tests — CreateObjectUseCase end-to-end:
  - Uses real SQLAlchemy repositories (SQLite)
  - BlobStoragePort is mocked (blob tested separately in test_minio_adapter.py)
  - Verifies object, version, and OWNER permission are all created atomically
"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

from app.application.dto.object.CreateObjectCommand import CreateObjectCommand
from app.application.service.audit.AuditService import AuditService
from app.application.usecase.object.CreateObjectUseCase import CreateObjectUseCase
from app.common.constants.ObjectStatus import ObjectStatus
from app.common.constants.ObjectType import ObjectType
from app.common.constants.Role import Role
from app.common.constants.Visibility import Visibility
from app.common.util.IdGenerator import generate_id
from app.infrastructure.persistence.repository.audit.SqlAlchemyAuditRepository import (
    SqlAlchemyAuditRepository,
)
from app.infrastructure.persistence.repository.object.SqlAlchemyObjectRepository import (
    SqlAlchemyObjectRepository,
)
from app.infrastructure.persistence.repository.permission.SqlAlchemyPermissionRepository import (
    SqlAlchemyPermissionRepository,
)
from app.infrastructure.persistence.repository.version.SqlAlchemyVersionRepository import (
    SqlAlchemyVersionRepository,
)
from test.integration.conftest import FakeSessionFactory, fake_transaction

pytestmark = pytest.mark.asyncio

_IMAGE_DATA = b"\xFF\xD8\xFF\xE0" + b"\x00" * 100  # minimal JPEG-ish bytes


def _make_blob_mock(pointer: str = "owner/obj/file.jpg") -> MagicMock:
    blob = MagicMock()
    blob.generate_pointer = AsyncMock(return_value=pointer)
    blob.upload = AsyncMock(return_value=None)
    blob.download = AsyncMock(return_value=_IMAGE_DATA)
    blob.delete = AsyncMock(return_value=None)
    return blob


def _make_routing(shard: str = "DATA_SHARD_01") -> MagicMock:
    routing = MagicMock()
    routing.compute_shard.return_value = shard
    return routing


@pytest_asyncio.fixture
async def use_case_and_repos(db_session):
    sf = FakeSessionFactory(db_session)

    obj_repo  = SqlAlchemyObjectRepository(sf)
    ver_repo  = SqlAlchemyVersionRepository(sf)
    perm_repo = SqlAlchemyPermissionRepository(sf)
    audit_repo = SqlAlchemyAuditRepository(sf)
    audit_svc  = AuditService(audit_repo)
    blob       = _make_blob_mock()

    uc = CreateObjectUseCase(
        transaction=fake_transaction,
        blob_storage=blob,
        save_object=obj_repo,
        save_version=ver_repo,
        save_permission=perm_repo,
        routing_service=_make_routing(),
        audit_service=audit_svc,
    )
    return uc, obj_repo, ver_repo, perm_repo, blob


# ── Happy path ────────────────────────────────────────────────────────────────

async def test_create_object_persists_data_object(use_case_and_repos, db_session):
    uc, obj_repo, *_ = use_case_and_repos
    requester = generate_id()

    result = await uc.execute(CreateObjectCommand(
        requester_identity_id=requester,
        object_type=ObjectType.IMAGE,
        visibility=Visibility.PRIVATE,
        filename="photo.jpg",
        content_type="image/jpeg",
        data=_IMAGE_DATA,
        tenant_id=None,
    ))
    await db_session.flush()

    obj = await obj_repo.find_by_id(result.object_id)
    assert obj is not None
    assert obj.owner_identity_id == requester
    assert obj.status == ObjectStatus.ACTIVE
    assert obj.shard_id == "DATA_SHARD_01"


async def test_create_object_creates_version_1(use_case_and_repos, db_session):
    uc, obj_repo, ver_repo, *_ = use_case_and_repos
    requester = generate_id()

    result = await uc.execute(CreateObjectCommand(
        requester_identity_id=requester,
        object_type=ObjectType.IMAGE,
        visibility=Visibility.PRIVATE,
        filename="photo.jpg",
        content_type="image/jpeg",
        data=_IMAGE_DATA,
        tenant_id=None,
    ))
    await db_session.flush()

    versions = await ver_repo.find_by_object(result.object_id)
    assert len(versions) == 1
    v = versions[0]
    assert v.version_number == 1
    assert v.mime_type == "image/jpeg"
    assert len(v.content_hash) == 64  # SHA-256 hex


async def test_create_object_grants_owner_permission(use_case_and_repos, db_session):
    uc, _, _, perm_repo, _ = use_case_and_repos
    requester = generate_id()

    result = await uc.execute(CreateObjectCommand(
        requester_identity_id=requester,
        object_type=ObjectType.IMAGE,
        visibility=Visibility.PRIVATE,
        filename="photo.jpg",
        content_type="image/jpeg",
        data=_IMAGE_DATA,
        tenant_id=None,
    ))
    await db_session.flush()

    perm = await perm_repo.find_by_subject_and_object(requester, result.object_id)
    assert perm is not None
    assert perm.role == Role.OWNER


async def test_create_object_uploads_blob(use_case_and_repos):
    uc, _, _, _, blob = use_case_and_repos
    requester = generate_id()

    await uc.execute(CreateObjectCommand(
        requester_identity_id=requester,
        object_type=ObjectType.DOCUMENT,
        visibility=Visibility.INTERNAL,
        filename="report.pdf",
        content_type="application/pdf",
        data=b"%PDF-1.4 fake",
        tenant_id="tenant-abc",
    ))

    blob.upload.assert_called_once()
    call_kwargs = blob.upload.call_args
    # Second positional arg is the data
    assert call_kwargs.args[1] == b"%PDF-1.4 fake"


async def test_create_object_current_version_id_set(use_case_and_repos, db_session):
    uc, obj_repo, ver_repo, *_ = use_case_and_repos
    requester = generate_id()

    result = await uc.execute(CreateObjectCommand(
        requester_identity_id=requester,
        object_type=ObjectType.IMAGE,
        visibility=Visibility.PRIVATE,
        filename="img.png",
        content_type="image/png",
        data=_IMAGE_DATA,
        tenant_id=None,
    ))
    await db_session.flush()

    obj = await obj_repo.find_by_id(result.object_id)
    versions = await ver_repo.find_by_object(result.object_id)
    assert obj.current_version_id == versions[0].version_id
