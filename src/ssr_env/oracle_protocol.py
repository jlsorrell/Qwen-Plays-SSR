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


_SHORT_ESCAPES = {
    ord('"'): '"',
    ord("\\"): "\\",
    ord("b"): "\b",
    ord("f"): "\f",
    ord("n"): "\n",
    ord("r"): "\r",
    ord("t"): "\t",
}
_SHORT_ESCAPE_CODEPOINTS = frozenset(ord(value) for value in "\b\f\n\r\t")
_LOWER_HEX_BYTES = frozenset(b"0123456789abcdef")


class _CanonicalJsonReader:
    def __init__(
        self, payload: bytes, line_number: int, *, source: str
    ) -> None:
        self._payload = payload
        self._offset = 0
        self.line_number = line_number
        self.source = source

    def _fail(self, message: str, *, offset: int | None = None) -> None:
        error_offset = self._offset if offset is None else offset
        raise OracleProtocolError(
            f"{self.source}: line {self.line_number}, "
            f"byte {error_offset + 1}: {message}"
        )

    def _expect(self, expected: int) -> None:
        if self._offset >= len(self._payload):
            self._fail(f"expected {chr(expected)!r} before end of record")
        if self._payload[self._offset] != expected:
            self._fail(f"expected {chr(expected)!r}")
        self._offset += 1

    def _starts_with(self, token: bytes) -> bool:
        return self._payload.startswith(token, self._offset)

    def read_string(self) -> str:
        self._expect(ord('"'))
        pieces: list[str] = []
        literal_start = self._offset
        while self._offset < len(self._payload):
            byte = self._payload[self._offset]
            if byte == ord('"'):
                pieces.append(self._decode_literal(literal_start, self._offset))
                self._offset += 1
                return "".join(pieces)
            if byte == ord("\\"):
                pieces.append(self._decode_literal(literal_start, self._offset))
                self._offset += 1
                if self._offset >= len(self._payload):
                    self._fail("truncated escape")
                escape = self._payload[self._offset]
                self._offset += 1
                if escape in _SHORT_ESCAPES:
                    pieces.append(_SHORT_ESCAPES[escape])
                elif escape == ord("u"):
                    pieces.append(self._read_control_escape())
                else:
                    self._fail(
                        "noncanonical string escape", offset=self._offset - 1
                    )
                literal_start = self._offset
                continue
            if byte < 0x20:
                self._fail("unescaped control character")
            self._offset += 1
        self._fail("unterminated string")
        raise AssertionError("unreachable")

    def _decode_literal(self, start: int, end: int) -> str:
        try:
            return self._payload[start:end].decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            error_offset = start + exc.start
            raise OracleProtocolError(
                f"{self.source}: line {self.line_number}, "
                f"byte {error_offset + 1}: invalid UTF-8 in string"
            ) from exc

    def _read_control_escape(self) -> str:
        end = self._offset + 4
        if end > len(self._payload):
            self._fail("truncated unicode escape")
        digits = self._payload[self._offset:end]
        if digits[:2] != b"00" or any(
            digit not in _LOWER_HEX_BYTES for digit in digits
        ):
            self._fail("unicode escape is not lowercase \\u00xx")
        codepoint = int(digits, 16)
        if codepoint > 0x1F:
            self._fail("printable characters must use literal UTF-8")
        if codepoint in _SHORT_ESCAPE_CODEPOINTS:
            self._fail("control character requires its short escape")
        self._offset = end
        return chr(codepoint)

    def finish(self) -> None:
        if self._offset != len(self._payload):
            self._fail("trailing bytes after record")
