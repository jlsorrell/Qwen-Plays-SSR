"""Entering and leaving levels.

This path had no coverage at all until now — it was accidentally deleted during
an edit and the whole suite still passed. These tests close that gap.
"""

from dataclasses import replace

from ssr_env.entity import Entity, pack_cookdata
from ssr_env.mechanics import check_level_exit, check_overworld_entry, level_pose
from ssr_env.state import GameState
from ssr_env.types import Coord, Direction, EntType

ISLAND_POS = Coord(10, 10, 0)
LOCAL = [2, 3, 1]
ENTRY = Coord(12, 13, 1)
FACING = Direction.NORTH

META = {
    "player": {"lvl": {"pos": LOCAL, "direction": int(FACING)}},
    "sausages": {"lvl": [{"pos": [0, 0, 1], "direction": int(Direction.EAST)}]},
}


def world(player_pos=ENTRY, facing=FACING, **kw):
    island = Entity(pos=ISLAND_POS, type=EntType.ISLAND, id=1, dat="lvl")
    player = Entity(pos=player_pos, type=EntType.PLAYER, id=2, direction=facing)
    return GameState(entities=(island, player), **kw)


def test_level_pose_is_island_position_plus_local():
    pos, direction = level_pose(world(), "lvl", META)
    assert pos == ISLAND_POS + Coord(*LOCAL)
    assert direction is FACING


def test_entering_requires_the_right_cell():
    off = world(player_pos=ENTRY + Direction.EAST.delta)
    assert check_overworld_entry(off, META).overworld


def test_entering_requires_the_right_facing():
    """Standing on the entry cell is not enough — the facing must match too."""
    wrong = world(facing=Direction.SOUTH)
    assert check_overworld_entry(wrong, META).overworld


def test_entering_spawns_the_levels_sausages():
    entered = check_overworld_entry(world(), META)
    assert not entered.overworld
    assert entered.pushtargetlevel == "lvl"
    assert len(entered.of_type(EntType.SAUSAGE)) == 1


def test_entering_sets_the_islands_issued_flag():
    """cookdata on an island means 'sausages issued' — see mechanics.md 10.5."""
    entered = check_overworld_entry(world(), META)
    assert entered.by_id(1).cookdata == 1


def test_a_completed_level_is_not_re_entered():
    already = world(completed=frozenset({"lvl"}))
    assert check_overworld_entry(already, META).overworld


def entered_with(faces):
    st = check_overworld_entry(world(), META)
    s = st.of_type(EntType.SAUSAGE)[0]
    return st.replace_entity(replace(s, cookdata=pack_cookdata(faces)))


def test_leaving_requires_the_level_to_be_solved():
    unsolved = entered_with((1, 2, 0, 2))
    assert not check_level_exit(unsolved, META).overworld


def test_leaving_requires_standing_at_the_exit_pose():
    solved = entered_with((1, 2, 1, 2))
    away = solved.replace_entity(
        replace(solved.player, pos=ENTRY + Direction.EAST.delta)
    )
    assert not check_level_exit(away, META).overworld


def test_leaving_requires_the_exit_facing():
    solved = entered_with((1, 2, 1, 2))
    turned = solved.replace_entity(replace(solved.player, direction=Direction.SOUTH))
    assert not check_level_exit(turned, META).overworld


def test_leaving_a_solved_level_returns_to_the_overworld():
    left = check_level_exit(entered_with((1, 2, 1, 2)), META)
    assert left.overworld
    assert left.pushtargetlevel == ""
    assert "lvl" in left.completed


def test_leaving_despawns_the_sausages():
    left = check_level_exit(entered_with((1, 2, 1, 2)), META)
    assert not left.of_type(EntType.SAUSAGE)


def test_the_full_cycle_is_idempotent_once_complete():
    """After leaving, the same pose must not immediately re-enter."""
    left = check_level_exit(entered_with((1, 2, 1, 2)), META)
    assert check_overworld_entry(left, META).overworld


def test_exit_is_a_no_op_in_the_overworld():
    st = world()
    assert check_level_exit(st, META) is st


def entered_with_exit_on_sausage():
    """A level whose exit cell sits directly on top of a sausage."""
    island = Entity(pos=ISLAND_POS, type=EntType.ISLAND, id=1, dat="lvl")
    player = Entity(pos=ENTRY, type=EntType.PLAYER, id=2, direction=FACING)
    carrier = Entity(
        pos=ENTRY + Direction.DOWN.delta,
        type=EntType.SAUSAGE,
        id=3,
        direction=Direction.EAST,
    )
    meta = {
        "player": {"lvl": {"pos": LOCAL, "direction": int(FACING)}},
        "sausages": {"lvl": []},
    }
    return check_overworld_entry(
        GameState(entities=(island, player, carrier)), meta
    ), meta


def test_exit_attaches_to_a_sausage_beneath_it():
    state, _ = entered_with_exit_on_sausage()
    assert state.exit_attachment == 3
    assert state.exit_pos == ENTRY
    assert state.exit_up


def test_exit_does_not_attach_when_nothing_is_beneath():
    entered = check_overworld_entry(world(), META)
    assert entered.exit_attachment is None


def test_sliding_the_carrier_moves_the_exit():
    """A slide carries the exit without flipping it."""
    from ssr_env.mechanics import try_push

    state, _ = entered_with_exit_on_sausage()
    after = try_push(state, state.by_id(3), Direction.EAST)
    assert after.exit_pos == ENTRY + Direction.EAST.delta
    assert after.exit_up
    assert after.exit_dir is FACING


def test_rolling_the_carrier_flips_the_exit():
    """A roll flips exit_up, which switches the exit off until it flips back."""
    from ssr_env.mechanics import try_push

    state, _ = entered_with_exit_on_sausage()
    rolled = try_push(state, state.by_id(3), Direction.NORTH)
    assert rolled.exit_pos == ENTRY + Direction.NORTH.delta
    assert not rolled.exit_up


def test_an_exit_that_is_flipped_off_cannot_be_used():
    """CheckOnLevelExit requires exitUp."""
    state, meta = entered_with_exit_on_sausage()
    flipped = replace(state, exit_up=False)
    assert not check_level_exit(flipped, meta).overworld


def test_the_exit_pose_defaults_to_the_entry_pose():
    entered = check_overworld_entry(world(), META)
    assert entered.exit_pos == ENTRY
    assert entered.exit_dir is FACING
