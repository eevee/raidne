"""The Dungeon is a container for multiple dungeon floors, and is responsible
for generating, saving, and loading them as the player progresses, as well as
the interaction between the player and the game world.
"""
from raidne import exceptions
from raidne.game import things
from raidne.game.fractor import RoomFractor
from raidne.util import Offset, Position

class Dungeon(object):
    """The game world itself."""
    def __init__(self):
        # TODO Need some better idea of how the dungeon should be structured.
        # List of floors isn't really going to cut it.  Floors should probably
        # identify themselves and know their own connections, in which case:
        # does the dungeon itself need to know much?  Also, should floors
        # remember their connections as weakrefs, or just identifiers that this
        # object looks up?

        fractor = RoomFractor()
        self.floors = []
        self.floors.append(fractor.generate())
        self.floors.append(fractor.generate())

        self.current_floor = self.floors[0]

        # TODO Eventually, all but the current dungeon floors will be stored on
        # disk; no need to keep them going if they're not playing.  When that
        # happens, moving items between floors (including the player's starting
        # position) will have to work by having a Dungeon.moving_things dict,
        # mapping floor identifiers to lists of things waiting to move there.

        # Create the player object and inject it into the first floor
        # XXX grody
        self.player = things.Player()
        self.current_floor.put(self.player, Position(3, 3))

    def do_monster_turns(self, proxy):
        # Find all creatures
        # XXX when real timing is implemented, we'll get a slightly less
        # brute-force alg here that involves a queue of creatures that can go
        # next
        for position in self.current_floor.size.iter_positions():
            tile = self.current_floor.tile(position)
            if not tile.creature:
                continue
            if tile.creature is self.player:
                # XXX perhaps do the player's turn here.  hell we could make
                # this the whole event loop and yield for the player.  8)
                continue
            
            # XXX probably want to pass a dungeon proxy object or something
            action = tile.creature.think(self, self.current_floor)
            if action:
                action(proxy, self)


            # XXX this on the other hand is definitely not right
            if self.player.health.current == 0:
                raise Exception("you died, game over!!")

    ### Player commands.  Each of these methods represents an action the player
    ### has deliberately taken
    # XXX: is passing the entire toplevel interface down here such a good idea?
    def _cmd_move_delta(self, ui, offset):
        try:
            new_tile = self.current_floor.move(self.player, offset)
        except exceptions.CollisionError:
            return

        items = new_tile.items
        if items:
            ui.message(u"You see here: {0}.".format(
                u','.join(item.name() for item in items)))

    def cmd_move_up(self, ui):
        self._cmd_move_delta(ui, Offset(drow=-1, dcol=0))
    def cmd_move_down(self, ui):
        self._cmd_move_delta(ui, Offset(drow=+1, dcol=0))
    def cmd_move_left(self, ui):
        self._cmd_move_delta(ui, Offset(drow=0, dcol=-1))
    def cmd_move_right(self, ui):
        self._cmd_move_delta(ui, Offset(drow=0, dcol=+1))

    def cmd_wait(self, ui):
        pass

    def cmd_descend(self, ui):
        map = self.current_floor
        # XXX is this right?  perhaps objects should instead respond to
        # attempted actions themselves.
        if not isinstance(map.find(self.player).architecture, things.StaircaseDown):
            ui.message("You can't go down here.")
            return

        map.remove(self.player)
        map = self.current_floor = self.floors[1]  # XXX uhhhhhh.
        # XXX need to put the player on the corresponding up staircase, or
        # somewhere else if it's blocked or doesn't exist...
        map.put(self.player, Position(1, 1))

    def cmd_take(self, ui):
        tile = self.current_floor.find(self.player)
        items = tile.items

        self.player.inventory.extend(items)
        for item in items:
            self.current_floor.remove(item)
            ui.message("Got {0}.".format(item.name()))

