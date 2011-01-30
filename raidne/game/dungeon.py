"""Core entry point for interacting with the game.

A DungeonLevel represents where the player is, and is what's shown on the
screen.  This is the interface for most of the player's actions, as the player
is always a Thing on the current dungeon level.  A Dungeon is a container for
multiple DungeonLevels, and is responsible for generating, saving, and loading
them as the player progresses.
"""

from raidne.game import things
from raidne.game.things import Wall, Floor, Player
from raidne.util import Offset, Position, Size

class DungeonTile(object):
    """Represents one grid tile in the dungeon and remembers what exists here.

    Must contain one tile of architecture.  May contain any number of items,
    and up to one creature.
    """
    __slots__ = ('architecture', 'items', 'creature')

    # TODO make a void object to use as the default architecture
    def __init__(self, architecture, items=[], creature=None):
        self.architecture = architecture
        self.items = items
        self.creature = creature

    def add(self, thing):
        if isinstance(thing, things.Creature):
            if self.creature:
                # XXX need a new exception hierarchy...
                raise TypeError("Can't have multiple creatures in one tile")
            self.creature = thing
        else:
            self.items.append(thing)

    def remove(self, thing):
        if thing is self.creature:
            self.creature = None
        else:
            # Throws KeyError if thing isn't here
            self.items.remove(thing)

    @property
    def topmost_thing(self):
        """Returns the topmost Thing positioned on this tile."""
        if self.creature:
            return self.creature
        elif self.items:
            return self.items[-1]
        else:
            return self.architecture


class DungeonLevel(object):
    """Represents a single level in the dungeon.  Logic for most object
    interaction is here.
    """
    def __init__(self):
        self.size = Size(10, 10)
        self.tiles = [
            [DungeonTile(Wall()) for col in xrange(self.size.cols)]
            for row in xrange(self.size.rows)
        ]
        self.thing_positions = {}

        # Build a little test room...
        for row in range(1, self.size.rows - 1):
            for col in range(1, self.size.cols - 1):
                if row == col == 4:
                    continue
                self.tiles[row][col].architecture = Floor()

        # Insert player at starting point
        self.player = Player()
        player_pos = Position(1, 1)
        self[player_pos].add(self.player)
        self.thing_positions[self.player] = player_pos

    # n.b.: There's deliberately no __setitem__, as the tile at any given
    # position has no reason to ever be overwritten.
    def __getitem__(self, slice):
        try:
            row, col = slice
            return self.tiles[row][col]
        except (ValueError, TypeError):
            raise KeyError("DungeonLevel keys must be Position objects or tuples")

    def enumerate(self):
        """Iterates over every possible Position within this level."""
        for row in self.size.rows:
            for col in self.size.cols:
                yield Position(row, col)

    def position_of(self, thing):
        """Returns the position of the given Thing, which must exist on this
        dungeon level.
        """
        return self.thing_positions[thing]


    def move_thing(self, thing, target):
        """Call to move a thing to a new target position.  `target` may be
        either a Position or an Offset.

        This method makes no attempt to validate whether the thing has the
        ability to move this far, or indeed at all -- it's only concerned with
        the arrival of the thing on the new square.  For example, traps will
        activate, and the move will be canceled if there's a wall or monster at
        the target position.

        Returns True if the thing actually moved; False otherwise.
        """
        # XXX return something more useful?

        old_position = self.position_of(thing)

        # If an offset is given, apply it to the thing's current position
        if isinstance(target, Offset):
            new_position = old_position.plus_offset(target)
        else:
            new_position = target

        if self[new_position].architecture.move_onto(self, thing):
            self[old_position].remove(thing)
            self[new_position].add(thing)
            self.thing_positions[thing] = new_position
            return True

        return False


class Dungeon(object):
    # TODO
    pass


