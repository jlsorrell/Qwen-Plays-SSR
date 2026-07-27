from copy import deepcopy
from dataclasses import replace

from ssr_env.diagnostics import EntitySnapshot, entity_deltas, snapshot_dynamic
from ssr_env.entity import Entity, pack_cookdata
from ssr_env.state import GameState
from ssr_env.types import Coord, Direction, EntType


def dynamic_state(*entities: Entity) -> GameState:
    return GameState(entities=entities)


def player(ident: int = 1) -> Entity:
    return Entity(
        pos=Coord(2, 3, 1),
        type=EntType.PLAYER,
        id=ident,
        direction=Direction.NORTH,
    )


def sausage(ident: int = 2) -> Entity:
    return Entity(
        pos=Coord(4, 5, 1),
        type=EntType.SAUSAGE,
        id=ident,
        direction=Direction.EAST,
        cookdata=pack_cookdata((0, 1, 2, 3)),
        rot=1,
        dat="M;grill-a;",
    )


def test_snapshot_contains_stable_dynamic_state():
    snapshot = EntitySnapshot.from_entity(sausage())
    assert snapshot.to_dict() == {
        "id": 2,
        "type": "SAUSAGE",
        "pos": [4, 5, 1],
        "direction": "EAST",
        "rot": 1,
        "faces": [0, 1, 2, 3],
        "stuckto": -1,
        "status": "M",
    }


def test_snapshot_dynamic_excludes_static_entities():
    ground = Entity(pos=Coord(0, 0, 0), type=EntType.GROUND, id=9)
    snapshots = snapshot_dynamic(dynamic_state(player(), sausage(), ground))
    assert set(snapshots) == {1, 2}


def test_unchanged_entities_do_not_produce_deltas():
    state = dynamic_state(player(), sausage())
    assert entity_deltas(state, state) == ()


def test_entity_delta_reports_before_and_after():
    before = dynamic_state(player(), sausage())
    moved = replace(
        sausage(),
        pos=Coord(5, 5, 1),
        direction=Direction.SOUTH,
        rot=0,
        stuckto=1,
    )
    after = dynamic_state(player(), moved)
    deltas = entity_deltas(before, after)
    assert len(deltas) == 1
    assert deltas[0].entity_id == 2
    assert deltas[0].before.pos == Coord(4, 5, 1)
    assert deltas[0].after.pos == Coord(5, 5, 1)


def test_spawn_and_removal_use_none_for_the_absent_side():
    before = dynamic_state(player())
    after = dynamic_state(sausage())
    deltas = entity_deltas(before, after)
    by_id = {delta.entity_id: delta for delta in deltas}
    assert by_id[1].before is not None and by_id[1].after is None
    assert by_id[2].before is None and by_id[2].after is not None


def test_delta_calculation_does_not_mutate_either_state():
    before = dynamic_state(player(), sausage())
    after = dynamic_state(player(), replace(sausage(), pos=Coord(5, 5, 1)))
    expected_before = deepcopy(before)
    expected_after = deepcopy(after)
    entity_deltas(before, after)
    assert before == expected_before
    assert after == expected_after
