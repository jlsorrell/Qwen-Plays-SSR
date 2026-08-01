# SSR Passive Trace Protocol Validator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a bounded, canonical schema-v1 Python parser and success validator for passive SSR traces, together with a deterministic CLI and synthetic cross-language contract fixtures.

**Architecture:** A bounded framing layer consumes either an authenticated open binary descriptor or a path opened by a thin convenience wrapper. A hand-written lexical reader validates canonical JSON before immutable record decoding; sequence validation and the three-step relational gate remain separate so a terminal-error trace stays inspectable without becoming a success.

**Tech Stack:** Python 3.12+, standard library only, pytest, dataclasses, pathlib, hand-written bounded JSON lexical validation.

## Global Constraints

- The authoritative design is `docs/superpowers/specs/2026-07-31-oracle-passive-trace-capture-design.md`, especially sections 7 and 9.
- This plan is offline-only. Do not deploy to, mutate, or launch the installed game.
- Accept only schema version `1`, mode `passive`, plugin version `0.2.0`, expected input count `3`, and game assembly SHA-256 `886660b51e0cc6358c8a2cd194d2fc7f2d26303c19dfb307d93b53a2fda1c564`.
- Treat `raw_save` as an opaque string. Do not parse entities, normalize identities, compare against the simulator, or add replay behavior.
- Each NDJSON record is compact canonical JSON with no insignificant whitespace, one LF terminator, literal UTF-8 for valid non-control Unicode, and the exact key order from the design.
- The 16 MiB record bound includes the LF. The 128 MiB file bound includes every byte. Reject before an unbounded allocation.
- Reject a BOM, CR or CRLF, missing final LF, blank line, invalid UTF-8, unpaired surrogate, optional `\/`, optional printable `\u` escapes, noncanonical control escape, duplicate/reordered/unknown key, noncanonical integer, float, non-finite number, and boolean where an integer is required.
- Preserve the exact seven-fractional-digit UTC timestamp text; Python's six-digit `datetime` precision must not silently truncate it. Timestamp digits are ASCII `[0-9]`, never Unicode `\d`.
- `read_oracle_trace_stream(stream, *, source)` is the descriptor-authenticated parser entry point. `read_oracle_trace(path)` only opens the named path and delegates with that already-open descriptor.
- Both parser entry points accept a well-formed success or terminal-error shape. `require_passive_success(trace)` is the only operation that applies the three-step success relation.
- The CLI contract is fixed here: default mode returns `0` only for relational success, `1` for a structurally valid non-success trace, and `2` for malformed input or invalid arguments. `--structural-only` returns `0` for either structurally valid terminal shape while printing its explicit `outcome`.
- Use strict TDD: add each task's named behavioral RED cohort, run it against the task base and observe the stated RED, make the minimum production change, then rerun GREEN before committing. Rows explicitly labeled as inherited or integration coverage may begin GREEN and do not substitute for that task's behavioral RED.

## File map

- Create `src/ssr_env/oracle_protocol.py`: bounded framing, canonical lexical parsing, immutable models, record and sequence validation, relational gate, and CLI `main`.
- Create `tools/oracle_trace_check.py`: import-only executable wrapper around `ssr_env.oracle_protocol.main`.
- Create `tests/test_oracle_protocol.py`: unit, boundary, descriptor-authentication, schema, relation, and CLI regressions.
- Create `tests/fixtures/oracle_trace/passive-success.ndjson`: exact six-record synthetic success contract.
- Create `tests/fixtures/oracle_trace/passive-error.ndjson`: exact four-record synthetic terminal-error contract.

---

### Task 1: Frame bounded records from an already-open descriptor

**Files:**
- Create: `src/ssr_env/oracle_protocol.py`
- Create: `tests/test_oracle_protocol.py`

**Interfaces:**
- Consumes: no earlier code interface; only design sections 7 and 9 and the standard `BinaryIO.readline(size)` contract.
- Produces: `OracleProtocolError(ValueError)`.
- Produces: `_read_record_lines(stream: BinaryIO, *, source: str) -> Iterator[tuple[int, bytes]]`.
- Produces: `SCHEMA_VERSION`, `MAX_RECORD_BYTES`, `MAX_TRACE_BYTES`, `EXPECTED_INPUT_COUNT`, and `EXPECTED_ASSEMBLY_SHA256`.
- Internal consumers: Tasks 2–20 use the error/constants; Task 15 calls `_read_record_lines` with an already-open descriptor.
- External plan link: `docs/superpowers/plans/2026-07-31-oracle-passive-trace-implementation.md`, Task 1 executes and reviews this task; no private framing helper is imported cross-plan.

- [ ] **Step 1: Write the RED framing tests**

Create `tests/test_oracle_protocol.py` with exactly:

```python
from __future__ import annotations

import io
from pathlib import Path

import pytest

from ssr_env.oracle_protocol import (
    MAX_RECORD_BYTES,
    MAX_TRACE_BYTES,
    OracleProtocolError,
    _read_record_lines,
)


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
```

- [ ] **Step 2: Run the framing cohort and confirm RED**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py -k 'record_reader'
```

Expected: collection fails with `ModuleNotFoundError: No module named 'ssr_env.oracle_protocol'`. An out-of-memory result is not the required RED.

- [ ] **Step 3: Implement the bounded descriptor framing function**

Create `src/ssr_env/oracle_protocol.py` with exactly:

```python
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
```

- [ ] **Step 4: Run framing GREEN**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py -k 'record_reader'
git diff --check
```

Expected: `12 passed`; `git diff --check` prints nothing and exits `0`.

- [ ] **Step 5: Commit the bounded framing implementation**

Commit:

```bash
git add src/ssr_env/oracle_protocol.py tests/test_oracle_protocol.py
git commit -m "feat: bound oracle trace framing"
```

---

### Task 2: Parse canonical JSON strings

**Files:**
- Modify: `src/ssr_env/oracle_protocol.py`
- Modify: `tests/test_oracle_protocol.py`

**Interfaces:**
- Consumes: `OracleProtocolError(ValueError)` from Task 1.
- Produces: `_CanonicalJsonReader(payload: bytes, line_number: int, *, source: str)`, `read_string() -> str`, and `finish() -> None`.
- Internal consumer: Task 3 in this plan extends the same class with scalar/object methods.
- External plan link: `docs/superpowers/plans/2026-07-31-oracle-passive-trace-implementation.md`, Task 1 executes and reviews this task; no cross-plan API leaves this task yet.

- [ ] **Step 1: Add RED string-token tests**

Append exactly to `tests/test_oracle_protocol.py`:

```python
from collections.abc import Callable

from ssr_env.oracle_protocol import _CanonicalJsonReader


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
```

