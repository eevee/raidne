from raidne.util import Position

class Damage(object):
    """Some amount of damage to be inflicted."""

    def __init__(self, amount):
        self.amount = amount


class MeleeAttack(object):
    cost = 24  # TODO

    def __init__(self, actor, target):
        self.actor = actor
        self.target = target

    def __call__(self, ui_proxy, dungeon):
        # XXX assert they are both on the floor and within melee distance of each other

        # Calculate attacker's damage
        damage = Damage(self.actor.attack_power)

        # Inform the player that this happened
        ui_proxy.message("{0} attacks {1}!!".format(self.actor.name(), self.target.name()))

        # And inflict!
        self.target.health.modify(- damage.amount)

        # Handle death.
        # XXX this should probably go in the creature's damage handler.
        # XXX we need a real event queue to put this on
        # XXX looks like thing types can't use the python class system.  type needs to be an attr
        if self.target.health.current == 0:
            # XXX meters should probably support bool or something
            ui_proxy.message("{0} dies".format(self.target.name()))
            dungeon.current_floor.remove(self.target)

class Walk(object):
    cost = 24  # TODO

    def __init__(self, actor, direction):
        self.actor = actor
        self.direction = direction

    # XXX: is passing the entire toplevel interface down here such a good idea?
    def __call__(self, ui_proxy, dungeon):
        try:
            new_tile = dungeon.current_floor.move(self.actor, self.direction)
        except exceptions.CollisionError:
            # XXX this shouldn't happen for monsters
            # XXX should "is this possible" be separate from actually doing it?
            return

        # this message needs to fire when the player moves at *all*; how to do
        # this.  hook methods?
        if self.actor.is_player:
            items = new_tile.items
            if items:
                ui_proxy.message(u"You see here: {0}.".format(
                    u','.join(item.name() for item in items)))


class Descend(object):
    # target is a staircase.
    # TODO do more standardized initialization and specifying of targets;
    # eventually these should all inherit from some Event base class
    cost = None  # TODO

    def __init__(self, actor, target):
        # XXX should there even be a target, or should this just use the
        # actor's current position
        self.actor = actor
        self.target = target

    def __call__(self, ui_proxy, dungeon):
        map = dungeon.current_floor
        # XXX this is just all kinds of wrong.
        if self.actor == dungeon.player and not map.find(self.actor).architecture.__class__.__name__ == 'StaircaseDown':
            ui_proxy.message("You can't go down here.")
            return

        map.remove(self.actor)

        # XXX THIS IS DEFINITELY ALL KINDS OF WRONG.  WHERE SHOULD THIS LOGIC GO OMG
        assert self.actor == dungeon.player
        map = dungeon.current_floor = dungeon.floors[1]  # XXX uhhhhhh.
        # XXX need to put the player on the corresponding up staircase, or
        # somewhere else if it's blocked or doesn't exist...
        map.put(self.actor, Position(1, 1))


class PickUp(object):
    """Actor is picking up an item."""

    def __init__(self, actor, target):
        self.actor = actor
        self.target = target

    def __call__(self, ui_proxy, dungeon):
        actor_tile = dungeon.current_floor.find(self.actor)
        target_tile = dungeon.current_floor.find(self.target)

        assert actor_tile == target_tile
        # XXX assert is item, or actually check that the thing responds to being taken
        # XXX assert actor has an inventory

        self.actor.inventory.append(self.target)
        dungeon.current_floor.remove(self.target)
        # TODO this message should specify the actor, obv.
        ui_proxy.message("Got {0}.".format(self.target.name()))

        #items = tile.items
        #self.player.inventory.extend(items)
        #for item in items:
        #    self.current_floor.remove(item)
        #    ui.message("Got {0}.".format(item.name()))

