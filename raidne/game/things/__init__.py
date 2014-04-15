# encoding: utf8
"""Everything that exists within the game.  Items, walls, monsters, whatever.

Various Things are organized into submodules, but you should import them from
this module directly; it contains everything.
"""
import random

from raidne.game import action, effect
from raidne.game.things.bits import Meter

class Thing(object):
    """Represents a discrete object that can appear within the dungeon.
    Includes walls, floors, the player, traps, items, etc.
    """

    is_player = False



    def __init__(self, type, **kwargs):
        """Create an object.

        type
            A ThingType object encapsulating this Thing's behavior.
        """
        # TODO finish this change and build a parallel hierarchy of thingtype classes
        assert isinstance(type, ThingType)

        self._type = type

        self._hooks = []

        self.inventory = []
        if type.max_health:
            self.health = Meter(type.max_health)

        self._component_data = {}

    def __conform__(self, iface):
        # z.i method called on an object to ask it to adapt itself to some
        # interface
        # TODO keyerror
        component = self._type.components[iface]
        return component(iface, self)


    def isa(self, thing_type):
        if isinstance(thing_type, type):
            return isinstance(self._type, thing_type)
        else:
            return self._type is thing_type


    ### Properties
    # XXX only some thingtypes have certain properties.  components ahoy?
    # XXX this is where i can do hooks, caching, etc

    @property
    def solid(self):
        return self._type.solid

    @property
    def name(self):
        return self._type.name

    @property
    def attack_power(self):
        return self._type.attack_power

    ### Other ThingType proxies

    def think(self, dungeon, map):
        """Invokes creature AI."""
        # XXX several potential states here later:
        # idle: do nothing
        # patrol: wander around a small area
        # hunt: pathfind player
        # chase: run directly toward player
        # and so on.  you know, FSM stuff.

        # For now, there are no states.  Our AI is HTTP.
        here = map.find(self)
        adjacent_tiles = list(here.adjacent_tiles())

        # And our only target is the player.
        player = dungeon.player
        assert player in map

        # 1. Is the player in range?  If so, attack that asshole!
        # TODO the definition of "in range" and "attack" is pretty fluid, but
        # for now we assume melee and walking one step at a time.  later, this
        # stuff should become "reach" algorithms that can figure things out for
        # us.
        delta = map.distance_between(self, player)
        # TODO if delta in attack_range:...
        if delta.drow**2 + delta.dcol**2 <= 1:
            # XXX move this into the dungeon, whatever
            return action.MeleeAttack(self, player)

        # 2. Is the player visible?  If so, run straight at him like a lunatic.
        # TODO the map is currently just a big room and all, so the player is
        # always visible...
        pass

        # 3. Otherwise, just mill around or something.
        # TODO solid doesn't really cut it here.  also want to
        # avoid traps and veer towards items, for example.
        # TODO but some traps are good!!  this is insane
        possible_tiles = [tile for tile in adjacent_tiles if not any(thing.solid for thing in tile)]
        if possible_tiles:
            return action.Walk(self, random.choice(possible_tiles).position)

        return None


class ThingType:
    """Contains behavior for a particular type of Thing."""
    solid = False
    max_health = 0
    name = "it"

    def __init__(self, *components, solid=False, max_health=None, name=None):
        if solid:
            self.solid = solid
        if max_health:
            self.max_health = max_health
        if name:
            self.name = name

        self.components = {}
        for component in components:
            for iface in zi.implementedBy(component):
                if iface is IComponent:
                    continue
                if iface in self.components:
                    raise TypeError(
                        "Got two components for the same interface "
                        "({!r}): {!r} and {!r}"
                        .format(iface, self.components[iface], component))
                self.components[iface] = component

    def __call__(self, *args, **kwargs):
        return Thing(self, *args, **kwargs)


    # TODO doc me bro

### ARCHITECTURE
# TODO Most of these are immutable and can just be singletons; would save a lot
# of rams.  Make it so.
class Architecture(ThingType):
    """Some part of the dungeon layout: a floor, a trap, etc.  Every point on a
    dungeon floor has some kind of architecture.
    """

floor = Architecture()
wall = Architecture(solid=True)
staircase_up = Architecture()
staircase_down = Architecture()
trap = Architecture()






### CREATURES
#Stats = namedtuple('Stats', "str per end cha int agi lck")
class Creature(ThingType):
    # XXX these should be controlled by something.
    #     probably depends how stats work, how species plays a part, how they
    #     affect health, etc.
    stats = None
    attack_power = 1
    name = "it"

class Player(Creature):
    is_player = True

    def act(self):
        """Players don't have AI!  If this gets called something is wrong."""
        # XXX it would be terribly clever if this returned control to the UI event loop
        raise TypeError("Players have no AI; they have real I instead")

newt = Creature(max_health=1, name="newt")
player = Creature(max_health=10, name="you")


### ITEMS
class Item(ThingType): pass




import zope.interface as zi


class IComponent(zi.Interface):
    pass


@zi.implementer(IComponent)
class Component:
    def __init__(self, iface, entity):
        self.iface = iface
        self.entity = entity

    def __getattr__(self, key):
        # TODO keyerror?  or let it raise?
        attr = self.iface[key]
        if isinstance(attr, zi.interface.Method):
            raise AttributeError("missing method??")
        elif isinstance(attr, zi.Attribute):
            return self.entity._component_data[attr]
        else:
            # TODO ???  can this happen.  also are there other Attributes
            raise AttributeError("wat")


class IUsable(IComponent):
    def use():
        pass


@zi.implementer(IUsable)
class UsablePotion(Component):
    def use(self):
        return effect.Heal()

potion = Item(UsablePotion, name="potion")
