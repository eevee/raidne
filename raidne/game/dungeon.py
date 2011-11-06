"""The Dungeon is a container for multiple dungeon floors, and is responsible
for generating, saving, and loading them as the player progresses, as well as
the interaction between the player and the game world.
"""
from raidne import exceptions
from raidne.game import things
from raidne.game.fractor import BSPFractor, RoomFractor
from raidne.util import Offset, Position

class Dungeon(object):
    """The game world itself."""
    def __init__(self):
        self._message_queue = []

        # TODO Need some better idea of how the dungeon should be structured.
        # List of floors isn't really going to cut it.  Floors should probably
        # identify themselves and know their own connections, in which case:
        # does the dungeon itself need to know much?  Also, should floors
        # remember their connections as weakrefs, or just identifiers that this
        # object looks up?

        fractor = BSPFractor()
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
        self.player = things.Thing(type=things.player)
        self.current_floor.put(self.player, Position(3, 3))

    def do_monster_turns(self):
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

            # XXX probably want to pass a proxy object or something
            action = tile.creature.think(self, self.current_floor)
            if not action:
                # we're done here
                return

            for effect, target in action(self) or []:
                effect(self, action.actor, None, target)

            # XXX this on the other hand is definitely not right
            if self.player.health.current == 0:
                raise Exception("you died, game over!!")

    def player_command(self, action):
        """Call me when the player performs an action."""
        assert action.actor == self.player

        for effect, target in action(self) or []:
            effect(self, action.actor, None, target)

    def message(self, message):
        self._message_queue.append(message)

    def new_messages(self):
        # TODO for saving, it might be nice to remember old messages
        ret = self._message_queue
        self._message_queue = []

        return ret
