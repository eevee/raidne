#!/usr/bin/env python
# encoding: utf8

from collections import namedtuple

import urwid
from urwid.util import apply_target_encoding


Size = namedtuple('Size', ['rows', 'cols'])
Position = namedtuple('Position', ['row', 'col'])
Offset = namedtuple('Offset', ['drow', 'dcol'])

class Architecture(object):
    """Represents some part of the dungeon: a floor, a trap, etc.  Every point
    on a dungeon floor has some kind of architecture.
    """
    def rendering(self):
        # XXX temporary
        pass

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


class Thing(object):
    pass

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

    def move(self, thing, offset):
        """Attempts to move the given thing by the given offset."""
        target = Position(
            thing.position.row + offset.drow,
            thing.position.col + offset.dcol)

        if target.row < 0 or target.col < 0 or \
            target.row > self.size.rows or target.col > self.size.cols:
            return False

        if self.architecture[target.row][target.col].move_onto(self, thing):
            thing.position = target
            return True

        return False


class Dungeon(object):
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
            self.dungeon_level.move(self.dungeon_level.player, Offset(drow=-1, dcol=0))
            self._invalidate()
        elif key == 'down':
            self.dungeon_level.move(self.dungeon_level.player, Offset(drow=+1, dcol=0))
            self._invalidate()
        elif key == 'left':
            self.dungeon_level.move(self.dungeon_level.player, Offset(drow=0, dcol=-1))
            self._invalidate()
        elif key == 'right':
            self.dungeon_level.move(self.dungeon_level.player, Offset(drow=0, dcol=+1))
            self._invalidate()
        elif len(key) == 1:
            self.letter = key
        else:
            return key

    def mouse_event(self, *args, **kwargs):
        return True


play_area = PlayingFieldWidget(DungeonLevel())
loop = urwid.MainLoop(play_area)

loop.run()
