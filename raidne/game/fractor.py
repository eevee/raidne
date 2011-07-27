"""Procedural generation of dungeon maps.  "Fractor" is the agent noun form of
"fractal", where "fractal" is a verb for the purposes of this explanation.
"""
from raidne.game import things
from raidne.game.map import Map
from raidne.util import Position

class Fractor(object):
    """A procedural generator for a map.  Creates a map, randomly decorates it,
    etc.  The actual logic of map creation is thus kept out of the map proper.

    This is the base class.  It doesn't do much of interest.
    """
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
        return [[None] * width for _ in xrange(height)]

    def generate(self):
        canvas = self._scrap_canvas(height=20, width=30)
        self.draw_room(canvas, top=0, bottom=19, left=0, right=29)

        # Place the stairs
        canvas[10][10] = things.StaircaseDown()

        map = Map.from_fractor_canvas(canvas)

        # Place an item
        map.put(things.Potion(), Position(2, 3))

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
        for col in xrange(left, right + 1):
            map[top][col] = things.Wall()
            map[bottom][col] = things.Wall()

        # Draw the left and right walls, and the space inside
        for row in xrange(top + 1, bottom):
            map[row][left] = things.Wall()
            map[row][right] = things.Wall()

            for col in xrange(left + 1, right):
                map[row][col] = things.Floor()
