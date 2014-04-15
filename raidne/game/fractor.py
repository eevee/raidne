"""Procedural generation of dungeon maps.  "Fractor" is the agent noun form of
"fractal", where "fractal" is a verb for the purposes of this explanation.
"""
from raidne.game import things
from raidne.game.map import Map
from raidne.util import Position

# TODO fractors should be able to fill a sub-area of a map

class Fractor(object):
    """A procedural generator for a map.  Creates a map, randomly decorates it,
    etc.  The actual logic of map creation is thus kept out of the map proper.

    This is the base class.  It doesn't do much of interest.
    """

    height = 40
    width = 120

    def __init__(self):
        # XXX get the player attributes, options, state, whatever else here
        pass

    def generate(self):
        """Returns a brand spankin' new map."""
        # The general approach here (in theory) follows several steps:
        # 1. Internally, draw rooms and hallways, so collision calculations can
        # be done without scattering architecture objects everywhere.
        # 2. Actually draw those onto the map.  Include variations in floors
        # and walls here.
        # 3. Then fill in other elements, like traps and items and monsters.
        raise NotImplementedError()

class RoomFractor(Fractor):
    """Generates maps containing a simple room."""

    def _scrap_canvas(self, height, width):
        # TODO flesh this out into a real class with abstract shape objects
        # like Room(), Hallway().  probably.  for now it's just a LoL
        return [[None] * width for _ in range(height)]

    def generate(self):
        canvas = self._scrap_canvas(height=80, width=30)
        self.draw_room(canvas, top=0, bottom=79, left=0, right=29)

        # Place the stairs
        canvas[10][10] = things.Thing(type=things.staircase_down)

        map = Map.from_fractor_canvas(canvas)

        # Place an item
        map.put(things.Thing(type=things.potion), Position(2, 3))
        # Or two
        map.put(things.Thing(type=things.newt), Position(2, 9))

        return map

    def draw_room(self, map, top, bottom, left, right):
        """Draw a room with edges at the given offsets."""
        assert top < bottom
        assert left < right
        assert 0 <= top < len(map)
        assert 0 <= bottom < len(map)
        assert 0 <= left < len(map[0])
        assert 0 <= right < len(map[0])

        # Draw the top and bottom walls
        for col in range(left, right + 1):
            map[top][col] = things.Thing(type=things.wall)
            map[bottom][col] = things.Thing(type=things.wall)

        # Draw the left and right walls, and the space inside
        for row in range(top + 1, bottom):
            map[row][left] = things.Thing(type=things.wall)
            map[row][right] = things.Thing(type=things.wall)

            for col in range(left + 1, right):
                map[row][col] = things.Thing(type=things.floor)


class BSPFractor(Fractor):
    """Use binary partitioning to generate a Rogue-like assortment of rooms and
    hallways.
    """

    def generate(self):
        canvas = WorldCanvas(width=self.width, height=self.height)

        midpoint = 30
        subcanvas1, subcanvas2 = canvas.partition_vert(midpoint)

        subcanvas1.add_box(subcanvas1.box.expand(-2))
        subcanvas2.add_box(subcanvas2.box.expand(-2))

        import pprint; pprint.pprint(canvas.__dict__)

        return canvas.to_map()




from collections import namedtuple
class Box(namedtuple('Box', ('x', 'y', 'width', 'height'))):
    __slots__ = ()

    def __contains__(self, other):
        return (
            self.x <= other.x and
            self.y <= other.y and
            self.x + self.width >= other.x + other.width and
            self.y + self.height >= other.y + other.height)

    def overlaps(self, other):
        """Returns true iff the two boxes have any point in common."""
        # These four conditions test whether one edge of the box is beyond the
        # other edge of the other box
        return not (
            other.x > self.x + self.width or
            self.x > other.x + other.width or
            other.y > self.y + self.height or
            self.y > other.y + other.height)
        return (
            0 <= other.x - self.x <= self.width or
            0 <= other.y - self.y <= self.height or
            0 <= self.x - other.x <= other.width or
            0 <= self.y - other.y <= other.height)

    def offset(self, x, y):
        return type(self)(
            self.x + x, self.y + y,
            self.width, self.height)

    def expand(self, amount):
        """Return a box whose edges have expanded or shrunk by the given
        amount.
        """
        assert self.width > amount * 2
        assert self.height > amount * 2

        return type(self)(
            self.x - amount,
            self.y - amount,
            self.width + amount * 2,
            self.height + amount * 2)

    def __iter__(self):
        """Iterate over every coordinate within this box."""
        import itertools
        return itertools.product(
            range(self.x, self.x + self.width),
            range(self.y, self.y + self.height))




class WorldCanvas(object):
    """Life is my canvas, and I am its paintbrush.

    Serves as temporary scratch space for world generation.
    """

    def __init__(self, width, height, offset_x=0, offset_y=0, parent=None):
        self.box = Box(offset_x, offset_y, width, height)

        self.contents = []

        if parent:
            # TODO this should really be a subclass instead of intertwining this logic
            self._parent = parent
        else:
            self._parent = None
            # XXX is this canvas needed, if everything is represented as
            # abstract shapes?
            #self._canvas = [[None] * height for _ in range(width)]

    def subcanvas(self, x, y, width, height):
        assert 0 <= x < self.box.width
        assert 0 <= y < self.box.height
        assert 0 < x + width <= self.box.width
        assert 0 < y + height <= self.box.height

        return type(self)(
            width=width, height=height,
            offset_x=self.box.x + x, offset_y=self.box.y + y,
            parent=self)

    def partition_vert(self, midpoint):
        return (
            self.subcanvas(0, 0, width=midpoint, height=self.box.height),
            self.subcanvas(midpoint, 0, width=self.box.width - midpoint, height=self.box.height),
        )

    def add_box(self, box):
        """Add the given box as a container.  Must not overlap any existing
        boxes.
        """
        if self._parent:
            self._parent.add_box(box)
            return
            self._parent.add_box(box.offset(self.box.x, self.box.y))

        assert box in self.box

        assert all(not box.overlaps(other) for other in self.contents)

        self.contents.append(box)

    def to_map(self):
        map = Map.from_fractor_canvas(self)

        canvas = [[None] * self.box.width for _ in range(self.box.height)]

        wall = things.Thing(type=things.wall)
        for col, row in self.box:
            canvas[row][col] = wall

        floor = things.Thing(type=things.floor)
        for box in self.contents:
            for col, row in box:
                canvas[row][col] = floor

        map._architecture = canvas

        # Place an item
        map.put(things.Thing(type=things.potion), Position(2, 3))
        # Or two
        map.put(things.Thing(type=things.newt), Position(2, 9))

        return map
