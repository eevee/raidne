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

class PickUp(object):
    """Actor is picking up an item."""

    def __init__(self, actor, target):
        self.actor = actor
        self.target = target

    def __call__(self, ui_proxy, dungeon):
        actor_tile = dungeon.current_floor.find(self.actor)
        target_tile = dungeon.current_floor.find(self.target)

        assert actor_tile == target_tile

        self.actor.inventory.extend(self.target)
        dungeon.current_floor.remove(self.target)
        ui_proxy.message("Got {0}.".format(self.target.name()))

        #items = tile.items
        #self.player.inventory.extend(items)
        #for item in items:
        #    self.current_floor.remove(item)
        #    ui.message("Got {0}.".format(item.name()))

