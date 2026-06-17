"""
Unit tests — domain enrichment (Phase 5):
  - AccessPolicy pure decision rules
  - ShardRouter deterministic placement
  - Immutable state changes (SubjectPermission, SubjectInfo)
  - Constructor invariants (DataObject, ObjectVersion)
  - ObjectVersion.is_initial()
"""
from datetime import datetime, timezone

import pytest

from app.domain.permission.capability.AclCapability import AclCapability
from app.domain.permission.capability.ObjectCapability import ObjectCapability
from app.domain.permission.model.ObjectPermission import ObjectPermission
from app.domain.permission.model.SubjectPermission import SubjectPermission
from app.domain.permission.policy.AccessPolicy import AccessPolicy
from app.domain.permission.role.Role import Role
from app.domain.subject.model.SubjectInfo import SubjectInfo
from app.domain.subject.valueobject.SubjectType import SubjectType
from app.domain.sharedkernel.model.Id import Id
from app.domain.sharedkernel.routing.ShardRouter import ShardRouter
from app.domain.object.model.ObjectVersion import ObjectVersion
from app.domain.object.valueobject.ObjectVisibility import ObjectVisibility
from test.conftest import OBJECT_ID, OTHER_ID, OWNER_ID, PERM_ID, make_object, make_version

_NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)
_LATER = datetime(2026, 2, 1, tzinfo=timezone.utc)


# ── AccessPolicy ──────────────────────────────────────────────────────────────

def test_policy_owner_is_recognized():
    policy = AccessPolicy()
    obj = make_object(owner_identity_id=OWNER_ID)
    assert policy.is_owner(obj, Id(OWNER_ID)) is True
    assert policy.is_owner(obj, Id(OTHER_ID)) is False


def test_policy_public_allows_read_and_download_only():
    policy = AccessPolicy()
    pub = make_object(visibility=ObjectVisibility.PUBLIC)
    assert policy.public_allows(pub, AclCapability.READ) is True
    assert policy.public_allows(pub, AclCapability.DOWNLOAD) is True
    assert policy.public_allows(pub, AclCapability.WRITE) is False
    priv = make_object(visibility=ObjectVisibility.PRIVATE)
    assert policy.public_allows(priv, AclCapability.READ) is False


def test_policy_required_system_capability_mapping():
    policy = AccessPolicy()
    assert policy.required_system_capability(AclCapability.READ) == ObjectCapability.DATA_READ_ANY
    assert policy.required_system_capability(AclCapability.WRITE) == ObjectCapability.DATA_WRITE_ANY


def test_policy_has_system_capability():
    policy = AccessPolicy()
    sp = SubjectPermission(
        permission_id=Id(PERM_ID),
        subject_identity_id=Id(OTHER_ID),
        subject_type=SubjectType("HUMAN"),
        permission=ObjectCapability.DATA_READ_ANY,
        created_at=_NOW,
        updated_at=_NOW,
    )
    assert policy.has_system_capability([sp], ObjectCapability.DATA_READ_ANY) is True
    assert policy.has_system_capability([sp], ObjectCapability.DATA_WRITE_ANY) is False
    assert policy.has_system_capability([], ObjectCapability.DATA_READ_ANY) is False


def test_policy_acl_allows():
    policy = AccessPolicy()
    perm = ObjectPermission(
        permission_id=Id(PERM_ID),
        object_id=Id(OBJECT_ID),
        subject_identity_id=Id(OTHER_ID),
        subject_type="HUMAN",
        role=Role.VIEWER,
        created_at=_NOW,
    )
    assert policy.acl_allows(perm, AclCapability.READ) is True
    assert policy.acl_allows(perm, AclCapability.WRITE) is False
    assert policy.acl_allows(None, AclCapability.READ) is False


# ── ShardRouter ───────────────────────────────────────────────────────────────

def test_shard_router_single_shard_always_returns_it():
    router = ShardRouter()
    assert router.route(Id(OWNER_ID), ["DATA_SHARD_01"]) == "DATA_SHARD_01"


def test_shard_router_is_deterministic():
    router = ShardRouter()
    shards = ["A", "B", "C"]
    first = router.route(Id(OWNER_ID), shards)
    assert router.route(Id(OWNER_ID), shards) == first


def test_shard_router_empty_raises():
    router = ShardRouter()
    with pytest.raises(ValueError):
        router.route(Id(OWNER_ID), [])


# ── Immutable state changes ───────────────────────────────────────────────────

def test_subject_permission_update_is_immutable():
    sp = SubjectPermission(
        permission_id=Id(PERM_ID),
        subject_identity_id=Id(OTHER_ID),
        subject_type=SubjectType("HUMAN"),
        permission=ObjectCapability.DATA_READ_ANY,
        created_at=_NOW,
        updated_at=_NOW,
    )
    updated = sp.update_permission(ObjectCapability.DATA_WRITE_ANY, _LATER)
    assert updated is not sp
    assert sp.permission == ObjectCapability.DATA_READ_ANY  # original untouched
    assert updated.permission == ObjectCapability.DATA_WRITE_ANY
    assert updated.updated_at == _LATER
    assert updated.permission_id == sp.permission_id


def test_subject_info_update_name_is_immutable():
    si = SubjectInfo(
        identity_id=Id(OWNER_ID),
        subject_type=SubjectType("HUMAN"),
        name="old",
        updated_at=_NOW,
    )
    updated = si.update_name("new", _LATER)
    assert updated is not si
    assert si.name == "old"
    assert updated.name == "new"
    assert updated.updated_at == _LATER


# ── Constructor invariants ────────────────────────────────────────────────────

def test_dataobject_rejects_bad_permission_version():
    with pytest.raises(ValueError):
        make_object(permission_version=0)


def test_dataobject_rejects_empty_shard():
    with pytest.raises(ValueError):
        make_object(shard_id="")


def test_objectversion_rejects_zero_version_number():
    with pytest.raises(ValueError):
        make_version(version_number=0)


def test_objectversion_rejects_negative_size():
    with pytest.raises(ValueError):
        make_version(content_size=-1)


def test_objectversion_is_initial():
    assert make_version(version_number=1).is_initial() is True
    assert make_version(version_number=2).is_initial() is False
