# encoding: utf8
"""NetHack-style console interface."""

import urwid
import urwid.util
from urwid.main_loop import ExitMainLoop
from urwid.util import apply_target_encoding, rle_append_modify, rle_len

from raidne.game import action
from raidne.game.dungeon import Dungeon
from raidne.ui.console.rendering import PALETTE_ENTRIES, rendering_for
from raidne.util import Offset, Position

# TODO probably needs to be scrollable -- in which case the SolidFill overlay below can go away
class PlayingFieldWidget(urwid.BoxWidget):
    def __init__(self, dungeon):
        # XXX should this just accept a map, even?
        self.dungeon = dungeon

    #def pack(self, size, focus=False):
    #    # Returns the size of the fixed playing field.
    #    #return self.dungeon.current_floor.size
    #    return size

    empty_char = u' '

    def _render_padding(self, width, chars, attrs):
        if not width:
            return
        encoded_char = (self.empty_char * width).encode(urwid.util._target_encoding)
        chars.append(encoded_char)
        rle_append_modify(attrs, (None, len(encoded_char)))


    def render(self, size, focus=False):
        # Build a view of the architecture
        viewport = []
        attrs = []
        map = self.dungeon.current_floor

        maxcol, maxrow = size
        top, left = 0, 0

        # TODO actually compute the offset more cleverly here  :)
        # TODO optimize me more??  somehow?

        for screen_row in xrange(maxrow):
            viewport_chars = []
            attr_row = []

            if screen_row < top or screen_row >= map.size.rows + top:
                # Outside the bounds of the map; just show blank space
                self._render_padding(maxcol, chars=viewport_chars, attrs=attr_row)

                viewport.append(''.join(viewport_chars))
                attrs.append(attr_row)
                continue

            # Blank space for the left padding
            self._render_padding(left, chars=viewport_chars, attrs=attr_row)

            for col in xrange(map.size.cols):
                pos = Position(screen_row - top, col)
                char, palette = rendering_for(map.tile(pos).topmost)

                # XXX this is getting way inefficient man; surely a better approach
                encoded_char = char.encode(urwid.util._target_encoding)
                viewport_chars.append(encoded_char)
                rle_append_modify(attr_row, (palette, len(encoded_char)))

            # Blank space for the right padding
            self._render_padding((maxcol - map.size.cols - left),
                chars=viewport_chars, attrs=attr_row)

            viewport.append(''.join(viewport_chars))
            attrs.append(attr_row)

        map_canv = urwid.TextCanvas(viewport, attr=attrs)
        return map_canv

    def mouse_event(self, *args, **kwargs):
        return True


### Player status, on the right side

class PlayerStatusWidget(urwid.Pile):
    def __init__(self, player):
        self._player = player

        widgets = []

        # TODO use a widget for rendering meters here
        self.health_widget = urwid.Text("xxx")

        widgets.append(('flow', self.health_widget))
        widgets.append(urwid.SolidFill('x'))

        urwid.Pile.__init__(self, widgets)

    def update(self):
        # XXX yeah do this for real before committing bro
        self.health_widget.set_text("HP {0}".format(self._player.health.current))
        # TODO this should detect whether anything changed and call _invalidate
        # on itself only if necessary (or even just the child widgets?)

class MeterWidget(urwid.Text):
    pass


### Message pane

class MessagesWidget(urwid.ListBox):
    def __init__(self, dungeon):
        self._dungeon = dungeon
        self.__super.__init__(urwid.SimpleListWalker([]))
        # TODO may want to write a custom list walker class

    def update(self):
        new_messages = self._dungeon.new_messages()
        if not new_messages:
            # Don't nuke messages until there are new ones
            return

        for subwidget in self.body:
            subwidget.set_text(
                ('message-old', subwidget.text))

        for message in new_messages:
            self.body.append(
                urwid.Text(('message-fresh', message)))

        self.set_focus(len(self.body) - 1)


### Inventory

class InventoryWidget(urwid.ListBox):
    signals = ['return']

    def __init__(self, player):
        # Create ourselves a walker
        walker = urwid.SimpleListWalker([])
        urwid.ListBox.__init__(self, walker)

        self.action = None

        self.player = player

    def set_inventory(self, inventory):
        walker = self.body
        walker[:] = []  # Empty in-place

        for item in inventory:
            widget = InventoryItemWidget(item)
            # XXX maybe the map should be part of the item widget?
            wrapped = urwid.AttrMap(widget, 'inventory-default', 'inventory-selected')
            walker.append(wrapped)

    def keypress(self, size, key):
        if key == 'esc':
            self.close()
        elif key == 'enter':
            # TODO...
            self.close(action.UseItem(self.player, self.body[0]._original_widget.item))
        else:
            return urwid.ListBox.keypress(self, size, key)

    def close(self, command=None):
        # TODO a more generic version of this may want to return an item
        # instead
        self._emit('return', command)

