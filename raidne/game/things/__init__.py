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

    ### Player interaction

    def name(self):
        raise NotImplementedError()

    ### Capability introspection

    def can_be_moved_onto(self, actor):
        """Returns a bool, declaring whether the `actor` can move onto this
        thing.
        """
        raise NotImplementedError()


    ### Triggers; like little event hooks

    def trigger_moved_onto(self, actor):
        """Hook to do something-or-other when an `actor` moves onto this thing.

        No useful return value.

        May raise a CollisionError if this isn't allowed, though callers should
        check the above method first.
        """
        pass


### ARCHITECTURE
# TODO Most of these are immutable and can just be singletons; would save a lot
# of rams.  Make it so.
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

class Staircase(Architecture):
    """A passageway to another dungeon floor."""
    def can_be_moved_onto(self, actor):
        return True

class StaircaseDown(Staircase):
    def name(self):
        return "a staircase going down"
class StaircaseUp(Staircase):
    def name(self):
        return "a staircase going up"


### CREATURES
class Creature(Thing):
    def __init__(self):
        super(Creature, self).__init__()

        self.inventory = []

    def can_be_moved_onto(self, actor):
        return False

    # Non-overridden methods
    # XXX inventory management, perhaps?  who controls take/drop?

class Player(Creature):
    pass


### ITEMS
class Item(Thing):
    def can_be_moved_onto(self, actor):
        return True

class Potion(Item):
    def name(self):
        return "potion"
