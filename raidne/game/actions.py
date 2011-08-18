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

    def __call__(self, ui_proxy, dungeon):
        dungeon.current_floor.move(self.actor, self.direction)
