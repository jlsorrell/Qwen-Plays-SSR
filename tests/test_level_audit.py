import json
from dataclasses import replace

from tools.level_audit import (
    Segment,
    audit,
    format_event,
    format_segment_row,
    segment_to_dict,
)
from ssr_env.diagnostics import EntityDelta
from ssr_env.mechanics import StepResult, UnimplementedMechanic, step


def raising_step(
    global_move: int,
    exc: Exception,
    *,
    refusals: frozenset[int] = frozenset(),
):
    calls = 0

    def injected(state, action, history, masks, level_name, meta):
        nonlocal calls
        calls += 1
        if calls == global_move:
            raise exc
        if calls in refusals:
            return StepResult(state=state, moved=False, reason="injected refusal")
        return step(state, action, history, masks, level_name, meta)

    return injected


def test_first_levelb11_loss_has_an_exact_location():
    segments = audit(limit=21, trace_mode="failures")
    failing = next(segment for segment in segments if segment.level == "levelb11")
    assert failing.lost
    assert failing.lost_at is not None
    assert failing.failure_at == failing.lost_at
    assert failing.events[-1].global_move == failing.lost_at
    assert failing.events[-1].loss


def test_failure_trace_retains_at_most_five_preceding_events():
    segments = audit(limit=21, trace_mode="failures")
    failing = next(segment for segment in segments if segment.level == "levelb11")
    assert 1 <= len(failing.events) <= 6
    assert failing.events == sorted(
        failing.events, key=lambda event: event.input_index
    )


def test_segment_json_uses_only_json_primitives():
    segments = audit(limit=21, trace_mode="failures")
    failing = next(segment for segment in segments if segment.level == "levelb11")
    encoded = json.dumps(segment_to_dict(failing))
    decoded = json.loads(encoded)
    assert decoded["level"] == "levelb11"
    assert decoded["lost_at"] == failing.lost_at


def test_segment_filter_does_not_skip_prior_replay_state():
    unfiltered = audit(limit=21, trace_mode="failures")
    filtered = audit(limit=21, trace_mode="failures", segment_filter="2-3")
    expected = next(segment for segment in unfiltered if segment.name == "2-3")
    actual = next(segment for segment in filtered if segment.name == "2-3")
    assert actual.level == expected.level == "levelb11"
    assert actual.lost_at == expected.lost_at
    assert all(
        not segment.events
        for segment in filtered
        if segment.name != "2-3"
    )


def test_human_trace_includes_both_move_numbering_systems():
    segments = audit(limit=21, trace_mode="failures", segment_filter="2-3")
    failing = next(segment for segment in segments if segment.name == "2-3")
    rendered = format_event(failing.events[-1])
    assert f"global {failing.events[-1].global_move}" in rendered
    assert f"2-3:{failing.events[-1].segment_move}" in rendered
    assert failing.events[-1].input.name in rendered


def test_human_trace_renders_real_levelb11_entity_deltas():
    segments = audit(limit=21, trace_mode="failures", segment_filter="2-3")
    failing = next(segment for segment in segments if segment.name == "2-3")
    by_move = {event.global_move: event for event in failing.events}

    assert (
        "PLAYER#205(pos=[2,-32,-1]->[2,-31,-1])"
        in format_event(by_move[1236])
    )
    assert "PLAYER#205(direction=SOUTH->WEST)" in format_event(by_move[1237])
    assert (
        "SAUSAGE#208(pos=[-1,-33,-1]->[0,-33,-1], rot=0->1, "
        "faces=[0,2,2,0]->[0,3,3,0], status=M->B)"
        in format_event(by_move[1241])
    )


def test_human_trace_uses_explicit_spawn_and_removed_notation():
    segments = audit(limit=21, trace_mode="failures", segment_filter="2-3")
    terminal = next(segment for segment in segments if segment.name == "2-3").events[-1]
    sausage = terminal.changes[-1].after
    assert sausage is not None

    spawned = replace(
        terminal,
        changes=(EntityDelta(sausage.id, None, sausage),),
    )
    removed = replace(
        terminal,
        changes=(EntityDelta(sausage.id, sausage, None),),
    )

    assert "SAUSAGE#208(spawn " in format_event(spawned)
    assert "SAUSAGE#208(removed " in format_event(removed)


