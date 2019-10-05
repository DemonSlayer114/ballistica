"""Defines some standard message objects for use with handlemessage() calls."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import _ba

if TYPE_CHECKING:
    from typing import Sequence
    import ba


@dataclass
class OutOfBoundsMessage:
    """A message telling an object that it is out of bounds.

    Category: Message Classes
    """


@dataclass
class DieMessage:
    """A message telling an object to die.

    Category: Message Classes

    Most ba.Actors respond to this.

    Attributes:

        immediate
            If this is set to True, the actor should disappear immediately.
            This is for 'removing' stuff from the game more so than 'killing'
            it. If False, the actor should die a 'normal' death and can take
            its time with lingering corpses, sound effects, etc.

        how
            The particular reason for death; 'fall', 'impact', 'leftGame', etc.
            This can be examined for scoring or other purposes.

    """
    immediate: bool = False
    how: str = 'generic'


@dataclass
class StandMessage:
    """A message telling an object to move to a position in space.

    Category: Message Classes

    Used when teleporting players to home base, etc.

    Attributes:

        position
            Where to move to.

        angle
            The angle to face (in degrees)
    """
    position: Sequence[float] = (0.0, 0.0, 0.0)
    angle: float = 0.0


@dataclass
class PickUpMessage:
    """Tells an object that it has picked something up.

    Category: Message Classes

    Attributes:

        node
            The ba.Node that is getting picked up.
    """
    node: ba.Node


@dataclass
class DropMessage:
    """Tells an object that it has dropped what it was holding.

    Category: Message Classes
    """


@dataclass
class PickedUpMessage:
    """Tells an object that it has been picked up by something.

    Category: Message Classes

    Attributes:

        node
            The ba.Node doing the picking up.
    """
    node: ba.Node


@dataclass
class DroppedMessage:
    """Tells an object that it has been dropped.

    Category: Message Classes

    Attributes:

        node
            The ba.Node doing the dropping.
    """
    node: ba.Node


@dataclass
class ShouldShatterMessage:
    """Tells an object that it should shatter.

    Category: Message Classes
    """


@dataclass
class ImpactDamageMessage:
    """Tells an object that it has been jarred violently.

    Category: Message Classes

    Attributes:

        intensity
            The intensity of the impact.
    """
    intensity: float


@dataclass
class FreezeMessage:
    """Tells an object to become frozen.

    Category: Message Classes

    As seen in the effects of an ice ba.Bomb.
    """


@dataclass
class ThawMessage:
    """Tells an object to stop being frozen.

    Category: Message Classes
    """


@dataclass(init=False)
class HitMessage:
    """Tells an object it has been hit in some way.

    Category: Message Classes

    This is used by punches, explosions, etc to convey
    their effect to a target.
    """

    def __init__(self,
                 srcnode: ba.Node = None,
                 pos: Sequence[float] = None,
                 velocity: Sequence[float] = None,
                 magnitude: float = 1.0,
                 velocity_magnitude: float = 0.0,
                 radius: float = 1.0,
                 source_player: ba.Player = None,
                 kick_back: float = 1.0,
                 flat_damage: float = None,
                 hit_type: str = 'generic',
                 force_direction: Sequence[float] = None,
                 hit_subtype: str = 'default'):
        """Instantiate a message with given values."""

        self.srcnode = srcnode
        self.pos = pos if pos is not None else _ba.Vec3()
        self.velocity = velocity if velocity is not None else _ba.Vec3()
        self.magnitude = magnitude
        self.velocity_magnitude = velocity_magnitude
        self.radius = radius
        self.source_player = source_player
        self.kick_back = kick_back
        self.flat_damage = flat_damage
        self.hit_type = hit_type
        self.hit_subtype = hit_subtype
        self.force_direction = (force_direction
                                if force_direction is not None else velocity)


@dataclass
class PlayerProfilesChangedMessage:
    """Signals player profiles may have changed and should be reloaded."""
