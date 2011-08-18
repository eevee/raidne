# encoding: utf8
"""NetHack-style console interface."""

import urwid
from urwid.main_loop import ExitMainLoop
from urwid.util import apply_target_encoding

from raidne.game.dungeon import Dungeon
from raidne.ui.console.rendering import PALETTE_ENTRIES, rendering_for
from raidne.util import Offset, Position

# TODO probably needs to be scrollable -- in which case the SolidFill overlay below can go away
class PlayingFieldWidget(urwid.FixedWidget):
    def __init__(self, dungeon):
        # XXX should this just accept a map, even?
        self.dungeon = dungeon

    def pack(self, size, focus=False):
        # Returns the size of the fixed playing field.
        return self.dungeon.current_floor.size

    def render(self, size, focus=False):
        # Build a view of the architecture
        viewport = []
        attrs = []
        map = self.dungeon.current_floor

        for row in xrange(map.size.rows):
            viewport_chars = []
            attr_row = []
            for col in xrange(map.size.cols):
                topmost_thing = map.tile(Position(row, col)).topmost
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

    def mouse_event(self, *args, **kwargs):
        return True


### Player status, on the right side

class PlayerStatusWidget(urwid.Pile):
    def __init__(self):
        widgets = []

        # TODO use a widget for rendering meters here
        self.health_widget = urwid.Text("xxx")

        widgets.append(('flow', self.health_widget))
        widgets.append(urwid.SolidFill('x'))

        urwid.Pile.__init__(self, widgets)

    def update(self, player):
        self.health_widget.set_text("HP {0}".format(player.health.current))
        # TODO this should detect whether anything changed and call _invalidate
        # on itself only if necessary (or even just the child widgets?)

class MeterWidget(urwid.Text):
    pass


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


class MainWidget(urwid.WidgetWrap):
    """The main game window."""
    # +-------------+-------+
    # |             | stats |
    # |     map     | etc.  |
    # |             |       |
    # +-------------+-------+
    # | messages area       |
    # +---------------------+
    _selectable = True

    def __init__(self, dungeon, proxy):
        self.dungeon = dungeon
        self.interface_proxy = proxy

        self.playing_field = PlayingFieldWidget(dungeon)
        play_area = urwid.Overlay(
            self.playing_field, urwid.SolidFill(' '),
            align='left', width=None,
            valign='top', height=None,
        )

        self.message_pane = urwid.ListBox(
            urwid.SimpleListWalker([])
        )

        self.player_status_pane = PlayerStatusWidget()

        # Arrange into two rows, the top of which is two columns
        top = urwid.Columns(
            [play_area, ('fixed', 40, self.player_status_pane)],
        )
        main_widget = urwid.Pile(
            [top, ('fixed', 10, self.message_pane)],
        )

        # Call the superclass's actual constructor, which accepts a wrappee
        urwid.WidgetWrap.__init__(self, w=main_widget)

    def keypress(self, size, key):
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
        elif key == '.':
            self.dungeon.cmd_wait(self.interface_proxy)
        elif key == ',':
            self.dungeon.cmd_take(self.interface_proxy)
        elif key == 'i':
            # XXX why does this go through the proxy?
            self.interface_proxy.show_inventory()
        else:
            return key

        # TODO: _invalidate() should probably be decided by the dungeon floor.
        # could use some more finely-tuned form of repainting
        self._invalidate()

        # TODO the current idea is that this will just run through everyone who
        # needs to take their turn before the player -- thus returning
        # immediately if the player didn't just do something that consumed a
        # turn.  it'll need to be more complex later for animating, long
        # events, other delays, whatever.
        self.dungeon.do_monster_turns(self.interface_proxy)

        # Update the display
        # TODO this is max inefficient
        self._invalidate()
        self.playing_field._invalidate()

        self.player_status_pane.update(self.dungeon.player)


class RaidneInterface(object):

    def __init__(self):
        self.init_display()

    def init_display(self):
        self.proxy = ConsoleProxy(self)

        self.dungeon = Dungeon()
        # FIXME this is a circular reference.  can urwid objects find their own containers?
        self.main_widget = MainWidget(self.dungeon, self.proxy)

    def run(self):
        self.loop = urwid.MainLoop(self.main_widget)

        # XXX what happens if the terminal doesn't actually support 256 colors?
        # TODO create this screen separately, since multiple loops use it
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
        # XXX move most of this logic to the message pane itelf dood
        walker = self.main_widget.message_pane.body
        if walker:
            last_message = walker[-1]
            last_message.set_text(
                ('message-old', last_message.text))

        walker.append(
            urwid.Text(('message-fresh', message)))
        self.main_widget.message_pane.set_focus(len(walker) - 1)

def main():
    RaidneInterface().run()
