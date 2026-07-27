import json

from tools.level_audit import audit, segment_to_dict


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
