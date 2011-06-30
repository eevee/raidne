"""Core entry point for interacting with the game.

A DungeonLevel represents where the player is, and is what's shown on the
screen.  This is the interface for most of the player's actions, as the player
is always a Thing on the current dungeon level.  A Dungeon is a container for
multiple DungeonLevels, and is responsible for generating, saving, and loading
them as the player progresses.
"""

from raidne import exceptions
from raidne.game import things
from raidne.game.things import Wall, Floor, StaircaseDown, Player
from raidne.util import Offset, Position, Size

class DungeonTile(object):
    """Represents one grid tile in the dungeon and remembers what exists here.

    Must contain one tile of architecture.  May contain any number of items,
    and up to one creature.
    """
    __slots__ = ('architecture', 'items', 'creature')

    # TODO make a void object to use as the default architecture
    def __init__(self, architecture, items=None, creature=None):
        self.architecture = architecture
        self.items = items or []
        self.creature = creature

    def __iter__(self):
        """Iteration support; yields every Thing on this tile, in z-order from
        top to bottom.
        """
        if self.creature:
            yield self.creature
        for item in self.items:
            yield item
        if self.architecture:
            yield self.architecture

    @property
    def topmost_thing(self):
        """Returns the topmost Thing positioned on this tile."""
        return next(iter(self))

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


class DungeonFloor(object):
    """A single floor in the dungeon.  This is where most of the interaction
    within the game world occurs.
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

        # Make some potions
        for col in range(4, 7):
            pot = things.Potion()
            pot_pos = Position(2, col)
            self[pot_pos].add(pot)
            self.thing_positions[pot] = pot_pos

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


    def move_thing(self, actor, target):
        """Call to move a thing to a new target position.  `target` may be
        either a Position or an Offset.

        This method makes no attempt to validate whether the thing has the
        ability to move this far, or indeed at all -- it's only concerned with
        the arrival of the thing on the new square.  For example, traps will
        activate, and the move will be canceled if there's a wall or monster at
        the target position.

        Returns the new position's tile, or None if the movement is impossible.
        """
        # XXX return something more useful?

        old_position = self.position_of(actor)

        # If an offset is given, apply it to the thing's current position
        if isinstance(target, Offset):
            new_position = old_position.plus_offset(target)
        else:
            new_position = target

        # Check whether the target tile will accept the new thing
        for thing in self[new_position]:
            if not thing.can_be_moved_onto(actor):
                # XXX should this be an exception?
                return

        # Perform the move
        self[old_position].remove(actor)
        self[new_position].add(actor)
        self.thing_positions[actor] = new_position

        # Let the new tile react
        for thing in self[new_position]:
            thing.trigger_moved_onto(actor)

        return self[new_position]


class Dungeon(object):
    """The game world itself.  This is the object the player interacts with
    directly.  It also handles generating individual floors.
    """
    def __init__(self):
        # TODO Need some better idea of how the dungeon should be structured.
        # List of floors isn't really going to cut it.  Floors should probably
        # identify themselves and know their own connections, in which case:
        # does the dungeon itself need to know much?  Also, should floors
        # remember their connections as weakrefs, or just identifiers that this
        # object looks up?
        self.floors = []
        self.floors.append(DungeonFloor())
        self.floors.append(DungeonFloor())

        self.current_floor = self.floors[0]

        # TODO Eventually, all but the current dungeon floors will be stored on
        # disk; no need to keep them going if they're not playing.  When that
        # happens, moving items between floors (including the player's starting
        # position) will have to work by having a Dungeon.moving_things dict,
        # mapping floor identifiers to lists of things waiting to move there.

        # Create the player object and inject it into the first floor
        # XXX grody
        self.player = Player()
        player_pos = Position(1, 1)  # XXX this sucks.  positioning needs a lot of work
        self.current_floor[player_pos].add(self.player)
        self.current_floor.thing_positions[self.player] = player_pos

        # Inject stairs into the first floor too
        stairs = StaircaseDown()
        self.current_floor[Position(1, 2)].architecture = stairs


    ### Player commands.  Each of these methods represents an action the player
    ### has deliberately taken
    # XXX: is passing the entire toplevel interface down here such a good idea?
    def _cmd_move_delta(self, ui, offset):
        new_tile = self.current_floor.move_thing(self.player, offset)
        if new_tile and new_tile.items:
            ui.message(u"You see here: {0}.".format(
                u','.join(item.name() for item in new_tile.items)))

    def cmd_move_up(self, ui):
        self._cmd_move_delta(ui, Offset(drow=-1, dcol=0))
    def cmd_move_down(self, ui):
        self._cmd_move_delta(ui, Offset(drow=+1, dcol=0))
    def cmd_move_left(self, ui):
        self._cmd_move_delta(ui, Offset(drow=0, dcol=-1))
    def cmd_move_right(self, ui):
        self._cmd_move_delta(ui, Offset(drow=0, dcol=+1))

    def cmd_descend(self, ui):
        # XXX is this right
        if not isinstance(self.current_floor[self.current_floor.thing_positions[self.player]].architecture, StaircaseDown):
            ui.message("You can't go down here.")
            return
        del self.current_floor.thing_positions[self.player]
        self.current_floor = self.floors[1]  # XXX uhhhhhh.
        # XXX need to put the player on the corresponding up staircase, or
        # somewhere else if it's blocked or doesn't exist...
        player_pos = Position(1, 1)
        self.current_floor[player_pos].add(self.player)
        self.current_floor.thing_positions[self.player] = player_pos

    def cmd_take(self, ui):
        tile = self.current_floor[self.current_floor.thing_positions[self.player]]
        items = tile.items
        tile.items = []

        self.player.inventory.extend(items)
        for item in items:
            del self.current_floor.thing_positions[item]
            ui.message("Got {0}.".format(item.name()))

