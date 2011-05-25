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

    def __init__(self, dungeon_level, interface_proxy):
        self.dungeon_level = dungeon_level
        self.interface_proxy = interface_proxy

    def pack(self, size, focus=False):
        # Returns the size of the fixed playing field.
        return self.dungeon_level.size

    def render(self, size, focus=False):
        # Build a view of the architecture
        viewport = []
        attrs = []
        for row in range(self.dungeon_level.size.rows):
            viewport_chars = []
            attr_row = []
            for col in range(self.dungeon_level.size.cols):
                tile = self.dungeon_level[row, col]
                char, palette = rendering_for(tile.topmost_thing)

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
        if key == 'q':
            raise ExitMainLoop

        if key == 'up':
            self.dungeon_level.act_move_up(self.interface_proxy)
        elif key == 'down':
            self.dungeon_level.act_move_down(self.interface_proxy)
        elif key == 'left':
            self.dungeon_level.act_move_left(self.interface_proxy)
        elif key == 'right':
            self.dungeon_level.act_move_right(self.interface_proxy)
        else:
            return key

        # TODO: _invalidate() should probably be decided by the dungeon level.
        # could use some more finely-tuned form of repainting
        self._invalidate()

    def mouse_event(self, *args, **kwargs):
        return True


class ConsoleProxy(object):
    """This is the `ui` object passed to a lot of DungeonLevel methods.  It
    allows game logic to trigger particular behaviors in the UI, while letting
    the UI decide how to actually implement them.
    """

    def __init__(self, interface):
        self.interface = interface

    def message(self, message):
        self.interface.push_message(message)


class RaidneInterface(object):

    def init_display(self):
        # +-------------+-------+
        # |             | stats |
        # |     map     | inv.  |
        # |             |       |
        # +-------------+-------+
        # | messages area       |
        # +---------------------+

        self.proxy = ConsoleProxy(self)

        # FIXME this is a circular reference.  can urwid objects find their own containers?
        playing_field = PlayingFieldWidget(DungeonLevel(), self.proxy)
        play_area = urwid.Overlay(
            playing_field, urwid.SolidFill(' '),
            align='left', width=None,
            valign='top', height=None,
        )

        player_status = urwid.Text("Player status is heeeere.")

        self.message_pane = urwid.ListBox(
            urwid.SimpleListWalker([])
        )

        #play_area = urwid.SolidFill(' ')
        player_status = urwid.SolidFill('x')
        top = urwid.Columns(
            [play_area, ('fixed', 40, player_status)],
        )
        main = urwid.Pile(
            [top, ('fixed', 10, self.message_pane)],
        )



        # TODO I'm not sure the main loop should be inside a thing that calls itself?
        loop = urwid.MainLoop(main)

        # XXX what happens if the terminal doesn't actually support 256 colors?
        loop.screen.set_terminal_properties(colors=256)
        loop.screen.register_palette(PALETTE_ENTRIES)

        # Game loop
        self.push_message('Welcome to raidne!')
        loop.run()

        # End
        print "Bye!"

    def push_message(self, message):
        walker = self.message_pane.body
        if walker:
            last_message = walker[-1]
            last_message.set_text(
                ('message-old', last_message.text))

        walker.append(
            urwid.Text(('message-fresh', message)))
        self.message_pane.set_focus(len(walker) - 1)

def main():
    RaidneInterface().init_display()
