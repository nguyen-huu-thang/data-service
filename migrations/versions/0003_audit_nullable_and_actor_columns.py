"""make object_audit.object_id nullable and add actor columns

Align the object_audit table with the ObjectAuditEntity / domain model:
  - object_id becomes nullable (subject-level actions are not tied to an object)
  - add actor_subject_type / actor_name (present in the entity, missing in 0001)
  - widen action to String(30) for the fuller AuditAction set

Đồng bộ bảng object_audit với entity/domain: object_id cho phép null (hành động
cấp-subject), thêm actor_subject_type/actor_name, mở rộng action.

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-17
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "object_audit",
        "object_id",
        existing_type=sa.LargeBinary(24),
        nullable=True,
    )
    op.add_column(
        "object_audit",
        sa.Column("actor_subject_type", sa.String(30), nullable=False, server_default="HUMAN"),
    )
    op.add_column(
        "object_audit",
        sa.Column("actor_name", sa.String(255), nullable=False, server_default=""),
    )
    op.alter_column(
        "object_audit",
        "action",
        existing_type=sa.String(20),
        type_=sa.String(30),
    )
    # Drop the temporary server defaults — the application always supplies values.
    op.alter_column("object_audit", "actor_subject_type", server_default=None)
    op.alter_column("object_audit", "actor_name", server_default=None)


def downgrade() -> None:
    op.alter_column(
        "object_audit",
        "action",
        existing_type=sa.String(30),
        type_=sa.String(20),
    )
    op.drop_column("object_audit", "actor_name")
    op.drop_column("object_audit", "actor_subject_type")
    op.alter_column(
        "object_audit",
        "object_id",
        existing_type=sa.LargeBinary(24),
        nullable=False,
    )
