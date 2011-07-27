"""Utility classes.

Nothing here should do much that's either game- or UI-specific; it's all fair
game to be used by either side.
"""

from collections import namedtuple

### Dealing with dimensions

class Size(namedtuple('Size', ['rows', 'cols'])):
    """The size of a dungeon floor or other rectangular area."""
    __slots__ = ()

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
