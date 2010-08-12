#!/usr/bin/env python
# encoding: utf8

from collections import namedtuple

import urwid
from urwid.main_loop import ExitMainLoop
from urwid.util import apply_target_encoding


### UTILITIES
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
            position.row <= self.rows and
            position.row <= self.cols
        )

class Position(namedtuple('Position', ['row', 'col'])):
    """Coordinate of a dungeon floor."""
    __slots__ = ()

    def plus_offset(self, offset):
        """Returns a new Position shifted by the given Offset."""
        return type(self)(
            self.row + offset.drow,
            self.col + offset.dcol)

class Offset(namedtuple('Offset', ['drow', 'dcol'])):
    """Distance traveled from a Position."""
    __slots__ = ()



class Thing(object):
    """Any discrete object that can appear within the dungeon.  Includes walls,
    floors, the player, traps, items, etc.
    """

    def rendering(self):
        # XXX temporary
        pass

### ARCHITECTURE
class Architecture(Thing):
    """Some part of the dungeon layout: a floor, a trap, etc.  Every point on a
    dungeon floor has some kind of architecture.
    """
    def move_onto(self, dlvl, thing):
        """`thing` is trying to move onto this square!

        Return True if this is okay, False otherwise.
        """
        raise NotImplementedError

class Floor(Architecture):
    """Empty generic cave floor."""
    def rendering(self):
        return u'·'

    def move_onto(self, dlvl, thing):
        return True

class Wall(Architecture):
    """Generic cave wall."""
    def rendering(self):
        return u'▓'

    def move_onto(self, dlvl, thing):
        return False


class Creature(Thing):
    pass

class Player(Creature):
    def rendering(self):
        return u'☺'


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


class PlayingFieldWidget(urwid.BoxWidget):
    _selectable = True

    def __init__(self, dungeon_level):
        self.dungeon_level = dungeon_level

    def render(self, size, focus=False):
        (maxcol, maxrow) = size
        self.last_size = size

        # Build a view of the architecture
        viewport = []
        for (row, arch_row) in enumerate(self.dungeon_level.architecture):
            if row >= maxrow:
                break

            viewport_chars = []
            for (col, arch) in enumerate(arch_row):
                if col >= maxcol:
                    break

                rendering = arch.rendering()

                # Check things.  XXX make this a separate widget and less kludgy.
                if (row, col) == self.dungeon_level.player.position:
                    rendering = self.dungeon_level.player.rendering()

                viewport_chars.append(rendering)

            viewport_line = u''.join(viewport_chars)
            viewport.append(viewport_line)

        # Pad the thing
        # XXX shouldn't be necessary...  overlay this on a blank filler widget
        for row in range(maxrow):
            if row >= len(viewport):
                viewport.append(u'')

            new_line = viewport[row] + u' ' * (maxcol - len(viewport[row]))

            # Handle encoding
            encoded_line, charset = apply_target_encoding(new_line)
            viewport[row] = encoded_line

        return urwid.TextCanvas(viewport)

    def keypress(self, size, key):
        if key == 'up':
            self.dungeon_level.move_thing(self.dungeon_level.player, Offset(drow=-1, dcol=0))
            self._invalidate()
        elif key == 'down':
            self.dungeon_level.move_thing(self.dungeon_level.player, Offset(drow=+1, dcol=0))
            self._invalidate()
        elif key == 'left':
            self.dungeon_level.move_thing(self.dungeon_level.player, Offset(drow=0, dcol=-1))
            self._invalidate()
        elif key == 'right':
            self.dungeon_level.move_thing(self.dungeon_level.player, Offset(drow=0, dcol=+1))
            self._invalidate()
        elif key == 'q':
            raise ExitMainLoop
        else:
            return key

    def mouse_event(self, *args, **kwargs):
        return True


# Setup
play_area = PlayingFieldWidget(DungeonLevel())
loop = urwid.MainLoop(play_area)

# Game loop
loop.run()

# End
print "Bye!"
