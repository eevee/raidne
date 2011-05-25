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

    ### Capability introspection

    def can_be_moved_onto(self, actor):
        """Returns a bool, declaring whether the `actor` can move onto this
        thing.
        """
        raise NotImplementedError


    ### Triggers; like little event hooks

    def trigger_moved_onto(self, actor):
        """Hook to do something-or-other when an `actor` moves onto this thing.

        No useful return value.

        May raise a CollisionError if this isn't allowed, though callers should
        check the above method first.
        """
        pass


### ARCHITECTURE
class Architecture(Thing):
    """Some part of the dungeon layout: a floor, a trap, etc.  Every point on a
    dungeon floor has some kind of architecture.
    """

class Floor(Architecture):
    """Empty generic cave floor."""
    def can_be_moved_onto(self, actor):
        return True

class Wall(Architecture):
    """Generic cave wall."""
    def can_be_moved_onto(self, actor):
        return False


### CREATURES
class Creature(Thing):
    def can_be_moved_onto(self, actor):
        return False

class Player(Creature):
    pass


### ITEMS
class Item(Thing):
    def can_be_moved_onto(self, actor):
        return True

class Potion(Item):
    pass