- [ ] **Step 2: Run string-token tests and confirm RED**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py -k 'canonical_json and strings'
```

Expected: collection fails with `ImportError: cannot import name '_CanonicalJsonReader'`.

- [ ] **Step 3: Implement only the canonical string reader**

Append exactly to `src/ssr_env/oracle_protocol.py`:

```python
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

    def _fail(self, message: str) -> None:
        raise OracleProtocolError(
            f"{self.source}: line {self.line_number}, "
            f"byte {self._offset + 1}: {message}"
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
                    self._fail("noncanonical string escape")
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
            self._fail("invalid UTF-8 in string")
            raise AssertionError("unreachable") from exc

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
```

- [ ] **Step 4: Run string GREEN**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py -k 'canonical_json and strings'
git diff --check
```

Expected: `13 passed`; `git diff --check` prints nothing and exits `0`.

- [ ] **Step 5: Commit the canonical string reader**

Commit:

```bash
git add src/ssr_env/oracle_protocol.py tests/test_oracle_protocol.py
git commit -m "feat: parse canonical oracle strings"
```

---

### Task 3: Parse bounded canonical JSON scalars and objects

**Files:**
- Modify: `src/ssr_env/oracle_protocol.py`
- Modify: `tests/test_oracle_protocol.py`

**Interfaces:**
- Consumes: `_CanonicalJsonReader(payload: bytes, line_number: int, *, source: str)`, `read_string() -> str`, and `finish() -> None` from Task 2.
- Produces: `read_object(fields: Sequence[tuple[str, Callable[[], object]]]) -> dict[str, object]`, `read_integer() -> int`, `read_boolean() -> bool`, `read_null() -> None`, and `read_optional(reader: Callable[[], object]) -> object | None`.
- Internal consumers: Tasks 6–14 in this plan use these exact methods.
- External plan link: `docs/superpowers/plans/2026-07-31-oracle-passive-trace-implementation.md`, Task 1 executes and reviews this task; no private lexical method is imported cross-plan.

- [ ] **Step 1: Add RED integer, literal, object, and long-lexeme tests**

Append exactly to `tests/test_oracle_protocol.py`:

```python
@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        (b"0", 0),
        (b"1", 1),
        (b"-1", -1),
        (b"2147483647", 2147483647),
        (b"-2147483648", -2147483648),
    ],
)
def test_canonical_json_accepts_signed_32_bit_integers(
    payload: bytes, expected: int
) -> None:
    assert _read_token(payload, "read_integer") == expected


@pytest.mark.parametrize(
    "payload",
    [
        b"-0",
        b"+0",
        b"00",
        b"01",
        b"1.0",
        b"1e0",
        b"NaN",
        b"Infinity",
        b"true",
        b"2147483648",
        b"-2147483649",
    ],
)
def test_canonical_json_rejects_noncanonical_integers(payload: bytes) -> None:
    with pytest.raises(OracleProtocolError):
        _read_token(payload, "read_integer")


@pytest.mark.parametrize("payload", [b"9" * 100_000, b"-" + b"9" * 100_000])
def test_canonical_json_rejects_long_integer_before_conversion(
    payload: bytes,
) -> None:
    with pytest.raises(
        OracleProtocolError, match="integer lexeme exceeds 11 bytes"
    ):
        _read_token(payload, "read_integer")


@pytest.mark.parametrize(
    ("payload", "method_name", "expected"),
    [
        (b"true", "read_boolean", True),
        (b"false", "read_boolean", False),
        (b"null", "read_null", None),
    ],
)
def test_canonical_json_accepts_exact_literals(
    payload: bytes, method_name: str, expected: object
) -> None:
    assert _read_token(payload, method_name) is expected


def _read_pair(payload: bytes) -> dict[str, object]:
    reader = _CanonicalJsonReader(payload, 4, source="pair")
    values = reader.read_object(
        (("count", reader.read_integer), ("ready", reader.read_boolean))
    )
    reader.finish()
    return values


def test_canonical_json_accepts_compact_ordered_object() -> None:
    assert _read_pair(b'{"count":1,"ready":false}') == {
        "count": 1,
        "ready": False,
    }


@pytest.mark.parametrize(
    "payload",
    [
        b'{"ready":false,"count":1}',
        b'{"count":1,"count":1}',
        b'{"count":1,"extra":false}',
        b'{"count":1}',
        b'{"count":1,"ready":false,"extra":0}',
        b'{ "count":1,"ready":false}',
        b'{"count" :1,"ready":false}',
        b'{"count": 1,"ready":false}',
        b'{"count":1, "ready":false}',
        b'{"count":1,"ready":false }',
        b'{"count":1,"ready":false}\t',
    ],
)
def test_canonical_json_rejects_noncanonical_objects(payload: bytes) -> None:
    with pytest.raises(OracleProtocolError):
        _read_pair(payload)


def test_canonical_json_optional_reads_null_or_value() -> None:
    null_reader = _CanonicalJsonReader(b"null", 1, source="optional")
    assert null_reader.read_optional(null_reader.read_string) is None
    null_reader.finish()

    value_reader = _CanonicalJsonReader(b'"North"', 1, source="optional")
    assert value_reader.read_optional(value_reader.read_string) == "North"
    value_reader.finish()
```

- [ ] **Step 2: Run scalar/object tests and confirm RED**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py -k 'canonical_json and not strings'
```

Expected: every selected test fails with `AttributeError` naming the first missing scalar/object method; the process must not raise Python's decimal-conversion-limit `ValueError`.

- [ ] **Step 3: Add the bounded scalar/object methods**

Change the typing import in `src/ssr_env/oracle_protocol.py` to:

```python
from collections.abc import Callable, Sequence
from typing import BinaryIO, Iterator
```

Insert exactly before `_CanonicalJsonReader.finish`:

```python
    def read_object(
        self, fields: Sequence[tuple[str, Callable[[], object]]]
    ) -> dict[str, object]:
        self._expect(ord("{"))
        values: dict[str, object] = {}
        for index, (expected_key, read_value) in enumerate(fields):
            if index != 0:
                self._expect(ord(","))
            actual_key = self.read_string()
            if actual_key != expected_key:
                self._fail(
                    f"expected key {expected_key!r}, got {actual_key!r}"
                )
            self._expect(ord(":"))
            values[expected_key] = read_value()
        self._expect(ord("}"))
        return values

    def read_integer(self) -> int:
        start = self._offset
        while (
            self._offset < len(self._payload)
            and self._payload[self._offset] not in (ord(","), ord("}"))
        ):
            if self._offset - start >= 11:
                self._fail("integer lexeme exceeds 11 bytes")
            self._offset += 1
        token = self._payload[start:self._offset]
        if token == b"0":
            value = 0
        elif token.startswith(b"-"):
            digits = token[1:]
            if not digits or digits[0] == ord("0") or not digits.isdigit():
                self._fail("noncanonical integer")
            value = -int(digits)
        else:
            if not token or token[0] == ord("0") or not token.isdigit():
                self._fail("noncanonical integer")
            value = int(token)
        if not -(2**31) <= value <= 2**31 - 1:
            self._fail("integer is outside signed 32-bit range")
        return value

    def read_boolean(self) -> bool:
        if self._starts_with(b"true"):
            self._offset += 4
            return True
        if self._starts_with(b"false"):
            self._offset += 5
            return False
        self._fail("expected boolean")
        raise AssertionError("unreachable")

    def read_null(self) -> None:
        if not self._starts_with(b"null"):
            self._fail("expected null")
        self._offset += 4
        return None

    def read_optional(self, reader: Callable[[], object]) -> object | None:
        if self._starts_with(b"null"):
            return self.read_null()
        return reader()
```

- [ ] **Step 4: Run scalar/object GREEN**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py -k 'canonical_json and not strings'
git diff --check
```

Expected: `34 passed`; both long-decimal cases fail at the explicit 11-byte guard before `int`; `git diff --check` prints nothing and exits `0`.

- [ ] **Step 5: Commit the bounded scalar/object reader**

Commit:

```bash
git add src/ssr_env/oracle_protocol.py tests/test_oracle_protocol.py
git commit -m "feat: parse bounded canonical oracle scalars"
```

---

### Task 4: Define immutable protocol records and the private error table

**Files:**
- Modify: `src/ssr_env/oracle_protocol.py`
- Modify: `tests/test_oracle_protocol.py`

**Interfaces:**
- Consumes: no protocol callable; Task 3 guarantees `read_integer() -> int`, `read_boolean() -> bool`, `read_string() -> str`, and `read_optional(reader: Callable[[], object]) -> object | None`, which define the field value types modeled here.
- Produces: `InputName`, `TerminalOutcome`, `RecordKind`, `INPUT_NAMES: frozenset[str]`, `RunHeader`, `OracleCapture`, `InitialRecord`, `StepRecord`, `EndRecord`, `ErrorRecord`, `OracleRun`, `OracleRecord`, and `_DecodedLine`.
- Produces: private immutable `_ERROR_MESSAGES: Mapping[str, str]`; no mutable alias to its backing dictionary exists.
- Internal consumers: Tasks 6–26 in this plan consume these dataclasses; Task 14 consumes `_ERROR_MESSAGES` privately.
- External consumers: `docs/superpowers/plans/2026-07-31-oracle-passive-probe.md`, Task 10A imports `OracleRun`, `ErrorRecord`, and `OracleProtocolError`; `docs/superpowers/plans/2026-07-31-oracle-passive-trace-implementation.md`, Task 1 executes this task.

- [ ] **Step 1: Add RED immutable-model tests**

Append exactly to `tests/test_oracle_protocol.py`:

```python
from dataclasses import FrozenInstanceError

from ssr_env.oracle_protocol import (
    EndRecord,
    ErrorRecord,
    InitialRecord,
    OracleCapture,
    OracleRun,
    RunHeader,
    StepRecord,
    _ERROR_MESSAGES,
)


def test_protocol_model_is_frozen_slotted_and_complete() -> None:
    capture = OracleCapture(
        raw_save="save",
        state_identity="-17",
        level="level",
        overworld=False,
        won=False,
        returning=False,
        have_ever_cooked_all=False,
        lost_reason="",
        display_name="name",
        sausages_cooked=0,
        movement_count=0,
        pushes_to_try=0,
    )
    initial = InitialRecord(capture=capture)
    step = StepRecord(
        input_index=0,
        input="West",
        accepted=True,
        movement_scheduled=True,
        settle_frames=2,
        state_replaced=False,
        capture=capture,
    )
    end = EndRecord(
        input_count=3,
        finished_at_utc="2026-07-31T19:11:00.0000000Z",
    )
    trace = OracleRun(
        header=RunHeader(
            run_id="0123456789abcdef0123456789abcdef",
            game_assembly_sha256=(
                "886660b51e0cc6358c8a2cd194d2fc7f2d26303c19dfb307d93b53a2fda1c564"
            ),
            started_at_utc="2026-07-31T19:09:50.3199100Z",
        ),
        initial=initial,
        steps=(step,),
        terminal=end,
        outcome="success",
    )
    assert trace.initial == initial
    assert trace.steps == (step,)
    assert trace.terminal == end
    assert not hasattr(capture, "__dict__")
    with pytest.raises(FrozenInstanceError):
        capture.level = "changed"  # type: ignore[misc]


def test_error_record_allows_the_schema_null_forms() -> None:
    record = ErrorRecord(
        input_index=None,
        input=None,
        code="capture_failed",
        message="game-state capture failed",
        settle_frames=0,
        last_capture=None,
    )
    assert record.input_index is None
    assert record.input is None
    assert record.last_capture is None


def test_error_code_message_table_is_exact_private_and_immutable() -> None:
    assert _ERROR_MESSAGES == {
        "patch_install_failed": "observation patch installation failed",
        "input_before_initial": "manual input arrived before initial capture",
        "overlapping_input": "manual input arrived while settling",
        "unexpected_input": "native input was outside the passive vocabulary",
        "unscoped_process_input": (
            "manual-looking input occurred outside the native poll scope"
        ),
        "hook_order_mismatch": "observation hook order mismatch",
        "game_method_exception": "observed game method threw",
        "observer_exception": "passive observer failed",
        "capture_failed": "game-state capture failed",
        "record_too_large": "encoded trace record exceeded its limit",
        "initial_settle_timeout": "initial capture did not settle",
        "settle_timeout": "input did not settle",
        "state_replaced": "game state identity changed",
        "save_path_changed": "isolated save path changed",
    }
    with pytest.raises(TypeError):
        _ERROR_MESSAGES["capture_failed"] = "changed"  # type: ignore[index]
    assert _ERROR_MESSAGES["capture_failed"] == "game-state capture failed"
```

- [ ] **Step 2: Run model tests and confirm RED**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py -k \
  'protocol_model or error_record_allows or error_code_message_table'
```

Expected: collection fails with `ImportError` naming `_ERROR_MESSAGES` or the first missing dataclass.

- [ ] **Step 3: Implement the immutable model and private mapping**

Replace the import block at the top of `src/ssr_env/oracle_protocol.py` with:

```python
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import BinaryIO, Iterator, Literal
```

Append exactly after `_CanonicalJsonReader`:

```python
InputName = Literal["North", "South", "West", "East", "Undo"]
TerminalOutcome = Literal["success", "error"]


@dataclass(frozen=True, slots=True)
class RunHeader:
    run_id: str
    game_assembly_sha256: str
    started_at_utc: str


@dataclass(frozen=True, slots=True)
class OracleCapture:
    raw_save: str
    state_identity: str
    level: str
    overworld: bool
    won: bool
    returning: bool
    have_ever_cooked_all: bool
    lost_reason: str
    display_name: str
    sausages_cooked: int
    movement_count: int
    pushes_to_try: int


@dataclass(frozen=True, slots=True)
class InitialRecord:
    capture: OracleCapture


@dataclass(frozen=True, slots=True)
class StepRecord:
    input_index: int
    input: InputName
    accepted: bool
    movement_scheduled: bool
    settle_frames: int
    state_replaced: bool
    capture: OracleCapture


@dataclass(frozen=True, slots=True)
class EndRecord:
    input_count: int
    finished_at_utc: str


@dataclass(frozen=True, slots=True)
class ErrorRecord:
    input_index: int | None
    input: InputName | None
    code: str
    message: str
    settle_frames: int
    last_capture: OracleCapture | None


@dataclass(frozen=True, slots=True)
class OracleRun:
    header: RunHeader
    initial: InitialRecord | None
    steps: tuple[StepRecord, ...]
    terminal: EndRecord | ErrorRecord
    outcome: TerminalOutcome


OracleRecord = RunHeader | InitialRecord | StepRecord | EndRecord | ErrorRecord
RecordKind = Literal["run", "initial", "step", "end", "error"]


@dataclass(frozen=True, slots=True)
class _DecodedLine:
    kind: RecordKind
    schema_version: int
    run_id: str
    record: OracleRecord


INPUT_NAMES = frozenset({"North", "South", "West", "East", "Undo"})
_ERROR_MESSAGES: Mapping[str, str] = MappingProxyType(
    {
        "patch_install_failed": "observation patch installation failed",
        "input_before_initial": "manual input arrived before initial capture",
        "overlapping_input": "manual input arrived while settling",
        "unexpected_input": "native input was outside the passive vocabulary",
        "unscoped_process_input": (
            "manual-looking input occurred outside the native poll scope"
        ),
        "hook_order_mismatch": "observation hook order mismatch",
        "game_method_exception": "observed game method threw",
        "observer_exception": "passive observer failed",
        "capture_failed": "game-state capture failed",
        "record_too_large": "encoded trace record exceeded its limit",
        "initial_settle_timeout": "initial capture did not settle",
        "settle_timeout": "input did not settle",
        "state_replaced": "game state identity changed",
        "save_path_changed": "isolated save path changed",
    }
)
```

- [ ] **Step 4: Run model/table GREEN**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py -k \
  'protocol_model or error_record_allows or error_code_message_table'
git diff --check
```

Expected: `3 passed`; the assignment raises `TypeError` and the original pair remains unchanged; `git diff --check` prints nothing and exits `0`.

- [ ] **Step 5: Commit the immutable models and error table**

Commit:

```bash
git add src/ssr_env/oracle_protocol.py tests/test_oracle_protocol.py
git commit -m "feat: define immutable oracle protocol records"
```

---

### Task 5: Validate ASCII timestamps, hashes, identities, and ranges

**Files:**
- Modify: `src/ssr_env/oracle_protocol.py`
- Modify: `tests/test_oracle_protocol.py`

**Interfaces:**
- Consumes: `InputName = Literal["North", "South", "West", "East", "Undo"]` and `INPUT_NAMES: frozenset[str]` from Task 4 plus `OracleProtocolError(ValueError)` from Task 1.
- Produces: `_timestamp_key(value: str, *, field: str = "timestamp") -> tuple[int, int, int, int, int, int, int]`, `_validate_run_id(value: str) -> str`, `_validate_hash(value: str, *, field: str) -> str`, `_validate_state_identity(value: str) -> str`, `_nonnegative(value: int, *, field: str, maximum: int = 2**31 - 1) -> int`, and `_input_name(value: str, *, allow_none: bool = False) -> InputName`.
- Internal consumers: Tasks 8–14 and 19 in this plan use these exact validators.
- External plan link: `docs/superpowers/plans/2026-07-31-oracle-passive-trace-implementation.md`, Task 1 executes this task; callers outside `ssr_env.oracle_protocol` do not import these private validators.

- [ ] **Step 1: Add RED ASCII timestamp, bounded identity, and range tests**

Append exactly to `tests/test_oracle_protocol.py`:

```python
from ssr_env.oracle_protocol import _timestamp_key, _validate_state_identity


def test_timestamp_preserves_the_seventh_fractional_digit() -> None:
    assert _timestamp_key("2026-07-31T19:09:50.3199107Z") == (
        2026,
        7,
        31,
        19,
        9,
        50,
        3199107,
    )


@pytest.mark.parametrize(
    "value",
    [
        "2026-07-31T19:09:50.319910Z",
        "2026-07-31T19:09:50.3199100+00:00",
        "2026-07-31T19:09:50.3199100z",
        "2026-02-30T19:09:50.3199100Z",
        "0000-07-31T19:09:50.3199100Z",
        "٢٠٢٦-07-31T19:09:50.3199100Z",
        "２０２６-07-31T19:09:50.3199100Z",
    ],
)
def test_timestamp_rejects_noncanonical_or_unicode_digits(value: str) -> None:
    with pytest.raises(OracleProtocolError):
        _timestamp_key(value)


@pytest.mark.parametrize(
    "value", ["0", "1", "-1", "2147483647", "-2147483648"]
)
def test_state_identity_accepts_canonical_signed_32_bit_text(value: str) -> None:
    assert _validate_state_identity(value) == value


@pytest.mark.parametrize(
    "value", ["-0", "+1", "01", "١", "2147483648", "-2147483649"]
)
def test_state_identity_rejects_noncanonical_text(value: str) -> None:
    with pytest.raises(OracleProtocolError):
        _validate_state_identity(value)


@pytest.mark.parametrize("value", ["9" * 100_000, "-" + "9" * 100_000])
def test_state_identity_rejects_long_decimal_before_conversion(value: str) -> None:
    with pytest.raises(
        OracleProtocolError, match="state_identity exceeds 11 characters"
    ):
        _validate_state_identity(value)
```

- [ ] **Step 2: Run scalar grammar tests and confirm RED**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py -k 'timestamp or state_identity'
```

Expected: collection fails with `ImportError` naming `_timestamp_key` or `_validate_state_identity`; neither long-decimal case may reach Python's `int` digit limit.

- [ ] **Step 3: Implement ASCII-only bounded scalar validators**

Add these imports at the top of `src/ssr_env/oracle_protocol.py`:

```python
import re
from datetime import datetime, timezone
```

Append exactly after `_ERROR_MESSAGES`:

```python
_RUN_ID_RE = re.compile(r"[0-9a-f]{32}\Z")
_HASH_RE = re.compile(r"[0-9a-f]{64}\Z")
_SIGNED_DECIMAL_RE = re.compile(r"(?:0|-[1-9][0-9]*|[1-9][0-9]*)\Z")
_TIMESTAMP_RE = re.compile(
    r"(?P<year>[0-9]{4})-(?P<month>[0-9]{2})-(?P<day>[0-9]{2})T"
    r"(?P<hour>[0-9]{2}):(?P<minute>[0-9]{2}):(?P<second>[0-9]{2})\."
    r"(?P<fraction>[0-9]{7})Z\Z"
)


def _timestamp_key(
    value: str, *, field: str = "timestamp"
) -> tuple[int, int, int, int, int, int, int]:
    match = _TIMESTAMP_RE.fullmatch(value)
    if match is None:
        raise OracleProtocolError(f"{field} is not canonical UTC O-format text")
    parts = tuple(int(match.group(name)) for name in (
        "year",
        "month",
        "day",
        "hour",
        "minute",
        "second",
        "fraction",
    ))
    year, month, day, hour, minute, second, fraction = parts
    try:
        datetime(
            year,
            month,
            day,
            hour,
            minute,
            second,
            fraction // 10,
            tzinfo=timezone.utc,
        )
    except ValueError as exc:
        raise OracleProtocolError(f"{field} has invalid calendar values") from exc
    return year, month, day, hour, minute, second, fraction


def _validate_run_id(value: str) -> str:
    if _RUN_ID_RE.fullmatch(value) is None:
        raise OracleProtocolError("run_id must be 32 lowercase hexadecimal characters")
    return value


def _validate_hash(value: str, *, field: str) -> str:
    if _HASH_RE.fullmatch(value) is None:
        raise OracleProtocolError(
            f"{field} must be 64 lowercase hexadecimal characters"
        )
    return value


def _validate_state_identity(value: str) -> str:
    if len(value) > 11:
        raise OracleProtocolError("state_identity exceeds 11 characters")
    if _SIGNED_DECIMAL_RE.fullmatch(value) is None:
        raise OracleProtocolError("state_identity is not canonical signed decimal")
    parsed = int(value)
    if not -(2**31) <= parsed <= 2**31 - 1:
        raise OracleProtocolError("state_identity is outside signed 32-bit range")
    if str(parsed) != value:
        raise OracleProtocolError("state_identity does not round-trip canonically")
    return value


def _nonnegative(value: int, *, field: str, maximum: int = 2**31 - 1) -> int:
    if not 0 <= value <= maximum:
        raise OracleProtocolError(f"{field} must be in 0..{maximum}")
    return value


def _input_name(value: str, *, allow_none: bool = False) -> InputName:
    if value not in INPUT_NAMES:
        suffix = " or null" if allow_none else ""
        raise OracleProtocolError(f"input must use the passive vocabulary{suffix}")
    return value  # type: ignore[return-value]
```

- [ ] **Step 4: Run scalar grammar GREEN**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py -k 'timestamp or state_identity'
git diff --check
```

Expected: `21 passed`; both 100,000-digit identity cases hit the explicit length guard before `int`; `git diff --check` prints nothing and exits `0`.

- [ ] **Step 5: Commit the scalar validators**

Commit:

```bash
git add src/ssr_env/oracle_protocol.py tests/test_oracle_protocol.py
git commit -m "feat: validate bounded oracle protocol scalars"
```

---

### Task 6: Structurally decode run, initial, and capture records

**Files:**
- Modify: `src/ssr_env/oracle_protocol.py`
- Modify: `tests/test_oracle_protocol.py`

**Interfaces:**
- Consumes: `SCHEMA_VERSION: int`, `EXPECTED_INPUT_COUNT: int`, `EXPECTED_ASSEMBLY_SHA256: str`, and `OracleProtocolError(ValueError)` from Task 1; `_CanonicalJsonReader(payload: bytes, line_number: int, *, source: str)` plus `read_object(fields: Sequence[tuple[str, Callable[[], object]]]) -> dict[str, object]`, `read_string() -> str`, `read_integer() -> int`, `read_boolean() -> bool`, `read_optional(reader: Callable[[], object]) -> object | None`, and `finish() -> None` from Tasks 2–3; `RecordKind`, `RunHeader`, `OracleCapture`, `InitialRecord`, and `_DecodedLine` from Task 4.
- Produces: `_located(reader: _CanonicalJsonReader, operation: Callable[[], _T]) -> _T`, `_record_error(reader: _CanonicalJsonReader, message: str) -> NoReturn`, `_read_capture(reader: _CanonicalJsonReader) -> OracleCapture`, `_decode_run(reader: _CanonicalJsonReader) -> _DecodedLine`, `_decode_initial(reader: _CanonicalJsonReader) -> _DecodedLine`, and a two-kind `_decode_record(payload: bytes, line_number: int, *, source: str) -> _DecodedLine`.
- The task enforces canonical key order and JSON value types through the reader, but deliberately does not yet enforce semantic run/capture values. Tasks 8–9 activate those rules with behavioral RED tests.
- Internal consumer: Task 7 must delete and replace—not append to—the two-kind `_decode_record` while adding `step`.
- External plan link: `docs/superpowers/plans/2026-07-31-oracle-passive-trace-implementation.md`, Task 1 executes and reviews this task; the decoder remains private to `ssr_env.oracle_protocol`.

- [ ] **Step 1: Add literal records and the RED valid structural-decoding test**

Append exactly to `tests/test_oracle_protocol.py`:

```python
from ssr_env.oracle_protocol import (
    EXPECTED_ASSEMBLY_SHA256,
    EXPECTED_INPUT_COUNT,
    SCHEMA_VERSION,
    _decode_record,
)

RUN_ID = "0123456789abcdef0123456789abcdef"
OTHER_RUN_ID = "fedcba9876543210fedcba9876543210"
ASSEMBLY_HASH = EXPECTED_ASSEMBLY_SHA256
CAPTURE_JSON = (
    '{"raw_save":"initial","state_identity":"17","level":"",'
    '"overworld":false,"won":false,"returning":false,'
    '"have_ever_cooked_all":false,"lost_reason":"","display_name":"",'
    '"sausages_cooked":0,"movement_count":0,"pushes_to_try":0}'
)
MOVED_CAPTURE_JSON = CAPTURE_JSON.replace('"raw_save":"initial"', '"raw_save":"moved"')
RUN_LINE = (
    f'{{"kind":"run","schema_version":{SCHEMA_VERSION},'
    f'"run_id":"{RUN_ID}","mode":"passive",'
    f'"game_assembly_sha256":"{ASSEMBLY_HASH}",'
    '"plugin_version":"0.2.0","input_sha256":null,'
    f'"expected_input_count":{EXPECTED_INPUT_COUNT},'
    '"started_at_utc":"2026-07-31T19:09:50.3199100Z"}'
).encode("utf-8")
INITIAL_LINE = (
    f'{{"kind":"initial","schema_version":{SCHEMA_VERSION},'
    f'"run_id":"{RUN_ID}","input_index":null,"capture":{CAPTURE_JSON}'
    "}"
).encode("utf-8")
STEP0_LINE = (
    f'{{"kind":"step","schema_version":{SCHEMA_VERSION},'
    f'"run_id":"{RUN_ID}","input_index":0,"input":"West",'
    '"accepted":true,"movement_scheduled":true,"settle_frames":2,'
    f'"state_replaced":false,"capture":{MOVED_CAPTURE_JSON}'
    "}"
).encode("utf-8")
STEP1_LINE = (
    f'{{"kind":"step","schema_version":{SCHEMA_VERSION},'
    f'"run_id":"{RUN_ID}","input_index":1,"input":"North",'
    '"accepted":false,"movement_scheduled":false,"settle_frames":2,'
    f'"state_replaced":false,"capture":{MOVED_CAPTURE_JSON}'
    "}"
).encode("utf-8")
STEP2_LINE = (
    f'{{"kind":"step","schema_version":{SCHEMA_VERSION},'
    f'"run_id":"{RUN_ID}","input_index":2,"input":"Undo",'
    '"accepted":true,"movement_scheduled":false,"settle_frames":2,'
    f'"state_replaced":false,"capture":{CAPTURE_JSON}'
    "}"
).encode("utf-8")
END_LINE = (
    f'{{"kind":"end","schema_version":{SCHEMA_VERSION},'
    f'"run_id":"{RUN_ID}","input_count":{EXPECTED_INPUT_COUNT},'
    '"finished_at_utc":"2026-07-31T19:11:00.0000000Z"}'
).encode("utf-8")
ERROR_LINE = (
    f'{{"kind":"error","schema_version":{SCHEMA_VERSION},'
    f'"run_id":"{RUN_ID}","input_index":1,"input":"North",'
    '"code":"settle_timeout","message":"input did not settle",'
    f'"settle_frames":600,"last_capture":{MOVED_CAPTURE_JSON}'
    "}"
).encode("utf-8")


def _expected_capture(raw_save: str) -> OracleCapture:
    return OracleCapture(
        raw_save=raw_save,
        state_identity="17",
        level="",
        overworld=False,
        won=False,
        returning=False,
        have_ever_cooked_all=False,
        lost_reason="",
        display_name="",
        sausages_cooked=0,
        movement_count=0,
        pushes_to_try=0,
    )


def test_record_decoder_accepts_run_initial_and_complete_capture() -> None:
    run = _decode_record(RUN_LINE, 1, source="literal")
    initial = _decode_record(INITIAL_LINE, 2, source="literal")

    assert run.kind == "run"
    assert run.schema_version == SCHEMA_VERSION
    assert run.run_id == RUN_ID
    assert run.record == RunHeader(
        run_id=RUN_ID,
        game_assembly_sha256=ASSEMBLY_HASH,
        started_at_utc="2026-07-31T19:09:50.3199100Z",
    )
    assert initial.record == InitialRecord(capture=_expected_capture("initial"))
```

- [ ] **Step 2: Run the valid structural-decoding test and confirm RED**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py::test_record_decoder_accepts_run_initial_and_complete_capture
```

Expected: collection fails with `ImportError: cannot import name '_decode_record'`.

- [ ] **Step 3: Implement the structural capture and two-kind decoders**

Change the typing import in `src/ssr_env/oracle_protocol.py` to:

```python
from typing import BinaryIO, Iterator, Literal, NoReturn, TypeVar, cast
```

Append exactly:

```python
_T = TypeVar("_T")


def _located(reader: _CanonicalJsonReader, operation: Callable[[], _T]) -> _T:
    try:
        return operation()
    except OracleProtocolError as exc:
        raise OracleProtocolError(
            f"{reader.source}: line {reader.line_number}: {exc}"
        ) from exc


def _record_error(reader: _CanonicalJsonReader, message: str) -> NoReturn:
    raise OracleProtocolError(
        f"{reader.source}: line {reader.line_number}: {message}"
    )


def _read_capture(reader: _CanonicalJsonReader) -> OracleCapture:
    values = reader.read_object(
        (
            ("raw_save", reader.read_string),
            ("state_identity", reader.read_string),
            ("level", reader.read_string),
            ("overworld", reader.read_boolean),
            ("won", reader.read_boolean),
            ("returning", reader.read_boolean),
            ("have_ever_cooked_all", reader.read_boolean),
            ("lost_reason", reader.read_string),
            ("display_name", reader.read_string),
            ("sausages_cooked", reader.read_integer),
            ("movement_count", reader.read_integer),
            ("pushes_to_try", reader.read_integer),
        )
    )
    return OracleCapture(
        raw_save=cast(str, values["raw_save"]),
        state_identity=cast(str, values["state_identity"]),
        level=cast(str, values["level"]),
        overworld=cast(bool, values["overworld"]),
        won=cast(bool, values["won"]),
        returning=cast(bool, values["returning"]),
        have_ever_cooked_all=cast(bool, values["have_ever_cooked_all"]),
        lost_reason=cast(str, values["lost_reason"]),
        display_name=cast(str, values["display_name"]),
        sausages_cooked=cast(int, values["sausages_cooked"]),
        movement_count=cast(int, values["movement_count"]),
        pushes_to_try=cast(int, values["pushes_to_try"]),
    )


def _decode_run(reader: _CanonicalJsonReader) -> _DecodedLine:
    values = reader.read_object(
        (
            ("kind", reader.read_string),
            ("schema_version", reader.read_integer),
            ("run_id", reader.read_string),
            ("mode", reader.read_string),
            ("game_assembly_sha256", reader.read_string),
            ("plugin_version", reader.read_string),
            ("input_sha256", lambda: reader.read_optional(reader.read_string)),
            ("expected_input_count", reader.read_integer),
            ("started_at_utc", reader.read_string),
        )
    )
    reader.finish()
    kind = cast(RecordKind, values["kind"])
    run_id = cast(str, values["run_id"])
    return _DecodedLine(
        kind=kind,
        schema_version=cast(int, values["schema_version"]),
        run_id=run_id,
        record=RunHeader(
            run_id=run_id,
            game_assembly_sha256=cast(
                str, values["game_assembly_sha256"]
            ),
            started_at_utc=cast(str, values["started_at_utc"]),
        ),
    )


def _decode_initial(reader: _CanonicalJsonReader) -> _DecodedLine:
    values = reader.read_object(
        (
            ("kind", reader.read_string),
            ("schema_version", reader.read_integer),
            ("run_id", reader.read_string),
            ("input_index", lambda: reader.read_optional(reader.read_integer)),
            ("capture", lambda: _read_capture(reader)),
        )
    )
    reader.finish()
    return _DecodedLine(
        kind=cast(RecordKind, values["kind"]),
        schema_version=cast(int, values["schema_version"]),
        run_id=cast(str, values["run_id"]),
        record=InitialRecord(capture=cast(OracleCapture, values["capture"])),
    )


def _decode_record(
    payload: bytes, line_number: int, *, source: str
) -> _DecodedLine:
    reader = _CanonicalJsonReader(payload, line_number, source=source)
    if payload.startswith(b'{"kind":"run",'):
        return _decode_run(reader)
    if payload.startswith(b'{"kind":"initial",'):
        return _decode_initial(reader)
    _record_error(reader, "kind must be the first key and use a schema-v1 value")
    raise AssertionError("unreachable")
```

- [ ] **Step 4: Add parser-inherited structural rejection regressions**

Append exactly to `tests/test_oracle_protocol.py`:

```python
STRUCTURALLY_BAD_RUN_OR_CAPTURE_LINES = [
    pytest.param(RUN_LINE.replace(b'"kind":"run"', b'"kind":"wat"'), id="kind"),
    pytest.param(
        RUN_LINE.replace(b'"schema_version":1', b'"schema_version":true'),
        id="bool-as-schema-integer",
    ),
    pytest.param(
        RUN_LINE.replace(
            b'"mode":"passive","game_assembly_sha256"',
            b'"game_assembly_sha256":"' + ASSEMBLY_HASH.encode() + b'","mode"',
        ),
        id="reordered-top-level-key",
    ),
    pytest.param(
        RUN_LINE.replace(
            b'"mode":"passive",',
            b'"mode":"passive","mode":"passive",',
        ),
        id="duplicate-top-level-key",
    ),
    pytest.param(
        RUN_LINE.replace(
            b'"mode":"passive",',
            b'"mode":"passive","extra":false,',
        ),
        id="unknown-top-level-key",
    ),
    pytest.param(
        INITIAL_LINE.replace(
            b'"raw_save":"initial","state_identity":"17"',
            b'"state_identity":"17","raw_save":"initial"',
        ),
        id="reordered-capture-key",
    ),
    pytest.param(
        INITIAL_LINE.replace(b'"level":"",', b""),
        id="missing-capture-key",
    ),
    pytest.param(
        INITIAL_LINE.replace(
            b'"raw_save":"initial",',
            b'"raw_save":"initial","extra":false,',
        ),
        id="unknown-capture-key",
    ),
    pytest.param(
        INITIAL_LINE.replace(
            b'"raw_save":"initial",',
            b'"raw_save":"initial","raw_save":"initial",',
        ),
        id="duplicate-capture-key",
    ),
    pytest.param(
        INITIAL_LINE.replace(b'"raw_save":"initial"', b'"raw_save":null'),
        id="null-raw-save",
    ),
    pytest.param(
        INITIAL_LINE.replace(b'"sausages_cooked":0', b'"sausages_cooked":false'),
        id="bool-as-capture-integer",
    ),
    pytest.param(
        INITIAL_LINE.replace(b'"pushes_to_try":0', b'"pushes_to_try":2147483648'),
        id="overflow-capture-integer",
    ),
]


@pytest.mark.parametrize("payload", STRUCTURALLY_BAD_RUN_OR_CAPTURE_LINES)
def test_record_decoder_rejects_structurally_bad_run_or_capture(
    payload: bytes,
) -> None:
    with pytest.raises(OracleProtocolError):
        _decode_record(payload, 1, source="bad-structure")


def test_record_decoder_preserves_long_integer_lexer_guard() -> None:
    payload = RUN_LINE.replace(
        b'"expected_input_count":3',
        b'"expected_input_count":' + b"9" * 100_000,
    )
    with pytest.raises(
        OracleProtocolError, match="integer lexeme exceeds 11 bytes"
    ):
        _decode_record(payload, 1, source="long-integer")
```

These rows exercise reader behavior already delivered by Tasks 2–3; they are integration regressions, not claimed as a new RED cohort.

- [ ] **Step 5: Run structural decoder GREEN**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py -k \
  'record_decoder_accepts_run_initial or record_decoder_rejects_structurally_bad or record_decoder_preserves_long_integer'
git diff --check
```

Expected: `14 passed`; the 100,000-digit integer hits the explicit lexer guard, and `git diff --check` prints nothing and exits `0`.

- [ ] **Step 6: Commit the structural run/initial decoder**

Commit:

```bash
git add src/ssr_env/oracle_protocol.py tests/test_oracle_protocol.py
git commit -m "feat: structurally decode oracle run records"
```

---

### Task 7: Decode valid step records and replace the dispatcher

**Files:**
- Modify: `src/ssr_env/oracle_protocol.py`
- Modify: `tests/test_oracle_protocol.py`

**Interfaces:**
- Consumes: `_CanonicalJsonReader(payload: bytes, line_number: int, *, source: str)`, `_read_capture(reader: _CanonicalJsonReader) -> OracleCapture`, `_record_error(reader: _CanonicalJsonReader, message: str) -> NoReturn`, `_decode_run(reader: _CanonicalJsonReader) -> _DecodedLine`, `_decode_initial(reader: _CanonicalJsonReader) -> _DecodedLine`, and the two-kind `_decode_record(payload: bytes, line_number: int, *, source: str) -> _DecodedLine` from Task 6; `InputName`, `RecordKind`, `OracleCapture`, `StepRecord`, and `_DecodedLine` from Task 4.
- Produces: structural `_decode_step(reader: _CanonicalJsonReader) -> _DecodedLine` and one replacement `_decode_record(payload: bytes, line_number: int, *, source: str) -> _DecodedLine` supporting `run`, `initial`, and `step`.
- Internal consumers: Task 10 strengthens `_decode_step`; Tasks 11 and 13 replace the same single dispatcher while adding terminal kinds.
- External plan link: `docs/superpowers/plans/2026-07-31-oracle-passive-trace-implementation.md`, Task 1 executes this task; no decoder symbol is imported cross-plan.

- [ ] **Step 1: Add the RED valid-step and single-definition source tests**

Append exactly to `tests/test_oracle_protocol.py`:

```python
import ast

import ssr_env.oracle_protocol as oracle_protocol


def test_record_decoder_accepts_valid_step_record() -> None:
    step = _decode_record(STEP0_LINE, 3, source="literal")
    assert step.record == StepRecord(
        input_index=0,
        input="West",
        accepted=True,
        movement_scheduled=True,
        settle_frames=2,
        state_replaced=False,
        capture=_expected_capture("moved"),
    )


def test_decoder_source_has_exactly_one_record_dispatcher() -> None:
    source = Path(oracle_protocol.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    definitions = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        and node.name == "_decode_record"
    ]
    assert len(definitions) == 1
```

- [ ] **Step 2: Run the valid-step/source cohort and confirm RED**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py -k \
  'record_decoder_accepts_valid_step or decoder_source_has_exactly_one'
```

Expected: `1 failed, 1 passed`. The valid step reaches Task 6's two-kind dispatcher and raises `OracleProtocolError`; the source test proves there is exactly one pre-change definition.

- [ ] **Step 3: Add the structural step decoder and replace Task 6's dispatcher**

Insert `_decode_step` immediately before Task 6's `_decode_record`:

```python
def _decode_step(reader: _CanonicalJsonReader) -> _DecodedLine:
    values = reader.read_object(
        (
            ("kind", reader.read_string),
            ("schema_version", reader.read_integer),
            ("run_id", reader.read_string),
            ("input_index", reader.read_integer),
            ("input", reader.read_string),
            ("accepted", reader.read_boolean),
            ("movement_scheduled", reader.read_boolean),
            ("settle_frames", reader.read_integer),
            ("state_replaced", reader.read_boolean),
            ("capture", lambda: _read_capture(reader)),
        )
    )
    reader.finish()
    return _DecodedLine(
        kind=cast(RecordKind, values["kind"]),
        schema_version=cast(int, values["schema_version"]),
        run_id=cast(str, values["run_id"]),
        record=StepRecord(
            input_index=cast(int, values["input_index"]),
            input=cast(InputName, values["input"]),
            accepted=cast(bool, values["accepted"]),
            movement_scheduled=cast(bool, values["movement_scheduled"]),
            settle_frames=cast(int, values["settle_frames"]),
            state_replaced=cast(bool, values["state_replaced"]),
            capture=cast(OracleCapture, values["capture"]),
        ),
    )
```

Delete Task 6's entire two-kind `_decode_record` definition, then insert this replacement in the same location:

```python
def _decode_record(
    payload: bytes, line_number: int, *, source: str
) -> _DecodedLine:
    reader = _CanonicalJsonReader(payload, line_number, source=source)
    if payload.startswith(b'{"kind":"run",'):
        return _decode_run(reader)
    if payload.startswith(b'{"kind":"initial",'):
        return _decode_initial(reader)
    if payload.startswith(b'{"kind":"step",'):
        return _decode_step(reader)
    _record_error(reader, "kind must be the first key and use a schema-v1 value")
    raise AssertionError("unreachable")
```

Do not append a second dispatcher. The source regression must continue to count exactly one module-level `_decode_record`.

- [ ] **Step 4: Add the parser-inherited null-capture regression**

Append exactly to `tests/test_oracle_protocol.py`:

```python
def test_record_decoder_rejects_null_step_capture_structurally() -> None:
    payload = STEP0_LINE.replace(MOVED_CAPTURE_JSON.encode(), b"null")
    with pytest.raises(OracleProtocolError):
        _decode_record(payload, 3, source="null-step-capture")
```

- [ ] **Step 5: Run valid-step/dispatcher GREEN**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py -k \
  'record_decoder_accepts_valid_step or decoder_source_has_exactly_one or null_step_capture'
git diff --check
```

Expected: `3 passed`, exactly one dispatcher definition remains, and `git diff --check` prints nothing and exits `0`.

- [ ] **Step 6: Commit valid step decoding**

Commit:

```bash
git add src/ssr_env/oracle_protocol.py tests/test_oracle_protocol.py
git commit -m "feat: structurally decode oracle steps"
```

---

### Task 8: Validate run-header semantics

**Files:**
- Modify: `src/ssr_env/oracle_protocol.py`
- Modify: `tests/test_oracle_protocol.py`

**Interfaces:**
- Consumes: `SCHEMA_VERSION: int`, `EXPECTED_INPUT_COUNT: int`, and `EXPECTED_ASSEMBLY_SHA256: str` from Task 1; `RecordKind`, `RunHeader`, and `_DecodedLine` from Task 4; `_timestamp_key(value: str, *, field: str = "timestamp") -> tuple[int, int, int, int, int, int, int]`, `_validate_run_id(value: str) -> str`, and `_validate_hash(value: str, *, field: str) -> str` from Task 5; `_CanonicalJsonReader(payload: bytes, line_number: int, *, source: str)`, `_located(reader: _CanonicalJsonReader, operation: Callable[[], _T]) -> _T`, `_record_error(reader: _CanonicalJsonReader, message: str) -> NoReturn`, and structural `_decode_run(reader: _CanonicalJsonReader) -> _DecodedLine` from Task 6.
- Produces: `_validate_common(reader: _CanonicalJsonReader, values: dict[str, object], *, expected_kind: RecordKind) -> tuple[int, str]` and semantically strict `_decode_run(reader: _CanonicalJsonReader) -> _DecodedLine`.
- Internal consumers: Tasks 9–14 use `_validate_common`; Tasks 15–20 consume validated decoded records.
- External plan link: `docs/superpowers/plans/2026-07-31-oracle-passive-trace-implementation.md`, Task 1 executes this task; no private validator is imported cross-plan.

- [ ] **Step 1: Add the RED run-header semantic rejection cohort**

Append exactly to `tests/test_oracle_protocol.py`:

```python
BAD_RUN_SEMANTIC_LINES = [
    pytest.param(
        RUN_LINE.replace(b'"schema_version":1', b'"schema_version":2'),
        id="schema-version",
    ),
    pytest.param(
        RUN_LINE.replace(RUN_ID.encode(), RUN_ID.upper().encode()),
        id="run-id-uppercase",
    ),
    pytest.param(
        RUN_LINE.replace(RUN_ID.encode(), RUN_ID[:-1].encode()),
        id="run-id-short",
    ),
    pytest.param(
        RUN_LINE.replace(RUN_ID.encode(), (RUN_ID + "0").encode()),
        id="run-id-long",
    ),
    pytest.param(
        RUN_LINE.replace(RUN_ID.encode(), ("g" + RUN_ID[1:]).encode()),
        id="run-id-nonhex-32",
    ),
    pytest.param(
        RUN_LINE.replace(b'"mode":"passive"', b'"mode":"replay"'),
        id="mode",
    ),
    pytest.param(
        RUN_LINE.replace(ASSEMBLY_HASH.encode(), b"0" * 64),
        id="assembly-reviewed-value",
    ),
    pytest.param(
        RUN_LINE.replace(ASSEMBLY_HASH.encode(), b"0" * 63),
        id="assembly-length-short",
    ),
    pytest.param(
        RUN_LINE.replace(ASSEMBLY_HASH.encode(), b"0" * 65),
        id="assembly-length-long",
    ),
    pytest.param(
        RUN_LINE.replace(ASSEMBLY_HASH.encode(), ASSEMBLY_HASH.upper().encode()),
        id="assembly-uppercase",
    ),
    pytest.param(
        RUN_LINE.replace(ASSEMBLY_HASH.encode(), b"g" * 64),
        id="assembly-nonhex",
    ),
    pytest.param(
        RUN_LINE.replace(b'"plugin_version":"0.2.0"', b'"plugin_version":"0.1.0"'),
        id="plugin-version",
    ),
    pytest.param(
        RUN_LINE.replace(b'"input_sha256":null', b'"input_sha256":"00"'),
        id="input-hash",
    ),
    pytest.param(
        RUN_LINE.replace(b'"expected_input_count":3', b'"expected_input_count":2'),
        id="expected-input-count",
    ),
    pytest.param(
        RUN_LINE.replace(
            b"2026-07-31T19:09:50.3199100Z",
            b"2026-02-30T19:09:50.3199100Z",
        ),
        id="start-timestamp",
    ),
]


@pytest.mark.parametrize("payload", BAD_RUN_SEMANTIC_LINES)
def test_record_decoder_rejects_invalid_run_semantics(payload: bytes) -> None:
    with pytest.raises(OracleProtocolError):
        _decode_record(payload, 1, source="bad-run-semantics")


@pytest.mark.parametrize(
    "unicode_year",
    ["٢٠٢٦", "２０２６"],
    ids=["arabic-indic-digits", "fullwidth-digits"],
)
def test_record_decoder_rejects_unicode_timestamp_digits(
    unicode_year: str,
) -> None:
    payload = RUN_LINE.replace(
        b"2026-07-31", f"{unicode_year}-07-31".encode("utf-8")
    )
    with pytest.raises(OracleProtocolError, match="canonical UTC"):
        _decode_record(payload, 1, source="unicode-time")
```

- [ ] **Step 2: Run run-header semantics and confirm behavioral RED**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py -k \
  'record_decoder_rejects_invalid_run_semantics or record_decoder_rejects_unicode_timestamp_digits'
```

Expected: `17 failed`, each with `DID NOT RAISE OracleProtocolError`. Task 6 structurally accepts every row, so this RED proves the semantic rules are absent rather than relying on generic kind rejection.

- [ ] **Step 3: Implement common and run-header semantic validation**

Insert immediately before `_decode_run`:

```python
def _validate_common(
    reader: _CanonicalJsonReader,
    values: dict[str, object],
    *,
    expected_kind: RecordKind,
) -> tuple[int, str]:
    kind = cast(str, values["kind"])
    schema_version = cast(int, values["schema_version"])
    run_id_text = cast(str, values["run_id"])
    if kind != expected_kind:
        _record_error(reader, f"kind must be {expected_kind!r}")
    if schema_version != SCHEMA_VERSION:
        _record_error(reader, f"schema_version must be {SCHEMA_VERSION}")
    run_id = _located(reader, lambda: _validate_run_id(run_id_text))
    return schema_version, run_id
```

Replace the complete structural `_decode_run` with:

```python
def _decode_run(reader: _CanonicalJsonReader) -> _DecodedLine:
    values = reader.read_object(
        (
            ("kind", reader.read_string),
            ("schema_version", reader.read_integer),
            ("run_id", reader.read_string),
            ("mode", reader.read_string),
            ("game_assembly_sha256", reader.read_string),
            ("plugin_version", reader.read_string),
            ("input_sha256", lambda: reader.read_optional(reader.read_string)),
            ("expected_input_count", reader.read_integer),
            ("started_at_utc", reader.read_string),
        )
    )
    reader.finish()
    schema_version, run_id = _validate_common(
        reader, values, expected_kind="run"
    )
    if cast(str, values["mode"]) != "passive":
        _record_error(reader, "mode must be 'passive'")
    assembly_text = cast(str, values["game_assembly_sha256"])
    assembly_hash = _located(
        reader,
        lambda: _validate_hash(assembly_text, field="game_assembly_sha256"),
    )
    if assembly_hash != EXPECTED_ASSEMBLY_SHA256:
        _record_error(reader, "game_assembly_sha256 is not the reviewed hash")
    if cast(str, values["plugin_version"]) != "0.2.0":
        _record_error(reader, "plugin_version must be '0.2.0'")
    if values["input_sha256"] is not None:
        _record_error(reader, "input_sha256 must be null in passive mode")
    if cast(int, values["expected_input_count"]) != EXPECTED_INPUT_COUNT:
        _record_error(
            reader,
            f"expected_input_count must be {EXPECTED_INPUT_COUNT}",
        )
    started_at_utc = cast(str, values["started_at_utc"])
    _located(
        reader,
        lambda: _timestamp_key(started_at_utc, field="started_at_utc"),
    )
    return _DecodedLine(
        kind="run",
        schema_version=schema_version,
        run_id=run_id,
        record=RunHeader(
            run_id=run_id,
            game_assembly_sha256=assembly_hash,
            started_at_utc=started_at_utc,
        ),
    )
```

- [ ] **Step 4: Run run-header semantics GREEN**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py -k \
  'record_decoder_rejects_invalid_run_semantics or record_decoder_rejects_unicode_timestamp_digits'
git diff --check
```

Expected: `17 passed`; run IDs that are short, long, uppercase, or exactly 32 characters containing nonhex text are independently rejected, and `git diff --check` prints nothing and exits `0`.

- [ ] **Step 5: Commit strict run-header validation**

Commit:

```bash
git add src/ssr_env/oracle_protocol.py tests/test_oracle_protocol.py
git commit -m "feat: validate oracle run headers"
```

---

### Task 9: Validate initial and capture semantics

**Files:**
- Modify: `src/ssr_env/oracle_protocol.py`
- Modify: `tests/test_oracle_protocol.py`

**Interfaces:**
- Consumes: `OracleCapture`, `InitialRecord`, and `_DecodedLine` from Task 4; `_validate_state_identity(value: str) -> str` and `_nonnegative(value: int, *, field: str, maximum: int = 2**31 - 1) -> int` from Task 5; `_CanonicalJsonReader(payload: bytes, line_number: int, *, source: str)`, `_located(reader: _CanonicalJsonReader, operation: Callable[[], _T]) -> _T`, `_record_error(reader: _CanonicalJsonReader, message: str) -> NoReturn`, structural `_read_capture(reader: _CanonicalJsonReader) -> OracleCapture`, and structural `_decode_initial(reader: _CanonicalJsonReader) -> _DecodedLine` from Task 6; `_validate_common(reader: _CanonicalJsonReader, values: dict[str, object], *, expected_kind: RecordKind) -> tuple[int, str]` from Task 8.
- Produces: semantically strict replacements for `_read_capture(reader: _CanonicalJsonReader) -> OracleCapture` and `_decode_initial(reader: _CanonicalJsonReader) -> _DecodedLine`.
- Internal consumers: Tasks 10, 13–14, and 15–20 receive validated captures and initial records.
- External plan link: `docs/superpowers/plans/2026-07-31-oracle-passive-trace-implementation.md`, Task 1 executes this task; no private capture helper is imported cross-plan.

- [ ] **Step 1: Add the RED capture semantic rejection cohort**

Append exactly to `tests/test_oracle_protocol.py`:

```python
BAD_INITIAL_CAPTURE_SEMANTIC_LINES = [
    pytest.param(
        INITIAL_LINE.replace(b'"input_index":null', b'"input_index":0'),
        id="initial-index",
    ),
    pytest.param(
        INITIAL_LINE.replace(b'"state_identity":"17"', b'"state_identity":"01"'),
        id="state-identity",
    ),
    pytest.param(
        INITIAL_LINE.replace(b'"movement_count":0', b'"movement_count":-1'),
        id="negative-capture-integer",
    ),
]


@pytest.mark.parametrize("payload", BAD_INITIAL_CAPTURE_SEMANTIC_LINES)
def test_record_decoder_rejects_invalid_initial_or_capture_semantics(
    payload: bytes,
) -> None:
    with pytest.raises(OracleProtocolError):
        _decode_record(payload, 2, source="bad-capture-semantics")


def test_record_decoder_rejects_long_state_identity_before_conversion() -> None:
    payload = INITIAL_LINE.replace(
        b'"state_identity":"17"',
        b'"state_identity":"' + b"9" * 100_000 + b'"',
    )
    with pytest.raises(
        OracleProtocolError, match="state_identity exceeds 11 characters"
    ):
        _decode_record(payload, 2, source="long-state-identity")
```

- [ ] **Step 2: Run capture semantics and confirm behavioral RED**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py -k \
  'invalid_initial_or_capture_semantics or long_state_identity_before_conversion'
```

Expected: `4 failed`, each with `DID NOT RAISE OracleProtocolError`. The 100,000-character identity remains text in Task 6 and must not be converted before this task adds the explicit length guard.

- [ ] **Step 3: Replace structural capture and initial decoding with strict validation**

Replace the complete `_read_capture` with:

```python
def _read_capture(reader: _CanonicalJsonReader) -> OracleCapture:
    values = reader.read_object(
        (
            ("raw_save", reader.read_string),
            ("state_identity", reader.read_string),
            ("level", reader.read_string),
            ("overworld", reader.read_boolean),
            ("won", reader.read_boolean),
            ("returning", reader.read_boolean),
            ("have_ever_cooked_all", reader.read_boolean),
            ("lost_reason", reader.read_string),
            ("display_name", reader.read_string),
            ("sausages_cooked", reader.read_integer),
            ("movement_count", reader.read_integer),
            ("pushes_to_try", reader.read_integer),
        )
    )
    state_identity_text = cast(str, values["state_identity"])
    sausages_cooked_value = cast(int, values["sausages_cooked"])
    movement_count_value = cast(int, values["movement_count"])
    pushes_to_try_value = cast(int, values["pushes_to_try"])
    return OracleCapture(
        raw_save=cast(str, values["raw_save"]),
        state_identity=_located(
            reader, lambda: _validate_state_identity(state_identity_text)
        ),
        level=cast(str, values["level"]),
        overworld=cast(bool, values["overworld"]),
        won=cast(bool, values["won"]),
        returning=cast(bool, values["returning"]),
        have_ever_cooked_all=cast(bool, values["have_ever_cooked_all"]),
        lost_reason=cast(str, values["lost_reason"]),
        display_name=cast(str, values["display_name"]),
        sausages_cooked=_located(
            reader,
            lambda: _nonnegative(
                sausages_cooked_value, field="sausages_cooked"
            ),
        ),
        movement_count=_located(
            reader,
            lambda: _nonnegative(movement_count_value, field="movement_count"),
        ),
        pushes_to_try=_located(
            reader,
            lambda: _nonnegative(pushes_to_try_value, field="pushes_to_try"),
        ),
    )
```

Replace the complete structural `_decode_initial` with:

```python
def _decode_initial(reader: _CanonicalJsonReader) -> _DecodedLine:
    values = reader.read_object(
        (
            ("kind", reader.read_string),
            ("schema_version", reader.read_integer),
            ("run_id", reader.read_string),
            ("input_index", lambda: reader.read_optional(reader.read_integer)),
            ("capture", lambda: _read_capture(reader)),
        )
    )
    reader.finish()
    schema_version, run_id = _validate_common(
        reader, values, expected_kind="initial"
    )
    if values["input_index"] is not None:
        _record_error(reader, "initial input_index must be null")
    return _DecodedLine(
        kind="initial",
        schema_version=schema_version,
        run_id=run_id,
        record=InitialRecord(capture=cast(OracleCapture, values["capture"])),
    )
```

- [ ] **Step 4: Run capture semantics GREEN**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py -k \
  'invalid_initial_or_capture_semantics or long_state_identity_before_conversion'
git diff --check
```

Expected: `4 passed`; the long identity reaches `state_identity exceeds 11 characters` before `int`, and `git diff --check` prints nothing and exits `0`.

- [ ] **Step 5: Commit strict initial/capture validation**

Commit:

```bash
git add src/ssr_env/oracle_protocol.py tests/test_oracle_protocol.py
git commit -m "feat: validate oracle initial captures"
```

---

### Task 10: Validate step semantics

**Files:**
- Modify: `src/ssr_env/oracle_protocol.py`
- Modify: `tests/test_oracle_protocol.py`

**Interfaces:**
- Consumes: `InputName`, `OracleCapture`, `StepRecord`, and `_DecodedLine` from Task 4; `_input_name(value: str, *, allow_none: bool = False) -> InputName` and `_nonnegative(value: int, *, field: str, maximum: int = 2**31 - 1) -> int` from Task 5; `_CanonicalJsonReader(payload: bytes, line_number: int, *, source: str)`, `_located(reader: _CanonicalJsonReader, operation: Callable[[], _T]) -> _T`, `_record_error(reader: _CanonicalJsonReader, message: str) -> NoReturn`, and `_read_capture(reader: _CanonicalJsonReader) -> OracleCapture` from Tasks 6 and 9; structural `_decode_step(reader: _CanonicalJsonReader) -> _DecodedLine` from Task 7; `_validate_common(reader: _CanonicalJsonReader, values: dict[str, object], *, expected_kind: RecordKind) -> tuple[int, str]` from Task 8.
- Produces: semantically strict `_decode_step(reader: _CanonicalJsonReader) -> _DecodedLine` with `settle_frames in 2..600` and `state_replaced is false`.
- Internal consumers: Tasks 15–20 receive validated step records.
- External plan link: `docs/superpowers/plans/2026-07-31-oracle-passive-trace-implementation.md`, Task 1 executes this task; no private step helper is imported cross-plan.

- [ ] **Step 1: Add the RED step semantic rejection cohort**

Append exactly to `tests/test_oracle_protocol.py`:

```python
BAD_STEP_SEMANTIC_LINES = [
    pytest.param(
        STEP0_LINE.replace(b'"input":"West"', b'"input":"Jump"'),
        id="input",
    ),
    pytest.param(
        STEP0_LINE.replace(b'"input_index":0', b'"input_index":-1'),
        id="index",
    ),
    pytest.param(
        STEP0_LINE.replace(b'"settle_frames":2', b'"settle_frames":0'),
        id="step-settle-zero",
    ),
    pytest.param(
        STEP0_LINE.replace(b'"settle_frames":2', b'"settle_frames":1'),
        id="step-settle-low",
    ),
    pytest.param(
        STEP0_LINE.replace(b'"settle_frames":2', b'"settle_frames":601'),
        id="step-settle-high",
    ),
    pytest.param(
        STEP0_LINE.replace(
            b'"state_replaced":false', b'"state_replaced":true'
        ),
        id="state-replaced",
    ),
]


@pytest.mark.parametrize("payload", BAD_STEP_SEMANTIC_LINES)
def test_record_decoder_rejects_invalid_step_semantics(payload: bytes) -> None:
    with pytest.raises(OracleProtocolError):
        _decode_record(payload, 3, source="bad-step-semantics")
```

- [ ] **Step 2: Run step semantics and confirm behavioral RED**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py::test_record_decoder_rejects_invalid_step_semantics
```

Expected: `6 failed`, each with `DID NOT RAISE OracleProtocolError`. Task 7 decodes all six values into `StepRecord`, so generic unsupported-kind rejection cannot satisfy this cohort.

- [ ] **Step 3: Replace structural step decoding with strict validation**

Replace the complete `_decode_step` with:

```python
def _decode_step(reader: _CanonicalJsonReader) -> _DecodedLine:
    values = reader.read_object(
        (
            ("kind", reader.read_string),
            ("schema_version", reader.read_integer),
            ("run_id", reader.read_string),
            ("input_index", reader.read_integer),
            ("input", reader.read_string),
            ("accepted", reader.read_boolean),
            ("movement_scheduled", reader.read_boolean),
            ("settle_frames", reader.read_integer),
            ("state_replaced", reader.read_boolean),
            ("capture", lambda: _read_capture(reader)),
        )
    )
    reader.finish()
    schema_version, run_id = _validate_common(
        reader, values, expected_kind="step"
    )
    index_value = cast(int, values["input_index"])
    input_text = cast(str, values["input"])
    settle_frames = cast(int, values["settle_frames"])
    input_index = _located(
        reader, lambda: _nonnegative(index_value, field="input_index")
    )
    input_name = _located(reader, lambda: _input_name(input_text))
    if not 2 <= settle_frames <= 600:
        _record_error(reader, "step settle_frames must be in 2..600")
    state_replaced = cast(bool, values["state_replaced"])
    if state_replaced:
        _record_error(reader, "schema-v1 step state_replaced must be false")
    return _DecodedLine(
        kind="step",
        schema_version=schema_version,
        run_id=run_id,
        record=StepRecord(
            input_index=input_index,
            input=input_name,
            accepted=cast(bool, values["accepted"]),
            movement_scheduled=cast(bool, values["movement_scheduled"]),
            settle_frames=settle_frames,
            state_replaced=state_replaced,
            capture=cast(OracleCapture, values["capture"]),
        ),
    )
```

- [ ] **Step 4: Run step semantics GREEN**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py::test_record_decoder_rejects_invalid_step_semantics
git diff --check
```

Expected: `6 passed`; `git diff --check` prints nothing and exits `0`.

- [ ] **Step 5: Commit strict step validation**

Commit:

```bash
git add src/ssr_env/oracle_protocol.py tests/test_oracle_protocol.py
git commit -m "feat: validate oracle step records"
```

---

### Task 11: Decode valid end records

**Files:**
- Modify: `src/ssr_env/oracle_protocol.py`
- Modify: `tests/test_oracle_protocol.py`

**Interfaces:**
- Consumes: `RecordKind`, `EndRecord`, and `_DecodedLine` from Task 4; `_CanonicalJsonReader(payload: bytes, line_number: int, *, source: str)`, `_record_error(reader: _CanonicalJsonReader, message: str) -> NoReturn`, `_decode_run(reader: _CanonicalJsonReader) -> _DecodedLine`, and `_decode_initial(reader: _CanonicalJsonReader) -> _DecodedLine` from Task 6; `_decode_step(reader: _CanonicalJsonReader) -> _DecodedLine` and the single three-kind `_decode_record(payload: bytes, line_number: int, *, source: str) -> _DecodedLine` from Task 7.
- Produces: structural `_decode_end(reader: _CanonicalJsonReader) -> _DecodedLine` and one replacement dispatcher supporting `run`, `initial`, `step`, and `end`.
- Internal consumer: Task 12 strengthens `_decode_end`; Task 13 replaces the dispatcher once more to add `error`.
- External plan link: `docs/superpowers/plans/2026-07-31-oracle-passive-trace-implementation.md`, Task 1 executes this task.

- [ ] **Step 1: Add the RED valid-end test**

Append exactly to `tests/test_oracle_protocol.py`:

```python
def test_record_decoder_accepts_valid_end_record() -> None:
    end = _decode_record(END_LINE, 6, source="literal")
    assert end.record == EndRecord(
        input_count=3,
        finished_at_utc="2026-07-31T19:11:00.0000000Z",
    )
```

- [ ] **Step 2: Run the valid-end test and confirm RED**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py::test_record_decoder_accepts_valid_end_record
```

Expected: `1 failed` because the Task 7 dispatcher rejects a valid `end` kind.

- [ ] **Step 3: Add the structural end decoder and replace the dispatcher**

Insert immediately before `_decode_record`:

```python
def _decode_end(reader: _CanonicalJsonReader) -> _DecodedLine:
    values = reader.read_object(
        (
            ("kind", reader.read_string),
            ("schema_version", reader.read_integer),
            ("run_id", reader.read_string),
            ("input_count", reader.read_integer),
            ("finished_at_utc", reader.read_string),
        )
    )
    reader.finish()
    return _DecodedLine(
        kind=cast(RecordKind, values["kind"]),
        schema_version=cast(int, values["schema_version"]),
        run_id=cast(str, values["run_id"]),
        record=EndRecord(
            input_count=cast(int, values["input_count"]),
            finished_at_utc=cast(str, values["finished_at_utc"]),
        ),
    )
```

Delete the complete existing dispatcher and insert this one replacement:

```python
def _decode_record(
    payload: bytes, line_number: int, *, source: str
) -> _DecodedLine:
    reader = _CanonicalJsonReader(payload, line_number, source=source)
    if payload.startswith(b'{"kind":"run",'):
        return _decode_run(reader)
    if payload.startswith(b'{"kind":"initial",'):
        return _decode_initial(reader)
    if payload.startswith(b'{"kind":"step",'):
        return _decode_step(reader)
    if payload.startswith(b'{"kind":"end",'):
        return _decode_end(reader)
    _record_error(reader, "kind must be the first key and use a schema-v1 value")
    raise AssertionError("unreachable")
```

- [ ] **Step 4: Run valid-end GREEN**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py::test_record_decoder_accepts_valid_end_record \
  tests/test_oracle_protocol.py::test_decoder_source_has_exactly_one_record_dispatcher
git diff --check
```

Expected: `2 passed`; exactly one dispatcher remains, and `git diff --check` prints nothing and exits `0`.

- [ ] **Step 5: Commit valid end decoding**

Commit:

```bash
git add src/ssr_env/oracle_protocol.py tests/test_oracle_protocol.py
git commit -m "feat: structurally decode oracle end records"
```

---

### Task 12: Validate end-record semantics

**Files:**
- Modify: `src/ssr_env/oracle_protocol.py`
- Modify: `tests/test_oracle_protocol.py`

**Interfaces:**
- Consumes: `EndRecord` and `_DecodedLine` from Task 4; `_timestamp_key(value: str, *, field: str = "timestamp") -> tuple[int, int, int, int, int, int, int]` and `_nonnegative(value: int, *, field: str, maximum: int = 2**31 - 1) -> int` from Task 5; `_CanonicalJsonReader(payload: bytes, line_number: int, *, source: str)` and `_located(reader: _CanonicalJsonReader, operation: Callable[[], _T]) -> _T` from Task 6; `_validate_common(reader: _CanonicalJsonReader, values: dict[str, object], *, expected_kind: RecordKind) -> tuple[int, str]` from Task 8; structural `_decode_end(reader: _CanonicalJsonReader) -> _DecodedLine` from Task 11.
- Produces: semantically strict `_decode_end(reader: _CanonicalJsonReader) -> _DecodedLine`.
- Internal consumers: Tasks 15–20 receive validated success terminals.
- External plan link: `docs/superpowers/plans/2026-07-31-oracle-passive-trace-implementation.md`, Task 1 executes this task.

- [ ] **Step 1: Add the RED end semantic rejection cohort**

Append exactly to `tests/test_oracle_protocol.py`:

```python
BAD_END_SEMANTIC_LINES = [
    pytest.param(
        END_LINE.replace(b'"input_count":3', b'"input_count":-1'),
        id="end-count",
    ),
    pytest.param(
        END_LINE.replace(
            b"2026-07-31T19:11:00.0000000Z",
            b"2026-07-31T19:11:00.000000Z",
        ),
        id="finish-timestamp",
    ),
]


@pytest.mark.parametrize("payload", BAD_END_SEMANTIC_LINES)
def test_record_decoder_rejects_invalid_end_semantics(payload: bytes) -> None:
    with pytest.raises(OracleProtocolError):
        _decode_record(payload, 6, source="bad-end-semantics")
```

- [ ] **Step 2: Run end semantics and confirm behavioral RED**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py::test_record_decoder_rejects_invalid_end_semantics
```

Expected: `2 failed`, each with `DID NOT RAISE OracleProtocolError`. Task 11 structurally decodes both rows.

- [ ] **Step 3: Replace structural end decoding with strict validation**

Replace the complete `_decode_end` with:

```python
def _decode_end(reader: _CanonicalJsonReader) -> _DecodedLine:
    values = reader.read_object(
        (
            ("kind", reader.read_string),
            ("schema_version", reader.read_integer),
            ("run_id", reader.read_string),
            ("input_count", reader.read_integer),
            ("finished_at_utc", reader.read_string),
        )
    )
    reader.finish()
    schema_version, run_id = _validate_common(
        reader, values, expected_kind="end"
    )
    input_count_value = cast(int, values["input_count"])
    input_count = _located(
        reader, lambda: _nonnegative(input_count_value, field="input_count")
    )
    finished_at_utc = cast(str, values["finished_at_utc"])
    _located(
        reader,
        lambda: _timestamp_key(finished_at_utc, field="finished_at_utc"),
    )
    return _DecodedLine(
        kind="end",
        schema_version=schema_version,
        run_id=run_id,
        record=EndRecord(
            input_count=input_count,
            finished_at_utc=finished_at_utc,
        ),
    )
```

- [ ] **Step 4: Run end semantics GREEN**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py::test_record_decoder_rejects_invalid_end_semantics
git diff --check
```

Expected: `2 passed`; `git diff --check` prints nothing and exits `0`.

- [ ] **Step 5: Commit strict end validation**

Commit:

```bash
git add src/ssr_env/oracle_protocol.py tests/test_oracle_protocol.py
git commit -m "feat: validate oracle end records"
```

---

### Task 13: Decode valid terminal-error records

**Files:**
- Modify: `src/ssr_env/oracle_protocol.py`
- Modify: `tests/test_oracle_protocol.py`

**Interfaces:**
- Consumes: `InputName`, `RecordKind`, `OracleCapture`, `ErrorRecord`, and `_DecodedLine` from Task 4; `_CanonicalJsonReader(payload: bytes, line_number: int, *, source: str)`, `_read_capture(reader: _CanonicalJsonReader) -> OracleCapture`, `_record_error(reader: _CanonicalJsonReader, message: str) -> NoReturn`, `_decode_run(reader: _CanonicalJsonReader) -> _DecodedLine`, and `_decode_initial(reader: _CanonicalJsonReader) -> _DecodedLine` from Tasks 6 and 9; `_decode_step(reader: _CanonicalJsonReader) -> _DecodedLine` from Task 10; `_decode_end(reader: _CanonicalJsonReader) -> _DecodedLine` and the single four-kind `_decode_record(payload: bytes, line_number: int, *, source: str) -> _DecodedLine` from Tasks 11–12.
- Produces: structural `_decode_error(reader: _CanonicalJsonReader) -> _DecodedLine` and the complete single `_decode_record(payload: bytes, line_number: int, *, source: str) -> _DecodedLine` supporting all five kinds.
- Internal consumer: Task 14 strengthens `_decode_error`; Tasks 15–20 consume the complete dispatcher.
- External plan link: `docs/superpowers/plans/2026-07-31-oracle-passive-trace-implementation.md`, Task 1 executes this task.

- [ ] **Step 1: Add the RED valid-error test**

Append exactly to `tests/test_oracle_protocol.py`:

```python
def test_record_decoder_accepts_valid_error_record() -> None:
    error = _decode_record(ERROR_LINE, 4, source="literal")
    assert error.record == ErrorRecord(
        input_index=1,
        input="North",
        code="settle_timeout",
        message="input did not settle",
        settle_frames=600,
        last_capture=_expected_capture("moved"),
    )
```

- [ ] **Step 2: Run the valid-error test and confirm RED**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py::test_record_decoder_accepts_valid_error_record
```

Expected: `1 failed` because the Task 11 dispatcher rejects a valid `error` kind.

- [ ] **Step 3: Add the structural error decoder and replace the dispatcher**

Insert immediately before `_decode_record`:

```python
def _decode_error(reader: _CanonicalJsonReader) -> _DecodedLine:
    values = reader.read_object(
        (
            ("kind", reader.read_string),
            ("schema_version", reader.read_integer),
            ("run_id", reader.read_string),
            ("input_index", lambda: reader.read_optional(reader.read_integer)),
            ("input", lambda: reader.read_optional(reader.read_string)),
            ("code", reader.read_string),
            ("message", reader.read_string),
            ("settle_frames", reader.read_integer),
            (
                "last_capture",
                lambda: reader.read_optional(lambda: _read_capture(reader)),
            ),
        )
    )
    reader.finish()
    return _DecodedLine(
        kind=cast(RecordKind, values["kind"]),
        schema_version=cast(int, values["schema_version"]),
        run_id=cast(str, values["run_id"]),
        record=ErrorRecord(
            input_index=cast(int | None, values["input_index"]),
            input=cast(InputName | None, values["input"]),
            code=cast(str, values["code"]),
            message=cast(str, values["message"]),
            settle_frames=cast(int, values["settle_frames"]),
            last_capture=cast(
                OracleCapture | None, values["last_capture"]
            ),
        ),
    )
```

Delete the complete existing dispatcher and insert this one replacement:

```python
def _decode_record(
    payload: bytes, line_number: int, *, source: str
) -> _DecodedLine:
    reader = _CanonicalJsonReader(payload, line_number, source=source)
    if payload.startswith(b'{"kind":"run",'):
        return _decode_run(reader)
    if payload.startswith(b'{"kind":"initial",'):
        return _decode_initial(reader)
    if payload.startswith(b'{"kind":"step",'):
        return _decode_step(reader)
    if payload.startswith(b'{"kind":"end",'):
        return _decode_end(reader)
    if payload.startswith(b'{"kind":"error",'):
        return _decode_error(reader)
    _record_error(reader, "kind must be the first key and use a schema-v1 value")
    raise AssertionError("unreachable")
```

- [ ] **Step 4: Add the parser-inherited incomplete-capture regression**

Append exactly to `tests/test_oracle_protocol.py`:

```python
def test_record_decoder_rejects_incomplete_error_last_capture() -> None:
    payload = ERROR_LINE.replace(MOVED_CAPTURE_JSON.encode(), b"{}")
    with pytest.raises(OracleProtocolError):
        _decode_record(payload, 4, source="incomplete-error-capture")
```

- [ ] **Step 5: Run valid-error/dispatcher GREEN**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py -k \
  'record_decoder_accepts_valid_error or incomplete_error_last_capture or decoder_source_has_exactly_one'
git diff --check
```

Expected: `3 passed`; exactly one complete dispatcher remains, and `git diff --check` prints nothing and exits `0`.

- [ ] **Step 6: Commit valid terminal-error decoding**

Commit:

```bash
git add src/ssr_env/oracle_protocol.py tests/test_oracle_protocol.py
git commit -m "feat: structurally decode oracle errors"
```

---

### Task 14: Validate terminal-error semantics

**Files:**
- Modify: `src/ssr_env/oracle_protocol.py`
- Modify: `tests/test_oracle_protocol.py`

**Interfaces:**
- Consumes: `InputName`, `OracleCapture`, `ErrorRecord`, `_ERROR_MESSAGES: Mapping[str, str]`, and `_DecodedLine` from Task 4; `_input_name(value: str, *, allow_none: bool = False) -> InputName` and `_nonnegative(value: int, *, field: str, maximum: int = 2**31 - 1) -> int` from Task 5; `_CanonicalJsonReader(payload: bytes, line_number: int, *, source: str)`, `_located(reader: _CanonicalJsonReader, operation: Callable[[], _T]) -> _T`, `_record_error(reader: _CanonicalJsonReader, message: str) -> NoReturn`, and `_read_capture(reader: _CanonicalJsonReader) -> OracleCapture` from Tasks 6 and 9; `_validate_common(reader: _CanonicalJsonReader, values: dict[str, object], *, expected_kind: RecordKind) -> tuple[int, str]` from Task 8; structural `_decode_error(reader: _CanonicalJsonReader) -> _DecodedLine` from Task 13.
- Produces: semantically strict `_decode_error(reader: _CanonicalJsonReader) -> _DecodedLine` with `settle_frames in 0..600` and exact private error code/message pairing.
- Internal consumers: Tasks 15–20 receive validated error terminals.
- External plan link: `docs/superpowers/plans/2026-07-31-oracle-passive-trace-implementation.md`, Task 1 executes this task; no decoder symbol is imported cross-plan.

- [ ] **Step 1: Add the RED error semantic rejection cohort**

Append exactly to `tests/test_oracle_protocol.py`:

```python
BAD_ERROR_SEMANTIC_LINES = [
    pytest.param(
        ERROR_LINE.replace(b'"settle_frames":600', b'"settle_frames":-1'),
        id="error-settle-low",
    ),
    pytest.param(
        ERROR_LINE.replace(b'"settle_frames":600', b'"settle_frames":601'),
        id="error-settle-high",
    ),
    pytest.param(
        ERROR_LINE.replace(
            b'"message":"input did not settle"', b'"message":"wrong"'
        ),
        id="error-message-pair",
    ),
    pytest.param(
        ERROR_LINE.replace(
            b'"code":"settle_timeout","message":"input did not settle"',
            b'"code":"invalid_mode","message":"input did not settle"',
        ),
        id="marker-only-code",
    ),
    pytest.param(
        ERROR_LINE.replace(b'"input":"North"', b'"input":"Jump"'),
        id="error-input",
    ),
]


@pytest.mark.parametrize("payload", BAD_ERROR_SEMANTIC_LINES)
def test_record_decoder_rejects_invalid_error_semantics(payload: bytes) -> None:
    with pytest.raises(OracleProtocolError):
        _decode_record(payload, 4, source="bad-error-semantics")
```

- [ ] **Step 2: Run error semantics and confirm behavioral RED**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py::test_record_decoder_rejects_invalid_error_semantics
```

Expected: `5 failed`, each with `DID NOT RAISE OracleProtocolError`. Task 13 constructs all five `ErrorRecord` values, so unsupported-kind rejection cannot satisfy the cohort.

- [ ] **Step 3: Replace structural error decoding with strict validation**

Replace the complete `_decode_error` with:

```python
def _decode_error(reader: _CanonicalJsonReader) -> _DecodedLine:
    values = reader.read_object(
        (
            ("kind", reader.read_string),
            ("schema_version", reader.read_integer),
            ("run_id", reader.read_string),
            ("input_index", lambda: reader.read_optional(reader.read_integer)),
            ("input", lambda: reader.read_optional(reader.read_string)),
            ("code", reader.read_string),
            ("message", reader.read_string),
            ("settle_frames", reader.read_integer),
            (
                "last_capture",
                lambda: reader.read_optional(lambda: _read_capture(reader)),
            ),
        )
    )
    reader.finish()
    schema_version, run_id = _validate_common(
        reader, values, expected_kind="error"
    )
    raw_index = cast(int | None, values["input_index"])
    input_index = (
        None
        if raw_index is None
        else _located(
            reader, lambda: _nonnegative(raw_index, field="input_index")
        )
    )
    raw_input = cast(str | None, values["input"])
    input_name = (
        None
        if raw_input is None
        else _located(reader, lambda: _input_name(raw_input, allow_none=True))
    )
    code = cast(str, values["code"])
    message = cast(str, values["message"])
    expected_message = _ERROR_MESSAGES.get(code)
    if expected_message is None:
        _record_error(reader, "error code is not in the schema-v1 record table")
    if message != expected_message:
        _record_error(reader, "error code/message pair is not canonical")
    settle_frames = cast(int, values["settle_frames"])
    if not 0 <= settle_frames <= 600:
        _record_error(reader, "error settle_frames must be in 0..600")
    return _DecodedLine(
        kind="error",
        schema_version=schema_version,
        run_id=run_id,
        record=ErrorRecord(
            input_index=input_index,
            input=input_name,
            code=code,
            message=message,
            settle_frames=settle_frames,
            last_capture=cast(
                OracleCapture | None, values["last_capture"]
            ),
        ),
    )
```

- [ ] **Step 4: Run error semantics GREEN**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py::test_record_decoder_rejects_invalid_error_semantics
git diff --check
```

Expected: `5 passed`; `git diff --check` prints nothing and exits `0`.

- [ ] **Step 5: Commit strict terminal-error validation**

Commit:

```bash
git add src/ssr_env/oracle_protocol.py tests/test_oracle_protocol.py
git commit -m "feat: validate oracle error records"
```

---

### Task 15: Assemble a valid success trace from the open stream

**Files:**
- Modify: `src/ssr_env/oracle_protocol.py`
- Modify: `tests/test_oracle_protocol.py`

**Interfaces:**
- Consumes: `_read_record_lines(stream: BinaryIO, *, source: str) -> Iterator[tuple[int, bytes]]` and `OracleProtocolError` from Task 1; `RunHeader`, `InitialRecord`, `StepRecord`, `EndRecord`, `ErrorRecord`, `OracleRun`, `TerminalOutcome`, and `_DecodedLine` from Task 4; complete `_decode_record(payload: bytes, line_number: int, *, source: str) -> _DecodedLine` from Tasks 6–14.
- Produces: `_sequence_error(source: str, message: str) -> NoReturn`, lazy `_decode_trace_lines(stream: BinaryIO, *, source: str) -> Iterator[_DecodedLine]`, and success-only `read_oracle_trace_stream(stream: BinaryIO, *, source: str) -> OracleRun`.
- The stream API consumes the supplied descriptor at its current position and never resolves or reopens `source`; `source` is diagnostic text only.
- Internal consumers: Tasks 16–20 incrementally complete sequence validation without changing the public signature.
- External consumers: `docs/superpowers/plans/2026-07-31-oracle-passive-probe.md`, Tasks 10A–10C declare and consume `read_oracle_trace_stream(stream: BinaryIO, *, source: str) -> OracleRun`; `docs/superpowers/plans/2026-07-31-oracle-passive-trace-implementation.md`, Task 1 executes this task.

- [ ] **Step 1: Add trace literals and the RED valid-success test**

Append exactly to `tests/test_oracle_protocol.py`:

```python
from ssr_env.oracle_protocol import read_oracle_trace_stream


def _trace_bytes(*records: bytes) -> bytes:
    return b"\n".join(records) + b"\n"


SUCCESS_TRACE_BYTES = _trace_bytes(
    RUN_LINE,
    INITIAL_LINE,
    STEP0_LINE,
    STEP1_LINE,
    STEP2_LINE,
    END_LINE,
)
ERROR_TRACE_BYTES = _trace_bytes(
    RUN_LINE,
    INITIAL_LINE,
    STEP0_LINE,
    ERROR_LINE,
)
RUN_ONLY_ERROR_LINE = (
    f'{{"kind":"error","schema_version":{SCHEMA_VERSION},'
    f'"run_id":"{RUN_ID}","input_index":null,"input":null,'
    '"code":"capture_failed","message":"game-state capture failed",'
    '"settle_frames":0,"last_capture":null}'
).encode("utf-8")
ERROR_INDEX_0_LINE = ERROR_LINE.replace(b'"input_index":1', b'"input_index":0')
ERROR_INDEX_2_LINE = ERROR_LINE.replace(b'"input_index":1', b'"input_index":2')
ERROR_INDEX_3_LINE = ERROR_LINE.replace(b'"input_index":1', b'"input_index":3')


def test_trace_stream_accepts_complete_success_shape() -> None:
    trace = read_oracle_trace_stream(
        io.BytesIO(SUCCESS_TRACE_BYTES), source="success-memory"
    )
    assert trace.header == RunHeader(
        run_id=RUN_ID,
        game_assembly_sha256=ASSEMBLY_HASH,
        started_at_utc="2026-07-31T19:09:50.3199100Z",
    )
    assert trace.initial == InitialRecord(capture=_expected_capture("initial"))
    assert trace.steps == (
        StepRecord(
            input_index=0,
            input="West",
            accepted=True,
            movement_scheduled=True,
            settle_frames=2,
            state_replaced=False,
            capture=_expected_capture("moved"),
        ),
        StepRecord(
            input_index=1,
            input="North",
            accepted=False,
            movement_scheduled=False,
            settle_frames=2,
            state_replaced=False,
            capture=_expected_capture("moved"),
        ),
        StepRecord(
            input_index=2,
            input="Undo",
            accepted=True,
            movement_scheduled=False,
            settle_frames=2,
            state_replaced=False,
            capture=_expected_capture("initial"),
        ),
    )
    assert trace.terminal == EndRecord(
        input_count=3,
        finished_at_utc="2026-07-31T19:11:00.0000000Z",
    )
    assert trace.outcome == "success"
```

- [ ] **Step 2: Run the valid-success test and confirm RED**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py::test_trace_stream_accepts_complete_success_shape
```

Expected: collection fails with `ImportError: cannot import name 'read_oracle_trace_stream'`.

- [ ] **Step 3: Implement success-only descriptor-stream assembly**

Append exactly:

```python
def _sequence_error(source: str, message: str) -> NoReturn:
    raise OracleProtocolError(f"{source}: {message}")


def _decode_trace_lines(
    stream: BinaryIO, *, source: str
) -> Iterator[_DecodedLine]:
    for line_number, payload in _read_record_lines(stream, source=source):
        yield _decode_record(payload, line_number, source=source)


def read_oracle_trace_stream(
    stream: BinaryIO, *, source: str
) -> OracleRun:
    decoded = list(_decode_trace_lines(stream, source=source))
    header = cast(RunHeader, decoded[0].record)
    initial = cast(InitialRecord, decoded[1].record)
    steps = tuple(
        cast(StepRecord, item.record) for item in decoded[2:-1]
    )
    terminal = decoded[-1].record
    if not isinstance(terminal, EndRecord):
        _sequence_error(source, "terminal-error support is not implemented")
    outcome: TerminalOutcome = "success"
    return OracleRun(
        header=header,
        initial=initial,
        steps=steps,
        terminal=terminal,
        outcome=outcome,
    )
```

- [ ] **Step 4: Run valid-success GREEN**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py::test_trace_stream_accepts_complete_success_shape
git diff --check
```

Expected: `1 passed`; `git diff --check` prints nothing and exits `0`.

- [ ] **Step 5: Commit success-trace assembly**

Commit:

```bash
git add src/ssr_env/oracle_protocol.py tests/test_oracle_protocol.py
git commit -m "feat: assemble successful oracle traces"
```

---

### Task 16: Accept every allowed terminal-error prefix

**Files:**
- Modify: `src/ssr_env/oracle_protocol.py`
- Modify: `tests/test_oracle_protocol.py`

**Interfaces:**
- Consumes: `RunHeader`, `InitialRecord`, `StepRecord`, `EndRecord`, `ErrorRecord`, `OracleRun`, `TerminalOutcome`, and `_DecodedLine` from Task 4; `_decode_trace_lines(stream: BinaryIO, *, source: str) -> Iterator[_DecodedLine]` and success-only `read_oracle_trace_stream(stream: BinaryIO, *, source: str) -> OracleRun` from Task 15.
- Produces: `read_oracle_trace_stream(stream: BinaryIO, *, source: str) -> OracleRun` accepting `run,error` and initial-plus-step prefixes of lengths `0`, `1`, `2`, and `3`.
- Internal consumers: Tasks 17–20 add rejection rules around these valid shapes.
- External consumers: `docs/superpowers/plans/2026-07-31-oracle-passive-probe.md`, Tasks 10A–10C consume the completed stream API; `docs/superpowers/plans/2026-07-31-oracle-passive-trace-implementation.md`, Task 1 executes this task.

- [ ] **Step 1: Add the RED valid terminal-error tests**

Append exactly to `tests/test_oracle_protocol.py`:

```python
def test_trace_stream_accepts_initial_step_error_prefix() -> None:
    trace = read_oracle_trace_stream(
        io.BytesIO(ERROR_TRACE_BYTES), source="error-memory"
    )
    assert trace.initial == InitialRecord(capture=_expected_capture("initial"))
    assert len(trace.steps) == 1
    assert trace.steps[0].input_index == 0
    assert trace.terminal == ErrorRecord(
        input_index=1,
        input="North",
        code="settle_timeout",
        message="input did not settle",
        settle_frames=600,
        last_capture=_expected_capture("moved"),
    )
    assert trace.outcome == "error"


def test_trace_stream_accepts_run_error_shape() -> None:
    trace = read_oracle_trace_stream(
        io.BytesIO(_trace_bytes(RUN_LINE, RUN_ONLY_ERROR_LINE)),
        source="startup-error-memory",
    )
    assert trace.initial is None
    assert trace.steps == ()
    assert trace.terminal == ErrorRecord(
        input_index=None,
        input=None,
        code="capture_failed",
        message="game-state capture failed",
        settle_frames=0,
        last_capture=None,
    )
    assert trace.outcome == "error"


@pytest.mark.parametrize(
    ("steps", "error_line", "expected_count"),
    [
        ((), ERROR_INDEX_0_LINE, 0),
        ((STEP0_LINE, STEP1_LINE), ERROR_INDEX_2_LINE, 2),
        ((STEP0_LINE, STEP1_LINE, STEP2_LINE), ERROR_INDEX_3_LINE, 3),
    ],
    ids=["zero", "two", "three"],
)
def test_trace_stream_accepts_every_other_error_prefix_length(
    steps: tuple[bytes, ...], error_line: bytes, expected_count: int
) -> None:
    payload = _trace_bytes(RUN_LINE, INITIAL_LINE, *steps, error_line)
    trace = read_oracle_trace_stream(
        io.BytesIO(payload), source=f"prefix-{expected_count}"
    )
    assert trace.outcome == "error"
    assert len(trace.steps) == expected_count
    assert isinstance(trace.terminal, ErrorRecord)
    assert trace.terminal.input_index == expected_count
```

- [ ] **Step 2: Run valid terminal-error shapes and confirm RED**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py -k 'trace_stream_accepts and error'
```

Expected: `5 failed` because Task 15 rejects every `ErrorRecord` terminal with `terminal-error support is not implemented`.

- [ ] **Step 3: Extend stream assembly to terminal errors**

Replace the complete `read_oracle_trace_stream` with:

```python
def read_oracle_trace_stream(
    stream: BinaryIO, *, source: str
) -> OracleRun:
    decoded = list(_decode_trace_lines(stream, source=source))
    header = cast(RunHeader, decoded[0].record)
    terminal = cast(EndRecord | ErrorRecord, decoded[-1].record)
    if isinstance(terminal, ErrorRecord) and len(decoded) == 2:
        initial = None
        steps: tuple[StepRecord, ...] = ()
    else:
        initial = cast(InitialRecord, decoded[1].record)
        steps = tuple(
            cast(StepRecord, item.record) for item in decoded[2:-1]
        )
    outcome: TerminalOutcome = (
        "error" if isinstance(terminal, ErrorRecord) else "success"
    )
    return OracleRun(
        header=header,
        initial=initial,
        steps=steps,
        terminal=terminal,
        outcome=outcome,
    )
```

- [ ] **Step 4: Run terminal-error shape GREEN**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py -k 'trace_stream_accepts'
git diff --check
```

Expected: `6 passed` total: one success, `run,error`, and initial prefixes of lengths `0`, `1`, `2`, and `3`. `git diff --check` prints nothing and exits `0`.

- [ ] **Step 5: Commit valid terminal-error assembly**

Commit:

```bash
git add src/ssr_env/oracle_protocol.py tests/test_oracle_protocol.py
git commit -m "feat: assemble oracle error traces"
```

---

### Task 17: Reject invalid trace boundaries and terminal placement

**Files:**
- Modify: `src/ssr_env/oracle_protocol.py`
- Modify: `tests/test_oracle_protocol.py`

**Interfaces:**
- Consumes: `RunHeader`, `InitialRecord`, `StepRecord`, `EndRecord`, `ErrorRecord`, `OracleRun`, `TerminalOutcome`, and `_DecodedLine` from Task 4; `_decode_trace_lines(stream: BinaryIO, *, source: str) -> Iterator[_DecodedLine]`, `_sequence_error(source: str, message: str) -> NoReturn`, and permissive `read_oracle_trace_stream(stream: BinaryIO, *, source: str) -> OracleRun` from Tasks 15–16.
- Produces: the same stream API with exact first-run, single-run, required-terminal, and no-record-after-terminal rules.
- Internal consumers: Tasks 18–20 strengthen ordering, success, and error relations.
- External consumers: `docs/superpowers/plans/2026-07-31-oracle-passive-probe.md`, Tasks 10A–10C; `docs/superpowers/plans/2026-07-31-oracle-passive-trace-implementation.md`, Task 1.

- [ ] **Step 1: Add the RED boundary/terminal rejection cohort**

Append exactly to `tests/test_oracle_protocol.py`:

```python
import re


BAD_SEQUENCE_BOUNDARY_TRACES = [
    pytest.param(
        b"",
        "trace is empty; first record must be run",
        id="empty",
    ),
    pytest.param(
        _trace_bytes(INITIAL_LINE),
        "first record must be run",
        id="initial-before-run",
    ),
    pytest.param(
        _trace_bytes(ERROR_LINE),
        "first record must be run",
        id="error-before-run",
    ),
    pytest.param(
        _trace_bytes(RUN_LINE, RUN_LINE, RUN_ONLY_ERROR_LINE),
        "run record may appear only once",
        id="two-runs",
    ),
    pytest.param(
        _trace_bytes(RUN_LINE, INITIAL_LINE, STEP0_LINE, STEP1_LINE, STEP2_LINE),
        "trace has no terminal end or error record",
        id="missing-terminal",
    ),
    pytest.param(
        SUCCESS_TRACE_BYTES + STEP0_LINE + b"\n",
        "record appears after terminal record",
        id="record-after-end",
    ),
    pytest.param(
        SUCCESS_TRACE_BYTES + ERROR_LINE + b"\n",
        "record appears after terminal record",
        id="error-after-end",
    ),
    pytest.param(
        ERROR_TRACE_BYTES + STEP1_LINE + b"\n",
        "record appears after terminal record",
        id="record-after-error",
    ),
]


@pytest.mark.parametrize(("payload", "message"), BAD_SEQUENCE_BOUNDARY_TRACES)
def test_trace_stream_rejects_invalid_boundaries(
    payload: bytes, message: str
) -> None:
    with pytest.raises(OracleProtocolError, match=re.escape(message)):
        read_oracle_trace_stream(io.BytesIO(payload), source="bad-boundary")


class _StopAfterTwoLines(io.BytesIO):
    def __init__(self, payload: bytes) -> None:
        super().__init__(payload)
        self.readline_calls = 0

    def readline(self, size: int = -1, /) -> bytes:
        self.readline_calls += 1
        if self.readline_calls > 2:
            raise AssertionError("parser consumed the tail after a second run")
        return super().readline(size)


def test_trace_stream_stops_at_first_sequence_invalid_record() -> None:
    stream = _StopAfterTwoLines(
        _trace_bytes(RUN_LINE, RUN_LINE, *([STEP0_LINE] * 32))
    )
    with pytest.raises(
        OracleProtocolError, match="run record may appear only once"
    ):
        read_oracle_trace_stream(stream, source="guarded-tail")
    assert stream.readline_calls == 2
```

- [ ] **Step 2: Run boundary/terminal rejection and confirm behavioral RED**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py -k \
  'trace_stream_rejects_invalid_boundaries or trace_stream_stops_at_first_sequence_invalid_record'
```

Expected: `9 failed`. The eight matrix rows either return a malformed `OracleRun` or raise a non-protocol indexing exception. The guarded-stream row raises its injected `AssertionError` because Task 16 eagerly consumes the third line; none satisfies the exact `OracleProtocolError` contract.

- [ ] **Step 3: Replace permissive assembly with boundary-aware iteration**

Replace the complete `read_oracle_trace_stream` with:

```python
def read_oracle_trace_stream(
    stream: BinaryIO, *, source: str
) -> OracleRun:
    header: RunHeader | None = None
    initial: InitialRecord | None = None
    steps: list[StepRecord] = []
    terminal: EndRecord | ErrorRecord | None = None

    for decoded in _decode_trace_lines(stream, source=source):
        if terminal is not None:
            _sequence_error(source, "record appears after terminal record")

        if header is None:
            if not isinstance(decoded.record, RunHeader):
                _sequence_error(source, "first record must be run")
            header = decoded.record
            continue

        record = decoded.record
        if isinstance(record, RunHeader):
            _sequence_error(source, "run record may appear only once")
        if isinstance(record, InitialRecord):
            initial = record
            continue
        if isinstance(record, StepRecord):
            steps.append(record)
            continue
        if isinstance(record, (EndRecord, ErrorRecord)):
            terminal = record
            continue
        raise AssertionError("unreachable record type")

    if header is None:
        _sequence_error(source, "trace is empty; first record must be run")
    if terminal is None:
        _sequence_error(source, "trace has no terminal end or error record")
    outcome: TerminalOutcome = (
        "success" if isinstance(terminal, EndRecord) else "error"
    )
    return OracleRun(
        header=header,
        initial=initial,
        steps=tuple(steps),
        terminal=terminal,
        outcome=outcome,
    )
```

- [ ] **Step 4: Run boundary/terminal rejection GREEN**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py -k \
  'trace_stream_rejects_invalid_boundaries or trace_stream_stops_at_first_sequence_invalid_record'
git diff --check
```

Expected: `9 passed` with the exact messages; the guarded stream performs exactly two bounded `readline` calls and never consumes the tail. `git diff --check` prints nothing and exits `0`.

- [ ] **Step 5: Commit boundary-aware trace iteration**

Commit:

```bash
git add src/ssr_env/oracle_protocol.py tests/test_oracle_protocol.py
git commit -m "feat: validate oracle trace boundaries"
```

---

### Task 18: Enforce trace identity, initial order, and contiguous steps

**Files:**
- Modify: `src/ssr_env/oracle_protocol.py`
- Modify: `tests/test_oracle_protocol.py`

**Interfaces:**
- Consumes: `EXPECTED_INPUT_COUNT: int` from Task 1; `RunHeader`, `InitialRecord`, and `StepRecord` from Task 4; `_DecodedLine.run_id: str` from Task 4 through `_decode_trace_lines(stream: BinaryIO, *, source: str) -> Iterator[_DecodedLine]`; boundary-aware `read_oracle_trace_stream(stream: BinaryIO, *, source: str) -> OracleRun` and `_sequence_error(source: str, message: str) -> NoReturn` from Task 17.
- Produces: the same stream API with one run identity, initial-before-step ordering, at most three steps, and contiguous zero-based `input_index`.
- Internal consumers: Tasks 19–20 add terminal-specific relations.
- External consumers: `docs/superpowers/plans/2026-07-31-oracle-passive-probe.md`, Tasks 10A–10C; `docs/superpowers/plans/2026-07-31-oracle-passive-trace-implementation.md`, Task 1.

- [ ] **Step 1: Add the RED identity/order/index rejection cohort**

Append exactly to `tests/test_oracle_protocol.py`:

```python
MIXED_STEP0_LINE = STEP0_LINE.replace(RUN_ID.encode(), OTHER_RUN_ID.encode())
REPEATED_STEP_LINE = STEP1_LINE.replace(b'"input_index":1', b'"input_index":0')
SKIPPED_STEP_LINE = STEP1_LINE.replace(b'"input_index":1', b'"input_index":2')
FOURTH_STEP_LINE = (
    STEP2_LINE.replace(b'"input_index":2', b'"input_index":3')
    .replace(b'"input":"Undo"', b'"input":"East"')
)

BAD_SEQUENCE_ORDER_TRACES = [
    pytest.param(
        _trace_bytes(
            RUN_LINE,
            INITIAL_LINE,
            MIXED_STEP0_LINE,
            STEP1_LINE,
            STEP2_LINE,
            END_LINE,
        ),
        "record run_id does not match the run header",
        id="mixed-run-id",
    ),
    pytest.param(
        _trace_bytes(RUN_LINE, STEP0_LINE, STEP1_LINE, STEP2_LINE, END_LINE),
        "step record requires an initial record",
        id="step-without-initial",
    ),
    pytest.param(
        _trace_bytes(
            RUN_LINE,
            INITIAL_LINE,
            INITIAL_LINE,
            STEP0_LINE,
            STEP1_LINE,
            STEP2_LINE,
            END_LINE,
        ),
        "initial record must appear exactly second",
        id="duplicate-initial",
    ),
    pytest.param(
        _trace_bytes(
            RUN_LINE,
            INITIAL_LINE,
            STEP0_LINE,
            SKIPPED_STEP_LINE,
            STEP2_LINE,
            END_LINE,
        ),
        "step input_index is not contiguous",
        id="skipped-index",
    ),
    pytest.param(
        _trace_bytes(
            RUN_LINE,
            INITIAL_LINE,
            STEP0_LINE,
            REPEATED_STEP_LINE,
            STEP2_LINE,
            END_LINE,
        ),
        "step input_index is not contiguous",
        id="repeated-index",
    ),
    pytest.param(
        _trace_bytes(RUN_LINE, INITIAL_LINE, STEP1_LINE, ERROR_LINE),
        "step input_index is not contiguous",
        id="error-prefix-gap",
    ),
    pytest.param(
        _trace_bytes(
            RUN_LINE,
            INITIAL_LINE,
            STEP0_LINE,
            STEP1_LINE,
            STEP2_LINE,
            FOURTH_STEP_LINE,
            END_LINE,
        ),
        "trace contains more than three steps",
        id="fourth-step",
    ),
]


@pytest.mark.parametrize(("payload", "message"), BAD_SEQUENCE_ORDER_TRACES)
def test_trace_stream_rejects_invalid_identity_or_order(
    payload: bytes, message: str
) -> None:
    with pytest.raises(OracleProtocolError, match=re.escape(message)):
        read_oracle_trace_stream(io.BytesIO(payload), source="bad-order")
```

- [ ] **Step 2: Run identity/order/index rejection and confirm behavioral RED**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py::test_trace_stream_rejects_invalid_identity_or_order
```

Expected: `7 failed` with `DID NOT RAISE OracleProtocolError`; Task 17 returns every malformed trace.

- [ ] **Step 3: Insert identity and ordered-step checks**

Inside `read_oracle_trace_stream`, insert this immediately after the `header is None` block:

```python
        if decoded.run_id != header.run_id:
            _sequence_error(source, "record run_id does not match the run header")
```

Replace the `InitialRecord` and `StepRecord` branches with:

```python
        if isinstance(record, InitialRecord):
            if initial is not None or steps:
                _sequence_error(source, "initial record must appear exactly second")
            initial = record
            continue
        if isinstance(record, StepRecord):
            if initial is None:
                _sequence_error(source, "step record requires an initial record")
            if len(steps) >= EXPECTED_INPUT_COUNT:
                _sequence_error(source, "trace contains more than three steps")
            if record.input_index != len(steps):
                _sequence_error(source, "step input_index is not contiguous")
            steps.append(record)
            continue
```

- [ ] **Step 4: Run identity/order/index rejection GREEN**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py::test_trace_stream_rejects_invalid_identity_or_order
git diff --check
```

Expected: `7 passed` with exact messages; `git diff --check` prints nothing and exits `0`.

- [ ] **Step 5: Commit trace identity and step ordering**

Commit:

```bash
git add src/ssr_env/oracle_protocol.py tests/test_oracle_protocol.py
git commit -m "feat: validate oracle trace step order"
```

---

### Task 19: Enforce success-terminal counts and timestamps

**Files:**
- Modify: `src/ssr_env/oracle_protocol.py`
- Modify: `tests/test_oracle_protocol.py`

**Interfaces:**
- Consumes: `EXPECTED_INPUT_COUNT: int` from Task 1; `EndRecord` and `RunHeader` from Task 4; `_timestamp_key(value: str, *, field: str = "timestamp") -> tuple[int, int, int, int, int, int, int]` from Task 5; ordered `read_oracle_trace_stream(stream: BinaryIO, *, source: str) -> OracleRun` and `_sequence_error(source: str, message: str) -> NoReturn` from Task 18.
- Produces: the same stream API with required initial record, exactly three success steps, exact terminal `input_count`, and `finished_at_utc >= started_at_utc`.
- Internal consumer: Task 20 completes terminal-error consistency.
- External consumers: `docs/superpowers/plans/2026-07-31-oracle-passive-probe.md`, Tasks 10A–10C; `docs/superpowers/plans/2026-07-31-oracle-passive-trace-implementation.md`, Task 1.

- [ ] **Step 1: Add the RED success-terminal rejection cohort**

Append exactly to `tests/test_oracle_protocol.py`:

```python
WRONG_END_COUNT_LINE = END_LINE.replace(b'"input_count":3', b'"input_count":2')
EARLY_END_LINE = END_LINE.replace(
    b"2026-07-31T19:11:00.0000000Z",
    b"2026-07-31T19:09:50.3199099Z",
)

BAD_SUCCESS_TERMINAL_TRACES = [
    pytest.param(
        _trace_bytes(RUN_LINE, INITIAL_LINE, STEP0_LINE, STEP1_LINE, END_LINE),
        "success requires exactly three steps",
        id="success-missing-step",
    ),
    pytest.param(
        _trace_bytes(
            RUN_LINE,
            INITIAL_LINE,
            STEP0_LINE,
            STEP1_LINE,
            STEP2_LINE,
            WRONG_END_COUNT_LINE,
        ),
        "end input_count must be three",
        id="wrong-end-count",
    ),
    pytest.param(
        _trace_bytes(
            RUN_LINE,
            INITIAL_LINE,
            STEP0_LINE,
            STEP1_LINE,
            STEP2_LINE,
            EARLY_END_LINE,
        ),
        "finish time precedes start time",
        id="finish-before-start",
    ),
    pytest.param(
        _trace_bytes(RUN_LINE, END_LINE),
        "end record requires an initial record",
        id="end-before-initial",
    ),
    pytest.param(
        _trace_bytes(RUN_LINE, INITIAL_LINE, STEP0_LINE, END_LINE),
        "success requires exactly three steps",
        id="end-before-third-step",
    ),
]


@pytest.mark.parametrize(("payload", "message"), BAD_SUCCESS_TERMINAL_TRACES)
def test_trace_stream_rejects_invalid_success_terminal(
    payload: bytes, message: str
) -> None:
    with pytest.raises(OracleProtocolError, match=re.escape(message)):
        read_oracle_trace_stream(io.BytesIO(payload), source="bad-success")
```

- [ ] **Step 2: Run success-terminal rejection and confirm behavioral RED**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py::test_trace_stream_rejects_invalid_success_terminal
```

Expected: `5 failed` with `DID NOT RAISE OracleProtocolError`; Task 18 returns all five malformed success traces.

- [ ] **Step 3: Add success-terminal validation**

Replace the terminal branch:

```python
        if isinstance(record, (EndRecord, ErrorRecord)):
            terminal = record
            continue
```

with:

```python
        if isinstance(record, EndRecord):
            if initial is None:
                _sequence_error(source, "end record requires an initial record")
            if len(steps) != EXPECTED_INPUT_COUNT:
                _sequence_error(source, "success requires exactly three steps")
            if record.input_count != EXPECTED_INPUT_COUNT:
                _sequence_error(source, "end input_count must be three")
            if _timestamp_key(
                record.finished_at_utc, field="finished_at_utc"
            ) < _timestamp_key(header.started_at_utc, field="started_at_utc"):
                _sequence_error(source, "finish time precedes start time")
            terminal = record
            continue
        if isinstance(record, ErrorRecord):
            terminal = record
            continue
```

Immediately before assigning `outcome` after the loop, insert:

```python
    if isinstance(terminal, EndRecord):
        if initial is None or len(steps) != EXPECTED_INPUT_COUNT:
            _sequence_error(source, "success terminal shape is incomplete")
```

- [ ] **Step 4: Run success-terminal rejection GREEN**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py::test_trace_stream_rejects_invalid_success_terminal
git diff --check
```

Expected: `5 passed` with exact messages; `git diff --check` prints nothing and exits `0`.

- [ ] **Step 5: Commit success-terminal validation**

Commit:

```bash
git add src/ssr_env/oracle_protocol.py tests/test_oracle_protocol.py
git commit -m "feat: validate oracle success terminals"
```

---

### Task 20: Enforce terminal-error index consistency and close the sequence matrix

**Files:**
- Modify: `src/ssr_env/oracle_protocol.py`
- Modify: `tests/test_oracle_protocol.py`

**Interfaces:**
- Consumes: `ErrorRecord` from Task 4; `_sequence_error(source: str, message: str) -> NoReturn` and success-validating `read_oracle_trace_stream(stream: BinaryIO, *, source: str) -> OracleRun` from Task 19; strict `_decode_step(reader: _CanonicalJsonReader) -> _DecodedLine` and `_decode_error(reader: _CanonicalJsonReader) -> _DecodedLine` from Tasks 10 and 14.
- Produces: completed `read_oracle_trace_stream(stream: BinaryIO, *, source: str) -> OracleRun` with error `input_index` equal to the flushed-step count when non-null.
- Produces: a 27-item malformed-sequence regression matrix partitioned across Tasks 17–20, including five record-validation integration rows.
- External consumers: `docs/superpowers/plans/2026-07-31-oracle-passive-probe.md`, Tasks 10A–10C consume the completed stream API; `docs/superpowers/plans/2026-07-31-oracle-passive-trace-implementation.md`, Task 1 executes this task.

- [ ] **Step 1: Add the RED terminal-error index cohort**

Append exactly to `tests/test_oracle_protocol.py`:

```python
WRONG_ERROR_INDEX_LINE = ERROR_LINE.replace(
    b'"input_index":1', b'"input_index":2'
)

BAD_ERROR_TERMINAL_TRACES = [
    pytest.param(
        _trace_bytes(RUN_LINE, INITIAL_LINE, STEP0_LINE, WRONG_ERROR_INDEX_LINE),
        "error input_index must equal the flushed-step count",
        id="error-index-mismatch",
    ),
    pytest.param(
        _trace_bytes(RUN_LINE, ERROR_LINE),
        "error input_index must equal the flushed-step count",
        id="run-error-index-mismatch",
    ),
]


@pytest.mark.parametrize(("payload", "message"), BAD_ERROR_TERMINAL_TRACES)
def test_trace_stream_rejects_invalid_error_terminal(
    payload: bytes, message: str
) -> None:
    with pytest.raises(OracleProtocolError, match=re.escape(message)):
        read_oracle_trace_stream(io.BytesIO(payload), source="bad-error")
```

- [ ] **Step 2: Run terminal-error index rejection and confirm behavioral RED**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py::test_trace_stream_rejects_invalid_error_terminal
```

Expected: `2 failed` with `DID NOT RAISE OracleProtocolError`; Task 19 returns both malformed error traces.

- [ ] **Step 3: Add record-validation integration rows**

Append exactly to `tests/test_oracle_protocol.py`:

```python
BAD_RECORD_IN_SEQUENCE_TRACES = [
    pytest.param(
        _trace_bytes(
            RUN_LINE,
            INITIAL_LINE,
            STEP0_LINE.replace(b'"settle_frames":2', b'"settle_frames":0'),
            ERROR_LINE,
        ),
        id="error-prefix-step-settle-zero",
    ),
    pytest.param(
        _trace_bytes(
            RUN_LINE,
            INITIAL_LINE,
            STEP0_LINE.replace(b'"settle_frames":2', b'"settle_frames":1'),
            ERROR_LINE,
        ),
        id="error-prefix-step-settle-one",
    ),
    pytest.param(
        _trace_bytes(
            RUN_LINE,
            INITIAL_LINE,
            STEP0_LINE.replace(b'"settle_frames":2', b'"settle_frames":601'),
            ERROR_LINE,
        ),
        id="error-prefix-step-settle-high",
    ),
    pytest.param(
        _trace_bytes(
            RUN_LINE,
            INITIAL_LINE,
            STEP0_LINE.replace(
                b'"state_replaced":false', b'"state_replaced":true'
            ),
            ERROR_LINE,
        ),
        id="error-prefix-state-replaced",
    ),
    pytest.param(
        _trace_bytes(
            RUN_LINE,
            INITIAL_LINE,
            STEP0_LINE,
            ERROR_LINE.replace(b'"settle_frames":600', b'"settle_frames":601'),
        ),
        id="error-prefix-error-settle-high",
    ),
]


@pytest.mark.parametrize("payload", BAD_RECORD_IN_SEQUENCE_TRACES)
def test_trace_stream_preserves_record_validation(payload: bytes) -> None:
    with pytest.raises(OracleProtocolError):
        read_oracle_trace_stream(io.BytesIO(payload), source="bad-record")
```

These five integration rows are already GREEN through Tasks 10 and 14. The new behavioral RED in this task is exclusively the two-row error-index cohort.

- [ ] **Step 4: Add terminal-error index validation**

Replace the `ErrorRecord` branch with:

```python
        if isinstance(record, ErrorRecord):
            if (
                record.input_index is not None
                and record.input_index != len(steps)
            ):
                _sequence_error(
                    source,
                    "error input_index must equal the flushed-step count",
                )
            terminal = record
            continue
```

- [ ] **Step 5: Run the complete sequence matrix GREEN**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py -k 'trace_stream'
git diff --check
```

Expected: `34 passed`: six valid traces, exactly 27 malformed rows (`8 + 7 + 5 + 2 + 5`), and the separate guarded-tail traversal regression. `git diff --check` prints nothing and exits `0`.

- [ ] **Step 6: Commit complete sequence validation**

Commit:

```bash
git add src/ssr_env/oracle_protocol.py tests/test_oracle_protocol.py
git commit -m "feat: complete oracle trace validation"
```

---

### Task 21: Preserve descriptor identity in the path convenience API

**Files:**
- Modify: `src/ssr_env/oracle_protocol.py`
- Modify: `tests/test_oracle_protocol.py`

**Interfaces:**
- Consumes: `OracleProtocolError(ValueError)` from Task 1, `OracleRun` from Task 4, and completed `read_oracle_trace_stream(stream: BinaryIO, *, source: str) -> OracleRun` from Task 20; uses standard-library `Path.open("rb")` exactly once.
- Produces: `read_oracle_trace(path: Path) -> OracleRun` as an opening-only wrapper; it opens once and delegates with that descriptor.
- Internal consumers: Tasks 24 and 26 use the path wrapper; this task validates only its descriptor behavior.
- External consumers: `docs/superpowers/plans/2026-07-31-oracle-passive-probe.md`, Tasks 10A–10C deliberately use the stream API and never this convenience wrapper; `docs/superpowers/plans/2026-07-31-oracle-passive-trace-implementation.md`, Task 1 executes this task.

- [ ] **Step 1: Add RED open-failure and named-path replacement tests**

Append exactly to `tests/test_oracle_protocol.py`:

```python
import os

from ssr_env.oracle_protocol import read_oracle_trace


def test_descriptor_stream_ignores_named_path_replacement_after_open(
    tmp_path: Path,
) -> None:
    trace_path = tmp_path / "trace.ndjson"
    replacement_path = tmp_path / "replacement.ndjson"
    trace_path.write_bytes(SUCCESS_TRACE_BYTES)
    replacement_path.write_bytes(b"not-json\n")

    with trace_path.open("rb") as authenticated_stream:
        os.replace(replacement_path, trace_path)
        trace = read_oracle_trace_stream(
            authenticated_stream, source=str(trace_path)
        )

    assert trace.outcome == "success"
    assert trace_path.read_bytes() == b"not-json\n"


def test_path_wrapper_opens_before_delegating(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    trace_path = tmp_path / "trace.ndjson"
    replacement_path = tmp_path / "replacement.ndjson"
    trace_path.write_bytes(SUCCESS_TRACE_BYTES)
    replacement_path.write_bytes(b"not-json\n")
    real_stream_reader = oracle_protocol.read_oracle_trace_stream

    def replace_name_then_read(stream: object, *, source: str) -> OracleRun:
        assert hasattr(stream, "readline")
        os.replace(replacement_path, trace_path)
        return real_stream_reader(stream, source=source)  # type: ignore[arg-type]

    monkeypatch.setattr(
        oracle_protocol, "read_oracle_trace_stream", replace_name_then_read
    )
    trace = oracle_protocol.read_oracle_trace(trace_path)

    assert trace.outcome == "success"
    assert trace_path.read_bytes() == b"not-json\n"


def test_path_wrapper_translates_open_failure(tmp_path: Path) -> None:
    missing = tmp_path / "missing.ndjson"
    with pytest.raises(OracleProtocolError, match="could not open trace") as caught:
        read_oracle_trace(missing)
    assert isinstance(caught.value.__cause__, OSError)
```

- [ ] **Step 2: Run the path-wrapper tests and confirm RED**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py -k 'descriptor_stream or path_wrapper'
```

Expected: collection fails with `ImportError: cannot import name 'read_oracle_trace'`; the stream-only named-replacement case is already GREEN from Task 20 and remains part of the final cohort.

- [ ] **Step 3: Implement the opening-only path wrapper**

Add `Path` to the imports in `src/ssr_env/oracle_protocol.py`:

```python
from pathlib import Path
```

Append exactly:

```python
def read_oracle_trace(path: Path) -> OracleRun:
    source = str(path)
    try:
        stream = path.open("rb")
    except OSError as exc:
        raise OracleProtocolError(
            f"{source}: could not open trace: {exc}"
        ) from exc
    with stream:
        return read_oracle_trace_stream(stream, source=source)
```

- [ ] **Step 4: Run descriptor/path GREEN**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py -k \
  'descriptor_stream or path_wrapper'
git diff --check
```

Expected: `3 passed`; both replacement tests parse the already-open original inode while the named path contains `not-json\n`, and the open failure retains its `OSError` cause; `git diff --check` prints nothing and exits `0`.

- [ ] **Step 5: Commit the path wrapper**

Commit:

```bash
git add src/ssr_env/oracle_protocol.py tests/test_oracle_protocol.py
git commit -m "feat: open oracle traces once"
```

---

### Task 22: Enforce relational shape and input-result flags

**Files:**
- Modify: `src/ssr_env/oracle_protocol.py`
- Modify: `tests/test_oracle_protocol.py`

**Interfaces:**
- Consumes: `EXPECTED_INPUT_COUNT: int` and `OracleProtocolError(ValueError)` from Task 1; `OracleRun`, `EndRecord`, `ErrorRecord`, `InitialRecord`, and `StepRecord` from Task 4; callers normally obtain the run from `read_oracle_trace_stream(stream: BinaryIO, *, source: str) -> OracleRun` in Task 20 or `read_oracle_trace(path: Path) -> OracleRun` in Task 21.
- Produces: `require_passive_success(trace: OracleRun) -> None`.
- Produces: deterministic checks for terminal shape, initial/end counts, indices, input kinds, accepted flags, movement flags, and changed step-0 `raw_save`.
- Internal consumer: Task 23 extends the same function with complete-capture and quiescence relations.
- External consumers: `docs/superpowers/plans/2026-07-31-oracle-passive-probe.md`, Task 10A imports `require_passive_success(trace: OracleRun) -> None`, which Tasks 10C, 11, and 19B call on authenticated stream results; `docs/superpowers/plans/2026-07-31-oracle-passive-trace-implementation.md`, Task 1 executes this task.

- [ ] **Step 1: Add the RED accepted relation and core mutation tests**

Append exactly to `tests/test_oracle_protocol.py`:

```python
from dataclasses import replace

from ssr_env.oracle_protocol import require_passive_success


def _relation_trace() -> OracleRun:
    initial_capture = _expected_capture("initial")
    moved_capture = _expected_capture("moved")
    return OracleRun(
        header=RunHeader(
            run_id=RUN_ID,
            game_assembly_sha256=ASSEMBLY_HASH,
            started_at_utc="2026-07-31T19:09:50.3199100Z",
        ),
        initial=InitialRecord(capture=initial_capture),
        steps=(
            StepRecord(
                input_index=0,
                input="West",
                accepted=True,
                movement_scheduled=True,
                settle_frames=2,
                state_replaced=False,
                capture=moved_capture,
            ),
            StepRecord(
                input_index=1,
                input="North",
                accepted=False,
                movement_scheduled=False,
                settle_frames=2,
                state_replaced=False,
                capture=moved_capture,
            ),
            StepRecord(
                input_index=2,
                input="Undo",
                accepted=True,
                movement_scheduled=False,
                settle_frames=2,
                state_replaced=False,
                capture=initial_capture,
            ),
        ),
        terminal=EndRecord(
            input_count=3,
            finished_at_utc="2026-07-31T19:11:00.0000000Z",
        ),
        outcome="success",
    )


def _replace_step(trace: OracleRun, index: int, step: StepRecord) -> OracleRun:
    steps = list(trace.steps)
    steps[index] = step
    return replace(trace, steps=tuple(steps))


def test_require_passive_success_accepts_exact_relation() -> None:
    assert require_passive_success(_relation_trace()) is None


def test_require_passive_success_rejects_terminal_error() -> None:
    trace = _relation_trace()
    error = ErrorRecord(
        input_index=3,
        input=None,
        code="capture_failed",
        message="game-state capture failed",
        settle_frames=0,
        last_capture=trace.steps[-1].capture,
    )
    with pytest.raises(OracleProtocolError, match="requires an end record"):
        require_passive_success(replace(trace, terminal=error, outcome="error"))


@pytest.mark.parametrize(
    "trace",
    [
        replace(_relation_trace(), steps=_relation_trace().steps[:2]),
        replace(_relation_trace(), initial=None),
        replace(
            _relation_trace(),
            terminal=EndRecord(
                input_count=2,
                finished_at_utc="2026-07-31T19:11:00.0000000Z",
            ),
        ),
        replace(
            _relation_trace(),
            steps=(
                _relation_trace().steps[0],
                replace(_relation_trace().steps[1], input_index=2),
                _relation_trace().steps[2],
            ),
        ),
    ],
    ids=["step-count", "missing-initial", "end-count", "indices"],
)
def test_require_passive_success_rejects_wrong_shape(trace: OracleRun) -> None:
    with pytest.raises(OracleProtocolError):
        require_passive_success(trace)


@pytest.mark.parametrize(
    "changes",
    [
        {"input": "Undo"},
        {"accepted": False},
        {"movement_scheduled": False},
    ],
    ids=["undo", "refused", "no-movement"],
)
def test_require_passive_success_rejects_step_zero_flags(
    changes: dict[str, object],
) -> None:
    trace = _relation_trace()
    changed = replace(trace.steps[0], **changes)
    with pytest.raises(OracleProtocolError):
        require_passive_success(_replace_step(trace, 0, changed))


def test_require_passive_success_rejects_unchanged_step_zero_save() -> None:
    trace = _relation_trace()
    changed = replace(trace.steps[0], capture=trace.initial.capture)
    with pytest.raises(OracleProtocolError, match="raw_save must change"):
        require_passive_success(_replace_step(trace, 0, changed))


@pytest.mark.parametrize(
    "changes",
    [
        {"input": "Undo"},
        {"accepted": True},
        {"movement_scheduled": True},
    ],
    ids=["undo", "accepted", "movement"],
)
def test_require_passive_success_rejects_step_one_flags(
    changes: dict[str, object],
) -> None:
    trace = _relation_trace()
    changed = replace(trace.steps[1], **changes)
    with pytest.raises(OracleProtocolError):
        require_passive_success(_replace_step(trace, 1, changed))


@pytest.mark.parametrize(
    "changes",
    [
        {"input": "East"},
        {"accepted": False},
        {"movement_scheduled": True},
    ],
    ids=["direction", "refused", "movement"],
)
def test_require_passive_success_rejects_step_two_flags(
    changes: dict[str, object],
) -> None:
    trace = _relation_trace()
    changed = replace(trace.steps[2], **changes)
    with pytest.raises(OracleProtocolError):
        require_passive_success(_replace_step(trace, 2, changed))
```

- [ ] **Step 2: Run the core relation tests and confirm RED**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py -k 'require_passive_success'
```

Expected: collection fails with `ImportError: cannot import name 'require_passive_success'`.

- [ ] **Step 3: Implement only shape and input-result relations**

Append exactly to `src/ssr_env/oracle_protocol.py`:

```python
_DIRECTIONS = frozenset({"North", "South", "West", "East"})


def require_passive_success(trace: OracleRun) -> None:
    if trace.outcome != "success" or not isinstance(trace.terminal, EndRecord):
        raise OracleProtocolError("passive success requires an end record")
    if trace.initial is None:
        raise OracleProtocolError("passive success requires an initial record")
    if trace.terminal.input_count != EXPECTED_INPUT_COUNT:
        raise OracleProtocolError("passive success end input_count must be three")
    if len(trace.steps) != EXPECTED_INPUT_COUNT:
        raise OracleProtocolError("passive success requires exactly three steps")
    if tuple(step.input_index for step in trace.steps) != (0, 1, 2):
        raise OracleProtocolError("passive success requires indices 0, 1, 2")

    initial_capture = trace.initial.capture
    step_zero, step_one, step_two = trace.steps

    if step_zero.input not in _DIRECTIONS:
        raise OracleProtocolError("step 0 must be a direction")
    if not step_zero.accepted:
        raise OracleProtocolError("step 0 must be accepted")
    if not step_zero.movement_scheduled:
        raise OracleProtocolError("step 0 must schedule movement")
    if step_zero.capture.raw_save == initial_capture.raw_save:
        raise OracleProtocolError("step 0 raw_save must change")

    if step_one.input not in _DIRECTIONS:
        raise OracleProtocolError("step 1 must be a direction")
    if step_one.accepted:
        raise OracleProtocolError("step 1 must be refused")
    if step_one.movement_scheduled:
        raise OracleProtocolError("step 1 must not schedule movement")

    if step_two.input != "Undo":
        raise OracleProtocolError("step 2 must be Undo")
    if not step_two.accepted:
        raise OracleProtocolError("step 2 Undo must be accepted")
    if step_two.movement_scheduled:
        raise OracleProtocolError("step 2 Undo must not schedule movement")
```

- [ ] **Step 4: Run core-relation GREEN**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py -k 'require_passive_success'
git diff --check
```

Expected: `16 passed`; the exact baseline relation passes and every core shape/input-result mutation rejects; `git diff --check` prints nothing and exits `0`.

- [ ] **Step 5: Commit the core passive relations**

Commit:

```bash
git add src/ssr_env/oracle_protocol.py tests/test_oracle_protocol.py
git commit -m "feat: validate passive input relations"
```

---

### Task 23: Enforce complete-capture, quiescence, and replacement relations

**Files:**
- Modify: `src/ssr_env/oracle_protocol.py`
- Modify: `tests/test_oracle_protocol.py`

**Interfaces:**
- Consumes: `OracleRun`, `OracleCapture`, `InitialRecord`, and `StepRecord` from Task 4 plus `require_passive_success(trace: OracleRun) -> None` from Task 22.
- Produces: the same public function extended with complete twelve-field equality for steps 1/2, zero `movement_count`/`pushes_to_try` for every capture, and false `state_replaced` for every step.
- External consumers: `docs/superpowers/plans/2026-07-31-oracle-passive-probe.md`, Tasks 10C, 11, and 19B consume the completed gate; `docs/superpowers/plans/2026-07-31-oracle-passive-trace-implementation.md`, Task 1 executes this task.

- [ ] **Step 1: Add RED full-envelope, quiescence, and state-replacement tests**

Append exactly to `tests/test_oracle_protocol.py`:

```python
CAPTURE_FIELD_MUTATIONS = {
    "raw_save": "different",
    "state_identity": "18",
    "level": "different",
    "overworld": True,
    "won": True,
    "returning": True,
    "have_ever_cooked_all": True,
    "lost_reason": "different",
    "display_name": "different",
    "sausages_cooked": 1,
    "movement_count": 1,
    "pushes_to_try": 1,
}


@pytest.mark.parametrize("step_index", [1, 2], ids=["step-one", "step-two"])
@pytest.mark.parametrize(
    ("field", "value"),
    list(CAPTURE_FIELD_MUTATIONS.items()),
    ids=list(CAPTURE_FIELD_MUTATIONS),
)
def test_require_passive_success_compares_every_capture_field(
    step_index: int, field: str, value: object
) -> None:
    trace = _relation_trace()
    changed_capture = replace(trace.steps[step_index].capture, **{field: value})
    changed_step = replace(trace.steps[step_index], capture=changed_capture)
    with pytest.raises(OracleProtocolError, match="complete capture"):
        require_passive_success(_replace_step(trace, step_index, changed_step))


@pytest.mark.parametrize("field", ["movement_count", "pushes_to_try"])
def test_require_passive_success_rejects_nonquiescent_initial_pair(
    field: str,
) -> None:
    trace = _relation_trace()
    changed_initial = replace(trace.initial.capture, **{field: 1})
    changed_step_two = replace(trace.steps[2], capture=changed_initial)
    changed = replace(
        trace,
        initial=InitialRecord(capture=changed_initial),
        steps=(trace.steps[0], trace.steps[1], changed_step_two),
    )
    with pytest.raises(OracleProtocolError, match="quiescent"):
        require_passive_success(changed)


@pytest.mark.parametrize("field", ["movement_count", "pushes_to_try"])
def test_require_passive_success_rejects_nonquiescent_moved_pair(
    field: str,
) -> None:
    trace = _relation_trace()
    changed_moved = replace(trace.steps[0].capture, **{field: 1})
    changed = replace(
        trace,
        steps=(
            replace(trace.steps[0], capture=changed_moved),
            replace(trace.steps[1], capture=changed_moved),
            trace.steps[2],
        ),
    )
    with pytest.raises(OracleProtocolError, match="quiescent"):
        require_passive_success(changed)


@pytest.mark.parametrize("step_index", [0, 1, 2])
def test_require_passive_success_defensively_rejects_state_replaced(
    step_index: int,
) -> None:
    trace = _relation_trace()
    changed_step = replace(trace.steps[step_index], state_replaced=True)
    with pytest.raises(OracleProtocolError, match="state_replaced"):
        require_passive_success(_replace_step(trace, step_index, changed_step))
```

- [ ] **Step 2: Run the complete-capture cohort and confirm behavioral RED**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py -k \
  'compares_every_capture_field or nonquiescent or state_replaced'
```

Expected: `31 failed`, each with `DID NOT RAISE`; Task 22 intentionally checks no complete-capture, quiescence, or replacement relation yet.

- [ ] **Step 3: Insert complete equality in numbered relation order**

Insert exactly after the step-1 movement check and before the step-2 input check:

```python
    if step_one.capture != step_zero.capture:
        raise OracleProtocolError(
            "step 1 complete capture must equal step 0 complete capture"
        )
```

Insert exactly after the step-2 movement check at the end of `require_passive_success`:

```python
    if step_two.capture != initial_capture:
        raise OracleProtocolError(
            "step 2 complete capture must equal the initial complete capture"
        )

    captures = (initial_capture,) + tuple(step.capture for step in trace.steps)
    if any(
        capture.movement_count != 0 or capture.pushes_to_try != 0
        for capture in captures
    ):
        raise OracleProtocolError("every accepted capture must be quiescent")
    if any(step.state_replaced for step in trace.steps):
        raise OracleProtocolError("every step state_replaced must be false")
```

- [ ] **Step 4: Run complete relational GREEN**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py -k 'require_passive_success'
git diff --check
```

Expected: `47 passed`; the exact accepted relation passes and every single-field mutation rejects in deterministic numbered order; `git diff --check` prints nothing and exits `0`.

- [ ] **Step 5: Commit the complete passive relations**

Commit:

```bash
git add src/ssr_env/oracle_protocol.py tests/test_oracle_protocol.py
git commit -m "feat: enforce complete passive capture relations"
```

---

### Task 24: Add deterministic direct-main CLI behavior

**Files:**
- Modify: `src/ssr_env/oracle_protocol.py`
- Modify: `tests/test_oracle_protocol.py`

**Interfaces:**
- Consumes: `OracleProtocolError(ValueError)` from Task 1; `OracleRun` and `ErrorRecord` from Task 4; `read_oracle_trace(path: Path) -> OracleRun` from Task 21; `require_passive_success(trace: OracleRun) -> None` from Task 23; standard-library `Path` and `Sequence` for the exact signature.
- Produces: `main(argv: Sequence[str] | None = None) -> int`.
- CLI: `oracle_trace_check.py [--structural-only] TRACE`.
- After argument parsing, successful stdout is one compact sorted-key JSON object plus LF. Protocol failures print `error: <message>` plus LF to stderr.
- Default relational rejection exits `1`; malformed input exits `2`; success exits `0`.
- Standard argparse usage errors raise `SystemExit(2)` and `--help` raises `SystemExit(0)`.
- Summary keys are exactly `error_code`, `outcome`, `record_count`, and `step_count`; `error_code` is null for success.
- Internal consumer: Task 25's executable wrapper imports `main`.
- External plan link: `docs/superpowers/plans/2026-07-31-oracle-passive-trace-implementation.md`, Task 1 executes this task; the passive probe does not invoke this CLI.

- [ ] **Step 1: Add RED direct-main behavior tests**

Append exactly to `tests/test_oracle_protocol.py`:

```python
from ssr_env.oracle_protocol import main


def _write_trace(tmp_path: Path, name: str, payload: bytes) -> Path:
    path = tmp_path / name
    path.write_bytes(payload)
    return path


def test_main_reports_relational_success(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = _write_trace(tmp_path, "success.ndjson", SUCCESS_TRACE_BYTES)
    assert main([str(path)]) == 0
    captured = capsys.readouterr()
    assert captured.out == (
        '{"error_code":null,"outcome":"success",'
        '"record_count":6,"step_count":3}\n'
    )
    assert captured.err == ""


def test_main_structural_only_reports_success(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = _write_trace(tmp_path, "success.ndjson", SUCCESS_TRACE_BYTES)
    assert main(["--structural-only", str(path)]) == 0
    captured = capsys.readouterr()
    assert captured.out == (
        '{"error_code":null,"outcome":"success",'
        '"record_count":6,"step_count":3}\n'
    )
    assert captured.err == ""


def test_main_default_rejects_terminal_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = _write_trace(tmp_path, "error.ndjson", ERROR_TRACE_BYTES)
    assert main([str(path)]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "error: passive success requires an end record\n"


def test_main_structural_only_reports_terminal_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = _write_trace(tmp_path, "error.ndjson", ERROR_TRACE_BYTES)
    assert main(["--structural-only", str(path)]) == 0
    captured = capsys.readouterr()
    assert captured.out == (
        '{"error_code":"settle_timeout","outcome":"error",'
        '"record_count":4,"step_count":1}\n'
    )
    assert captured.err == ""


def test_main_default_rejects_structural_success_with_wrong_relation(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    wrong_step_one = STEP1_LINE.replace(b'"accepted":false', b'"accepted":true')
    payload = _trace_bytes(
        RUN_LINE,
        INITIAL_LINE,
        STEP0_LINE,
        wrong_step_one,
        STEP2_LINE,
        END_LINE,
    )
    path = _write_trace(tmp_path, "wrong-relation.ndjson", payload)
    assert main([str(path)]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "error: step 1 must be refused\n"


def test_main_structural_only_accepts_success_with_wrong_relation(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    wrong_step_one = STEP1_LINE.replace(b'"accepted":false', b'"accepted":true')
    payload = _trace_bytes(
        RUN_LINE,
        INITIAL_LINE,
        STEP0_LINE,
        wrong_step_one,
        STEP2_LINE,
        END_LINE,
    )
    path = _write_trace(tmp_path, "structural-success.ndjson", payload)
    assert main(["--structural-only", str(path)]) == 0
    captured = capsys.readouterr()
    assert captured.out == (
        '{"error_code":null,"outcome":"success",'
        '"record_count":6,"step_count":3}\n'
    )
    assert captured.err == ""


@pytest.mark.parametrize("flags", [[], ["--structural-only"]])
def test_main_reports_malformed_trace_as_exit_two(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    flags: list[str],
) -> None:
    path = _write_trace(tmp_path, "malformed.ndjson", b"{}\n")
    assert main([*flags, str(path)]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == (
        f"error: {path}: line 1: kind must be the first key and use a "
        "schema-v1 value\n"
    )


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (
            SUCCESS_TRACE_BYTES.replace(
                b'"expected_input_count":3',
                b'"expected_input_count":' + b"9" * 100_000,
                1,
            ),
            "integer lexeme exceeds 11 bytes",
        ),
        (
            SUCCESS_TRACE_BYTES.replace(
                b'"state_identity":"17"',
                b'"state_identity":"' + b"9" * 100_000 + b'"',
                1,
            ),
            "state_identity exceeds 11 characters",
        ),
    ],
    ids=["integer", "state-identity"],
)
def test_main_reports_long_decimal_as_protocol_error(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    payload: bytes,
    message: str,
) -> None:
    path = _write_trace(tmp_path, "long-decimal.ndjson", payload)
    assert main([str(path)]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith(f"error: {path}:")
    assert message in captured.err


@pytest.mark.parametrize("argv", [[], ["one.ndjson", "two.ndjson"]])
def test_main_preserves_argparse_usage_errors(
    capsys: pytest.CaptureFixture[str], argv: list[str]
) -> None:
    with pytest.raises(SystemExit) as caught:
        main(argv)
    assert caught.value.code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "usage: oracle_trace_check.py" in captured.err


def test_main_preserves_argparse_help(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as caught:
        main(["--help"])
    assert caught.value.code == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out.startswith("usage: oracle_trace_check.py")
    assert "--structural-only" in captured.out
```

- [ ] **Step 2: Run direct-main tests and confirm RED**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py -k 'main and not wrapper'
```

Expected: collection fails with `ImportError: cannot import name 'main'`.

- [ ] **Step 3: Implement `main` with distinct parse and relation failures**

Add these standard-library imports at the top of `src/ssr_env/oracle_protocol.py`:

```python
import argparse
import json
import sys
```

Append exactly:

```python
def _summary(trace: OracleRun) -> dict[str, object]:
    error_code = (
        trace.terminal.code if isinstance(trace.terminal, ErrorRecord) else None
    )
    record_count = 1 + int(trace.initial is not None) + len(trace.steps) + 1
    return {
        "error_code": error_code,
        "outcome": trace.outcome,
        "record_count": record_count,
        "step_count": len(trace.steps),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="oracle_trace_check.py")
    parser.add_argument(
        "--structural-only",
        action="store_true",
        help="accept either structurally valid terminal shape",
    )
    parser.add_argument("trace", type=Path)
    arguments = parser.parse_args(argv)

    try:
        trace = read_oracle_trace(arguments.trace)
    except OracleProtocolError as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 2

    if not arguments.structural_only:
        try:
            require_passive_success(trace)
        except OracleProtocolError as exc:
            sys.stderr.write(f"error: {exc}\n")
            return 1

    encoded = json.dumps(
        _summary(trace),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    sys.stdout.write(encoded + "\n")
    return 0
```

- [ ] **Step 4: Run direct-main GREEN**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py -k 'main and not wrapper'
git diff --check
```

Expected: `13 passed`; malformed and both long-decimal traces exit `2`, relation failures exit `1`, both successful summary forms match byte for byte, and `git diff --check` prints nothing and exits `0`.

- [ ] **Step 5: Commit the direct CLI**

Commit:

```bash
git add src/ssr_env/oracle_protocol.py tests/test_oracle_protocol.py
git commit -m "feat: add deterministic oracle trace CLI"
```

---

### Task 25: Add the import-only executable wrapper

**Files:**
- Create: `tools/oracle_trace_check.py`
- Modify: `tests/test_oracle_protocol.py`

**Interfaces:**
- Consumes: `main(argv: Sequence[str] | None = None) -> int` from Task 24; uses standard-library `subprocess`, `sys`, and `Path` only in tests.
- Produces: executable `tools/oracle_trace_check.py` with no logic beyond `raise SystemExit(main())`.
- External plan link: `docs/superpowers/plans/2026-07-31-oracle-passive-trace-implementation.md`, Task 1 executes this task; no other plan imports the wrapper as a module.

- [ ] **Step 1: Add RED executable-wrapper tests**

Append exactly to `tests/test_oracle_protocol.py`:

```python
import subprocess
import sys


def test_wrapper_reports_success(tmp_path: Path) -> None:
    path = _write_trace(tmp_path, "success.ndjson", SUCCESS_TRACE_BYTES)
    repository = Path(__file__).resolve().parents[1]
    completed = subprocess.run(
        [sys.executable, str(repository / "tools/oracle_trace_check.py"), str(path)],
        cwd=repository,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    assert completed.stdout == (
        '{"error_code":null,"outcome":"success",'
        '"record_count":6,"step_count":3}\n'
    )
    assert completed.stderr == ""


def test_wrapper_preserves_argparse_exit_two() -> None:
    repository = Path(__file__).resolve().parents[1]
    completed = subprocess.run(
        [sys.executable, str(repository / "tools/oracle_trace_check.py")],
        cwd=repository,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 2
    assert completed.stdout == ""
    assert "usage: oracle_trace_check.py" in completed.stderr
```

- [ ] **Step 2: Run wrapper tests and confirm RED**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py -k 'wrapper_reports or wrapper_preserves'
```

Expected: both tests fail because `tools/oracle_trace_check.py` does not exist.

- [ ] **Step 3: Add the import-only wrapper**

Create `tools/oracle_trace_check.py` with exactly:

```python
#!/usr/bin/env python3
from ssr_env.oracle_protocol import main

if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run wrapper GREEN**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py -k 'wrapper_reports or wrapper_preserves'
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run python -m compileall -q \
  src/ssr_env/oracle_protocol.py tools/oracle_trace_check.py
git diff --check
```

Expected: pytest emits its standard `2 passed` summary and exits `0`; successful `compileall -q` emits no output; `git diff --check` prints nothing and exits `0`.

- [ ] **Step 5: Commit the executable wrapper**

Commit:

```bash
git add src/ssr_env/oracle_protocol.py tools/oracle_trace_check.py \
  tests/test_oracle_protocol.py
git commit -m "feat: add oracle trace validation CLI"
```

---

### Task 26: Freeze cross-language fixtures and verify the protocol track

**Files:**
- Create: `tests/fixtures/oracle_trace/passive-success.ndjson`
- Create: `tests/fixtures/oracle_trace/passive-error.ndjson`
- Modify: `tests/test_oracle_protocol.py`

**Interfaces:**
- Consumes: `ErrorRecord` and `OracleProtocolError` from Tasks 1 and 4; exact encodings accepted by `read_oracle_trace(path: Path) -> OracleRun` from Task 21; `require_passive_success(trace: OracleRun) -> None` from Task 23; and `main(argv: Sequence[str] | None = None) -> int` from Task 24.
- Produces: two synthetic, LF-terminated, compact canonical fixtures consumed by the C# plugin plan.
- The success fixture has six records.
- The error fixture has `run, initial, step, error` and uses `settle_timeout` at input index `1`.
- Neither fixture contains real save data, paths, usernames, or captured game evidence.
- External consumers: `docs/superpowers/plans/2026-07-31-oracle-passive-plugin.md`, Track 2 compares both fixtures byte for byte; `docs/superpowers/plans/2026-07-31-oracle-passive-probe.md`, Task 10A reads `passive-error.ndjson`; `docs/superpowers/plans/2026-07-31-oracle-passive-trace-implementation.md`, Tasks 1–2 order those consumers after this task.

- [ ] **Step 1: Add RED byte-contract and fixture-outcome tests**

Append exactly to `tests/test_oracle_protocol.py`:

```python
FIXTURE_DIRECTORY = Path(__file__).parent / "fixtures/oracle_trace"


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("passive-success.ndjson", SUCCESS_TRACE_BYTES),
        ("passive-error.ndjson", ERROR_TRACE_BYTES),
    ],
)
def test_golden_fixture_bytes_are_exact(name: str, expected: bytes) -> None:
    payload = (FIXTURE_DIRECTORY / name).read_bytes()
    assert payload == expected
    assert payload.endswith(b"\n")
    assert b"\r" not in payload
    assert not payload.startswith(b"\xef\xbb\xbf")


