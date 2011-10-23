"""Utility classes.

Nothing here should do much that's either game- or UI-specific; it's all fair
game to be used by either side.
"""

from collections import namedtuple
import itertools

### Dealing with dimensions

class Size(namedtuple('Size', ['rows', 'cols'])):
    """The size of a dungeon floor or other rectangular area."""
    __slots__ = ()

    def iter_positions(self):
        """Iterates over every position within this area."""
        for pair in itertools.product(xrange(self.rows), xrange(self.cols)):
            yield Position(*pair)

    def __contains__(self, position):
        """Checks whether the given `position` falls within the boundaries of
        this rectangle.
        """
        return (
            position.row >= 0 and
            position.col >= 0 and
            position.row < self.rows and
            position.row < self.cols
        )

class Position(namedtuple('Position', ['row', 'col'])):
    """Coordinate of a dungeon floor."""
    __slots__ = ()

    def relative_to(self, position):
        """Compatibility with `Offset.relative_to`."""
        return self

    def __sub__(self, other):
        """Subtract two `Position`s to get an `Offset`."""
        return Offset(
            drow=self.row - other.row,
            dcol=self.col - other.col)

class Offset(namedtuple('Offset', ['drow', 'dcol'])):
    """Distance traveled from a Position."""
    __slots__ = ()

    def relative_to(self, position):
        """Returns a new absolute `Position`, by applying this one to the
        passed `position`.
        """
        return Position(
            self.drow + position.row,
            self.dcol + position.col)

    @property
    def step_length(self):
        """Returns the maximum number of steps it would take to traverse this
        distance.
        """
        return max(abs(self.drow), abs(self.dcol))
