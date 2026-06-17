"""
Unit tests — IdFactory / Id (KSUID): size, uniqueness, sortability, timestamp.
"""
from datetime import datetime, timezone

from app.domain.sharedkernel.factory.IdFactory import IdFactory
from app.domain.sharedkernel.model.Id import Id


def test_generate_returns_id_of_24_bytes():
    id_ = IdFactory.generate()
    assert isinstance(id_, Id)
    assert len(id_.to_bytes()) == 24
    assert id_.is_24_bytes()


def test_generated_ids_are_unique():
    ids = {IdFactory.generate().to_bytes() for _ in range(1000)}
    assert len(ids) == 1000


def test_later_id_has_greater_or_equal_timestamp_prefix():
    a = IdFactory.generate().to_bytes()
    b = IdFactory.generate().to_bytes()
    # Timestamp occupies the first 4 bytes (second precision) -> b >= a always.
    # Tem thời gian nằm 4 byte đầu (độ chính xác giây) -> b >= a luôn đúng.
    assert b[:4] >= a[:4]


def test_timestamp_is_close_to_now():
    before = datetime.now(timezone.utc)
    ts = IdFactory.generate().get_timestamp()
    after = datetime.now(timezone.utc)
    # Id timestamp is truncated to whole seconds, allow a small window.
    # Tem thời gian của Id làm tròn xuống giây, cho phép sai số nhỏ.
    assert (before - ts).total_seconds() <= 2
    assert (ts - after).total_seconds() <= 2