class InventoryItemWidget(urwid.Text):
    _selectable = True

    def __init__(self, item):
        self.item = item
        super(InventoryItemWidget, self).__init__(item.name)

    def keypress(self, size, key):
        return key


### Main stuff

class MainWidget(urwid.PopUpLauncher):
    """The main game window."""
    # +-------------+-------+
    # |             | stats |
    # |     map     | etc.  |
    # |             |       |
    # +-------------+-------+
    # | messages area       |
    # +---------------------+
    _selectable = True
    _sizing = 'box'

    def __init__(self, dungeon):
        self.dungeon = dungeon

        self.playing_field = PlayingFieldWidget(dungeon)
        play_area = urwid.Overlay(
            self.playing_field, urwid.SolidFill(' '),
            align='left', width=None,
            valign='top', height=None,
        )
        play_area = self.playing_field

        self.message_pane = MessagesWidget(dungeon)
        self.player_status_pane = PlayerStatusWidget(self.dungeon.player)

        # Arrange into two rows, the top of which is two columns
        top = urwid.Columns([
            play_area,
            ('fixed', 40, self.player_status_pane)
        ])
        main_widget = urwid.Pile([
            top,
            ('fixed', 10, self.message_pane)
        ])

        self.update_widgets()

        self.__super.__init__(main_widget)

    def keypress(self, size, key):
        if key == 'q':
            raise ExitMainLoop

        if key == 'up':
            self._act_in_direction(Offset(drow=-1, dcol=0))
        elif key == 'down':
            self._act_in_direction(Offset(drow=+1, dcol=0))
        elif key == 'left':
            self._act_in_direction(Offset(drow=0, dcol=-1))
        elif key == 'right':
            self._act_in_direction(Offset(drow=0, dcol=+1))
        elif key == '>':
            self.dungeon.player_command(action.Descend(self.dungeon.player, self.dungeon.current_floor.find(self.dungeon.player).architecture))
        elif key == '.':
            pass
        elif key == ',':
            # XXX broken
            self.dungeon.player_command(action.PickUp(self.dungeon.player, self.dungeon.current_floor.find(self.dungeon.player).items[0]))
        elif key == 'i':
            # TODO i don't think this takes a turn, since it isn't really an action
            command = self.open_pop_up()
        else:
            return key

        # TODO the current idea is that this will just run through everyone who
        # needs to take their turn before the player -- thus returning
        # immediately if the player didn't just do something that consumed a
        # turn.  it'll need to be more complex later for animating, long
        # events, other delays, whatever.
        # TODO if that's the case, how do we update between monster turns?
        self.dungeon.do_monster_turns()

        self.update_widgets()

    def _act_in_direction(self, direction):
        """Figure out the right action to perform when the player tries to move
        in the given direction.
        """
        assert direction.step_length == 1
        # TODO this still seems pretty wordy to me.  should dungeon wrap its
        # own current floor?
        # XXX this will explode if the player tries to move off the map
        target_tile = self.dungeon.current_floor.tile(
            direction.relative_to(
                self.dungeon.current_floor.find(self.dungeon.player).position))

        if target_tile.creature:
            command = action.MeleeAttack(self.dungeon.player, target_tile.creature)
        else:
            command = action.Walk(self.dungeon.player, direction)

        return self.dungeon.player_command(command)


    def update_widgets(self):
        # Update the display
        # TODO this is max inefficient
        # TODO: _invalidate() should probably be decided by the dungeon floor.
        # could use some more finely-tuned form of repainting
        self.playing_field._invalidate()

        self.message_pane.update()

        self.player_status_pane.update()

        #self._invalidate()


    def create_pop_up(self):
        inv = self.dungeon.player.inventory
        if not inv:
            # XXX gross
            self.dungeon.message("You aren't carrying anything.")
            return

        widget = InventoryWidget(self.dungeon.player)
        widget.set_inventory(inv)

        def close(widget, command):
            self.close_pop_up()
            if command:
                self.dungeon.player_command(command)
            self.update_widgets()

        urwid.connect_signal(widget, 'return', close)

        return widget

    def get_pop_up_parameters(self):
        return dict(left=1, top=1, overlay_width=20, overlay_height=8)


class RaidneInterface(object):

    def __init__(self):
        self.init_display()

    def init_display(self):
        self.dungeon = Dungeon()
        self.dungeon.message('Welcome to raidne!')
        # FIXME this is a circular reference.  can urwid objects find their own containers?
        self.main_widget = MainWidget(self.dungeon)

    def run(self):
        self.loop = urwid.MainLoop(self.main_widget, pop_ups=True)

        # XXX what happens if the terminal doesn't actually support 256 colors?
        self.loop.screen.set_terminal_properties(colors=256)
        self.loop.screen.register_palette(PALETTE_ENTRIES)

        # Game loop
        self.loop.run()

        # End
        print "Bye!"


def main():
    RaidneInterface().run()
