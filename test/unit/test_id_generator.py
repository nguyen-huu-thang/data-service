"""
Unit tests — KSUID generator: size, uniqueness, sortability, timestamp extraction.
"""
import time

from app.common.util.IdGenerator import KSUID_EPOCH, generate_id, id_timestamp


def test_generate_id_returns_24_bytes():
    assert len(generate_id()) == 24

def test_generated_ids_are_unique():
    ids = {generate_id() for _ in range(1000)}
    assert len(ids) == 1000

def test_later_id_has_greater_or_equal_timestamp_prefix():
    id_a = generate_id()
    id_b = generate_id()
    # Timestamp occupies the first 4 bytes — second-precision, so b >= a always holds.
    # Full-byte comparison is not reliable when both IDs are generated in the same second
    # because the 20-byte random suffix may produce id_b < id_a.
    assert id_b[:4] >= id_a[:4]

def test_id_timestamp_is_close_to_current_time():
    before = int(time.time())
    ksuid = generate_id()
    after = int(time.time())
    extracted = id_timestamp(ksuid)
    assert before <= extracted <= after + 1  # +1 for rounding

def test_id_timestamp_uses_ksuid_epoch():
    ksuid = generate_id()
    ts = id_timestamp(ksuid)
    # Must be after KSUID epoch (May 2014) and before year 2100
    assert ts > KSUID_EPOCH
    assert ts < 4_000_000_000

def test_id_is_bytes_type():
    assert isinstance(generate_id(), bytes)
