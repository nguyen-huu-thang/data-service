import os
import struct
import time

# KSUID epoch: May 13, 2014 (Unix timestamp 1_400_000_000)
# Same convention as identity-service and user-service
KSUID_EPOCH = 1_400_000_000


def generate_id() -> bytes:
    """Generate a 24-byte KSUID: 4 bytes timestamp + 20 bytes random."""
    ts = int(time.time()) - KSUID_EPOCH
    return struct.pack(">I", ts) + os.urandom(20)


def id_to_hex(ksuid: bytes) -> str:
    return ksuid.hex()


def id_timestamp(ksuid: bytes) -> int:
    """Return Unix timestamp embedded in the KSUID."""
    return struct.unpack(">I", ksuid[:4])[0] + KSUID_EPOCH
