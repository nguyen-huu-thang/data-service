"""
Integration tests — CreateObjectUseCase end-to-end:
  - Uses real SQLAlchemy repositories (SQLite)
  - StorageService is mocked; a real BlobWriter streams the upload into it
  - Verifies object, version, and OWNER permission are all created atomically
"""
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

from app.application.dto.object.CreateObjectCommand import CreateObjectCommand
from app.application.dto.upload.UploadStream import BytesUploadStream
from app.application.service.audit.AuditService import AuditService
from app.application.service.storage.BlobWriter import BlobWriter
from app.application.service.storage.ObjectKeyPolicy import ObjectKeyPolicy
from app.application.usecase.object.CreateObjectUseCase import CreateObjectUseCase
from app.domain.object.valueobject.ObjectStatus import ObjectStatus
from app.domain.object.valueobject.ObjectType import ObjectType
from app.domain.object.valueobject.ObjectVisibility import ObjectVisibility
from app.domain.permission.role.Role import Role
from app.domain.sharedkernel.factory.IdFactory import IdFactory
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
from test.conftest import mock_runtime_config
from test.integration.conftest import FakeSessionFactory, fake_transaction

pytestmark = pytest.mark.asyncio

_IMAGE_DATA = b"\xFF\xD8\xFF\xE0" + b"\x00" * 100  # minimal JPEG-ish bytes


def _make_storage_mock() -> MagicMock:
    # put_stream drains the chunk iterator (so BlobWriter computes a real hash)
    # and records the streamed bytes under `captured` for assertions.
    # put_stream rút iterator (để BlobWriter tính hash thật) và ghi lại bytes đã
    # stream vào `captured` cho assertion.
    storage = MagicMock()
    storage.captured = {"data": b""}

    async def _put_stream(key, chunks, content_type=None):
        buf = bytearray()
        async for c in chunks:
            buf += c
        storage.captured["data"] = bytes(buf)

    storage.put_stream = AsyncMock(side_effect=_put_stream)
    storage.get = AsyncMock(return_value=_IMAGE_DATA)
    storage.delete = AsyncMock(return_value=None)
    return storage


def _make_routing(shard: str = "DATA_SHARD_01") -> MagicMock:
    routing = MagicMock()
    routing.compute_shard.return_value = shard
    return routing


def _cmd(
    requester,
    *,
    data: bytes = _IMAGE_DATA,
    filename: str = "photo.jpg",
    content_type: str = "image/jpeg",
    object_type: str = "IMAGE",
    visibility: ObjectVisibility = ObjectVisibility.PRIVATE,
    tenant_id: str | None = None,
) -> CreateObjectCommand:
    return CreateObjectCommand(
        requester_identity_id=requester,
        requester_subject_type="HUMAN",
        requester_name="test",
        object_type=ObjectType(object_type),
        visibility=visibility,
        source=BytesUploadStream(data, filename, content_type),
        tenant_id=tenant_id,
    )


@pytest_asyncio.fixture
async def use_case_and_repos(db_session):
    sf = FakeSessionFactory(db_session)

    obj_repo  = SqlAlchemyObjectRepository(sf)
    ver_repo  = SqlAlchemyVersionRepository(sf)
    perm_repo = SqlAlchemyPermissionRepository(sf)
    audit_repo = SqlAlchemyAuditRepository(sf)
    audit_svc  = AuditService(audit_repo)
    storage    = _make_storage_mock()
    blob_writer = BlobWriter(storage, mock_runtime_config())

    uc = CreateObjectUseCase(
        transaction=fake_transaction,
        blob_writer=blob_writer,
        key_policy=ObjectKeyPolicy(),
        save_object=obj_repo,
        save_version=ver_repo,
        save_permission=perm_repo,
        routing_service=_make_routing(),
        audit_service=audit_svc,
    )
    return uc, obj_repo, ver_repo, perm_repo, storage


# ── Happy path ────────────────────────────────────────────────────────────────

async def test_create_object_persists_data_object(use_case_and_repos, db_session):
    uc, obj_repo, *_ = use_case_and_repos
    requester = IdFactory.generate()

    result = await uc.execute(_cmd(requester))
    await db_session.flush()

    obj = await obj_repo.find_by_id(result.object_id)
    assert obj is not None
    assert obj.owner_identity_id == requester
    assert obj.status == ObjectStatus.ACTIVE
    assert obj.shard_id == "DATA_SHARD_01"


async def test_create_object_creates_version_1(use_case_and_repos, db_session):
    uc, obj_repo, ver_repo, *_ = use_case_and_repos
    requester = IdFactory.generate()

    result = await uc.execute(_cmd(requester))
    await db_session.flush()

    versions = await ver_repo.find_by_object(result.object_id)
    assert len(versions) == 1
    v = versions[0]
    assert v.version_number == 1
    assert v.mime_type.value == "image/jpeg"
    assert len(v.content_hash.value) == 64  # SHA-256 hex


async def test_create_object_grants_owner_permission(use_case_and_repos, db_session):
    uc, _, _, perm_repo, _ = use_case_and_repos
    requester = IdFactory.generate()

    result = await uc.execute(_cmd(requester))
    await db_session.flush()

    perm = await perm_repo.find_by_subject_and_object(requester, result.object_id)
    assert perm is not None
    assert perm.role == Role.OWNER


async def test_create_object_uploads_blob(use_case_and_repos):
    uc, _, _, _, storage = use_case_and_repos
    requester = IdFactory.generate()

    await uc.execute(_cmd(
        requester,
        data=b"%PDF-1.4 fake",
        filename="report.pdf",
        content_type="application/pdf",
        object_type="DOCUMENT",
        visibility=ObjectVisibility.INTERNAL,
        tenant_id="tenant-abc",
    ))

    storage.put_stream.assert_called_once()
    # The streamed bytes must match the uploaded content.
    assert storage.captured["data"] == b"%PDF-1.4 fake"


async def test_create_object_current_version_id_set(use_case_and_repos, db_session):
    uc, obj_repo, ver_repo, *_ = use_case_and_repos
    requester = IdFactory.generate()

    result = await uc.execute(_cmd(requester, filename="img.png", content_type="image/png"))
    await db_session.flush()

    obj = await obj_repo.find_by_id(result.object_id)
    versions = await ver_repo.find_by_object(result.object_id)
    assert obj.current_version_id == versions[0].version_id
