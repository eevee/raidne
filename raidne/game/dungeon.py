"""Core entry point for interacting with the game.

A DungeonLevel represents where the player is, and is what's shown on the
screen.  This is the interface for most of the player's actions, as the player
is always a Thing on the current dungeon level.  A Dungeon is a container for
multiple DungeonLevels, and is responsible for generating, saving, and loading
them as the player progresses.
"""

from raidne.game.things import Wall, Floor, Player
from raidne.util import Offset, Position, Size

class DungeonLevel(object):
    """Represents a single level in the dungeon.  Logic for most object
    interaction is here.
    """
    def __init__(self):
        self.size = Size(10, 10)
        self.architecture = []
        self.things = []

        # Build a little test room...
        self.architecture.append([ Wall() for _ in range(self.size.cols) ])
        for row in range(self.size.rows - 2):
            line = [Wall()]
            for col in range(self.size.cols - 2):
                line.append(Floor())
            line.append(Wall())
            self.architecture.append(line)

        self.architecture.append([ Wall() for _ in range(self.size.cols) ])

        self.architecture[4][4] = Wall()

        # Insert player at starting point
        self.player = Player()
        self.player.position = Position(1, 1)
        self.things.append(self.player)

    def architecture_at(self, position):
        """Returns the Architecture object at the given position."""
        return self.architecture[position.row][position.col]

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

        # If an offset is given, apply it to the thing's current position
        if isinstance(target, Offset):
            target = thing.position.plus_offset(target)

        if target not in self.size:
            return False

        if self.architecture_at(target).move_onto(self, thing):
            thing.position = target
            return True

        return False


class Dungeon(object):
    # TODO
    pass


