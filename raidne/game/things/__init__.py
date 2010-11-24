# encoding: utf8
"""Everything that exists within the game.  Items, walls, monsters, whatever.

Various Things are organized into submodules, but you should import them from
this module directly; it contains everything.
"""

### Ultimate base class slash documentation
class Thing(object):
    """Any discrete object that can appear within the dungeon.  Includes walls,
    floors, the player, traps, items, etc.
    """
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
    def move_onto(self, dlvl, thing):
        return True

class Wall(Architecture):
    """Generic cave wall."""
    def move_onto(self, dlvl, thing):
        return False


### CREATURES
class Creature(Thing):
    pass

class Player(Creature):
    pass
