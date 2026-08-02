from __future__ import annotations

from collections.abc import Callable

import io
from pathlib import Path
import re

import pytest

from ssr_env.oracle_protocol import (
    EXPECTED_ASSEMBLY_SHA256,
    EXPECTED_INPUT_COUNT,
    MAX_RECORD_BYTES,
    MAX_TRACE_BYTES,
    OracleProtocolError,
    SCHEMA_VERSION,
    _decode_record,
    _read_record_lines,
)
from ssr_env.oracle_protocol import (
    ErrorRecord,
    InitialRecord,
    OracleCapture,
    RunHeader,
    StepRecord,
    _CanonicalJsonReader,
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
    ("payload", "byte_number"),
    [
        (b'"\\/"', None),
        (b'"\\u0061"', None),
        (b'"\\u00AF"', None),
        (b'"\\u0008"', None),
        (b'"\\u000a"', None),
        (b'"\x01"', None),
        (b'"a\\v"', 4),
        (b'"\\ud800"', None),
        (b'"\\udfff"', None),
        (b'"a\xed\xa0\x80"', 3),
    ],
)
def test_canonical_json_rejects_noncanonical_strings(
    payload: bytes, byte_number: int | None
) -> None:
    with pytest.raises(OracleProtocolError) as error:
        _read_token(payload, "read_string")
    if byte_number is not None:
        assert f"byte {byte_number}:" in str(error.value)


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


def test_record_decoder_rejects_null_step_capture_structurally() -> None:
    payload = STEP0_LINE.replace(MOVED_CAPTURE_JSON.encode(), b"null")
    with pytest.raises(OracleProtocolError):
        _decode_record(payload, 3, source="null-step-capture")


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


def test_record_decoder_accepts_valid_end_record() -> None:
    end = _decode_record(END_LINE, 6, source="literal")
    assert end.record == EndRecord(
        input_count=3,
        finished_at_utc="2026-07-31T19:11:00.0000000Z",
    )


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


def test_record_decoder_rejects_incomplete_error_last_capture() -> None:
    payload = ERROR_LINE.replace(MOVED_CAPTURE_JSON.encode(), b"{}")
    with pytest.raises(OracleProtocolError):
        _decode_record(payload, 4, source="incomplete-error-capture")


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
