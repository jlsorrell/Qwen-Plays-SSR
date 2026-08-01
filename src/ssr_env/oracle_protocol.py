from __future__ import annotations

from typing import BinaryIO, Iterator

SCHEMA_VERSION = 1
MAX_RECORD_BYTES = 16 * 1024 * 1024
MAX_TRACE_BYTES = 128 * 1024 * 1024
EXPECTED_INPUT_COUNT = 3
EXPECTED_ASSEMBLY_SHA256 = (
    "886660b51e0cc6358c8a2cd194d2fc7f2d26303c19dfb307d93b53a2fda1c564"
)


class OracleProtocolError(ValueError):
    """The trace is not canonical schema-v1 oracle evidence."""


def _read_record_lines(
    stream: BinaryIO, *, source: str
) -> Iterator[tuple[int, bytes]]:
    total_bytes = 0
    line_number = 0
    while True:
        remaining = MAX_TRACE_BYTES - total_bytes
        read_limit = min(MAX_RECORD_BYTES, remaining) + 1
        try:
            framed = stream.readline(read_limit)
        except OSError as exc:
            raise OracleProtocolError(f"{source}: trace read failed: {exc}") from exc
        if framed == b"":
            return

        line_number += 1
        total_bytes += len(framed)
        if total_bytes > MAX_TRACE_BYTES:
            raise OracleProtocolError(
                f"{source}: trace exceeds {MAX_TRACE_BYTES} bytes"
            )
        if len(framed) > MAX_RECORD_BYTES:
            raise OracleProtocolError(
                f"{source}: line {line_number}: record exceeds "
                f"{MAX_RECORD_BYTES} bytes including LF"
            )
        if not framed.endswith(b"\n"):
            raise OracleProtocolError(
                f"{source}: line {line_number}: record is missing final LF"
            )
        if b"\r" in framed:
            raise OracleProtocolError(
                f"{source}: line {line_number}: CR is not canonical"
            )

        payload = framed[:-1]
        if payload == b"":
            raise OracleProtocolError(f"{source}: line {line_number}: blank line")
        if line_number == 1 and payload.startswith(b"\xef\xbb\xbf"):
            raise OracleProtocolError(f"{source}: line 1: UTF-8 BOM is forbidden")
        try:
            payload.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise OracleProtocolError(
                f"{source}: line {line_number}: invalid UTF-8"
            ) from exc
        yield line_number, payload
