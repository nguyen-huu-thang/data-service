"""
Unit tests — error catalog integrity (CI-style guards).

Enforces the platform standard so a future edit cannot silently break it:
  - no duplicate code / errorKey
  - errorKey == "E" + 6-digit zero-padded code
  - every code sits in a valid block (common 0-9999 or data 60000-69999)
  - visibility matches the thousands zone of the in-block offset
    (Private 0-3999 | System 4000-6999 | Public 7000-9999)
"""
from app.domain.error.error_code import ERROR_CODES, generic_for, get_error
from app.domain.error.GrpcCode import GrpcCode
from app.domain.error.Visibility import Visibility

_COMMON = range(0, 10000)
_DATA = range(60000, 70000)


def _zone_visibility(code: int) -> Visibility:
    offset = code % 10000
    if offset < 4000:
        return Visibility.PRIVATE
    if offset < 7000:
        return Visibility.SYSTEM
    return Visibility.PUBLIC


def test_keys_match_their_def():
    for key, ed in ERROR_CODES.items():
        assert ed.error_key == key


def test_no_duplicate_codes():
    codes = [ed.code for ed in ERROR_CODES.values()]
    assert len(codes) == len(set(codes)), "duplicate numeric code in catalog"


def test_error_key_format():
    for ed in ERROR_CODES.values():
        assert ed.error_key == f"E{ed.code:06d}"


def test_codes_in_valid_block():
    for ed in ERROR_CODES.values():
        assert ed.code in _COMMON or ed.code in _DATA, f"{ed.error_key} outside known blocks"


def test_visibility_matches_zone():
    for ed in ERROR_CODES.values():
        assert ed.visibility is _zone_visibility(ed.code), (
            f"{ed.error_key} visibility {ed.visibility} does not match its number zone"
        )


def test_http_and_grpc_types():
    for ed in ERROR_CODES.values():
        assert isinstance(ed.http_status, int)
        assert isinstance(ed.grpc_code, GrpcCode)


def test_unknown_key_falls_back_to_e000000():
    assert get_error("E999999").error_key == "E000000"


def test_generic_for_maps_to_common_public():
    # A SYSTEM/data error collapses to a common Public code of the same status family.
    not_found = get_error("E067000")  # NOT_FOUND
    assert generic_for(not_found).error_key == "E007005"