def test_unimplemented_exception_retains_failure_context_and_exact_move():
    segments = audit(
        limit=21,
        trace_mode="failures",
        segment_filter="2-3",
        step_fn=raising_step(
            1241,
            UnimplementedMechanic("test mechanic"),
        ),
    )
    failing = next(segment for segment in segments if segment.name == "2-3")

    assert failing.error == "unimplemented: test mechanic"
    assert failing.failure_at == 1241
    assert failing.lost_at is None
    assert 1 <= len(failing.events) <= 6
    assert all(event.changes for event in failing.events[:-1])
    exception = failing.events[-1]
    assert exception.to_dict() == {
        "kind": "exception",
        "input_index": 1240,
        "global_move": 1241,
        "segment": "2-3",
        "segment_index": 36,
        "segment_move": 37,
        "input": "NORTH",
        "error": "unimplemented: test mechanic",
        "changes": [],
    }
    assert "exception=unimplemented: test mechanic" in format_event(exception)
    json.dumps(segment_to_dict(failing))


def test_unexpected_exception_does_not_overwrite_an_earlier_loss():
    segments = audit(
        limit=21,
        trace_mode="failures",
        segment_filter="2-3",
        step_fn=raising_step(1242, RuntimeError("after loss")),
    )
    failing = next(segment for segment in segments if segment.name == "2-3")

    assert failing.lost_at == 1241
    assert failing.failure_at == 1241
    assert failing.error == "RuntimeError: after loss"
    exception = failing.events[-1]
    assert exception.global_move == 1242
    assert exception.segment_move == 38
    assert exception.to_dict()["error"] == "RuntimeError: after loss"
    assert "exception=RuntimeError: after loss" in format_event(exception)


def test_failure_history_ignores_refusals_without_entity_changes():
    segments = audit(
        limit=21,
        trace_mode="failures",
        segment_filter="2-3",
        step_fn=raising_step(
            1241,
            UnimplementedMechanic("after refusals"),
            refusals=frozenset(range(1233, 1241)),
        ),
    )
    failing = next(segment for segment in segments if segment.name == "2-3")

    assert [event.global_move for event in failing.events] == [
        1228,
        1229,
        1230,
        1231,
        1232,
        1241,
    ]
    assert all(event.changes for event in failing.events[:-1])
    assert failing.events[-1].to_dict()["kind"] == "exception"


def test_human_table_displays_stored_entry_and_completion_indices_as_moves():
    segment = Segment(
        name="9-9",
        start=0,
        end=4,
        level="example",
        entered_at=0,
        completed_at=4,
        failure_at=3,
        under_test=True,
    )

    assert format_segment_row(segment).split() == [
        "9-9",
        "example",
        "ok",
        "3",
        "1",
        "5",
        "clean",
    ]


def test_continuous_replay_preserves_the_confirmed_eighteen_level_prefix():
    segments = audit(limit=21)
    under_test = [segment for segment in segments if segment.under_test]
    protected = under_test[:18]
    assert [(segment.name, segment.level) for segment in protected] == [
        ("1-1", "level47"),
        ("1-2", "level56"),
        ("1-3", "level49"),
        ("1-4", "level23"),
        ("1-5", "generated1"),
        ("1-6", "level28"),
        ("1-7", "level26"),
        ("1-8", "level16"),
        ("1-9", "level11"),
        ("1-10", "level24"),
        ("1-11", "level46"),
        ("1-12", "level27"),
        ("1-13", "level4"),
        ("1-14", "level9b8"),
        ("1-15", "level41"),
        ("1-16", "level35"),
        ("2-1", "improv3"),
        ("2-2", "levelb4b"),
    ]
    assert all(segment.status == "ok" for segment in protected)
    assert all(not segment.resynced_before for segment in protected)
    frontier = under_test[18]
    assert frontier.name == "2-3"
    assert frontier.level == "levelb11"
    assert not frontier.resynced_before
