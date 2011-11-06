"""Fairly dumb representation of dungeon geometry."""

from collections import defaultdict, namedtuple

import raidne.exceptions as exceptions
from raidne.game import things
from raidne.util import Offset, Position, Size

class Map(object):
    """Geometry of a dungeon floor.  Functions both as structure (architectural
    layout) and a two-dimensional container for things (monsters, items, etc).

    Can't be instantiated directly!  Use a fractor.
    """
    def __init__(self, _internal_call=False):
        if not _internal_call:
            raise TypeError("Can't instantiate Map directly; please use a fractor")

    @classmethod
    def from_fractor_canvas(cls, canvas):
        self = cls(_internal_call=True)
        self.size = Size(rows=canvas.box.height, cols=canvas.box.width)
        #rows=len(canvas), cols=len(canvas[0]))

        # There are three layers of objects on any given tile:
        # - exactly one architecture,
        # - zero or more items, and
        # - zero or one creatures.
        # The latter two are taken care of with two sparse dictionaries and a
        # lot of type-checking.
        self._architecture = canvas
        self._items = defaultdict(list)
        self._critters = dict()

        # TODO assert architecture is populated fully, somewhere

        return self

    def __contains__(self, thing):
        """Tests whether the given thing is on this map.  Note that this only
        counts things actually on the map proper: inventories and containers
        and so forth are not inspected.
        """
        # TODO index or whatever, then swap these impls
        try:
            self.find(thing)
            return True
        except ValueError:
            return False


    def tile(self, position):
        """Returns a little wrapper object representing this spot on the map.
        """
        assert position in self.size
        return Tile(self, position)

    def find(self, thing):
        """Finds the given thing.  Doesn't work on architecture."""
        # TODO index me or whatever
        for position, critter in self._critters.items():
            if thing is critter:
                return self.tile(position)
        for position, thinglist in self._items.items():
            if thing in thinglist:
                return self.tile(position)
        raise ValueError("No such thing on this map")

    def distance_between(self, a, b):
        """Returns some kinda object representing the space between two things.
        """
        # XXX this should return a useful object that can be used for pathing
        # etc later
        tile_a = self.find(a)
        tile_b = self.find(b)

        return tile_b.position - tile_a.position

    def put(self, thing, position):
        """Put the given `thing` somewhere on the map."""
        assert isinstance(position, Position)
        assert position in self.size
        # XXX assert thing not already on the map
        # XXX possibly move the collision stuff here, instead of in move()?
        if thing.isa(things.Creature):
            assert position not in self._critters
            self._critters[position] = thing
        elif thing.isa(things.Item):
            self._items[position].append(thing)
        else:
            raise ValueError("Don't know what that thing is")

    def remove(self, thing):
        position = self.find(thing).position
        if thing.isa(things.Creature):
            assert self._critters[position] is thing
            del self._critters[position]
        elif thing.isa(things.Item):
            self._items[position].remove(thing)
        else:
            raise ValueError("Don't know what that thing is")

    def move(self, actor, place):
        """Moves the given thing somewhere else.  `place` can be a position or
        offset.  If `actor` is already at `place`, nothing happens.

        This is pretty low-level and just cares about the departure and
        arrival.  It doesn't deal with any of the following:
        - whether the thing can move
        - whether the thing is capable of moving to this new position

        It DOES prevent moving to an impossible position, by raising a
        CollisionError.

        Returns the new position.
        """
        # XXX Return something useful?
        # XXX Should this fire triggers on the target tile, or is that the
        # caller's responsibility?
        old_position = self.find(actor).position
        new_position = place.relative_to(old_position)
        assert new_position in self.size
        if old_position == new_position:
            return

        # Perform the move
        self.remove(actor)
        self.put(actor, new_position)

class Tile(namedtuple('Tile', ('map', 'position'))):
    """Transient class representing the contents of a single tile.  Meant for
    mucking about with a single point on the map more easily.
    """
    __slots__ = ()

    def __iter__(self):
        """Iterates over things here, from top to bottom, including the
        architecture at the bottom.
        """
        include_architecture = True

        if self.position in self.map._critters:
            yield self.map._critters[self.position]

        for item in reversed(self.map._items[self.position]):
            yield item

        if include_architecture:
            yield self.map._architecture[self.position.row][self.position.col]

    def __eq__(self, other):
        return self.map == other.map and self.position == other.position

    @property
    def topmost(self):
        """The topmost thing here, including the architecture if this tile is
        empty.  That is, what thing you'd see looking down at this tile from
        above.
        """
        return next(iter(self))

    @property
    def architecture(self):
        """The architecture here."""
        return self.map._architecture[self.position.row][self.position.col]

    @property
    def items(self):
        """Returns the items here, in order from top to bottom."""
        return list(reversed(self.map._items[self.position]))

    @property
    def creature(self):
        """The creature here, or `None`."""
        if self.position in self.map._critters:
            return self.map._critters[self.position]
        return None

    _directions = (
        Offset(0, +1), Offset(0, -1),
        Offset(+1, 0), Offset(-1, 0))
    def adjacent_tiles(self):
        for direction in self._directions:
            position = direction.relative_to(self.position)
            if position in self.map.size:
                yield self.map.tile(position)
