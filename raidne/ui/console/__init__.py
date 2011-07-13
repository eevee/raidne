# encoding: utf8
"""NetHack-style console interface."""

import urwid
from urwid.main_loop import ExitMainLoop
from urwid.util import apply_target_encoding

from raidne.game.dungeon import Dungeon
from raidne.ui.console.rendering import PALETTE_ENTRIES, rendering_for
from raidne.util import Offset

# TODO probably needs to be scrollable -- in which case the SolidFill overlay below can go away
class PlayingFieldWidget(urwid.FixedWidget):
    _selectable = True

    def __init__(self, dungeon, interface_proxy):
        self.dungeon = dungeon
        self.interface_proxy = interface_proxy

    def pack(self, size, focus=False):
        # Returns the size of the fixed playing field.
        return self.dungeon.current_floor.size

    def render(self, size, focus=False):
        # Build a view of the architecture
        viewport = []
        attrs = []
        for row in range(self.dungeon.current_floor.size.rows):
            viewport_chars = []
            attr_row = []
            for col in range(self.dungeon.current_floor.size.cols):
                tile = self.dungeon.current_floor[row, col]
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
        # TODO it seems like these should be handled by the interface object.
        # maybe that should become a widget itself and get keypresses from
        # here?  surely something besides a dungeon FLOOR object should be
        # responsible for this.
        if key == 'q':
            raise ExitMainLoop

        if key == 'up':
            self.dungeon.cmd_move_up(self.interface_proxy)
        elif key == 'down':
            self.dungeon.cmd_move_down(self.interface_proxy)
        elif key == 'left':
            self.dungeon.cmd_move_left(self.interface_proxy)
        elif key == 'right':
            self.dungeon.cmd_move_right(self.interface_proxy)
        elif key == '>':
            self.dungeon.cmd_descend(self.interface_proxy)
        elif key == ',':
            self.dungeon.cmd_take(self.interface_proxy)
        elif key == 'i':
            self.interface_proxy.show_inventory()
        else:
            return key

        # TODO: _invalidate() should probably be decided by the dungeon floor.
        # could use some more finely-tuned form of repainting
        self._invalidate()

    def mouse_event(self, *args, **kwargs):
        return True


### Inventory

class InventoryWidget(urwid.ListBox):

    def __init__(self):
        # Create ourselves a walker
        walker = urwid.SimpleListWalker([])
        urwid.ListBox.__init__(self, walker)

    def set_inventory(self, inventory):
        walker = self.body
        walker[:] = []  # Empty in-place

        for item in inventory:
            widget = InventoryItemWidget(item.name())
            # XXX maybe the map should be part of the item widget?
            wrapped = urwid.AttrMap(widget, 'inventory-default', 'inventory-selected')
            walker.append(wrapped)

    def keypress(self, size, key):
        if key == 'esc':
            raise urwid.ExitMainLoop()
        else:
            return urwid.ListBox.keypress(self, size, key)

class InventoryItemWidget(urwid.Text):
    _selectable = True

    def keypress(self, size, key):
        return key


### Main stuff

class ConsoleProxy(object):
    """This is the `ui` object passed to a lot of DungeonFloor methods.  It
    allows game logic to trigger particular behaviors in the UI, while letting
    the UI decide how to actually implement them.
    """

    def __init__(self, interface):
        self.interface = interface

    def message(self, message):
        self.interface.push_message(message)

    def show_inventory(self):
        self.interface.show_inventory()


class RaidneInterface(object):

    def __init__(self):
        self.init_display()

    def init_display(self):
        self.proxy = ConsoleProxy(self)

        ### Main window:
        # +-------------+-------+
        # |             | stats |
        # |     map     | etc.  |
        # |             |       |
        # +-------------+-------+
        # | messages area       |
        # +---------------------+

        self.dungeon = Dungeon()
        # FIXME this is a circular reference.  can urwid objects find their own containers?
        playing_field = PlayingFieldWidget(self.dungeon, interface_proxy=self.proxy)
        play_area = urwid.Overlay(
            playing_field, urwid.SolidFill(' '),
            align='left', width=None,
            valign='top', height=None,
        )

        self.message_pane = urwid.ListBox(
            urwid.SimpleListWalker([])
        )

        self.player_status_pane = urwid.SolidFill('x')
        top = urwid.Columns(
            [play_area, ('fixed', 40, self.player_status_pane)],
        )
        self.main_layer = urwid.Pile(
            [top, ('fixed', 10, self.message_pane)],
        )

    def run(self):
        self.loop = urwid.MainLoop(self.main_layer)

        # XXX what happens if the terminal doesn't actually support 256 colors?
        self.loop.screen.set_terminal_properties(colors=256)
        self.loop.screen.register_palette(PALETTE_ENTRIES)

        # Game loop
        self.push_message('Welcome to raidne!')
        self.loop.run()

        # End
        print "Bye!"

    def show_inventory(self):
        inv = self.dungeon.player.inventory
        if not inv:
            self.push_message("You aren't carrying anything.")
            return

        widget = InventoryWidget()
        widget.set_inventory(inv)

        # Run the inventory dialog within its own little event loop
        urwid.MainLoop(widget, screen=self.loop.screen).run()


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
    RaidneInterface().run()
