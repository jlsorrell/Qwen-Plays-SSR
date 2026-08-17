from __future__ import annotations

import argparse
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from types import MappingProxyType
from typing import BinaryIO, Iterator, Literal, NoReturn, TypeVar, cast

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

    def finish(self) -> None:
        if self._offset != len(self._payload):
            self._fail("trailing bytes after record")


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
    if cast(str, values["plugin_version"]) != "0.3.0":
        _record_error(reader, "plugin_version must be '0.3.0'")
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

        if decoded.run_id != header.run_id:
            _sequence_error(source, "record run_id does not match the run header")

        record = decoded.record
        if isinstance(record, RunHeader):
            _sequence_error(source, "run record may appear only once")
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
        raise AssertionError("unreachable record type")

    if header is None:
        _sequence_error(source, "trace is empty; first record must be run")
    if terminal is None:
        _sequence_error(source, "trace has no terminal end or error record")
    if isinstance(terminal, EndRecord):
        if initial is None or len(steps) != EXPECTED_INPUT_COUNT:
            _sequence_error(source, "success terminal shape is incomplete")
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
    if step_one.capture != step_zero.capture:
        raise OracleProtocolError(
            "step 1 complete capture must equal step 0 complete capture"
        )

    if step_two.input != "Undo":
        raise OracleProtocolError("step 2 must be Undo")
    if not step_two.accepted:
        raise OracleProtocolError("step 2 Undo must be accepted")
    if step_two.movement_scheduled:
        raise OracleProtocolError("step 2 Undo must not schedule movement")
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
