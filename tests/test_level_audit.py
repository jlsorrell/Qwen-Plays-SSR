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


def test_continuous_replay_preserves_the_confirmed_eighteen_level_prefix():
    segments = audit(limit=21)
    under_test = [segment for segment in segments if segment.under_test]
    solved = [segment for segment in under_test if segment.status == "ok"]
    assert [(segment.name, segment.level) for segment in solved] == [
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
    assert all(not segment.resynced_before for segment in solved)
    frontier = under_test[len(solved)]
    assert frontier.name == "2-3"
    assert frontier.level == "levelb11"
    assert not frontier.resynced_before
