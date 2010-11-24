# encoding: utf8
"""NetHack-style console interface."""

import urwid
from urwid.main_loop import ExitMainLoop
from urwid.util import apply_target_encoding

from raidne.game.dungeon import DungeonLevel
from raidne.ui.console.rendering import PALETTE_ENTRIES, rendering_for
from raidne.util import Offset

class PlayingFieldWidget(urwid.FixedWidget):
    _selectable = True

    def __init__(self, dungeon_level):
        self.dungeon_level = dungeon_level

    def pack(self, size, focus=False):
        # Returns the size of the fixed playing field.
        return self.dungeon_level.size

    def render(self, size, focus=False):
        # Build a view of the architecture
        viewport = []
        attrs = []
        for (row, arch_row) in enumerate(self.dungeon_level.architecture):
            viewport_chars = []
            attr_row = []
            for (col, arch) in enumerate(arch_row):
                topmost_thing = arch

                # Check things.  XXX make this a separate widget and less kludgy.
                if (row, col) == self.dungeon_level.player.position:
                    topmost_thing = self.dungeon_level.player

                char, palette = rendering_for(topmost_thing)
                # XXX this is getting way inefficient man; surely a better approach
                # TODO pass the rle to TextCanvas
                encoded_char, rle = apply_target_encoding(char)
                viewport_chars.append(encoded_char)
                attr_row.append((palette, len(encoded_char)))

            viewport.append(''.join(viewport_chars))
            attrs.append(attr_row)

        # Needs to be wrapped in CompositeCanvas for overlaying to work
        return urwid.CompositeCanvas(urwid.TextCanvas(viewport, attr=attrs))

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


def main():
    # Setup
    play_area = urwid.Overlay(PlayingFieldWidget(DungeonLevel()), urwid.SolidFill(' '), align='left', width=None, valign='top', height=None)
    loop = urwid.MainLoop(play_area)

    # XXX what happens if the terminal doesn't actually support 256 colors?
    loop.screen.set_terminal_properties(colors=256)
    loop.screen.register_palette(PALETTE_ENTRIES)

    # Game loop
    loop.run()

    # End
    print "Bye!"
