import json

from tools.level_audit import audit, format_event, segment_to_dict


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
