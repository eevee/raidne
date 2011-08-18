# encoding: utf8
"""Everything that exists within the game.  Items, walls, monsters, whatever.

Various Things are organized into submodules, but you should import them from
this module directly; it contains everything.
"""
import random

from raidne.game import actions
from raidne.game.things.bits import Meter

### Ultimate base class slash documentation
class Thing(object):
    """Any discrete object that can appear within the dungeon.  Includes walls,
    floors, the player, traps, items, etc.
    """

    ### Player interaction

    def name(self):
        raise NotImplementedError()

    ### Capability introspection

    def can_be_moved_onto(self, actor):
        """Returns a bool, declaring whether the `actor` can move onto this
        thing.
        """
        raise NotImplementedError()


    ### Triggers; like little event hooks

    def trigger_moved_onto(self, actor):
        """Hook to do something-or-other when an `actor` moves onto this thing.

        No useful return value.

        May raise a CollisionError if this isn't allowed, though callers should
        check the above method first.
        """
        pass


### ARCHITECTURE
# TODO Most of these are immutable and can just be singletons; would save a lot
# of rams.  Make it so.
class Architecture(Thing):
    """Some part of the dungeon layout: a floor, a trap, etc.  Every point on a
    dungeon floor has some kind of architecture.
    """

class Floor(Architecture):
    """Empty generic cave floor."""
    def can_be_moved_onto(self, actor):
        return True

class Wall(Architecture):
    """Generic cave wall."""
    def can_be_moved_onto(self, actor):
        return False

class Staircase(Architecture):
    """A passageway to another dungeon floor."""
    def can_be_moved_onto(self, actor):
        return True

class StaircaseDown(Staircase):
    def name(self):
        return "a staircase going down"
class StaircaseUp(Staircase):
    def name(self):
        return "a staircase going up"


### CREATURES
#Stats = namedtuple('Stats', "str per end cha int agi lck")
class Creature(Thing):
    # XXX these should be controlled by something.
    #     probably depends how stats work, how species plays a part, how they
    #     affect health, etc.
    stats = None
    attack_power = 1

    def __init__(self):
        super(Creature, self).__init__()

        self.inventory = []
        self.health = Meter(1)

    def can_be_moved_onto(self, actor):
        return False

    def name(self):
        return "it"

    # Non-overridden methods
    # XXX inventory management, perhaps?  who controls take/drop?

    def think(self, dungeon, map):
        """Invokes creature AI."""
        # XXX several potential states here later:
        # idle: do nothing
        # patrol: wander around a small area
        # hunt: pathfind player
        # chase: run directly toward player
        # and so on.  you know, FSM stuff.

        # For now, there are no states.  Our AI is HTTP.
        here = map.find(self)
        adjacent_tiles = list(here.adjacent_tiles())

        # And our only target is the player.
        player = dungeon.player
        assert player in map

        # 1. Is the player in range?  If so, attack that asshole!
        # TODO the definition of "in range" and "attack" is pretty fluid, but
        # for now we assume melee and walking one step at a time.  later, this
        # stuff should become "reach" algorithms that can figure things out for
        # us.
        delta = map.distance_between(self, player)
        # TODO if delta in attack_range:...
        if delta.drow**2 + delta.dcol**2 <= 1:
            # XXX move this into the dungeon, dungeon proxy, whatever
            return actions.MeleeAttack(self, player)

        # 2. Is the player visible?  If so, run straight at him like a lunatic.
        # TODO the map is currently just a big room and all, so the player is
        # always visible...
        pass

        # 3. Otherwise, just mill around or something.
        # TODO can_be_moved_onto doesn't really cut it here.  also want to
        # avoid traps and veer towards items, for example.
        # TODO but some traps are good!!  this is insane
        # TODO i don't like the can_be_moved_onto nonsense in the first
        # place to be honest
        possible_tiles = [tile for tile in adjacent_tiles if all(thing.can_be_moved_onto(self) for thing in tile)]
        if possible_tiles:
            return actions.Walk(self, random.choice(possible_tiles).position)

        return None

class Player(Creature):
    def __init__(self):
        super(Player, self).__init__()

        self.health = Meter(10)

    def name(self):
        return "you"

    def act(self):
        """Players don't have AI!  If this gets called something is wrong."""
        # XXX it would be terribly clever if this returned control to the UI event loop
        raise TypeError("Players have no AI; they have real I instead")

class Newt(Creature):
    pass


### ITEMS
class Item(Thing):
    def can_be_moved_onto(self, actor):
        return True

class Potion(Item):
    def name(self):
        return "potion"
