"""create initial tables

Revision ID: 0001
Revises:
Create Date: 2026-06-02
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------ #
    # data_object — bảng trung tâm                                        #
    # ------------------------------------------------------------------ #
    op.create_table(
        "data_object",
        sa.Column("object_id",          sa.LargeBinary(24), nullable=False),
        sa.Column("owner_identity_id",  sa.LargeBinary(24), nullable=False),
        sa.Column("tenant_id",          sa.String(100),     nullable=True),
        sa.Column("shard_id",           sa.String(30),      nullable=False),
        sa.Column("object_type",        sa.String(20),      nullable=False),
        sa.Column("visibility",         sa.String(20),      nullable=False),
        sa.Column("status",             sa.String(20),      nullable=False),
        sa.Column("current_version_id", sa.LargeBinary(24), nullable=True),
        sa.Column("storage_provider",   sa.String(20),      nullable=False),
        sa.Column("storage_pointer",    sa.String(500),     nullable=False),
        sa.Column("metadata_json",      sa.JSON(),          nullable=True),
        sa.Column("permission_version", sa.Integer(),       nullable=False, server_default="1"),
        sa.Column("created_at",         sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at",         sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("object_id"),
    )
    op.create_index(
        "ix_data_object_owner_tenant_status_type",
        "data_object",
        ["owner_identity_id", "tenant_id", "status", "object_type"],
    )

    # ------------------------------------------------------------------ #
    # object_version — lịch sử phiên bản nội dung                        #
    # ------------------------------------------------------------------ #
    op.create_table(
        "object_version",
        sa.Column("version_id",      sa.LargeBinary(24), nullable=False),
        sa.Column("object_id",       sa.LargeBinary(24), nullable=False),
        sa.Column("version_number",  sa.Integer(),       nullable=False),
        sa.Column("storage_pointer", sa.String(500),     nullable=False),
        sa.Column("content_hash",    sa.String(64),      nullable=False),
        sa.Column("content_size",    sa.BigInteger(),    nullable=False),
        sa.Column("mime_type",       sa.String(100),     nullable=False),
        sa.Column("created_by",      sa.LargeBinary(24), nullable=False),
        sa.Column("created_at",      sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("version_id"),
        sa.ForeignKeyConstraint(
            ["object_id"], ["data_object.object_id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint("object_id", "version_number", name="uq_object_version_number"),
    )
    op.create_index("ix_object_version_object_id", "object_version", ["object_id"])

    # ------------------------------------------------------------------ #
    # object_permission — ACL: ai có quyền gì trên object                 #
    # ------------------------------------------------------------------ #
    op.create_table(
        "object_permission",
        sa.Column("permission_id",       sa.LargeBinary(24), nullable=False),
        sa.Column("object_id",           sa.LargeBinary(24), nullable=False),
        sa.Column("subject_identity_id", sa.LargeBinary(24), nullable=False),
        sa.Column("role",                sa.String(20),      nullable=False),
        sa.Column("created_at",          sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("permission_id"),
        sa.ForeignKeyConstraint(
            ["object_id"], ["data_object.object_id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint(
            "subject_identity_id", "object_id", name="uq_permission_subject_object"
        ),
    )
    op.create_index(
        "ix_object_permission_subject_object",
        "object_permission",
        ["subject_identity_id", "object_id"],
    )

    # ------------------------------------------------------------------ #
    # object_audit — audit trail (không có FK — bản ghi sống lâu hơn object) #
    # ------------------------------------------------------------------ #
    op.create_table(
        "object_audit",
        sa.Column("audit_id",          sa.LargeBinary(24), nullable=False),
        sa.Column("object_id",         sa.LargeBinary(24), nullable=False),
        sa.Column("actor_identity_id", sa.LargeBinary(24), nullable=False),
        sa.Column("action",            sa.String(20),      nullable=False),
        sa.Column("created_at",        sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("audit_id"),
    )
    op.create_index("ix_object_audit_object_id", "object_audit", ["object_id"])
    op.create_index("ix_object_audit_actor",     "object_audit", ["actor_identity_id"])


def downgrade() -> None:
    op.drop_table("object_audit")
    op.drop_index("ix_object_permission_subject_object", table_name="object_permission")
    op.drop_table("object_permission")
    op.drop_index("ix_object_version_object_id", table_name="object_version")
    op.drop_table("object_version")
    op.drop_index("ix_data_object_owner_tenant_status_type", table_name="data_object")
    op.drop_table("data_object")
