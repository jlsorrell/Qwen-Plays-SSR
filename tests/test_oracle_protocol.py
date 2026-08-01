from __future__ import annotations

from collections.abc import Callable

import io
from pathlib import Path

import pytest

from ssr_env.oracle_protocol import (
    MAX_RECORD_BYTES,
    MAX_TRACE_BYTES,
    OracleProtocolError,
    _read_record_lines,
)
from ssr_env.oracle_protocol import _CanonicalJsonReader


def _read_lines(path: Path) -> list[tuple[int, bytes]]:
    with path.open("rb") as stream:
        return list(_read_record_lines(stream, source=str(path)))


def test_record_reader_accepts_lf_terminated_utf8(tmp_path: Path) -> None:
    path = tmp_path / "trace.ndjson"
    path.write_bytes('é/雪\n'.encode("utf-8"))
    assert _read_lines(path) == [(1, 'é/雪'.encode("utf-8"))]


def test_record_reader_rejects_bom(tmp_path: Path) -> None:
    path = tmp_path / "trace.ndjson"
    path.write_bytes(b"\xef\xbb\xbf{}\n")
    with pytest.raises(OracleProtocolError, match="BOM"):
        _read_lines(path)


@pytest.mark.parametrize("payload", [b"{}\r\n", b"{}\r"])
def test_record_reader_rejects_crlf_and_bare_cr(
    tmp_path: Path, payload: bytes
) -> None:
    path = tmp_path / "trace.ndjson"
    path.write_bytes(payload)
    with pytest.raises(OracleProtocolError, match="CR|final LF"):
        _read_lines(path)


def test_record_reader_rejects_missing_final_lf(tmp_path: Path) -> None:
    path = tmp_path / "trace.ndjson"
    path.write_bytes(b"{}")
    with pytest.raises(OracleProtocolError, match="final LF"):
        _read_lines(path)


def test_record_reader_rejects_blank_line(tmp_path: Path) -> None:
    path = tmp_path / "trace.ndjson"
    path.write_bytes(b"{}\n\n")
    with pytest.raises(OracleProtocolError, match="blank"):
        _read_lines(path)


def test_record_reader_rejects_invalid_utf8(tmp_path: Path) -> None:
    path = tmp_path / "trace.ndjson"
    path.write_bytes(b'"\xff"\n')
    with pytest.raises(OracleProtocolError, match="UTF-8"):
        _read_lines(path)


def test_record_reader_accepts_line_exactly_16_mib_including_lf(
    tmp_path: Path,
) -> None:
    path = tmp_path / "trace.ndjson"
    path.write_bytes(b"x" * (MAX_RECORD_BYTES - 1) + b"\n")
    with path.open("rb") as stream:
        records = _read_record_lines(stream, source=str(path))
        line_number, payload = next(records)
        assert line_number == 1
        assert len(payload) == MAX_RECORD_BYTES - 1
        with pytest.raises(StopIteration):
            next(records)


def test_record_reader_rejects_line_over_16_mib_before_decode(
    tmp_path: Path,
) -> None:
    path = tmp_path / "trace.ndjson"
    path.write_bytes(b"x" * MAX_RECORD_BYTES + b"\n")
    with pytest.raises(OracleProtocolError, match="record exceeds"):
        _read_lines(path)


def test_record_reader_accepts_file_exactly_128_mib(tmp_path: Path) -> None:
    path = tmp_path / "trace.ndjson"
    one_line = b"x" * (MAX_RECORD_BYTES - 1) + b"\n"
    with path.open("wb") as stream:
        for _ in range(MAX_TRACE_BYTES // MAX_RECORD_BYTES):
            stream.write(one_line)
    with path.open("rb") as stream:
        assert sum(1 for _ in _read_record_lines(stream, source=str(path))) == 8


def test_record_reader_rejects_file_over_128_mib_before_reading_tail(
    tmp_path: Path,
) -> None:
    path = tmp_path / "trace.ndjson"
    one_line = b"x" * (MAX_RECORD_BYTES - 1) + b"\n"
    with path.open("wb") as stream:
        for _ in range(MAX_TRACE_BYTES // MAX_RECORD_BYTES):
            stream.write(one_line)
        stream.write(b"x")
    with path.open("rb") as stream:
        with pytest.raises(OracleProtocolError, match="trace exceeds"):
            list(_read_record_lines(stream, source=str(path)))


class _ReadSizeRecorder(io.BytesIO):
    def __init__(self, value: bytes) -> None:
        super().__init__(value)
        self.requests: list[int] = []

    def readline(self, size: int = -1, /) -> bytes:
        self.requests.append(size)
        return super().readline(size)


def test_record_reader_never_requests_an_unbounded_read() -> None:
    stream = _ReadSizeRecorder(b"{}\n")
    assert list(_read_record_lines(stream, source="memory")) == [(1, b"{}")]
    assert stream.requests
    assert all(0 < size <= MAX_RECORD_BYTES + 1 for size in stream.requests)


def _read_token(payload: bytes, method_name: str) -> object:
    reader = _CanonicalJsonReader(payload, 1, source="token")
    method = getattr(reader, method_name)
    value = method()
    reader.finish()
    return value


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        (b'"plain"', "plain"),
        ('"é/雪"'.encode("utf-8"), "é/雪"),
        (b'"\\\"\\\\\\b\\f\\n\\r\\t\\u0000\\u001f"', '"\\\b\f\n\r\t\x00\x1f'),
    ],
)
def test_canonical_json_accepts_canonical_strings(
    payload: bytes, expected: str
) -> None:
    assert _read_token(payload, "read_string") == expected


@pytest.mark.parametrize(
    "payload",
    [
        b'"\\/"',
        b'"\\u0061"',
        b'"\\u00AF"',
        b'"\\u0008"',
        b'"\\u000a"',
        b'"\x01"',
        b'"\\v"',
        b'"\\ud800"',
        b'"\\udfff"',
        b'"\xed\xa0\x80"',
    ],
)
def test_canonical_json_rejects_noncanonical_strings(payload: bytes) -> None:
    with pytest.raises(OracleProtocolError):
        _read_token(payload, "read_string")