def test_golden_success_fixture_passes_relational_gate() -> None:
    trace = read_oracle_trace(FIXTURE_DIRECTORY / "passive-success.ndjson")
    assert trace.outcome == "success"
    assert len(trace.steps) == 3
    assert require_passive_success(trace) is None


def test_golden_error_fixture_is_structural_only(
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = FIXTURE_DIRECTORY / "passive-error.ndjson"
    trace = read_oracle_trace(path)
    assert trace.outcome == "error"
    assert isinstance(trace.terminal, ErrorRecord)
    assert trace.terminal.code == "settle_timeout"
    with pytest.raises(OracleProtocolError, match="requires an end record"):
        require_passive_success(trace)
    assert main(["--structural-only", str(path)]) == 0
    captured = capsys.readouterr()
    assert captured.out == (
        '{"error_code":"settle_timeout","outcome":"error",'
        '"record_count":4,"step_count":1}\n'
    )
    assert captured.err == ""
```

- [ ] **Step 2: Run fixture tests and confirm RED**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py -k 'golden_fixture or golden_success or golden_error'
```

Expected: `4 failed`; the two byte-contract parameter rows raise `FileNotFoundError`, while the success/error parser tests raise `OracleProtocolError` containing `could not open trace` with `FileNotFoundError` retained as `__cause__`.

- [ ] **Step 3: Add the exact six-line success fixture**

Create `tests/fixtures/oracle_trace/passive-success.ndjson` with exactly these six lines and one LF after the last line:

```json
{"kind":"run","schema_version":1,"run_id":"0123456789abcdef0123456789abcdef","mode":"passive","game_assembly_sha256":"886660b51e0cc6358c8a2cd194d2fc7f2d26303c19dfb307d93b53a2fda1c564","plugin_version":"0.2.0","input_sha256":null,"expected_input_count":3,"started_at_utc":"2026-07-31T19:09:50.3199100Z"}
{"kind":"initial","schema_version":1,"run_id":"0123456789abcdef0123456789abcdef","input_index":null,"capture":{"raw_save":"initial","state_identity":"17","level":"","overworld":false,"won":false,"returning":false,"have_ever_cooked_all":false,"lost_reason":"","display_name":"","sausages_cooked":0,"movement_count":0,"pushes_to_try":0}}
{"kind":"step","schema_version":1,"run_id":"0123456789abcdef0123456789abcdef","input_index":0,"input":"West","accepted":true,"movement_scheduled":true,"settle_frames":2,"state_replaced":false,"capture":{"raw_save":"moved","state_identity":"17","level":"","overworld":false,"won":false,"returning":false,"have_ever_cooked_all":false,"lost_reason":"","display_name":"","sausages_cooked":0,"movement_count":0,"pushes_to_try":0}}
{"kind":"step","schema_version":1,"run_id":"0123456789abcdef0123456789abcdef","input_index":1,"input":"North","accepted":false,"movement_scheduled":false,"settle_frames":2,"state_replaced":false,"capture":{"raw_save":"moved","state_identity":"17","level":"","overworld":false,"won":false,"returning":false,"have_ever_cooked_all":false,"lost_reason":"","display_name":"","sausages_cooked":0,"movement_count":0,"pushes_to_try":0}}
{"kind":"step","schema_version":1,"run_id":"0123456789abcdef0123456789abcdef","input_index":2,"input":"Undo","accepted":true,"movement_scheduled":false,"settle_frames":2,"state_replaced":false,"capture":{"raw_save":"initial","state_identity":"17","level":"","overworld":false,"won":false,"returning":false,"have_ever_cooked_all":false,"lost_reason":"","display_name":"","sausages_cooked":0,"movement_count":0,"pushes_to_try":0}}
{"kind":"end","schema_version":1,"run_id":"0123456789abcdef0123456789abcdef","input_count":3,"finished_at_utc":"2026-07-31T19:11:00.0000000Z"}
```

- [ ] **Step 4: Add the exact four-line error fixture**

Create `tests/fixtures/oracle_trace/passive-error.ndjson` with exactly these four lines and one LF after the last line:

```json
{"kind":"run","schema_version":1,"run_id":"0123456789abcdef0123456789abcdef","mode":"passive","game_assembly_sha256":"886660b51e0cc6358c8a2cd194d2fc7f2d26303c19dfb307d93b53a2fda1c564","plugin_version":"0.2.0","input_sha256":null,"expected_input_count":3,"started_at_utc":"2026-07-31T19:09:50.3199100Z"}
{"kind":"initial","schema_version":1,"run_id":"0123456789abcdef0123456789abcdef","input_index":null,"capture":{"raw_save":"initial","state_identity":"17","level":"","overworld":false,"won":false,"returning":false,"have_ever_cooked_all":false,"lost_reason":"","display_name":"","sausages_cooked":0,"movement_count":0,"pushes_to_try":0}}
{"kind":"step","schema_version":1,"run_id":"0123456789abcdef0123456789abcdef","input_index":0,"input":"West","accepted":true,"movement_scheduled":true,"settle_frames":2,"state_replaced":false,"capture":{"raw_save":"moved","state_identity":"17","level":"","overworld":false,"won":false,"returning":false,"have_ever_cooked_all":false,"lost_reason":"","display_name":"","sausages_cooked":0,"movement_count":0,"pushes_to_try":0}}
{"kind":"error","schema_version":1,"run_id":"0123456789abcdef0123456789abcdef","input_index":1,"input":"North","code":"settle_timeout","message":"input did not settle","settle_frames":600,"last_capture":{"raw_save":"moved","state_identity":"17","level":"","overworld":false,"won":false,"returning":false,"have_ever_cooked_all":false,"lost_reason":"","display_name":"","sausages_cooked":0,"movement_count":0,"pushes_to_try":0}}
```

- [ ] **Step 5: Run fixture GREEN and record the hashes**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py -k 'golden_fixture or golden_success or golden_error'
shasum -a 256 tests/fixtures/oracle_trace/passive-success.ndjson \
  tests/fixtures/oracle_trace/passive-error.ndjson
git diff --check
```

Expected: pytest emits its standard `4 passed` summary and exits `0`; `shasum` prints exactly:

```text
2f65cacacfcef02085ab87c253722d1fa758204e813c9786e0d350a5b864d1db  tests/fixtures/oracle_trace/passive-success.ndjson
eafed2877a6b91e3e5cd988ae9ce44008f59d06abb99631de885a763154c3f6b  tests/fixtures/oracle_trace/passive-error.ndjson
```

`git diff --check` prints nothing and exits `0`. Any hash mismatch is a failed contract, not a value to update during implementation.

- [ ] **Step 6: Run protocol and repository acceptance**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest --collect-only -q \
  tests/test_oracle_protocol.py
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q -rX
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run python -m compileall -q src tools tests
rg -n 'T(BD)|TO(DO)|FI(XME)|<re(place)|implement[ ]later|fill[ ]in' \
  src/ssr_env/oracle_protocol.py tools/oracle_trace_check.py \
  tests/test_oracle_protocol.py tests/fixtures/oracle_trace
git diff --check
```

Expected: freeze the pre-protocol full-suite baseline at exactly `1582 passed, 120 xfailed, 6 xpassed`. This reviewed plan and its implementation must collect exactly `P = 240` protocol test items, so the protocol run has `240 passed` and the full-suite summary has exactly `1822 passed`, `120 xfailed`, `6 xpassed`, zero failures, zero errors, zero skips, and no unexpected result class. If implementation review identifies a necessary additional protocol regression item, stop and revise and re-review this plan plus every downstream `P`/`B`/collection gate before implementation; do not float `P` inside this plan. The `-rX` report must name exactly these six non-strict XPASS node IDs:

```text
tests/test_oracle_boot.py::test_probe_rejects_evidence_directory_substitution_at_final_json_boundary
tests/test_oracle_boot.py::test_write_probe_json_rejects_pending_name_substitution_and_preserves_both_artifacts
tests/test_oracle_boot.py::test_write_probe_json_rejects_post_publish_evidence_path_substitution[return]
tests/test_oracle_boot.py::test_write_probe_json_rejects_post_publish_evidence_path_substitution[raise]
tests/test_oracle_boot.py::test_write_probe_json_rejects_post_publish_fsync_evidence_path_substitution[return]
tests/test_oracle_boot.py::test_write_probe_json_rejects_post_publish_fsync_evidence_path_substitution[raise]
```

No other XPASS is allowed. Successful compilation exits `0` without output; `rg` and `git diff --check` print nothing and exit `1` and `0`, respectively.

- [ ] **Step 7: Commit the verified cross-language contract**

Commit:

```bash
git add tests/fixtures/oracle_trace/passive-success.ndjson \
  tests/fixtures/oracle_trace/passive-error.ndjson \
  tests/test_oracle_protocol.py
git commit -m "test: freeze passive oracle trace contract"
```

---

## Execution handoff

Implement these 26 protocol tasks in order before the C# golden-fixture comparison and before the passive probe's trace-authentication step. With the standing subagent-driven choice, dispatch one fresh implementation subagent per task and perform specification review followed by code-quality review before advancing to the next task. No task in this plan authorizes game launch, installation, config mutation, or live evidence capture.
